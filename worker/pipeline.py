"""Pipeline orchestrator for ClearPath.
Runs all 5 stages sequentially and handles mock stubs via CP_STUBS environment variable.
Usage: python -m worker.pipeline <analysis_id> <url>
"""
import os
import shutil
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from worker.common import DATA_DIR, SAMPLES, now_iso, read_json, write_json


def is_stubbed(stage: str) -> bool:
    """Checks if a given pipeline stage should use mock data from contracts/samples/."""
    cp_stubs = os.getenv("CP_STUBS", "").strip().lower()
    if not cp_stubs:
        return False
    if cp_stubs == "all":
        return True
    active_stubs = [s.strip() for s in cp_stubs.split(",")]
    return stage in active_stubs


def update_status(out_dir: Path, analysis_id: str, url: str, status: str, error: str = None) -> None:
    """Updates data/{id}/status.json."""
    status_obj = {
        "id": analysis_id,
        "url": url,
        "status": status,
        "error": error,
        "updated_at": now_iso(),
    }
    write_json(out_dir / "status.json", status_obj)


def run_pipeline(analysis_id: str, url: str) -> None:
    out_dir = DATA_DIR / analysis_id
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Stage 1: Extract (Accessibility tree + Tab walk)
        update_status(out_dir, analysis_id, url, "extracting")
        if is_stubbed("extract"):
            nodes = read_json(SAMPLES / "nodes.json")
            nodes["url"] = url
        else:
            from worker.extract.extract import extract
            nodes = extract(url)
        write_json(out_dir / "nodes.json", nodes)

        # Stage 2: Analyze (Events + Audit)
        update_status(out_dir, analysis_id, url, "analyzing")
        if is_stubbed("events"):
            events = read_json(SAMPLES / "events.json")
        else:
            from worker.engine.events import build_events
            events = build_events(nodes)
        write_json(out_dir / "events.json", events)

        if is_stubbed("audit"):
            issues = read_json(SAMPLES / "issues.json")
        else:
            from worker.engine.audit import run_audit
            issues = run_audit(url, nodes)
        write_json(out_dir / "issues.json", issues)

        # Stage 3: Render (Video clip + Timeline)
        update_status(out_dir, analysis_id, url, "rendering")
        if is_stubbed("render"):
            timeline = read_json(SAMPLES / "timeline.json")
            sample_clip = SAMPLES / "clip.mp4"
            if sample_clip.exists():
                shutil.copy(sample_clip, out_dir / "clip.mp4")
        else:
            from worker.media.render import render_clip
            timeline = render_clip(url, nodes, events, out_dir)
        write_json(out_dir / "timeline.json", timeline)

        # Stage 4: Report (Assembly + Scoring)
        if is_stubbed("report"):
            report = read_json(SAMPLES / "report.json")
            report["id"] = analysis_id
            report["url"] = url
            report["clip_url"] = f"/media/{analysis_id}/clip.mp4"
        else:
            from worker.engine.report import build_report
            report = build_report(analysis_id, url, nodes, issues, timeline)
        write_json(out_dir / "report.json", report)

        # Final status: Done
        update_status(out_dir, analysis_id, url, "done")
        print(f"[pipeline:{analysis_id}] Completed successfully.")

    except Exception as e:
        err_msg = str(e).strip() or "Eroare la procesarea analizei."
        print(f"[pipeline:{analysis_id}] Error: {err_msg}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        update_status(out_dir, analysis_id, url, "failed", error=err_msg)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m worker.pipeline <analysis_id> <url>", file=sys.stderr)
        sys.exit(1)
    run_pipeline(sys.argv[1], sys.argv[2])
