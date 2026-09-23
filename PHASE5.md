# Phase 5 — Active Research Loop

Phase 5 turns Phase 4 review data into a bounded, explainable next-step plan.
It is proposal-only: no case, evidence, resolution, or asset verification
record is changed.

## Run

```bash
python pipeline/active_research.py batches/<id> --max-queries 40 --max-fetches 24 --max-review-minutes 180
python pipeline/render_dashboard.py batches/<id>
```

The planner accepts the Phase 4 JSONL names and common aliases:

```text
rankings.jsonl       score/components
gaps.jsonl           missing_fields/status=conflict
sources.jsonl        domains/content_sha256/source_kind
assets.jsonl         verified_type/verified
similarity.jsonl     similarity_score
```

Missing optional files are treated as empty so a partially built batch can be
planned safely. The generated rationale records which signal caused a task.

## Outputs and boundary

`research_priorities.jsonl` contains one proposed action per case and gap type.
`queries.jsonl` contains targeted incremental queries. `research_budget.json`
records query, fetch, review budgets and hard stop rules. The dashboard shows
the ten highest-scoring proposed gaps.

Every output keeps the review gate explicit:

```json
{
  "requires_human_review": true,
  "auto_apply": false,
  "status": "proposed"
}
```

Query records additionally start with `approved: false`. Phase 5 itself does
not accept evidence, resolve conflicts, or promote predicted asset types.

## Checks

```bash
python -m unittest discover -s tests -v
python -m compileall -q core pipeline scripts
```
