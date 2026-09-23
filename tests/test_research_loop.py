import json
import tempfile
import unittest
from pathlib import Path

from core.research_loop import build_plan, generate
from pipeline.render_dashboard import render


class ResearchLoopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.batch = Path(self.tmp.name)
        self._write("rankings.jsonl", [
            {"case_id": "case_high", "case_name": "高相关园区", "total_score": 92, "relevance": 0.95, "evidence_quality": 0.20, "completeness": 0.60},
            {"case_id": "case_conflict", "case_name": "冲突项目", "total_score": 84, "evidence_quality": 0.75, "completeness": 0.80},
            {"case_id": "case_similar", "case_name": "相似项目", "total_score": 78, "evidence_quality": 0.70, "completeness": 0.30},
        ])
        self._write("gaps.jsonl", [
            {"case_id": "case_high", "missing_fields": ["site_plan", "floor_area"]},
            {"case_id": "case_conflict", "field": "floor_area", "status": "conflict"},
        ])
        self._write("sources.jsonl", [
            {"case_id": "case_high", "source_id": "src1", "domain": "media.example", "content_sha256": "same"},
            {"case_id": "case_high", "source_id": "src2", "domain": "copy.example", "content_sha256": "same", "source_kind": "syndicated"},
        ])
        self._write("assets.jsonl", [{"case_id": "case_high", "asset_id": "a1", "verified_type": "render", "verified": True}])
        self._write("similarity.jsonl", [{"case_id": "case_similar", "similarity_score": 0.88}])

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, name, rows):
        (self.batch / name).write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")

    def test_all_requested_gap_types_and_manual_gate(self):
        priorities, queries, budget = build_plan(self.batch, max_queries=20)
        kinds = {row["gap_type"] for row in priorities}
        self.assertTrue({"high_relevance_low_evidence", "missing_key_drawings", "syndicated_only", "field_conflict", "similar_incomplete"} <= kinds)
        self.assertTrue(queries)
        self.assertLessEqual(len(queries), 20)
        self.assertEqual(budget["allocated_queries"], len(queries))
        self.assertTrue(all(row["requires_human_review"] and not row["auto_apply"] for row in priorities))
        self.assertTrue(all(row["requires_human_review"] and not row["approved"] for row in queries))

    def test_generate_outputs_and_dashboard(self):
        generate(self.batch, max_queries=3)
        _, limited_queries, limited_budget = build_plan(self.batch, max_queries=3)
        self.assertLessEqual(len(limited_queries), 3)
        self.assertEqual(limited_budget["allocated_queries"], len(limited_queries))
        _, no_queries, no_budget = build_plan(self.batch, max_queries=0)
        self.assertEqual(no_queries, [])
        self.assertEqual(no_budget["allocated_queries"], 0)
        dashboard = render(self.batch)
        self.assertTrue((self.batch / "research_priorities.jsonl").exists())
        self.assertTrue((self.batch / "queries.jsonl").exists())
        self.assertTrue((self.batch / "research_budget.json").exists())
        text = dashboard.read_text(encoding="utf-8")
        self.assertIn("下一步最值得研究的缺口", text)
        self.assertIn("Phase 5", text)

    def test_provenance_graph_can_supply_source_profile(self):
        (self.batch / "sources.jsonl").unlink()
        (self.batch / "provenance_graph.json").write_text(json.dumps({
            "nodes": [
                {"id": "case_high", "type": "case"},
                {"id": "src1", "type": "source", "domain": "copy.example", "source_kind": "syndicated"},
            ],
            "edges": [{"source": "case_high", "target": "src1"}],
        }), encoding="utf-8")
        priorities, _, _ = build_plan(self.batch, max_queries=20)
        high = [row for row in priorities if row["case_id"] == "case_high"]
        self.assertTrue(any(row["gap_type"] == "syndicated_only" for row in high))


if __name__ == "__main__":
    unittest.main()
