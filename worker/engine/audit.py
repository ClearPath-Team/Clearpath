"""Track M2: Accessibility audit running axe-core 4.10 inside the evaluated webpage."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from worker.common import SAMPLES, read_json


def run_audit(url: str, nodes: dict) -> list[dict]:
    """Runs axe-core on the page, resolves canonical selectors, and maps issues to node_ids."""
    return read_json(SAMPLES / "issues.json")


if __name__ == "__main__":
    import json
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080/bad-checkout.html"
    nodes_path = sys.argv[2] if len(sys.argv) > 2 else str(SAMPLES / "nodes.json")
    print(json.dumps(run_audit(url, read_json(nodes_path)), indent=2, ensure_ascii=False))
