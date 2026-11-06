"""Regression tests for render_clip() timeline.json output (M3-02).

RenderClipTests run the real render_clip() with Piper, ffmpeg/ffprobe and
Playwright mocked. RealRenderEndToEndTests generate an actual MP4 and are
skipped when those tools or the voice model are not installed.
"""
import json
import shutil
import subprocess
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
    @staticmethod
    def _probe(duration):
        return json.dumps({"format": {"duration": duration}})

    def test_returns_real_probed_duration_when_clip_covers_narration(self):
        self.assertEqual(_validate_clip_duration(self._probe("30.4"), 30.0), 30.4)
        self.assertEqual(_validate_clip_duration(self._probe("29.95"), 30.0), 29.95)

    def test_rejects_clip_truncated_before_last_announcement(self):
        # Previously accepted by the symmetric 2s tolerance.
        with self.assertRaisesRegex(RuntimeError, "truncated"):
            _validate_clip_duration(self._probe("28.5"), 30.0)
        with self.assertRaisesRegex(RuntimeError, "truncated"):
            _validate_clip_duration(self._probe("5"), 30.0)

    def test_rejects_clip_much_longer_than_narration(self):
        with self.assertRaisesRegex(RuntimeError, "longer than"):
            _validate_clip_duration(self._probe("31.5"), 30.0)

    def test_rejects_non_finite_or_non_positive_duration(self):
        for value in ("NaN", "inf", "-inf", "0", "-1.2"):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                _validate_clip_duration(self._probe(value), 30.0)

    def test_rejects_malformed_ffprobe_responses(self):
        cases = {
            "not json": "not json",
            "empty": "",
            "none": None,
            "top-level list": json.dumps([{"format": {"duration": "30"}}]),
            "format not object": json.dumps({"format": "30"}),
            "missing duration": json.dumps({"format": {}}),
            "null duration": self._probe(None),
            "boolean duration": self._probe(True),
            "object duration": self._probe({"value": "30"}),
            "non-numeric string": self._probe("thirty"),
        }
        for name, stdout in cases.items():
            with self.subTest(case=name), self.assertRaises(RuntimeError):
                _validate_clip_duration(stdout, 30.0)


def _real_render_unavailable_reason():
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        return "ffmpeg/ffprobe not installed"
    try:
        render._piper_bin()
    except RuntimeError:
        return "piper not installed"
    if not render._voice_path().is_file():
        return "Piper voice model not downloaded (scripts/fetch_assets.py)"
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as playwright:
            if not Path(playwright.chromium.executable_path).exists():
                return "Playwright Chromium not installed"
    except Exception as exc:
        return f"Playwright unavailable: {exc}"
    return None


_SKIP_REAL_RENDER = _real_render_unavailable_reason()


@unittest.skipIf(_SKIP_REAL_RENDER, _SKIP_REAL_RENDER or "")
class RealRenderEndToEndTests(unittest.TestCase):
    """Runs Piper, Chromium and ffmpeg for real on the offline test site."""

    def test_generated_mp4_is_synchronized_with_timeline(self):
        nodes = read_json(SAMPLES / "nodes.json")
        sample_events = read_json(SAMPLES / "events.json")["events"]
        events = {"events": [e for e in sample_events if e["node_id"] in ("n5", "n6", "n9")]}
        site = (Path(__file__).resolve().parents[2] / "test-site" / "bad-checkout.html").as_uri()
        out_dir = Path(tempfile.mkdtemp(prefix="cp-test-real-render-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)

        timeline = render_clip(site, nodes, events, out_dir)

        clip = out_dir / "clip.mp4"
        self.assertTrue(clip.is_file() and clip.stat().st_size > 0)
        probe = json.loads(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
             "-of", "json", str(clip)],
            capture_output=True, text=True, check=True, timeout=30).stdout)
        self.assertEqual(sorted(s["codec_type"] for s in probe["streams"]), ["audio", "video"])
        clip_seconds = float(probe["format"]["duration"])
        self.assertAlmostEqual(timeline["duration"], clip_seconds, places=2)
        self.assertEqual([e["node_id"] for e in timeline["entries"]], ["n5", "n6", "n9"])
        for entry in timeline["entries"]:
            self.assertLessEqual(entry["end"], clip_seconds + render.CLIP_END_SLACK_SECONDS)
        self.assertEqual(json.loads((out_dir / "timeline.json").read_text(encoding="utf-8")), timeline)

        issues = read_json(SAMPLES / "issues.json")
        report = build_report("e2e", site, nodes, issues, timeline)
        stamps = {i["rule"]: i["timestamp"] for i in report["issues"]}
        self.assertEqual(stamps["button-name"], timeline["entries"][1]["start"])
        self.assertLess(stamps["button-name"], report["duration"])


if __name__ == "__main__":
    unittest.main()
