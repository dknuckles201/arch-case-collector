"""Phase 5 active research planning.

The planner proposes work only. It never mutates cases, evidence, assets, or
resolution fields; a human must approve any follow-up search and evidence
acceptance.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DRAWING_TYPES = {
    "site_plan",
    "floor_plan",
    "section",
    "elevation",
    "detail",
    "axonometric",
}

TYPE_LABELS = {
    "high_relevance_low_evidence": "高相关但证据不足",
    "missing_key_drawings": "缺关键图纸",
    "syndicated_only": "只有转载来源",
    "field_conflict": "字段冲突未解决",
    "similar_incomplete": "相似但资料不足",
}

TYPE_ORDER = tuple(TYPE_LABELS)

DEFAULT_QUERY_BUDGET = {
    "max_queries": 40,
    "max_fetches": 24,
    "max_review_minutes": 180,
    "shares": {
        "high_relevance_low_evidence": 0.25,
        "missing_key_drawings": 0.25,
        "syndicated_only": 0.15,
        "field_conflict": 0.15,
        "similar_incomplete": 0.20,
    },
}


def _number(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _first(mapping: dict[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in mapping and mapping[name] is not None:
            return mapping[name]
    return default


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "verified", "accepted"}


def _tokens(value: Any) -> list[str]:
    text = str(value or "").lower()
    return re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", text)


def _text(record: dict[str, Any], *keys: str) -> str:
    values: list[str] = []
    for key in keys:
        value = record.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        elif isinstance(value, dict):
            values.extend(str(item) for item in value.values())
        elif value is not None:
            values.append(str(value))
    return " ".join(values)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: expected JSON object")
        rows.append(value)
    return rows


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_optional(batch: Path, *names: str) -> list[dict[str, Any]]:
    for name in names:
        path = batch / name
        if path.suffix == ".jsonl":
            rows = read_jsonl(path)
            if rows:
                return rows
        elif path.exists():
            value = read_json(path, [])
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                for key in ("items", "rows", "records", "gaps", "assets", "rankings"):
                    if isinstance(value.get(key), list):
                        return [item for item in value[key] if isinstance(item, dict)]
    return []


def load_provenance(batch: Path) -> list[dict[str, Any]]:
    """Flatten common node/edge provenance graphs into case-scoped sources."""
    path = batch / "provenance_graph.json"
    graph = read_json(path, None)
    if not isinstance(graph, dict):
        return load_optional(batch, "provenance.jsonl")
    nodes = [row for row in graph.get("nodes", []) if isinstance(row, dict)]
    edges = [row for row in graph.get("edges", []) if isinstance(row, dict)]
    by_id = {str(_first(row, "id", "node_id", default="")): row for row in nodes}
    flattened = list(nodes)
    for edge in edges:
        left = by_id.get(str(_first(edge, "source", "from", default="")), {})
        right = by_id.get(str(_first(edge, "target", "to", default="")), {})
        left_type = str(_first(left, "type", "node_type", default="")).lower()
        right_type = str(_first(right, "type", "node_type", default="")).lower()
        if left_type == "case" and right_type == "source":
            case_node, source_node = left, right
        elif right_type == "case" and left_type == "source":
            case_node, source_node = right, left
        elif edge.get("case_id") and edge.get("source_id"):
            case_node = {"id": edge["case_id"]}
            source_node = {"id": edge["source_id"], **edge}
        else:
            continue
        flattened.append({**source_node, "case_id": _first(case_node, "case_id", "id", default="")})
    return flattened


def _case_id(row: dict[str, Any]) -> str:
    return str(_first(row, "case_id", "id", "case", "project_id", default="unknown"))


def _case_name(row: dict[str, Any], cases: dict[str, dict[str, Any]]) -> str:
    return str(_first(row, "case_name", "name", "title", default=cases.get(_case_id(row), {}).get("name", _case_id(row))))


def _ranking_map(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {_case_id(row): row for row in rows if _case_id(row) != "unknown"}


def _case_map(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {_case_id(row): row for row in rows if _case_id(row) != "unknown"}


def _rank_score(row: dict[str, Any]) -> float:
    return max(0.0, min(100.0, _number(_first(row, "total_score", "score", "ranking_score", default=0))))


def _component(row: dict[str, Any], name: str) -> float:
    components = row.get("components") or row.get("scores") or {}
    value = row.get(name, components.get(name) if isinstance(components, dict) else None)
    value = _number(value)
    return value * 100 if 0 <= value <= 1 else value


def _missing_fields(gaps: list[dict[str, Any]], case_id: str) -> set[str]:
    found: set[str] = set()
    for row in gaps:
        if _case_id(row) != case_id:
            continue
        values = _first(row, "missing_fields", "missing", "gaps", "fields", default=[])
        if isinstance(values, dict):
            values = [key for key, value in values.items() if not value]
        if isinstance(values, str):
            values = re.split(r"[,;|]", values)
        if isinstance(values, list):
            found.update(str(value).strip() for value in values if str(value).strip())
        field = _first(row, "field", "field_name")
        if field and str(_first(row, "status", "state", default="missing")).lower() in {"missing", "gap", "unresolved"}:
            found.add(str(field))
    return found


def _conflicts(gaps: list[dict[str, Any]], case: dict[str, Any], case_id: str) -> list[str]:
    values: list[str] = []
    for row in gaps:
        if _case_id(row) != case_id:
            continue
        status = str(_first(row, "status", "state", "resolution", default="")).lower()
        if "conflict" in status or _bool(row.get("conflict")):
            values.append(str(_first(row, "field", "field_name", "name", default="unknown_field")))
    raw = _first(case, "conflicts", "conflict_fields", default=[])
    if isinstance(raw, dict):
        values.extend(str(key) for key in raw)
    elif isinstance(raw, list):
        values.extend(str(value) for value in raw)
    return sorted(set(values))


def _assets_for(assets: list[dict[str, Any]], case_id: str) -> list[dict[str, Any]]:
    return [row for row in assets if _case_id(row) == case_id]


def _verified_types(rows: list[dict[str, Any]]) -> set[str]:
    result: set[str] = set()
    for row in rows:
        kind = _first(row, "verified_type", "type", "asset_type", default=None)
        if kind and (_bool(row.get("verified")) or row.get("verified_type")):
            result.add(str(kind))
    return result


def _source_profile(sources: list[dict[str, Any]], provenance: list[dict[str, Any]], case_id: str) -> tuple[int, int, bool]:
    case_sources = [row for row in sources if _case_id(row) == case_id or str(row.get("case_id", "")) == case_id]
    if not case_sources:
        case_sources = [
            row for row in provenance
            if _case_id(row) == case_id
            and str(row.get("type", row.get("node_type", ""))).lower() == "source"
        ]
    domains = {str(_first(row, "domain", "host", "url", default="")).split("/")[0].lower() for row in case_sources}
    domains.discard("")
    effective = set()
    syndicated = False
    for row in case_sources:
        fingerprint = _first(row, "content_sha256", "content_hash", "duplicate_of", default=None)
        effective.add(str(fingerprint or _first(row, "source_id", "id", "url", default="")))
        source_kind = str(_first(row, "source_kind", "type", "authority", default="")).lower()
        syndicated = syndicated or _bool(row.get("is_syndicated")) or "syndicat" in source_kind or "转载" in source_kind
    if len(case_sources) > 1 and len(effective) <= 1:
        syndicated = True
    return len(domains), len(effective - {""}), syndicated


def _similarity_map(rows: list[dict[str, Any]]) -> dict[str, float]:
    result: dict[str, float] = {}
    for row in rows:
        case_id = _case_id(row)
        score = _number(_first(row, "similarity", "similarity_score", "score", default=0))
        if score <= 1:
            score *= 100
        result[case_id] = max(result.get(case_id, 0), score)
    return result


def _priority_for(kind: str, score: float) -> str:
    if kind == "field_conflict" or score >= 82:
        return "P0"
    if score >= 65:
        return "P1"
    return "P2"


def _query_terms(case: dict[str, Any], ranking: dict[str, Any], missing: set[str], kind: str) -> list[str]:
    name = _first(case, "name", "canonical_name", "title", default=_first(ranking, "case_name", "name", default="项目"))
    aliases = case.get("aliases", [])
    alias = aliases[0] if isinstance(aliases, list) and aliases else None
    subject = f'"{name}"' + (f' OR "{alias}"' if alias else "")
    field_terms = {
        "floor_area": "建筑面积",
        "site_area": "用地面积",
        "architect": "设计单位",
        "client": "业主",
        "location": "地址",
        "year": "建成 时间",
        "height": "高度 层数",
        "structural_grid": "柱网 结构",
        "loading": "荷载",
    }
    fields = [field_terms.get(field, field.replace("_", " ")) for field in sorted(missing)]
    if kind == "missing_key_drawings":
        return [f"{subject} {kind_name}" for kind_name in ("总平面图", "标准层平面图", "剖面图", "立面图")]
    if kind == "field_conflict":
        return [f"{subject} {term} 官方 公示" for term in fields or ["参数"]]
    if kind == "syndicated_only":
        return [f"{subject} {term}" for term in (fields or ["事务所 官网", "filetype:pdf", "规划公示"])]
    if kind == "similar_incomplete":
        return [f"{subject} {term}" for term in (fields or ["项目介绍", "建筑师", "总平面图"])]
    return [f"{subject} {term}" for term in (fields or ["官方", "事务所", "filetype:pdf"])]


def _rationale(kind: str, ranking: dict[str, Any], missing: set[str], conflicts: list[str], domains: int, effective: int, similarity: float) -> str:
    if kind == "high_relevance_low_evidence":
        return f"相关度 {_rank_score(ranking):.1f}，但证据质量 {_component(ranking, 'evidence_quality'):.1f}，优先补一手或直接证据。"
    if kind == "missing_key_drawings":
        return f"缺少关键图纸：{', '.join(sorted(missing)) or 'site_plan/floor_plan/section'}，需要定向找图纸来源。"
    if kind == "syndicated_only":
        return f"来源域名 {domains} 个、有效独立内容 {effective} 个，存在转载聚集，需寻找一手来源。"
    if kind == "field_conflict":
        return f"字段冲突未裁决：{', '.join(conflicts) or 'unknown_field'}；仅收集候选证据，不自动改值。"
    return f"与高价值案例相似度 {similarity:.1f}，但资料完整度 {_component(ranking, 'completeness'):.1f}，值得定向补齐。"


def _expected_gain(kind: str, ranking: dict[str, Any], missing: set[str]) -> dict[str, Any]:
    base = {
        "high_relevance_low_evidence": (0.22, 0.20),
        "missing_key_drawings": (0.18, 0.28),
        "syndicated_only": (0.25, 0.14),
        "field_conflict": (0.16, 0.12),
        "similar_incomplete": (0.20, 0.18),
    }[kind]
    return {
        "evidence_quality_gain": round(base[0], 3),
        "coverage_gain": round(base[1] if missing else base[1] * 0.7, 3),
        "decision_value": round((_rank_score(ranking) / 100) * (base[0] + base[1]), 3),
    }


def _candidate_score(kind: str, ranking: dict[str, Any], missing: set[str], conflicts: list[str], similarity: float, syndicated: bool) -> float:
    relevance = _rank_score(ranking)
    evidence = _component(ranking, "evidence_quality")
    completeness = _component(ranking, "completeness")
    if kind == "high_relevance_low_evidence":
        return relevance * 0.7 + (100 - evidence) * 0.3
    if kind == "missing_key_drawings":
        return relevance * 0.55 + min(100, len(missing) * 18) * 0.45
    if kind == "syndicated_only":
        return relevance * 0.55 + (35 if syndicated else 15) + 15
    if kind == "field_conflict":
        return relevance * 0.5 + min(100, len(conflicts) * 28) * 0.5
    return similarity * 0.55 + (100 - completeness) * 0.45


def _unique(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def build_plan(
    batch: Path,
    *,
    max_queries: int = DEFAULT_QUERY_BUDGET["max_queries"],
    max_fetches: int = DEFAULT_QUERY_BUDGET["max_fetches"],
    max_review_minutes: int = DEFAULT_QUERY_BUDGET["max_review_minutes"],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rankings = load_optional(batch, "rankings.jsonl", "review/rankings.jsonl")
    gaps = load_optional(batch, "gaps.jsonl", "review/gaps.jsonl", "gap_report.json")
    cases = _case_map(load_optional(batch, "cases.jsonl", "case.jsonl"))
    sources = load_optional(batch, "sources.jsonl", "source.jsonl")
    assets = load_optional(batch, "assets.jsonl", "asset.jsonl")
    provenance = load_provenance(batch)
    similarities = load_optional(batch, "similarity.jsonl", "similarities.jsonl", "review/similarity.jsonl")
    similarity_map = _similarity_map(similarities)
    ranking_map = _ranking_map(rankings)
    case_ids = _unique([*ranking_map, *cases, *[_case_id(row) for row in gaps]])
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    candidates: list[dict[str, Any]] = []
    for case_id in case_ids:
        ranking = ranking_map.get(case_id, {})
        case = cases.get(case_id, {})
        missing = _missing_fields(gaps, case_id)
        conflicts = _conflicts(gaps, case, case_id)
        case_assets = _assets_for(assets, case_id)
        verified = _verified_types(case_assets)
        missing_drawings = {field for field in missing if field in DRAWING_TYPES}
        if not missing_drawings and case_assets and not (verified & {"site_plan", "floor_plan", "section"}):
            missing_drawings = {"site_plan", "floor_plan", "section"}
        domains, effective, syndicated = _source_profile(sources, provenance, case_id)
        similarity = similarity_map.get(case_id, _number(_first(ranking, "similarity", "similarity_score", default=0)))
        if similarity <= 1:
            similarity *= 100
        rules = []
        if _rank_score(ranking) >= 60 and _component(ranking, "evidence_quality") < 55:
            rules.append("high_relevance_low_evidence")
        if missing_drawings:
            rules.append("missing_key_drawings")
        if syndicated:
            rules.append("syndicated_only")
        if conflicts:
            rules.append("field_conflict")
        if similarity >= 70 and _component(ranking, "completeness") < 65:
            rules.append("similar_incomplete")
        for kind in rules:
            score = round(max(0.0, min(100.0, _candidate_score(kind, ranking, missing_drawings, conflicts, similarity, syndicated))), 2)
            relevant_missing = missing_drawings if kind == "missing_key_drawings" else missing
            terms = _query_terms(case, ranking, relevant_missing, kind)
            candidates.append({
                "priority_id": f"rp_{len(candidates)+1:04d}",
                "case_id": case_id,
                "case_name": _case_name(ranking or case, cases),
                "gap_type": kind,
                "gap_label": TYPE_LABELS[kind],
                "priority": _priority_for(kind, score),
                "score": score,
                "rationale": _rationale(kind, ranking, relevant_missing, conflicts, domains, effective, similarity),
                "missing_fields": sorted(relevant_missing),
                "conflict_fields": conflicts,
                "source_profile": {"domains": domains, "effective_independent_sources": effective, "syndicated": syndicated},
                "similarity_score": round(similarity, 2),
                "expected_gain": _expected_gain(kind, ranking, missing | missing_drawings),
                "query_seeds": terms,
                "budget": {"allocated_queries": 0, "allocated_fetches": 0, "allocated_review_minutes": 0},
                "stop_conditions": [
                    "stop when a required gap is resolved by a human-approved evidence record",
                    "stop after 2 queries without a new source or candidate evidence",
                    "stop when the assigned query budget is exhausted",
                ],
                "requires_human_review": True,
                "auto_apply": False,
                "status": "proposed",
                "generated_at": now,
            })
    candidates.sort(key=lambda row: (-row["score"], row["case_id"], row["gap_type"]))
    for index, row in enumerate(candidates, 1):
        row["priority_id"] = f"rp_{index:04d}"

    shares = DEFAULT_QUERY_BUDGET["shares"]
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        by_type[row["gap_type"]].append(row)
    for row in candidates:
        row["budget"] = {"allocated_queries": 0, "allocated_fetches": 0, "allocated_review_minutes": 0}
    priority_order = {"P0": 0, "P1": 1, "P2": 2}
    present_types = sorted(by_type, key=lambda kind: (priority_order.get(by_type[kind][0]["priority"], 9), -by_type[kind][0]["score"], kind))
    allocations = {kind: 0 for kind in present_types}
    remaining = max_queries
    for kind in present_types:
        if remaining <= 0:
            break
        desired = max(1, int(max_queries * shares[kind])) if max_queries >= len(present_types) else 1
        cap = min(len(by_type[kind]) * 4, desired, remaining)
        allocations[kind] = cap
        remaining -= cap
    while remaining > 0:
        choices = [kind for kind in present_types if allocations[kind] < len(by_type[kind]) * 4]
        if not choices:
            break
        kind = max(choices, key=lambda value: (by_type[value][0]["score"], shares[value]))
        allocations[kind] += 1
        remaining -= 1

    queries: list[dict[str, Any]] = []
    for kind, rows in by_type.items():
        type_remaining = allocations.get(kind, 0)
        for row in rows:
            if type_remaining <= 0:
                break
            query_budget = min(4, len(row["query_seeds"]), type_remaining)
            if query_budget <= 0:
                continue
            row["budget"] = {
                "allocated_queries": query_budget,
                "allocated_fetches": min(2, query_budget),
                "allocated_review_minutes": min(20, 5 + query_budget * 3),
            }
            type_remaining -= query_budget
            for index, query in enumerate(row["query_seeds"][:query_budget], 1):
                queries.append({
                    "query_id": f"q_{len(queries)+1:04d}",
                    "priority_id": row["priority_id"],
                    "case_id": row["case_id"],
                    "gap_type": row["gap_type"],
                    "query": query,
                    "purpose": row["gap_label"],
                    "channel": "official_or_web" if row["gap_type"] in {"field_conflict", "syndicated_only"} else "web_or_media",
                    "incremental": True,
                    "budget_cost": {"queries": 1, "fetches": 1 if index <= 2 else 0, "review_minutes": 3},
                    "expected_yield": row["expected_gain"],
                    "stop_if": row["stop_conditions"],
                    "requires_human_review": True,
                    "approved": False,
                    "status": "proposed",
                })
    budget = {
        "max_queries": max_queries,
        "max_fetches": max_fetches,
        "max_review_minutes": max_review_minutes,
        "allocated_queries": len(queries),
        "allocated_fetches": min(max_fetches, sum(row["budget"]["allocated_fetches"] for row in candidates)),
        "allocated_review_minutes": min(max_review_minutes, sum(row["budget"]["allocated_review_minutes"] for row in candidates)),
        "by_gap_type": {kind: {"candidate_count": len(by_type.get(kind, [])), "allocated_priorities": sum(1 for row in by_type.get(kind, []) if row["budget"]["allocated_queries"]), "allocated_queries": sum(row["budget"]["allocated_queries"] for row in by_type.get(kind, []))} for kind in TYPE_ORDER},
        "stop_conditions": [
            "stop when all P0 priorities have a human-reviewed resolution or explicit rejection",
            "stop when two consecutive targeted queries add no new source, evidence, or asset",
            "stop when the configured query, fetch, or review budget is exhausted",
            "never auto-apply evidence, resolve conflicts, or promote predicted asset types",
        ],
        "generated_at": now,
    }
    return candidates, queries, budget


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def generate(batch: Path, **kwargs: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    priorities, queries, budget = build_plan(batch, **kwargs)
    write_jsonl(batch / "research_priorities.jsonl", priorities)
    write_jsonl(batch / "queries.jsonl", queries)
    (batch / "research_budget.json").write_text(json.dumps(budget, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return priorities, queries, budget
