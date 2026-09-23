"""Render a small, dependency-free review dashboard for a batch."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.research_loop import load_optional


def _cell(value: object) -> str:
    return html.escape(str(value if value not in (None, "") else "—"))


def render(batch: Path) -> Path:
    priorities = load_optional(batch, "research_priorities.jsonl")
    queries = load_optional(batch, "queries.jsonl")
    budget = {}
    budget_path = batch / "research_budget.json"
    if budget_path.exists():
        budget = json.loads(budget_path.read_text(encoding="utf-8"))
    rows = []
    for row in priorities[:10]:
        rows.append(
            "<tr>"
            f"<td>{_cell(row.get('priority'))}</td>"
            f"<td>{_cell(row.get('case_name', row.get('case_id')))}</td>"
            f"<td>{_cell(row.get('gap_label', row.get('gap_type')))}</td>"
            f"<td>{_cell(row.get('score'))}</td>"
            f"<td>{_cell(row.get('budget', {}).get('allocated_queries'))}</td>"
            f"<td>{_cell(row.get('rationale'))}</td>"
            "</tr>"
        )
    if not rows:
        rows.append('<tr><td colspan="6">暂无自动生成的研究缺口</td></tr>')
    stop_conditions = budget.get("stop_conditions", [
        "人工确认后才可采纳证据",
        "连续两条定向查询无新增来源/证据/素材时停止",
        "预算耗尽时停止",
    ])
    stop_html = "".join(f"<li>{_cell(item)}</li>" for item in stop_conditions)
    out = batch / "review" / "dashboard.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        """<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><title>Architecture Case Research Dashboard</title>
<style>body{font:14px system-ui,sans-serif;margin:32px;color:#222}table{border-collapse:collapse;width:100%;margin:12px 0 28px}th,td{border:1px solid #ddd;padding:8px;text-align:left;vertical-align:top}th{background:#f4f4f4}.p0{color:#a00}.meta{display:flex;gap:24px;flex-wrap:wrap}.card{background:#f7f7f7;padding:12px 16px;border-radius:6px}.note{color:#666}</style>
<body><h1>Coverage Dashboard</h1>
<p class="note">Phase 5 只提出研究建议，不自动写入案例事实、证据裁决或素材确认。</p>
<div class="meta">
<div class="card">研究缺口 <strong>__PRIORITIES__</strong></div>
<div class="card">增量查询 <strong>__QUERIES__</strong></div>
<div class="card">查询预算 <strong>__ALLOCATED__ / __MAX__</strong></div>
</div>
<h2>下一步最值得研究的缺口</h2>
<table><thead><tr><th>优先级</th><th>案例</th><th>缺口类型</th><th>分数</th><th>查询数</th><th>原因</th></tr></thead><tbody>__ROWS__</tbody></table>
<h2>停止条件</h2><ul>__STOP__</ul>
</body></html>
""".replace("__PRIORITIES__", str(len(priorities)))
        .replace("__QUERIES__", str(len(queries)))
        .replace("__ALLOCATED__", str(budget.get("allocated_queries", len(queries))))
        .replace("__MAX__", str(budget.get("max_queries", "—")))
        .replace("__ROWS__", "".join(rows))
        .replace("__STOP__", stop_html),
        encoding="utf-8",
    )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path)
    args = parser.parse_args()
    print(render(args.batch))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
