"""Regression tests for render_clip() timeline.json output (M3-02).

render_clip() runs for real; only the expensive boundaries are mocked:
Piper synthesis, ffmpeg/ffprobe subprocesses, and the Playwright browser.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from worker.common import SAMPLES, read_json
from worker.engine.report import build_report
from worker.media import render
from worker.media.render import PAUSE_SECONDS, _validate_clip_duration, render_clip

SPOKEN_SECONDS = 1.0
URL = "http://localhost:8080/bad-checkout.html"


def _narration_total(event_count):
    return event_count * SPOKEN_SECONDS + (event_count - 1) * PAUSE_SECONDS


class RenderClipTests(unittest.TestCase):
    def setUp(self):
        self.nodes = read_json(SAMPLES / "nodes.json")
        self.events = read_json(SAMPLES / "events.json")
        self.issues = read_json(SAMPLES / "issues.json")
        self.out_dir = Path(tempfile.mkdtemp(prefix="cp-test-render-"))
        self.addCleanup(shutil.rmtree, self.out_dir, ignore_errors=True)

    def _render(self, probed_duration):
        probe_stdout = json.dumps({"format": {"duration": str(probed_duration)}})

        def fake_run(args, *, input_text=None):
            return SimpleNamespace(stdout=probe_stdout if args[0] == "ffprobe" else "")

        with mock.patch.object(render.shutil, "which", return_value="/usr/bin/tool"), \
                mock.patch.object(render, "_synthesize", return_value=SPOKEN_SECONDS), \
                mock.patch.object(render, "_run", side_effect=fake_run), \
                mock.patch("playwright.sync_api.sync_playwright"):
            return render_clip(URL, self.nodes, self.events, self.out_dir)

    def test_returns_and_writes_contract_schema(self):
        expected_total = _narration_total(len(self.events["events"]))
        timeline = self._render(expected_total + 0.05)

        self.assertEqual(set(timeline), {"duration", "clip", "entries"})
        self.assertEqual(timeline["clip"], "clip.mp4")
        self.assertEqual(timeline["duration"], round(expected_total + 0.05, 3))
        self.assertEqual(len(timeline["entries"]), len(self.events["events"]))
        for entry, event in zip(timeline["entries"], self.events["events"]):
            self.assertEqual(set(entry), {"seq", "node_id", "text", "start", "end"})
            self.assertEqual(entry["seq"], event["seq"])
            self.assertEqual(entry["node_id"], event["node_id"])
            self.assertEqual(entry["text"], event["text"])
            self.assertLess(entry["start"], entry["end"])

        written = json.loads((self.out_dir / "timeline.json").read_text(encoding="utf-8"))
        self.assertEqual(written, timeline)

    def test_output_feeds_build_report_with_mapped_timestamps(self):
        timeline = self._render(_narration_total(len(self.events["events"])))

        report = build_report("regression", URL, self.nodes, self.issues, timeline)

        self.assertEqual(report["duration"], timeline["duration"])
        timestamps = {issue["rule"]: issue["timestamp"] for issue in report["issues"]}
        cart_index = next(i for i, e in enumerate(self.events["events"]) if e["node_id"] == "n6")
        self.assertAlmostEqual(timestamps["button-name"],
                               cart_index * (SPOKEN_SECONDS + PAUSE_SECONDS), places=3)
        self.assertIsNone(timestamps["html-has-lang"])

    def test_truncated_clip_fails_without_writing_timeline(self):
        with self.assertRaises(RuntimeError):
            self._render(5.0)
        self.assertFalse((self.out_dir / "timeline.json").exists())


class ValidateClipDurationTests(unittest.TestCase):
    def test_returns_real_probed_duration_within_tolerance(self):
        probe = json.dumps({"format": {"duration": "30.9"}})
        self.assertEqual(_validate_clip_duration(probe, 30.0), 30.9)

    def test_rejects_duration_mismatch(self):
        probe = json.dumps({"format": {"duration": "5"}})
        with self.assertRaises(RuntimeError):
            _validate_clip_duration(probe, 30.0)

    def test_rejects_non_finite_duration(self):
        for value in ("NaN", "inf", "-inf"):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                _validate_clip_duration(json.dumps({"format": {"duration": value}}), 30.0)

    def test_rejects_non_positive_duration(self):
        for value in ("0", "-1.2"):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                _validate_clip_duration(json.dumps({"format": {"duration": value}}), 0.0)

    def test_rejects_missing_or_unparseable_output(self):
        for stdout in ("not json", json.dumps({"format": {}}), "", None):
            with self.subTest(stdout=stdout), self.assertRaises(RuntimeError):
                _validate_clip_duration(stdout, 30.0)


if __name__ == "__main__":
    unittest.main()
