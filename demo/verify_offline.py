"""Replay and seek every demo in Edge, optionally with the host network offline.

Use verify_offline.ps1 for the physical-network rehearsal on Windows. This script
does not disable adapters itself. --launch-stack owns and cleans up its processes.
"""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.parse import urlparse
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def check_disconnected():
    try:
        connection = socket.create_connection(("1.1.1.1", 443), timeout=2)
    except OSError:
        pass
    else:
        connection.close()
        raise RuntimeError("External TCP connectivity is still available; offline test refused")
    if sys.platform == "win32":
        result = subprocess.run(["powershell.exe", "-NoProfile", "-Command",
                                 "@(Get-NetAdapter -Physical -ErrorAction Stop | Where-Object Status -eq 'Up').Count"],
                                capture_output=True, check=True, timeout=5)
        if int(result.stdout.strip()) != 0:
            raise RuntimeError("A physical adapter is still connected; turn Wi-Fi off before the physical test")


def verify(require_disconnected=False, launch_stack=False):
    from playwright.sync_api import sync_playwright, expect
    manifest = json.loads((ROOT / "demo/manifest.json").read_text(encoding="utf-8"))
    if require_disconnected:
        check_disconnected()
    manager = None
    log = None
    try:
        if launch_stack:
            for port in (3000, 8000, 8080):
                with socket.socket() as probe:
                    probe.settimeout(0.2)
                    if probe.connect_ex(("127.0.0.1", port)) == 0:
                        raise RuntimeError(f"Port {port} is occupied; stop the existing dev stack first")
            (ROOT / "data").mkdir(exist_ok=True)
            log = (ROOT / "data/offline-stack.log").open("w", encoding="utf-8")
            environment = {**os.environ, "CP_STUBS": "", "TTS_ENGINE": "piper", "NEXT_TELEMETRY_DISABLED": "1"}
            manager = subprocess.Popen([sys.executable, "scripts/dev.py"], cwd=ROOT,
                                       env=environment, stdout=log, stderr=subprocess.STDOUT,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                                       start_new_session=os.name != "nt")
            deadline = time.monotonic() + 25
            while True:
                try:
                    for url in ("http://localhost:8000/api/health", "http://localhost:3000",
                                "http://localhost:8080/bad-checkout.html"):
                        with urlopen(url, timeout=2) as response:
                            if response.status != 200:
                                raise OSError(f"{url}: HTTP {response.status}")
                    break
                except OSError:
                    if manager.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError("Dev stack did not start; inspect data/offline-stack.log")
                    time.sleep(0.25)
        evidence = {"browser": "Microsoft Edge", "host_network_disconnected": require_disconnected,
                    "stack_started_while_disconnected": launch_stack and require_disconnected, "runs": {}}
        if require_disconnected:
            evidence["external_tcp_unavailable_at_start_and_end"] = True
            if sys.platform == "win32":
                evidence["physical_adapters_up_at_start_and_end"] = 0
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge")
            try:
                evidence["browser_version"] = browser.version
                context = browser.new_context(viewport={"width": 1440, "height": 1000},
                                              service_workers="block",
                                              record_video_dir=str(ROOT / "data/offline-recording"),
                                              record_video_size={"width": 1280, "height": 720})
                external, errors = [], []
                page = context.new_page()
                page.on("request", lambda request: external.append(request.url)
                        if urlparse(request.url).hostname not in ("localhost", "127.0.0.1", "::1", None) else None)
                page.on("pageerror", lambda error: errors.append(str(error)))
                for run_id, record in manifest["runs"].items():
                    report = json.loads((ROOT / "demo" / run_id / "report.json").read_text(encoding="utf-8"))
                    media = []
                    capture_media = lambda response: media.append(response.status) if "/media/" in response.url else None
                    page.on("response", capture_media)
                    page.goto(f"http://localhost:3000/a/{run_id}", wait_until="networkidle", timeout=15000)
                    expect(page.locator("span.text-3xl.tracking-tight.leading-none")).to_have_text(str(record["score"]))
                    page.wait_for_function('document.querySelector("video")?.readyState >= 2', timeout=5000)
                    issue = next(i for i in report["issues"] if i["severity"] == "critical"
                                 and i["timestamp"] is not None and 0 < i["timestamp"] < record["duration"] - 2)
                    seconds = issue["timestamp"]
                    label = f"{int(seconds) // 60}:{int(seconds) % 60:02d}"
                    page.get_by_role("button", name=label, exact=True).first.click()
                    page.wait_for_function('!document.querySelector("video").paused', timeout=5000)
                    observed = page.locator("video").evaluate("video => video.currentTime")
                    if abs(observed - seconds) >= 2:
                        raise RuntimeError(f"{run_id}: timestamp seek did not reach the expected time")
                    active = page.locator("div.rounded-xl.border.transition-all.border-indigo-500")
                    expect(active).to_have_count(1)
                    expect(active).to_have_css("background-color", "rgb(30, 41, 59)")
                    page.wait_for_timeout(750)
                    if page.locator("video").evaluate("video => video.currentTime") <= observed or 206 not in media:
                        raise RuntimeError(f"{run_id}: playback/range request failed")
                    page.locator("video").evaluate("video => video.pause()")
                    evidence["runs"][run_id] = {"score": record["score"], "range_status": 206,
                                               "critical_issue_id": issue["id"], "seek_seconds": seconds,
                                               "observed_seek_seconds": round(observed, 3),
                                               "video_played": True, "active_card_highlight": True}
                    page.remove_listener("response", capture_media)
                    print(f"OK offline playback: {run_id}, critical timestamp={seconds}", flush=True)
                if external or errors:
                    raise RuntimeError(f"Unexpected external requests/browser errors: {external}, {errors}")
                if require_disconnected:
                    check_disconnected()
                evidence.update(external_requests=external, browser_errors=errors)
                recording = page.video
                page.close()
                context.close()
                recording.save_as(str(ROOT / "demo/offline-playback.webm"))
            finally:
                browser.close()
        (ROOT / "demo/verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    finally:
        if manager is not None and manager.poll() is None:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(manager.pid), "/T", "/F"], capture_output=True)
            else:
                import signal
                os.killpg(manager.pid, signal.SIGTERM)
            manager.wait(timeout=10)
        if log is not None:
            log.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-disconnected", action="store_true")
    parser.add_argument("--launch-stack", action="store_true")
    args = parser.parse_args()
    verify(args.require_disconnected, args.launch_stack)
