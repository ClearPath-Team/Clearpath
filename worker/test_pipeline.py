"""INTEG-01: pipeline handoff regression tests and opt-in live acceptance run.

Mocked tests: python -m unittest worker.test_pipeline
Live: CP_RUN_LIVE_E2E=1 python -m unittest worker.test_pipeline.LivePipelineTests
The live test needs Chromium, axe-core, Piper, ffmpeg/ffprobe and the demo page.
"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from worker import pipeline
from worker.common import ROOT, SAMPLES, read_json
from worker.engine.report import build_report, calculate_score

ARTIFACTS = ("status.json", "nodes.json", "events.json", "issues.json",
             "clip.mp4", "timeline.json", "report.json")


def assert_artifacts(test, folder, *, score=None):
    for filename in ARTIFACTS:
        path = folder / filename
        test.assertTrue(path.is_file(), f"Missing {path}")
        test.assertGreater(path.stat().st_size, 0, f"Empty {path}")
    status = read_json(folder / "status.json")
    test.assertEqual(status["status"], "done", status.get("error"))
    nodes = read_json(folder / "nodes.json")
    events = read_json(folder / "events.json")
    issues = read_json(folder / "issues.json")
    timeline = read_json(folder / "timeline.json")
    report = read_json(folder / "report.json")
    test.assertIsInstance(nodes["nodes"], list)
    test.assertTrue(nodes["nodes"])
    test.assertIsInstance(events["events"], list)
    test.assertTrue(events["events"])
    test.assertIsInstance(issues, list)
    test.assertEqual(set(timeline), {"duration", "clip", "entries"})
    test.assertEqual(timeline["clip"], "clip.mp4")
    test.assertTrue(math.isfinite(timeline["duration"]))
    test.assertGreater(timeline["duration"], 0)
    test.assertEqual(len(timeline["entries"]), len(events["events"]))
    for entry in timeline["entries"]:
        test.assertEqual(set(entry), {"seq", "node_id", "text", "start", "end"})
        test.assertTrue(0 <= entry["start"] < entry["end"])
        test.assertLessEqual(entry["start"], timeline["duration"] + 0.1)
    test.assertEqual(report["duration"], timeline["duration"])
    test.assertTrue(math.isfinite(report["score"]))
    test.assertEqual(report["score"], calculate_score(issues, bool(nodes.get("focus_trap"))))
    test.assertEqual(report["focus_trap"], bool(nodes.get("focus_trap")) or
                     any(i["rule"] == "keyboard-trap" for i in issues))
    if score is not None:
        test.assertEqual(report["score"], score)
    return nodes, events, issues, timeline, report


class MockedPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cp-integ-mock-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.data_patch = mock.patch.object(pipeline, "DATA_DIR", self.folder)
        self.data_patch.start()
        self.addCleanup(self.data_patch.stop)

    def test_all_stage_handoffs_and_artifacts(self):
        nodes = read_json(SAMPLES / "nodes.json")
        events = read_json(SAMPLES / "events.json")
        issues = read_json(SAMPLES / "issues.json")
        timeline = read_json(SAMPLES / "timeline.json")
        observed = []

        def fake_extract(url):
            observed.append("extract")
            self.assertEqual(url, "http://localhost:8080/bad-checkout.html")
            return nodes

        def fake_events(value):
            observed.append("events")
            self.assertIs(value, nodes)
            return events

        def fake_audit(url, value):
            observed.append("audit")
            self.assertIs(value, nodes)
            return issues

        def fake_render(url, value_nodes, value_events, out):
            observed.append("render")
            self.assertIs(value_nodes, nodes)
            self.assertIs(value_events, events)
            (out / "clip.mp4").write_bytes(b"mock mp4 - not a playable video")
            return timeline

        original_report = build_report
        def report_wrapper(*args):
            observed.append("report")
            self.assertIs(args[2], nodes)
            self.assertIs(args[3], issues)
            self.assertIs(args[4], timeline)
            return original_report(*args)

        with mock.patch.dict(os.environ, {"CP_STUBS": ""}), \
             mock.patch("worker.extract.extract.extract", side_effect=fake_extract), \
             mock.patch("worker.engine.events.build_events", side_effect=fake_events), \
             mock.patch("worker.engine.audit.run_audit", side_effect=fake_audit), \
             mock.patch("worker.media.render.render_clip", side_effect=fake_render), \
             mock.patch("worker.engine.report.build_report", side_effect=report_wrapper):
            pipeline.run_pipeline("mock", "http://localhost:8080/bad-checkout.html")

        self.assertEqual(observed, ["extract", "events", "audit", "render", "report"])
        assert_artifacts(self, self.folder / "mock", score=33)

    def test_failed_stage_sets_failed_status(self):
        with mock.patch.dict(os.environ, {"CP_STUBS": ""}), \
             mock.patch("worker.extract.extract.extract", side_effect=RuntimeError("extract failed")), \
             mock.patch.object(pipeline.sys, "exit", side_effect=SystemExit(1)):
            with self.assertRaises(SystemExit) as error:
                pipeline.run_pipeline("failed", "http://localhost:8080/bad-checkout.html")
        self.assertEqual(error.exception.code, 1)
        status = read_json(self.folder / "failed" / "status.json")
        self.assertEqual(status["status"], "failed")
        self.assertIn("extract failed", status["error"])
        self.assertFalse((self.folder / "failed" / "report.json").exists())

    def test_keyboard_trap_penalty_applied_once(self):
        issues = read_json(SAMPLES / "issues.json")
        trap = next(i for i in issues if i["rule"] == "keyboard-trap")
        self.assertEqual(calculate_score(issues, has_focus_trap=True), 33)
        self.assertEqual(calculate_score(issues + [trap], has_focus_trap=True), 33)


class LivePipelineTests(unittest.TestCase):
    def test_zero_stubs_bad_checkout(self):
        if os.environ.get("CP_RUN_LIVE_E2E") != "1":
            self.skipTest("Opt in with CP_RUN_LIVE_E2E=1 (requires browser, Piper, ffmpeg and assets)")
        from scripts.check_env import chromium_skip_reason
        reason = chromium_skip_reason()
        if reason:
            self.skipTest(reason)
        for executable in ("ffmpeg", "ffprobe"):
            if not shutil.which(executable):
                self.skipTest(f"{executable} not installed")
        from worker.common import AXE_PATH
        if not Path(AXE_PATH).is_file():
            self.skipTest(f"axe-core missing: {AXE_PATH}")
        from worker.media.render import _piper_bin, _voice_path
        try:
            _piper_bin()
        except RuntimeError as error:
            self.skipTest(str(error))
        if not _voice_path().is_file():
            self.skipTest(f"Piper model missing: {_voice_path()}")

        handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT / "test-site"))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory(prefix="cp-integ-live-") as directory:
                analysis_id = "ck-live"
                env = {**os.environ, "CP_STUBS": "", "TTS_ENGINE": "piper",
                       "DATA_DIR": directory}
                url = f"http://127.0.0.1:{server.server_port}/bad-checkout.html"
                result = subprocess.run(
                    [sys.executable, "-m", "worker.pipeline", analysis_id, url],
                    cwd=ROOT, env=env, capture_output=True, text=True,
                    encoding="utf-8", errors="replace", timeout=360,
                )
                self.assertEqual(result.returncode, 0,
                                 f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
                nodes, events, issues, timeline, report = assert_artifacts(
                    self, Path(directory) / analysis_id, score=33)
                self.assertEqual(len(issues), 9)  # 8 axe findings + keyboard trap
                self.assertEqual(nodes["focus_trap"]["selector"], "#promo")
                cart = next(n for n in nodes["nodes"] if n.get("selector") == "#cart")
                cart_events = [e for e in events["events"]
                               if e.get("node_id") == cart["id"]]
                self.assertTrue(cart_events, "Cart button missing from speech events")
                self.assertTrue(any("buton" in e["text"].lower() for e in cart_events))
                cart_entries = [e for e in timeline["entries"]
                                if e["node_id"] == cart["id"]]
                self.assertTrue(cart_entries, "Cart button missing from timeline")
                self.assertTrue(any(i.get("timestamp") is not None
                                    for i in report["issues"]
                                    if i.get("node_id") == cart["id"]))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
