"""Track M2: Report assembler and accessibility score calculator."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from worker.common import SAMPLES, read_json, write_json

SEVERITIES = ("critical", "serious", "moderate", "minor")


def calculate_score(issues: list, has_focus_trap: bool = False) -> int:
    """Apply issue #2 weights (10/5/2/1), plus a single independent trap penalty.

    This issue-specific scoring policy was explicitly selected over the older
    contract formula (10/6/3/1 with per-rule caps). The supplied issues score 38.
    """
    weights = {"critical": 10, "serious": 5, "moderate": 2, "minor": 1}
    penalties = sum(weights[issue["severity"]] for issue in issues if issue["rule"] != "keyboard-trap")
    has_trap = has_focus_trap or any(issue["rule"] == "keyboard-trap" for issue in issues)
    return max(0, round(100 - penalties - (15 if has_trap else 0)))


def build_report(analysis_id: str, url: str, nodes: dict, issues: list, timeline: dict) -> dict:
    """Assembles final report mapping timestamps, counts, and calculated score."""
    starts = {}
    for entry in timeline.get("entries", []):
        node_id = entry.get("node_id")
        start = entry.get("start")
        if node_id is not None and start is not None:
            starts[node_id] = min(starts.get(node_id, start), start)
    enriched = [{**issue, "timestamp": starts.get(issue.get("node_id"))} for issue in issues]
    enriched.sort(key=lambda issue: (
        SEVERITIES.index(issue["severity"]), issue["timestamp"] is None,
        issue["timestamp"] if issue["timestamp"] is not None else 0))
    has_trap = bool(nodes.get("focus_trap")) or any(issue["rule"] == "keyboard-trap" for issue in issues)
    return {
        "id": analysis_id, "url": url, "title": nodes.get("title") or "",
        "score": calculate_score(issues, has_focus_trap=has_trap),
        "counts": {severity: sum(issue["severity"] == severity for issue in issues) for severity in SEVERITIES},
        "clip_url": f"/media/{analysis_id}/clip.mp4", "duration": timeline["duration"],
        "focus_trap": has_trap, "issues": enriched,
    }


if __name__ == "__main__":
    import json
    issues_path = sys.argv[1] if len(sys.argv) > 1 else str(SAMPLES / "issues.json")
    timeline_path = sys.argv[2] if len(sys.argv) > 2 else str(SAMPLES / "timeline.json")
    nodes_path = sys.argv[3] if len(sys.argv) > 3 else str(SAMPLES / "nodes.json")
    rep = build_report("test", "http://localhost:8080/bad-checkout.html", read_json(nodes_path), read_json(issues_path), read_json(timeline_path))
    if len(sys.argv) > 4:
        write_json(Path(sys.argv[4]), rep)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps(rep, indent=2, ensure_ascii=False))
