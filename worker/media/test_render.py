"""Unit tests for binary resolution and synthesis in worker.media.render."""
import os
import shutil
import sys
import unittest
from pathlib import Path
from unittest import mock

from worker.media.render import (
    _resolve_binary,
    _piper_bin,
    _edge_tts_bin,
    _synthesize,
)


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
                mp3.touch()
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


if __name__ == "__main__":
    unittest.main()
