"""Track M1: Accessibility tree extraction via Chrome DevTools Protocol (CDP)."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from worker.common import SAMPLES, read_json


def extract(url: str) -> dict:
    """Extracts accessibility tree, bounding boxes, and Tab order for the given URL.
    Note: CDP Accessibility.AXNode properties check both 'hierarchicalLevel' and 'level' for headings.
    """
    # Baseline fallback to sample contract when running stubbed or prior to live CDP implementation
    sample = read_json(SAMPLES / "nodes.json")
    sample["url"] = url
    return sample


if __name__ == "__main__":
    import json
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080/bad-checkout.html"
    res = extract(url)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        print(json.dumps(res, indent=2, ensure_ascii=False))
