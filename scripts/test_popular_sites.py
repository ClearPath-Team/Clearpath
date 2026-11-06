#!/usr/bin/env python3
"""Automated End-to-End Testing Harness for Live Popular Websites.

Tests ClearPath against real-world public websites across all pipeline stages:
1. Extraction (CDP AX-tree + sequential Tab walk + focus trap detection)
2. Analysis (Speech announcement generation + axe-core accessibility audit)
3. Render (Piper TTS audio synthesis + Playwright overlay screenshots + ffmpeg video muxing)
4. Report (WCAG scoring + issue timestamp mapping + canonical report assembly)

Outputs a comprehensive JSON summary and markdown report.
"""

import argparse
import json
import os
import sys
import time
import traceback
from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from worker.common import DATA_DIR, read_json, write_json
from worker.pipeline import run_pipeline

DEFAULT_SITES = [
    {"name": "Google", "url": "https://www.google.com", "category": "Search / Minimal"},
    {"name": "Amazon", "url": "https://www.amazon.com", "category": "E-Commerce (Global)"},
    {"name": "Discord", "url": "https://discord.com", "category": "SaaS / Web App"},
    {"name": "eMAG", "url": "https://www.emag.ro", "category": "E-Commerce (Romanian)"},
    {"name": "Wikipedia", "url": "https://en.wikipedia.org", "category": "Content / Reference"},
    {"name": "GitHub", "url": "https://github.com", "category": "Developer Platform"},
    {"name": "Hacker News", "url": "https://news.ycombinator.com", "category": "Minimal / Legacy"},
    {"name": "BBC News", "url": "https://www.bbc.com", "category": "Media / News"},
]

ROMANIAN_SITES = [
    {"name": "Flip.ro", "url": "https://flip.ro", "category": "Refurbished electronics"},
    {"name": "Vivre", "url": "https://vivre.ro", "category": "Home and furniture"},
    {"name": "Tazz", "url": "https://tazz.ro", "category": "Food delivery"},
    {"name": "Pago", "url": "https://pago.ro", "category": "Fintech and bills"},
    {"name": "Salt Bank", "url": "https://salt.bank", "category": "Digital banking"},
    {"name": "Sameday", "url": "https://sameday.ro", "category": "Parcel tracking"},
    {"name": "eJobs", "url": "https://ejobs.ro", "category": "Recruitment"},
    {"name": "Elefant.ro", "url": "https://elefant.ro", "category": "Online retail"},
    {"name": "Kinderpedia", "url": "https://kinderpedia.co", "category": "Education"},
]
REQUIRED_ARTIFACTS = ("status.json", "nodes.json", "events.json", "issues.json",
                      "timeline.json", "report.json", "clip.mp4")


def verify_artifacts(out_dir: Path, *, full_render: bool) -> list[str]:
    """Errors are reported rather than silently labeling partial runs successful."""
    errors = []
    required = REQUIRED_ARTIFACTS if full_render else REQUIRED_ARTIFACTS[:-1]
    for name in required:
        file = out_dir / name
        if not file.is_file() or not file.stat().st_size:
            errors.append(f"Missing or empty {name}")
    if errors:
        return errors
    try:
        status = read_json(out_dir / "status.json")
        events = read_json(out_dir / "events.json")
        issues = read_json(out_dir / "issues.json")
        timeline = read_json(out_dir / "timeline.json")
        report = read_json(out_dir / "report.json")
        if status.get("status") != "done":
            errors.append("Pipeline did not finish with done status")
        if events.get("lang") != "ro" or report.get("lang", "ro") != "ro":
            errors.append("Narration language is not Romanian")
        if len(events.get("events", [])) != len(timeline.get("entries", [])):
            errors.append("Timeline/event cardinality mismatch")
        if len(issues) != len(report.get("issues", [])):
            errors.append("Issue/report cardinality mismatch")
        if full_render and not isinstance(timeline.get("duration"), (float, int)):
            errors.append("Missing clip duration")
        if full_render and report.get("clip_url") is None:
            errors.append("Missing report video URL")
        if report.get("score") is None or not 0 <= report["score"] <= 100:
            errors.append("Invalid accessibility score")
    except (ValueError, KeyError, TypeError, OSError) as exc:
        errors.append(f"Invalid artifact: {exc}")
    return errors


def write_markdown_report(results: list[dict], output: Path, *, full_render: bool) -> None:
    """Write a reviewable evidence manifest, without inventing unrun scores."""
    lines = [
        "# Romanian platform end-to-end audit",
        "",
        f"Generated (UTC): {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Execution mode: {'Full five-stage pipeline (no stubs)' if full_render else 'Development-only partial render stub (not E2E)'}",
        "",
        "Scores describe the evaluated page at the capture time, not the full service or WCAG certification.",
        "Authentication walls, anti-bot interstitials, network and consent overlays require manual review.",
        "",
        "| Platform | Status | Score | Findings (C/S/M/m) | Artifacts | Blocker |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for item in results:
        counts = item["issues_count"]
        severity = "/".join(str(counts.get(key, 0)) for key in ("critical", "serious", "moderate", "minor"))
        score = str(item["score"]) if item["score"] is not None else "—"
        artifact_path = f"data/{item['analysis_id']}/report.json"
        artifact = f"[report]({artifact_path})" if item["status"] == "success" else "—"
        blocker = (item.get("error_message") or "—").replace("|", "/").replace("\n", " ")
        lines.append(f"| {item['name']} | {item['status']} | {score} | {severity} | {artifact} | {blocker} |")
    lines.extend(["", "## Artifact locations", ""])
    for item in results:
        lines.append(f"- **{item['name']}**: `data/{item['analysis_id']}/` — {item['status']}; "
                     f"video: `data/{item['analysis_id']}/clip.mp4`"
                     if item["clip_rendered"] else
                     f"- **{item['name']}**: `data/{item['analysis_id']}/` — {item['status']}; video unavailable")
    lines += ["", "## Limitations", "",
              "- No anti-bot or CAPTCHA bypass is attempted.",
              "- No checkout, invoice payment or account login is performed.",
              "- A consent banner may still obscure content; review page screenshots before claiming accessibility.",
              "- Only runs labelled 'success' have complete, validated artifacts.", ""]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")



def test_site(site_info: dict, run_render: bool = True, romanian: bool = False) -> dict:
    name = site_info["name"]
    url = site_info["url"]
    category = site_info.get("category", "General")
    
    slug = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    # Unique per-run ID avoids mistaking stale reports from previous attempts for success.
    prefix = "e2e-ro-" if romanian else "e2e-"
    analysis_id = f"{prefix}{slug}-{uuid4().hex[:8]}"
    out_dir = DATA_DIR / analysis_id
    
    print(f"\n========================================================")
    print(f"Testing: {name} ({url}) [ID: {analysis_id}]")
    print(f"========================================================")
    
    start_time = time.monotonic()
    previous_stubs = os.environ.get("CP_STUBS")
    result = {
        "name": name,
        "url": url,
        "category": category,
        "analysis_id": analysis_id,
        "status": "pending",
        "error_stage": None,
        "error_message": None,
        "duration_seconds": 0.0,
        "nodes_count": 0,
        "events_count": 0,
        "issues_count": {},
        "total_issues": 0,
        "score": None,
        "trap_detected": False,
        "clip_rendered": False,
        "clip_duration": None,
        "artifact_dir": str(out_dir),
    }
    
    try:
        # If rendering is disabled to run fast audits, we can mock/skip render
        if not run_render:
            os.environ["CP_STUBS"] = "render"
        else:
            os.environ["CP_STUBS"] = ""
            
        # The current main pipeline defaults to Romanian; lang forwarding is a separate M4 task.
        run_pipeline(analysis_id, url)
        
        # Verify generated artifacts
        rep_path = out_dir / "report.json"
        nodes_path = out_dir / "nodes.json"
        events_path = out_dir / "events.json"
        issues_path = out_dir / "issues.json"
        clip_path = out_dir / "clip.mp4"
        timeline_path = out_dir / "timeline.json"
        
        if nodes_path.exists():
            nodes_data = read_json(nodes_path)
            result["nodes_count"] = len(nodes_data.get("nodes", []))
            result["trap_detected"] = bool(nodes_data.get("focus_trap"))
            
        if events_path.exists():
            events_data = read_json(events_path)
            result["events_count"] = len(events_data.get("events", []))
            
        if issues_path.exists():
            issues_data = read_json(issues_path)
            result["total_issues"] = len(issues_data)
            severities = {}
            for iss in issues_data:
                sev = iss.get("severity", "unknown")
                severities[sev] = severities.get(sev, 0) + 1
            result["issues_count"] = severities
            
        if clip_path.exists() and clip_path.stat().st_size > 0:
            result["clip_rendered"] = True
            
        if timeline_path.exists():
            tl_data = read_json(timeline_path)
            result["clip_duration"] = tl_data.get("duration")
            
        if rep_path.exists():
            report_data = read_json(rep_path)
            result["score"] = report_data.get("score")
            failures = verify_artifacts(out_dir, full_render=run_render)
            result["status"] = "success" if not failures else "partial"
            if failures:
                result["error_message"] = "; ".join(failures)
        else:
            result["status"] = "partial"
            result["error_message"] = "report.json was not generated"
            
    except (Exception, SystemExit) as exc:
        result["status"] = "failed"
        result["error_message"] = str(exc)
        
        # Determine failure stage from status.json if available
        status_file = out_dir / "status.json"
        if status_file.exists():
            try:
                st = read_json(status_file)
                result["error_stage"] = st.get("status")
            except Exception:
                pass
        print(f"FAILED on {name}: {exc}")
        traceback.print_exc()
        
    if previous_stubs is None:
        os.environ.pop("CP_STUBS", None)
    else:
        os.environ["CP_STUBS"] = previous_stubs
    result["duration_seconds"] = round(time.monotonic() - start_time, 2)
    print(f"Finished {name} in {result['duration_seconds']}s — Status: {result['status']}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Test ClearPath against popular websites.")
    parser.add_argument("--skip-render", action="store_true", help="Skip video rendering for fast audits (not full E2E)")
    parser.add_argument("--preset", choices=("global", "romanian"), default="global", help="Platform preset")
    parser.add_argument("--markdown", help="Write evidence-based Markdown audit report")
    parser.add_argument("--sites", nargs="*", help="Specific site names or URLs to test")
    parser.add_argument("--output", default="popular_sites_test_report.json", help="Path to save results JSON")
    args = parser.parse_args()
    
    sites_to_test = ROMANIAN_SITES if args.preset == "romanian" else DEFAULT_SITES
    if args.sites:
        filtered = []
        for s in args.sites:
            norm_s = "".join(c for c in s.lower() if c.isalnum())
            match = next((item for item in sites_to_test if "".join(c for c in item["name"].lower() if c.isalnum()) == norm_s), None)
            if match:
                filtered.append(match)
            else:
                filtered.append({"name": s, "url": s if s.startswith("http") else f"https://{s}", "category": "Custom"})
        sites_to_test = filtered

    results = []
    for site in sites_to_test:
        res = test_site(site, run_render=not args.skip_render, romanian=args.preset == "romanian")
        results.append(res)
        
    # Write JSON results
    out_file = Path(args.output)
    write_json(out_file, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_sites": len(results),
        "results": results
    })
    if args.markdown or args.preset == "romanian":
        md = Path(args.markdown) if args.markdown else out_file.with_suffix(".md")
        write_markdown_report(results, md, full_render=not args.skip_render)
        print(f"Markdown audit: {md}")
    print(f"\nAll tests completed. Summary written to {out_file}")


if __name__ == "__main__":
    main()
