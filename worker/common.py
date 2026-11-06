"""Shared constants and utilities for the entire worker. Modify only with team consensus."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

try:  # .env from repo root
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data"))
SAMPLES = ROOT / "contracts" / "samples"
SELECTOR_JS = (ROOT / "contracts" / "selector.js").read_text(encoding="utf-8").strip().rstrip(";")
AXE_PATH = os.getenv("AXE_PATH", str(ROOT / "assets" / "axe.min.js"))
PIPER_VOICE = os.getenv("PIPER_VOICE", str(ROOT / "assets" / "voices" / "ro_RO-mihai-medium.onnx"))
TTS_ENGINE = os.getenv("TTS_ENGINE", "piper")  # piper | espeak | say
VIEWPORT = {"width": 1280, "height": 720}
MAX_EVENTS = int(os.getenv("MAX_EVENTS", "40"))
VIDEO_OFFSET = float(os.getenv("VIDEO_OFFSET", "0.0"))
KEEP_TMP = os.getenv("KEEP_TMP", "0") == "1"
TEST_URL = os.getenv("TEST_URL", "http://localhost:8080/bad-checkout.html")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
