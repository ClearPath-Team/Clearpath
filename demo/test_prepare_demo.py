"""Staging regressions; synthetic MP4 headers are not playback test fixtures."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_demo", ROOT / "scripts/prepare_demo.py")
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class PrepareDemoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cache = self.root / "demo"
        self.data = self.root / "data"
        for run_id in demo.RUN_IDS:
            directory = self.cache / run_id
            directory.mkdir(parents=True)
            url = "https://example.com/" + run_id
            issue = {"id": "i1", "rule": "image-alt", "node_id": "n0", "severity": "critical"}
            event = {"seq": 0, "node_id": "n0", "text": "Imagine"}
            documents = {
                "status.json": {"id": run_id, "url": url, "status": "done", "error": None},
                "nodes.json": {"url": url, "nodes": [{"id": "n0"}]},
                "events.json": {"events": [event]},
                "issues.json": [issue],
                "timeline.json": {"duration": 3, "clip": "clip.mp4", "entries": [{**event, "start": 1, "end": 2}]},
                "report.json": {"id": run_id, "url": url, "score": 90, "duration": 3,
                                "clip_url": f"/media/{run_id}/clip.mp4", "issues": [{**issue, "timestamp": 1}]},
            }
            for name, value in documents.items():
                (directory / name).write_text(json.dumps(value), encoding="utf-8")
            (directory / "clip.mp4").write_bytes(b"\x00\x00\x00\x18ftypisom" + bytes(2048))
        demo.write_manifest(self.cache)

    def test_fresh_staging_and_idempotence(self):
        demo.prepare(self.cache, self.data)
        with patch.object(demo, "atomic_copy", wraps=demo.atomic_copy) as copy:
            demo.prepare(self.cache, self.data)
            copy.assert_not_called()
        for run_id in demo.RUN_IDS:
            self.assertEqual(demo.digest(self.cache / run_id / "clip.mp4"),
                             demo.digest(self.data / run_id / "clip.mp4"))

    def test_manifest_can_be_refreshed_without_hand_editing_hashes(self):
        manifest = demo.write_manifest(self.cache)
        self.assertEqual(manifest, demo.read_json(self.cache / "manifest.json"))
        self.assertEqual(manifest["runs"]["site1"]["timestamped_critical_issues"], 1)

    def test_cli_honors_the_api_data_dir(self):
        configured = self.root / "configured-data"
        result = subprocess.run([sys.executable, str(ROOT / "scripts/prepare_demo.py"),
                                 "--demo-dir", str(self.cache)], cwd=self.root,
                                env={**os.environ, "DATA_DIR": str(configured)},
                                capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((configured / "site2/report.json").is_file())

    def test_existing_conflict_requires_force(self):
        demo.prepare(self.cache, self.data)
        path = self.data / "site1/report.json"
        path.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Existing artifact differs"):
            demo.prepare(self.cache, self.data)
        self.assertEqual(path.read_text(), "{}")
        demo.prepare(self.cache, self.data, force=True)
        self.assertEqual(demo.digest(path), demo.digest(self.cache / "site1/report.json"))

    def test_corrupt_cache_is_rejected_before_any_copy(self):
        with (self.cache / "site2/clip.mp4").open("ab") as stream:
            stream.write(b"corrupt")
        with self.assertRaisesRegex(ValueError, "integrity check failed"):
            demo.prepare(self.cache, self.data)
        self.assertFalse(self.data.exists())

    def test_issue_identity_mismatch_with_same_count_is_rejected(self):
        path = self.cache / "site1/issues.json"
        issues = demo.read_json(path)
        issues[0]["id"] = "different"
        path.write_text(json.dumps(issues), encoding="utf-8")
        previous = (self.cache / "manifest.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "issue identities do not match"):
            demo.write_manifest(self.cache)
        self.assertEqual(previous, (self.cache / "manifest.json").read_bytes())

    def test_failed_copy_does_not_publish_partial_data(self):
        self.data.mkdir()
        destination = self.data / "clip.mp4"
        destination.write_bytes(b"previous artifact")
        source = self.cache / "site1/clip.mp4"
        expected = demo.read_json(self.cache / "manifest.json")["runs"]["site1"]["files"]["clip.mp4"]
        def broken_copy(src, target):
            Path(target).write_bytes(b"partial")
            raise OSError("interrupted copy")
        with patch.object(demo.shutil, "copy2", side_effect=broken_copy):
            with self.assertRaisesRegex(OSError, "interrupted copy"):
                demo.atomic_copy(source, destination, expected)
        self.assertEqual(destination.read_bytes(), b"previous artifact")
        self.assertEqual(list(self.data.iterdir()), [destination])

    def test_clips_longer_than_90_seconds_are_rejected(self):
        for name in ("timeline.json", "report.json"):
            path = self.cache / "site1" / name
            document = demo.read_json(path)
            document["duration"] = 91
            path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "90-second"):
            demo.write_manifest(self.cache)

    def test_each_demo_requires_a_timestamped_critical_finding(self):
        for name in ("issues.json", "report.json"):
            path = self.cache / "site1" / name
            document = demo.read_json(path)
            issues = document if isinstance(document, list) else document["issues"]
            issues[0]["severity"] = "serious"
            path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "no narrated critical issue"):
            demo.write_manifest(self.cache)

    def test_destination_files_are_hashed_only_once(self):
        with patch.object(demo, "digest", wraps=demo.digest) as digest:
            demo.prepare(self.cache, self.data)
        # One source hash plus one copied temporary/destination hash per artifact.
        self.assertEqual(digest.call_count, len(demo.RUN_IDS) * len(demo.REQUIRED) * 2)


if __name__ == "__main__":
    unittest.main()
