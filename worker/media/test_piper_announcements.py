"""Regression tests for Piper-safe announcement normalization (issue #29)."""
import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory

from worker.media import render


class PiperAnnouncementTests(unittest.TestCase):
    def test_punctuation_only_uses_spoken_fallback(self):
        for value in ("...", "---", "!!!", "  ", "", "|", "."):
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


if __name__ == "__main__":
    unittest.main()
