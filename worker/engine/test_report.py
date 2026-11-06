"""Scoring and timestamp regression tests for the M2-02 scoring contract."""
import copy
import unittest

from worker.common import SAMPLES, read_json
from worker.engine.report import build_report, calculate_score


class ReportTests(unittest.TestCase):
    def test_sample_score_is_33_under_contract_formula(self):
        issues = read_json(SAMPLES / "issues.json")
        # Three axe criticals, four serious, one moderate, plus one trap.
        self.assertEqual(calculate_score(issues), 100 - 3 * 10 - 4 * 5 - 2 - 15)

    def test_sample_report_agrees_with_live_scoring_metrics(self):
        sample = read_json(SAMPLES / "report.json")
        issues = read_json(SAMPLES / "issues.json")
        generated = build_report(sample["id"], sample["url"],
                                 read_json(SAMPLES / "nodes.json"), issues,
                                 read_json(SAMPLES / "timeline.json"))
        self.assertEqual(sample["score"], calculate_score(issues))
        for field in ("score", "counts", "focus_trap"):
            with self.subTest(field=field):
                self.assertEqual(sample[field], generated[field])

    def test_severity_weights_match_the_contract(self):
        for severity, expected_score in (("critical", 90), ("serious", 95),
                                         ("moderate", 98), ("minor", 99)):
            with self.subTest(severity=severity):
                self.assertEqual(calculate_score([{"rule": "label", "severity": severity}]), expected_score)

    def test_weights_are_per_occurrence_without_per_rule_cap(self):
        issues = [{"rule": "label", "severity": "critical"} for _ in range(3)]
        self.assertEqual(calculate_score(issues), 70)
        self.assertEqual(calculate_score([{"rule": "other", "severity": "minor"}]), 99)

    def test_trap_applies_once_whether_flagged_or_present(self):
        trap = {"rule": "keyboard-trap", "severity": "critical"}
        self.assertEqual(calculate_score([trap, trap], True), 85)
        self.assertEqual(calculate_score([], True), 85)
        self.assertEqual(calculate_score([]), 100)

    def test_score_cannot_be_negative(self):
        self.assertEqual(calculate_score([{"rule": "label", "severity": "critical"}] * 11), 0)

    def test_report_uses_inputs_and_does_not_mutate_them(self):
        nodes = read_json(SAMPLES / "nodes.json")
        issues = read_json(SAMPLES / "issues.json")
        timeline = read_json(SAMPLES / "timeline.json")
        original = copy.deepcopy((nodes, issues, timeline))
        report = build_report("custom", "https://example.com", nodes, issues, timeline)
        self.assertEqual(report["id"], "custom")
        self.assertEqual(report["url"], "https://example.com")
        self.assertEqual(report["clip_url"], "/media/custom/clip.mp4")
        self.assertEqual(report["duration"], timeline["duration"])
        self.assertEqual(report["score"], 33)
        self.assertTrue(report["focus_trap"])
        self.assertEqual(report["counts"], {"critical": 4, "serious": 4, "moderate": 1, "minor": 0})
        for issue in report["issues"]:
            starts = [e["start"] for e in timeline["entries"]
                      if issue["node_id"] is not None and e["node_id"] == issue["node_id"]]
            self.assertEqual(issue["timestamp"], min(starts) if starts else None)
        self.assertIsNone(next(i["timestamp"] for i in report["issues"] if i["rule"] == "html-has-lang"))
        self.assertEqual((nodes, issues, timeline), original)

    def test_earliest_timestamp_zero_and_null_are_distinct(self):
        issues = [
            {"id": "i1", "rule": "a", "severity": "critical", "node_id": None},
            {"id": "i2", "rule": "b", "severity": "critical", "node_id": "n1"},
            {"id": "i3", "rule": "c", "severity": "critical", "node_id": "n2"},
            {"id": "i4", "rule": "d", "severity": "minor", "node_id": "n1"},
        ]
        timeline = {"duration": 10, "entries": [
            {"node_id": None, "start": 0}, {"node_id": "n1", "start": 5},
            {"node_id": "n2", "start": 2}, {"node_id": "n1", "start": 0},
        ]}
        report = build_report("x", "url", {"title": "Custom", "focus_trap": None}, issues, timeline)
        self.assertEqual([issue["id"] for issue in report["issues"]], ["i2", "i3", "i1", "i4"])
        self.assertEqual([issue["timestamp"] for issue in report["issues"]], [0, 2, None, 0])
        self.assertFalse(report["focus_trap"])

    def test_empty_report_does_not_copy_sample_metrics(self):
        report = build_report("empty", "url", {}, [], {"duration": 0, "entries": []})
        self.assertEqual(report["score"], 100)
        self.assertEqual(report["issues"], [])
        self.assertEqual(sum(report["counts"].values()), 0)


if __name__ == "__main__":
    unittest.main()
