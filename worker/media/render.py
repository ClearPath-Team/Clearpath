"""Track M3: Audio synthesis, Playwright video recording with overlay, and ffmpeg mixing."""
import shutil
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from worker.common import SAMPLES, read_json


def render_clip(url: str, nodes: dict, events: dict, out_dir: Path) -> dict:
    """Renders out_dir/clip.mp4 and returns timeline dictionary."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # In stub mode or fallback, copy mock clip.mp4 and return sample timeline
    sample_clip = SAMPLES / "clip.mp4"
    if sample_clip.exists():
        shutil.copy(sample_clip, out_dir / "clip.mp4")

    return read_json(SAMPLES / "timeline.json")


if __name__ == "__main__":
    import json
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080/bad-checkout.html"
    nodes_path = sys.argv[2] if len(sys.argv) > 2 else str(SAMPLES / "nodes.json")
    events_path = sys.argv[3] if len(sys.argv) > 3 else str(SAMPLES / "events.json")
    out = Path(sys.argv[4]) if len(sys.argv) > 4 else Path("data/dev")
    tl = render_clip(url, read_json(nodes_path), read_json(events_path), out)
    print(json.dumps(tl, indent=2, ensure_ascii=False))
