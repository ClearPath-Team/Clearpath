"""Regression tests for Piper-safe announcement normalization (issue #29)."""
import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory

from worker.media import render


class PiperAnnouncementTests(unittest.TestCase):
    def test_punctuation_only_uses_spoken_fallback(self):
        for value in ("...", "---", "!!!", "  ", ""):
            with self.subTest(value=value):
                self.assertEqual(render._speakable_announcement(value), "Element fără conținut textual")

    def test_valid_romanian_is_preserved_and_normalized(self):
        self.assertEqual(render._speakable_announcement("  Bună ziua, 123!  "), "Bună ziua, 123!")
        self.assertEqual(render._speakable_announcement("Ştiinţă"), "Știință")

    def test_piper_receives_fallback_not_punctuation(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "voice.wav"
            with patch.dict(render.os.environ, {"TTS_ENGINE": "piper"}), \
                 patch.object(render, "_voice_path", return_value=Path(__file__)), \
                 patch.object(render, "_piper_bin", return_value="piper"), \
                 patch.object(render, "_run") as run, \
                 patch.object(render, "_duration", return_value=1.0):
                def create_wav(*args, **kwargs):
                    output.write_bytes(b"test")
                run.side_effect = create_wav
                self.assertEqual(render._synthesize("...", output), 1.0)
                self.assertEqual(run.call_args.kwargs["input_text"], "Element fără conținut textual")


    def test_render_caption_matches_synthesized_timeline_text(self):
        """Regression: screenshot captions must match what Piper narrates."""
        import sys
        from types import ModuleType, SimpleNamespace
        from unittest.mock import MagicMock

        fake_playwright = MagicMock()
        fake_sync_api = ModuleType("playwright.sync_api")
        fake_sync_api.sync_playwright = MagicMock(return_value=fake_playwright)

        events = {"events": [
            {"seq": 0, "node_id": None, "text": ","},
            {"seq": 1, "node_id": None, "text": "Ştiinţă"},
        ]}
        nodes = {"nodes": [], "viewport": {"width": 640, "height": 480}}
        spoken_texts = []
        with TemporaryDirectory() as directory:
            with (
                patch.dict(sys.modules, {"playwright.sync_api": fake_sync_api}),
                patch.object(render.shutil, "which", return_value="/usr/bin/ffmpeg"),
                patch.object(render, "_synthesize",
                             side_effect=lambda text, output: spoken_texts.append(text) or 1.0),
                patch.object(render, "_run", return_value=SimpleNamespace(stdout="{}")),
                patch.object(render, "_validate_clip_duration", return_value=2.3),
                patch.object(render, "_draw_overlay") as overlay,
            ):
                result = render.render_clip("http://localhost/test", nodes, events, Path(directory))

        timeline_texts = [entry["text"] for entry in result["entries"]]
        caption_texts = [call.args[2] for call in overlay.call_args_list]
        self.assertEqual(timeline_texts, ["Element fără conținut textual", "Știință"])
        self.assertEqual(spoken_texts, timeline_texts)
        self.assertEqual(caption_texts, timeline_texts)


if __name__ == "__main__":
    unittest.main()
