"""Environment check: python scripts/check_env.py"""
import shutil
import shlex
import sys
import tempfile
import wave
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
results = []


def check(name, fn, hint=""):
    try:
        detail = fn() or ""
        results.append((True, name, detail))
    except Exception as e:
        msg = (str(e).strip().splitlines() or [repr(e)])[0]
        results.append((False, name, f"{msg}  →  {hint}" if hint else msg))


def py_version():
    if sys.version_info < (3, 10):
        raise RuntimeError(f"found {sys.version.split()[0]}, requires 3.10+")
    return sys.version.split()[0]


def chromium():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        v = b.version
        b.close()
    return v


def chromium_install_hint():
    """Use this environment's interpreter, not a potentially different global CLI."""
    if sys.platform == "win32":
        python = f'& "{sys.executable}"'
        return (f"{python} -m playwright install chromium\n"
                "  Windows prerequisite, if Python is missing: "
                "winget install --id Python.Python.3.12 --exact\n"
                "  Linux shared-library packages do not apply to Windows. "
                "Use a supported Windows version and the same user/browser cache as installation.")
    python = shlex.quote(sys.executable)
    if sys.platform == "darwin":
        return (f"{python} -m playwright install chromium\n"
                "  Homebrew prerequisite, if Python is missing: brew install python@3.12\n"
                "  Linux shared-library packages do not apply to macOS. Use a supported macOS version.")
    return ("sudo apt-get update\n"
            f"  sudo {python} -m playwright install-deps chromium\n"
            f"  {python} -m playwright install chromium\n"
            f"  Combined Ubuntu/Debian/WSL setup: {python} -m playwright install --with-deps chromium\n"
            "  OS package installation requires root/sudo; ask the host/image maintainer if unavailable.")


@lru_cache(maxsize=1)
def chromium_skip_reason():
    """Skip only known browser installation/host dependency failures, never audit bugs."""
    from playwright.sync_api import Error as PlaywrightError
    try:
        chromium()
    except PlaywrightError as error:
        message = str(error)
        environmental_errors = (
            "host system is missing dependencies", "executable doesn't exist",
            "error while loading shared libraries", "cannot open shared object file",
            "library not loaded:", "dll was not found", "specified module could not be found",
        )
        if not any(marker in message.lower() for marker in environmental_errors):
            raise
        return f"Chromium unavailable: {message.strip().splitlines()[0]}. Fix: {chromium_install_hint()}"
    return None


def binary(name):
    def f():
        path = shutil.which(name)
        if not path:
            raise RuntimeError(f"{name} is not in PATH")
        return path
    return f


def axe():
    from worker.common import AXE_PATH
    if not Path(AXE_PATH).exists():
        raise RuntimeError(f"missing {AXE_PATH}")
    return AXE_PATH


def piper_synth():
    from worker.common import PIPER_VOICE
    from piper import PiperVoice
    voice = PiperVoice.load(PIPER_VOICE)
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "t.wav"
        with wave.open(str(path), "wb") as wf:
            voice.synthesize_wav("Buton", wf)
        with wave.open(str(path)) as wf:
            return f"{wf.getnframes() / wf.getframerate():.2f}s @ {wf.getframerate()} Hz"


def worker_common():
    from worker.common import SELECTOR_JS
    return f"selector.js loaded ({len(SELECTOR_JS)} chars)"


def main():
    results.clear()
    check("Python", py_version)
    check("worker/common.py + selector.js", worker_common)
    check("Playwright + Chromium", chromium, chromium_install_hint())
    check("ffmpeg", binary("ffmpeg"), "install ffmpeg (see doc/setup/setup.md, step 1)")
    check("ffprobe", binary("ffprobe"), "comes bundled with ffmpeg")
    check("axe-core", axe, "python scripts/fetch_assets.py")
    check("Piper + Romanian voice", piper_synth, "python scripts/fetch_assets.py or set TTS_ENGINE=espeak")
    check("Node.js", binary("node"), "required only for Web UI (Member 4)")
    check("npm", binary("npm"), "required only for Web UI (Member 4)")

    for ok, name, detail in results:
        print(f"{'OK ' if ok else 'NO '} {name:32} {detail}")
    return 0 if all(r[0] for r in results[:7]) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
