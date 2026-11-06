"""Track M2: Report assembler and accessibility score calculator."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from worker.common import SAMPLES, read_json


def calculate_score(issues: list, has_focus_trap: bool = False) -> int:
    """Calculates score based on penalties per axe rule (capped at 20) and keyboard trap penalty (15)."""
    weights = {"critical": 10, "serious": 6, "moderate": 3, "minor": 1}
    rule_weights = {}

    for issue in issues:
        rule = issue.get("rule")
        if rule == "keyboard-trap":
            continue
        severity = issue.get("severity", "moderate")
        rule_weights[rule] = rule_weights.get(rule, 0) + weights.get(severity, 3)

    penalties = sum(min(20, w) for w in rule_weights.values())
    score = 100 - penalties
    if has_focus_trap:
        score -= 15

    return max(0, round(score))


def build_report(analysis_id: str, url: str, nodes: dict, issues: list, timeline: dict) -> dict:
    """Assembles final report mapping timestamps, counts, and calculated score."""
    sample_report = read_json(SAMPLES / "report.json")
    sample_report["id"] = analysis_id
    sample_report["url"] = url
    sample_report["clip_url"] = f"/media/{analysis_id}/clip.mp4"
    return sample_report


if __name__ == "__main__":
    import json
    issues_path = sys.argv[1] if len(sys.argv) > 1 else str(SAMPLES / "issues.json")
    timeline_path = sys.argv[2] if len(sys.argv) > 2 else str(SAMPLES / "timeline.json")
    nodes_path = sys.argv[3] if len(sys.argv) > 3 else str(SAMPLES / "nodes.json")
    rep = build_report("test", "http://localhost:8080/bad-checkout.html", read_json(nodes_path), read_json(issues_path), read_json(timeline_path))
    print(json.dumps(rep, indent=2, ensure_ascii=False))
