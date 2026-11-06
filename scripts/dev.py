"""Starts all services needed for development in a single terminal: python scripts/dev.py
  - test site  http://localhost:8080/bad-checkout.html
  - API        http://localhost:8000/api/health
  - frontend   http://localhost:3000   (only if web/package.json exists)
Ctrl+C stops all services.
"""
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    procs = []
    procs.append(("test-site", subprocess.Popen(
        [sys.executable, "-m", "http.server", "8080", "-d", str(ROOT / "test-site")], cwd=ROOT)))
    procs.append(("api", subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--reload", "--port", "8000",
         "--reload-dir", "api", "--reload-dir", "worker"], cwd=ROOT)))
    npm = shutil.which("npm")
    if (ROOT / "web" / "package.json").exists() and npm:
        procs.append(("web", subprocess.Popen([npm, "run", "dev"], cwd=ROOT / "web")))
    else:
        print("[dev] web/ has no package.json yet or npm is missing: frontend not started")

    print("[dev] running:", ", ".join(n for n, _ in procs), "| Press Ctrl+C to stop")
    try:
        while True:
            for name, p in procs:
                if p.poll() is not None:
                    print(f"[dev] {name} exited with code {p.returncode}")
                    raise KeyboardInterrupt
            time.sleep(1)
    except KeyboardInterrupt:
        for _, p in procs:
            if p.poll() is None:
                p.send_signal(signal.SIGINT) if sys.platform != "win32" else p.terminate()
        for _, p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()


if __name__ == "__main__":
    main()
