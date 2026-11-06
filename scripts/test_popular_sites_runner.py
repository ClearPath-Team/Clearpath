"""Runner control-flow tests; synthetic clips here do not certify media playback."""
from contextlib import redirect_stderr, redirect_stdout
import io
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts import test_popular_sites as runner
from worker.common import SAMPLES, read_json, write_json


class PopularSitesRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.site = {"name": "Local fixture", "url": "http://localhost:8080/bad-checkout.html"}

    def artifacts(self, analysis_id, url, *, lang):
        self.assertEqual(lang, "ro")
        folder = self.root / analysis_id
        folder.mkdir()
        for name in ("nodes", "events", "issues", "timeline", "report"):
            shutil.copyfile(SAMPLES / f"{name}.json", folder / f"{name}.json")
        write_json(folder / "status.json", {"status": "done", "lang": "ro"})
        (folder / "clip.mp4").write_bytes(b"synthetic control-flow fixture")

    def run_site(self, side_effect=None, **kwargs):
        with patch.object(runner, "DATA_DIR", self.root), \
                patch.object(runner, "run_pipeline", side_effect=side_effect or self.artifacts), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return runner.test_site(self.site, **kwargs)

    def test_full_runs_are_unique_and_restore_stub_setting(self):
        def pipeline(*args, **kwargs):
            self.assertEqual(os.environ["CP_STUBS"], "")
            self.artifacts(*args, **kwargs)
        with patch.dict(os.environ, {"CP_STUBS": "all"}):
            first = self.run_site(pipeline, romanian=True)
            second = self.run_site(pipeline, romanian=True)
            self.assertEqual(os.environ["CP_STUBS"], "all")
        self.assertEqual(first["status"], "success")
        self.assertNotEqual(first["analysis_id"], second["analysis_id"])
        self.assertTrue(first["analysis_id"].startswith("e2e-ro-"))

    def test_system_exit_preserves_actual_blocker_and_runner_continues(self):
        def failure(analysis_id, url, **kwargs):
            folder = self.root / analysis_id
            folder.mkdir()
            write_json(folder / "status.json", {"status": "failed", "error": "Page navigation timed out"})
            raise SystemExit(1)
        failed = self.run_site(failure)
        self.assertEqual(failed["error_message"], "Page navigation timed out")
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(self.run_site()["status"], "success")

    def test_stubbed_render_is_never_labelled_full_success(self):
        self.assertEqual(self.run_site(run_render=False)["status"], "partial")

    def test_missing_clip_is_not_success(self):
        def no_clip(*args, **kwargs):
            self.artifacts(*args, **kwargs)
            (self.root / args[0] / "clip.mp4").unlink()
        result = self.run_site(no_clip)
        self.assertEqual(result["status"], "partial")
        self.assertIn("clip.mp4", result["error_message"])

    def test_invalid_duration_or_score_is_rejected(self):
        self.artifacts("invalid", "url", lang="ro")
        folder = self.root / "invalid"
        for name, key in (("timeline", "duration"), ("report", "score")):
            original = read_json(folder / f"{name}.json")
            for value in (True, float("nan"), float("inf"), "bad", None):
                with self.subTest(name=name, value=value):
                    write_json(folder / f"{name}.json", {**original, key: value})
                    self.assertTrue(runner.verify_artifacts(folder, full_render=True))
            write_json(folder / f"{name}.json", original)

    def test_wrong_narration_language_is_rejected(self):
        self.artifacts("english", "url", lang="ro")
        folder = self.root / "english"
        events = read_json(folder / "events.json")
        write_json(folder / "events.json", {**events, "lang": "en"})
        self.assertIn("Narration language is not Romanian", runner.verify_artifacts(folder, full_render=True))

    def test_markdown_links_resolve_from_output_directory(self):
        result = self.run_site()
        output = self.root / "reports" / "audit.md"
        runner.write_markdown_report([result], output, full_render=True)
        relative = f"../{result['analysis_id']}/report.json"
        self.assertIn(f"[report](<{relative}>)", output.read_text(encoding="utf-8"))

    def test_preset_has_all_nine_platforms(self):
        self.assertEqual(len(runner.ROMANIAN_SITES), 9)
        self.assertEqual(len({site["url"] for site in runner.ROMANIAN_SITES}), 9)


if __name__ == "__main__":
    unittest.main()
