"""Tests for the analysis timeline endpoint (M4-09)."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from api import main
from worker.common import SAMPLES, read_json


class TimelineEndpointTests(unittest.TestCase):
    def setUp(self):
        root = Path(tempfile.mkdtemp(prefix="cp-test-api-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        self.data_dir = root / "data"
        self.data_dir.mkdir()
        patcher = mock.patch.object(main, "DATA_DIR", self.data_dir)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = TestClient(main.app)
        # A timeline outside DATA_DIR that a traversal attempt would try to reach.
        (root / "status.json").write_text(json.dumps({"status": "done"}), encoding="utf-8")
        (root / "timeline.json").write_text(json.dumps({"secret": True}), encoding="utf-8")

    def _analysis(self, analysis_id, status, with_timeline=True):
        job = self.data_dir / analysis_id
        job.mkdir()
        (job / "status.json").write_text(json.dumps({"id": analysis_id, "status": status}), encoding="utf-8")
        if with_timeline:
            shutil.copy(SAMPLES / "timeline.json", job / "timeline.json")

    def test_done_analysis_returns_timeline_unchanged(self):
        self._analysis("a1b2c3d4", "done")
        res = self.client.get("/api/analyses/a1b2c3d4/timeline")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), read_json(SAMPLES / "timeline.json"))

    def test_demo_style_ids_are_accepted(self):
        self._analysis("bad-checkout", "done")
        self.assertEqual(self.client.get("/api/analyses/bad-checkout/timeline").status_code, 200)

    def test_unknown_analysis_is_404(self):
        res = self.client.get("/api/analyses/deadbeef/timeline")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["detail"], "Analysis not found.")

    def test_unfinished_analysis_is_409(self):
        for state in ("queued", "extracting", "analyzing", "rendering", "failed"):
            with self.subTest(state=state):
                self._analysis(f"run-{state}", state)
                res = self.client.get(f"/api/analyses/run-{state}/timeline")
                self.assertEqual(res.status_code, 409)
                self.assertEqual(res.json()["detail"], "Analysis is not finished yet.")

    def test_done_analysis_without_timeline_is_404(self):
        self._analysis("no-timeline", "done", with_timeline=False)
        res = self.client.get("/api/analyses/no-timeline/timeline")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["detail"], "Timeline not found for this analysis.")

    def test_ids_that_could_escape_data_dir_are_rejected(self):
        for raw in ("%2E%2E", "..", ".", "a.b", "%2E%2E%2F%2E%2E"):
            with self.subTest(id=raw):
                res = self.client.get(f"/api/analyses/{raw}/timeline")
                self.assertEqual(res.status_code, 404)
                self.assertNotIn("secret", res.text)

    def test_existing_endpoints_also_reject_escaping_ids(self):
        (self.data_dir.parent / "clip.mp4").write_bytes(b"not-a-demo-clip")
        self.assertEqual(self.client.get("/api/analyses/%2E%2E").status_code, 404)
        res = self.client.get("/media/%2E%2E/clip.mp4")
        self.assertEqual(res.status_code, 404)
        self.assertNotIn(b"not-a-demo-clip", res.content)

    def test_selected_language_reaches_worker_and_status(self):
        for lang in ("ro", "en"):
            with self.subTest(lang=lang), mock.patch.object(main, "validate_target_url"), \
                    mock.patch.object(main.subprocess, "Popen") as spawn:
                res = self.client.post("/api/analyses", json={"url": "https://example.com", "lang": lang})
                spawn.call_args.kwargs["stdout"].close()
                self.assertEqual(res.status_code, 202)
                self.assertEqual(res.json()["lang"], lang)
                self.assertEqual(spawn.call_args.args[0][-2:], ["--lang", lang])
                status = self.client.get(f"/api/analyses/{res.json()['id']}").json()
                self.assertEqual(status["lang"], lang)

    def test_legacy_requests_default_to_romanian(self):
        with mock.patch.object(main, "validate_target_url"), mock.patch.object(main.subprocess, "Popen") as spawn:
            res = self.client.post("/api/analyses", json={"url": "https://example.com"})
            spawn.call_args.kwargs["stdout"].close()
        self.assertEqual(res.status_code, 202)
        self.assertEqual(res.json()["lang"], "ro")

    def test_unsupported_language_is_rejected_before_starting_worker(self):
        with mock.patch.object(main.subprocess, "Popen") as spawn:
            res = self.client.post("/api/analyses", json={"url": "https://example.com", "lang": "fr"})
        self.assertEqual(res.status_code, 422)
        spawn.assert_not_called()


if __name__ == "__main__":
    unittest.main()
