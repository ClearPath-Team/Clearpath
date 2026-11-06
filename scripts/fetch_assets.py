"""Downloads axe-core and Piper Romanian voice into assets/. Run once: python scripts/fetch_assets.py"""
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
VOICES = ASSETS / "voices"
VOICE = "ro_RO-mihai-medium"
AXE_URLS = [
    "https://cdn.jsdelivr.net/npm/axe-core@4.10.2/axe.min.js",
    "https://unpkg.com/axe-core@4.10.2/axe.min.js",
]


def fetch_axe():
    dest = ASSETS / "axe.min.js"
    if dest.exists():
        print("axe-core: already exists")
        return True
    for url in AXE_URLS:
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                dest.write_bytes(r.read())
            print(f"axe-core: downloaded from {url}")
            return True
        except Exception as e:
            print(f"axe-core: failed from {url} ({e})")
    npm = shutil.which("npm")
    if npm:  # fallback: npm package
        tmp = ASSETS / "_npm"
        subprocess.run([npm, "install", "axe-core@4.10.2", "--prefix", str(tmp), "--no-save"], check=False, timeout=180)
        src = tmp / "node_modules" / "axe-core" / "axe.min.js"
        if src.exists():
            shutil.copy(src, dest)
            shutil.rmtree(tmp, ignore_errors=True)
            print("axe-core: copied from npm")
            return True
    return False


def fetch_voice():
    onnx_dest = VOICES / f"{VOICE}.onnx"
    json_dest = VOICES / f"{VOICE}.onnx.json"
    if onnx_dest.exists() and json_dest.exists():
        print("Piper voice: already exists")
        return True

    # 1. Try piper.download_voices CLI if available
    try:
        r = subprocess.run([sys.executable, "-m", "piper.download_voices", VOICE, "--data-dir", str(VOICES)], timeout=300)
        if r.returncode == 0 and onnx_dest.exists() and json_dest.exists():
            print("Piper voice: downloaded via piper.download_voices")
            return True
    except Exception as e:
        print(f"Piper voice: CLI download failed ({e}), falling back to direct URL...")

    # 2. Resilient fallback: Direct HTTP download from Hugging Face
    base_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ro/ro_RO/mihai/medium/{VOICE}"
    headers = {"User-Agent": "ClearPath-AssetFetcher/1.0"}
    for filename, dest in [(f"{VOICE}.onnx", onnx_dest), (f"{VOICE}.onnx.json", json_dest)]:
        if dest.exists():
            continue
        url = f"{base_url}.onnx" if filename.endswith(".onnx") else f"{base_url}.onnx.json"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as resp:
                dest.write_bytes(resp.read())
            print(f"Piper voice: downloaded {filename} directly from Hugging Face")
        except Exception as e:
            print(f"Piper voice: failed downloading {filename} from {url} ({e})")
            return False

    ok = onnx_dest.exists() and json_dest.exists()
    print("Piper voice: " + ("downloaded successfully" if ok else "FAILED (see doc/setup/troubleshooting.md)"))
    return ok


if __name__ == "__main__":
    VOICES.mkdir(parents=True, exist_ok=True)
    ok = fetch_axe() & fetch_voice()
    sys.exit(0 if ok else 1)
