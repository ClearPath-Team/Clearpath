"""Regression tests for render_clip() timeline.json output (M3-02).

RenderClipTests run the real render_clip() with Piper, ffmpeg/ffprobe and
Playwright mocked. RealRenderEndToEndTests generate an actual MP4 and are
skipped when those tools or the voice model are not installed.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from worker.common import SAMPLES, read_json
from worker.engine.report import build_report
from worker.media import render
from worker.media.render import (
    PAUSE_SECONDS,
    _edge_tts_bin,
    _piper_bin,
    _resolve_binary,
    _synthesize,
    _validate_clip_duration,
    normalize_romanian_text,
    render_clip,
)

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

    def _render(self, probed_duration, lang="ro", synthesis=None):
        probe_stdout = json.dumps({"format": {"duration": str(probed_duration)}})

        def fake_run(args, *, input_text=None):
            return SimpleNamespace(stdout=probe_stdout if args[0] == "ffprobe" else "")

        with mock.patch.object(render.shutil, "which", return_value="/usr/bin/tool"), \
                mock.patch.object(render, "_synthesize", new=synthesis or mock.Mock(return_value=SPOKEN_SECONDS)), \
                mock.patch.object(render, "_run", side_effect=fake_run), \
                mock.patch("playwright.sync_api.sync_playwright"):
            return (render_clip(URL, self.nodes, self.events, self.out_dir) if lang == "ro"
                    else render_clip(URL, self.nodes, self.events, self.out_dir, lang=lang))

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
        cart_id = next(n["id"] for n in self.nodes["nodes"] if n["selector"] == "#cart")
        cart_index = next(i for i, e in enumerate(self.events["events"]) if e["node_id"] == cart_id)
        self.assertAlmostEqual(timestamps["button-name"],
                               cart_index * (SPOKEN_SECONDS + PAUSE_SECONDS), places=3)
        self.assertIsNone(timestamps["html-has-lang"])

    def test_punctuation_caption_matches_synthesized_timeline(self):
        self.events = {"events": [{"seq": 0, "node_id": None, "text": ","}]}
        with mock.patch.object(render, "_draw_overlay") as overlay:
            result = self._render(1.05)
        text = "Element fără conținut textual"
        self.assertEqual(result["entries"][0]["text"], text)
        self.assertEqual(overlay.call_args.args[2], text)

    def test_english_punctuation_fallback(self):
        self.assertEqual(render._speakable_announcement("...", lang="en"), "No textual content")
        self.assertEqual(render._speakable_announcement("...", lang="ro"), "Element fără conținut textual")

    def test_english_render_uses_english_fallback_and_language(self):
        self.events = {"events": [{"seq": 0, "node_id": None, "text": ","}]}
        synth = mock.Mock(return_value=SPOKEN_SECONDS)
        with mock.patch.object(render, "_draw_overlay") as overlay:
            result = self._render(1.05, lang="en", synthesis=synth)
        self.assertEqual(result["entries"][0]["text"], "No textual content")
        self.assertEqual(overlay.call_args.args[2], "No textual content")
        self.assertEqual(synth.call_args.args[0], "No textual content")
        self.assertEqual(synth.call_args.kwargs["lang"], "en")

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


class BinaryResolutionTests(unittest.TestCase):
    def test_resolves_from_path(self):
        with mock.patch("shutil.which", return_value="/usr/local/bin/edge-tts"):
            self.assertEqual(_resolve_binary("edge-tts"), "/usr/local/bin/edge-tts")

    def test_resolves_from_venv_when_path_is_none(self):
        exe_name = "edge-tts.exe" if os.name == "nt" else "edge-tts"
        expected = str(Path(sys.executable).parent / exe_name)
        with mock.patch("shutil.which", return_value=None), \
             mock.patch.object(Path, "is_file", return_value=True):
            self.assertEqual(_resolve_binary("edge-tts"), expected)

    def test_raises_when_missing_from_path_and_venv(self):
        with mock.patch("shutil.which", return_value=None), \
             mock.patch.object(Path, "is_file", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "Missing executable: edge-tts"):
                _resolve_binary("edge-tts")

    def test_piper_bin_uses_resolve_binary(self):
        with mock.patch("worker.media.render._resolve_binary", return_value="/custom/piper") as mocked:
            self.assertEqual(_piper_bin(), "/custom/piper")
            mocked.assert_called_once_with("piper")

    def test_edge_tts_bin_uses_resolve_binary(self):
        with mock.patch("worker.media.render._resolve_binary", return_value="/custom/edge-tts") as mocked:
            self.assertEqual(_edge_tts_bin(), "/custom/edge-tts")
            mocked.assert_called_once_with("edge-tts")


class RomanianDiacriticNormalizationTests(unittest.TestCase):
    def test_converts_legacy_cedilla_to_comma_below(self):
        # ş -> ș, ţ -> ț, Ş -> Ș, Ţ -> Ț
        raw = "Aşa şi nu altfel; preţ şi Ţară, Ştefan"
        expected = "Așa și nu altfel; preț și Țară, Ștefan"
        self.assertEqual(normalize_romanian_text(raw), expected)

    def test_preserves_standard_diacritics(self):
        text = "Testăm diacriticele românești: ă, â, î, ș, ț."
        self.assertEqual(normalize_romanian_text(text), text)

    def test_empty_string_handling(self):
        self.assertEqual(normalize_romanian_text(""), "")
        self.assertEqual(normalize_romanian_text(None), "")


class EdgeTTSSynthesizeTests(unittest.TestCase):
    def test_unlinks_mp3_on_success(self):
        output = Path("test_output.wav")
        mp3 = output.with_suffix(".mp3")
        runs = []

        def fake_run(args, **kwargs):
            runs.append(args)
            if "--write-media" in args:
                mp3.write_bytes(b"fake_mp3_data")
            if args[0] == "ffmpeg":
                output.write_bytes(b"fake_wav_data")

        with mock.patch.dict(os.environ, {"TTS_ENGINE": "edge-tts"}), \
             mock.patch("worker.media.render._edge_tts_bin", return_value="/bin/edge-tts"), \
             mock.patch("worker.media.render._run", side_effect=fake_run), \
             mock.patch("worker.media.render._duration", return_value=1.5):
            try:
                duration = _synthesize("Salut lume", output)
                self.assertEqual(duration, 1.5)
                self.assertFalse(mp3.exists(), "Temporary mp3 should be unlinked")
            finally:
                if output.exists():
                    output.unlink()
                if mp3.exists():
                    mp3.unlink()

    def test_unlinks_mp3_on_failure(self):
        output = Path("test_fail.wav")
        mp3 = output.with_suffix(".mp3")

        def fake_run(args, **kwargs):
            if "--write-media" in args:
                mp3.write_bytes(b"fake_mp3_data")
                raise RuntimeError("Network disconnected")

        with mock.patch.dict(os.environ, {"TTS_ENGINE": "edge-tts"}), \
             mock.patch("worker.media.render._edge_tts_bin", return_value="/bin/edge-tts"), \
             mock.patch("worker.media.render._run", side_effect=fake_run):
            try:
                with self.assertRaisesRegex(RuntimeError, "Edge TTS synthesis failed"):
                    _synthesize("Salut lume", output)
                self.assertFalse(mp3.exists(), "Temporary mp3 should be unlinked even on failure")
            finally:
                if output.exists():
                    output.unlink()
                if mp3.exists():
                    mp3.unlink()


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
        from scripts.check_env import chromium_skip_reason
        reason = chromium_skip_reason()
        if reason:
            return reason
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
        cart_id = next(n["id"] for n in nodes["nodes"] if n["selector"] == "#cart")
        selected_ids = {n["id"] for n in nodes["nodes"]
                        if n["selector"] in ("#cart", "#product-image")
                        or (n["role"] == "link" and not n["name"])}
        events = {"events": [e for e in sample_events if e["node_id"] in selected_ids]}
        self.assertEqual(len(events["events"]), 3)
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
        self.assertEqual([e["node_id"] for e in timeline["entries"]],
                         [e["node_id"] for e in events["events"]])
        for entry in timeline["entries"]:
            self.assertLessEqual(entry["end"], clip_seconds + render.CLIP_END_SLACK_SECONDS)
        self.assertEqual(json.loads((out_dir / "timeline.json").read_text(encoding="utf-8")), timeline)

        issues = read_json(SAMPLES / "issues.json")
        report = build_report("e2e", site, nodes, issues, timeline)
        stamps = {i["rule"]: i["timestamp"] for i in report["issues"]}
        cart_start = next(e["start"] for e in timeline["entries"] if e["node_id"] == cart_id)
        self.assertEqual(stamps["button-name"], cart_start)
        self.assertLess(stamps["button-name"], report["duration"])



class EnglishVoiceTests(unittest.TestCase):
    def test_english_model_selection(self):
        with mock.patch.dict(os.environ, {"PIPER_MODEL_EN": "/tmp/custom-en.onnx"}):
            self.assertEqual(render._voice_path("en"), Path("/tmp/custom-en.onnx"))

    def test_english_edge_voice_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "voice.wav"
            def produce(args, **kwargs):
                if "--write-media" in args:
                    output.with_suffix(".mp3").write_bytes(b"mp3")
                if args[0] == "ffmpeg":
                    output.write_bytes(b"wav")
            with mock.patch.dict(os.environ, {"TTS_ENGINE": "edge-tts"}, clear=True):
                with mock.patch.object(render, "_edge_tts_bin", return_value="edge-tts"):
                    with mock.patch.object(render, "_run", side_effect=produce) as runner:
                        with mock.patch.object(render, "_duration", return_value=1.0):
                            self.assertEqual(render._synthesize("Hello", output, lang="en"), 1.0)
                            self.assertIn("en-US-ChristopherNeural", runner.call_args_list[0].args[0])


if __name__ == "__main__":
    unittest.main()
