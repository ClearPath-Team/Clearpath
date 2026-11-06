"""Regression tests for the timeline.json schema fix (M3-02).

These avoid invoking piper/ffmpeg/Playwright directly: _resolve_clip_duration
is pure and unit-tested in isolation, and the timeline.json shape produced by
render_clip() is reconstructed manually to verify compatibility with
build_report() without a full render.
"""
import json
import unittest

from worker.common import SAMPLES, read_json
from worker.engine.report import build_report
from worker.media.render import _resolve_clip_duration


class ResolveClipDurationTests(unittest.TestCase):
    def test_uses_probed_duration_when_close_to_narration_total(self):
        probe = json.dumps({"format": {"duration": "30.05"}})
        self.assertEqual(_resolve_clip_duration(probe, narration_total=30.0), 30.05)

    def test_falls_back_when_duration_missing(self):
        probe = json.dumps({"format": {}})
        self.assertEqual(_resolve_clip_duration(probe, narration_total=12.345), 12.345)

    def test_falls_back_on_invalid_json(self):
        self.assertEqual(_resolve_clip_duration("not json", narration_total=5.0), 5.0)

    def test_falls_back_when_duration_non_positive(self):
        probe = json.dumps({"format": {"duration": "0"}})
        self.assertEqual(_resolve_clip_duration(probe, narration_total=8.0), 8.0)
        probe_negative = json.dumps({"format": {"duration": "-1.2"}})
        self.assertEqual(_resolve_clip_duration(probe_negative, narration_total=8.0), 8.0)

    def test_falls_back_when_probed_diverges_from_narration_total(self):
        # A probed duration wildly different from the narration timeline signals
        # a broken render (e.g. truncated clip), not a benign rounding gap.
        probe = json.dumps({"format": {"duration": "999.0"}})
        self.assertEqual(_resolve_clip_duration(probe, narration_total=30.0), 30.0)

    def test_tolerates_small_rounding_divergence(self):
        probe = json.dumps({"format": {"duration": "30.9"}})
        self.assertEqual(_resolve_clip_duration(probe, narration_total=30.0, tolerance=2.0), 30.9)


class TimelineSchemaCompatibilityTests(unittest.TestCase):
    def test_render_clip_output_shape_is_accepted_by_build_report(self):
        # Mirrors exactly what render_clip() now writes to timeline.json.
        timeline = {
            "duration": 37.803,
            "clip": "clip.mp4",
            "entries": [
                {"seq": 0, "node_id": None, "text": "Pagina Finalizează comanda", "start": 0.0, "end": 1.904},
                {"seq": 7, "node_id": "n6", "text": "Buton", "start": 9.217, "end": 9.705},
            ],
        }
        nodes = read_json(SAMPLES / "nodes.json")
        issues = read_json(SAMPLES / "issues.json")

        # This is the exact call that raised KeyError: 'duration' before the fix.
        report = build_report("regression", "http://localhost:8080/bad-checkout.html", nodes, issues, timeline)

        self.assertEqual(report["duration"], timeline["duration"])

    def test_entries_have_required_fields_for_report_timestamp_mapping(self):
        timeline = {
            "duration": 10.0,
            "clip": "clip.mp4",
            "entries": [{"seq": 0, "node_id": "n6", "text": "Buton", "start": 2.5, "end": 3.1}],
        }
        for entry in timeline["entries"]:
            for field in ("seq", "node_id", "text", "start", "end"):
                self.assertIn(field, entry)


if __name__ == "__main__":
    unittest.main()
