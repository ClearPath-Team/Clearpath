"""Canonical taxonomy contracts and regression tests."""
import copy
import unittest

from worker.common import SAMPLES, read_json
from worker.engine.categories import (
    CATEGORY_LABELS, RULE_CATEGORIES, WCAG_PRINCIPLES, category_counts,
    classify_issue, enrich_issue,
)
from worker.engine.recommendations import RECOMMENDATIONS, EN_RECOMMENDATIONS
from worker.engine.report import build_report


class TaxonomyTests(unittest.TestCase):
    def test_all_curated_rules_and_category_keys_are_mapped(self):
        self.assertTrue(set(RECOMMENDATIONS) <= RULE_CATEGORIES.keys())
        self.assertTrue(set(EN_RECOMMENDATIONS) <= RULE_CATEGORIES.keys())
        for rule in set(RULE_CATEGORIES) | set(RECOMMENDATIONS) | {"aria-unknown-rule", "unrecognized"}:
            fields = classify_issue(rule)
            self.assertIn(fields["category"], CATEGORY_LABELS)
            self.assertIn(fields["wcag_principle"], WCAG_PRINCIPLES)
            self.assertEqual(set(fields["category_label"]), {"en", "ro"})

    def test_known_and_unknown_rules(self):
        examples = {
            "color-contrast": ("visual_contrast", "perceivable"),
            "link-in-text-block": ("visual_contrast", "perceivable"),
            "button-name": ("screen_reader", "robust"),
            "aria-valid-attr": ("screen_reader", "robust"),
            "keyboard-trap": ("motor_keyboard", "operable"),
            "html-has-lang": ("structure_navigation", "understandable"),
            "heading-order": ("structure_navigation", "perceivable"),
            "arbitrary-unknown-rule": ("structure_navigation", "perceivable"),
        }
        for rule, expected in examples.items():
            with self.subTest(rule=rule):
                payload = classify_issue(rule)
                self.assertEqual((payload["category"], payload["wcag_principle"]), expected)

    def test_input_is_not_modified_and_stale_category_replaced(self):
        original = {"id": "i1", "rule": "color-contrast", "category": "motor_keyboard"}
        before = copy.deepcopy(original)
        enriched = enrich_issue(original)
        self.assertEqual(original, before)
        self.assertEqual(enriched["category"], "visual_contrast")
        enriched["category_label"]["en"] = "Modified"
        self.assertEqual(CATEGORY_LABELS["visual_contrast"]["en"], "Contrast & Visual")

    def test_rollups_count_every_issue_and_preserve_score(self):
        issues = read_json(SAMPLES / "issues.json")
        report = build_report("t", "https://example.com", read_json(SAMPLES / "nodes.json"),
                              issues, read_json(SAMPLES / "timeline.json"))
        self.assertEqual(sum(report["categories"].values()), len(issues))
        self.assertEqual(report["categories"], category_counts(issues))
        self.assertEqual(report["score"], read_json(SAMPLES / "report.json")["score"])
        self.assertTrue(all("wcag_principle" in i for i in report["issues"]))
        self.assertEqual(set(report["categories"]), set(CATEGORY_LABELS))
        self.assertEqual(read_json(SAMPLES / "report.json")["categories"], report["categories"])

    def test_legacy_issues_gain_taxonomy_when_report_is_rebuilt(self):
        legacy = [{"id": "i1", "rule": "label", "severity": "critical", "node_id": "n1"}]
        before = copy.deepcopy(legacy)
        report = build_report("legacy", "url", {}, legacy,
                              {"duration": 2, "entries": [{"node_id": "n1", "start": 1}]})
        self.assertEqual(report["issues"][0]["category"], "screen_reader")
        self.assertEqual(report["issues"][0]["timestamp"], 1)
        self.assertEqual(report["categories"]["screen_reader"], 1)
        self.assertEqual(report["score"], 90)
        self.assertEqual(legacy, before)


if __name__ == "__main__":
    unittest.main()
