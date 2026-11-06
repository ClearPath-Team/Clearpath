"""Export behavior, evidence integrity and hostile page content regression tests."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from api import main
from api.export import generate_html_report, timestamp
from worker.common import SAMPLES, read_json


class ExportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        patcher = patch.object(main, "DATA_DIR", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = TestClient(main.app)
        self.report = read_json(SAMPLES / "report.json")
        job = self.root / "sample"
        job.mkdir()
        for name, value in (("status", {"status": "done", "updated_at": "2026-11-06T18:00:00Z"}),
                            ("report", self.report), ("timeline", read_json(SAMPLES / "timeline.json")),
                            ("nodes", read_json(SAMPLES / "nodes.json"))):
            (job / f"{name}.json").write_text(json.dumps(value), encoding="utf-8")

    def test_html_download_has_categories_transcript_and_print_styles(self):
        result = self.client.get("/api/analyses/sample/export?format=html")
        self.assertEqual(result.status_code, 200)
        self.assertIn("text/html", result.headers["content-type"])
        self.assertEqual(result.headers["content-disposition"], 'attachment; filename="clearpath-audit-sample.html"')
        for phrase in ("@media print", "2026-11-06T18:00:00Z", "ARIA", "Bounding box", "ClearPath", "WCAG 2.1 AA"):
            self.assertIn(phrase, result.text)
        self.assertIn("default-src 'none'", result.headers["content-security-policy"])

    def test_json_preserves_canonical_report(self):
        result = self.client.get("/api/analyses/sample/export?format=json")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json(), self.report)
        self.assertIn('sample.json"', result.headers["content-disposition"])

    def test_missing_and_unfinished(self):
        self.assertEqual(self.client.get("/api/analyses/missing/export").status_code, 404)
        for state in ("queued", "rendering", "failed"):
            (self.root / "sample/status.json").write_text(json.dumps({"status": state}))
            self.assertEqual(self.client.get("/api/analyses/sample/export").status_code, 409)

    def test_missing_report_and_invalid_format(self):
        self.assertEqual(self.client.get("/api/analyses/sample/export?format=pdf").status_code, 422)
        (self.root / "sample/report.json").unlink()
        self.assertEqual(self.client.get("/api/analyses/sample/export").status_code, 404)

    def test_untrusted_content_is_escaped_and_script_urls_are_removed(self):
        self.report.update(title='<script>alert("x")</script>', url="javascript:alert(1)")
        self.report["issues"][0].update(help_url="javascript:alert(2)", selector='<img src=x onerror="alert(3)">')
        html = generate_html_report(self.report)
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img", html)
        self.assertNotIn('href="javascript:', html)
        self.assertIn("&lt;script&gt;", html)

    def test_legacy_empty_reports_do_not_claim_compliance(self):
        html = generate_html_report({"lang": "en", "issues": [], "score": 100})
        self.assertEqual(html.count("No automated findings"), 4)
        self.assertIn("not a certification", html)
        self.assertIn("not a percentage", html)
        self.assertIn("Transcript was not recorded", html)
        self.assertIn("Not recorded", html)

    def test_html_does_not_mutate_input_or_trust_stale_categories(self):
        self.report["issues"][0]["category"] = "unknown"
        before = copy.deepcopy(self.report)
        html = generate_html_report(self.report)
        self.assertEqual(before, self.report)
        self.assertIn(self.report["issues"][0]["title"], html)

    def test_path_traversal_and_timestamp_edges(self):
        self.assertEqual(self.client.get("/api/analyses/%2E%2E/export").status_code, 404)
        self.assertEqual(timestamp(None), "—")
        self.assertEqual(timestamp(float("nan")), "—")
        self.assertEqual(timestamp(14.3), "00:14.3")
        self.assertEqual(timestamp(59.99), "01:00.0")


if __name__ == "__main__":
    unittest.main()
