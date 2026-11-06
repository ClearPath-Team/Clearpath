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


def test_site(site_info: dict, run_render: bool = True) -> dict:
    name = site_info["name"]
    url = site_info["url"]
    category = site_info.get("category", "General")
    
    slug = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    analysis_id = f"e2e-{slug}"
    out_dir = DATA_DIR / analysis_id
    
    print(f"\n========================================================")
    print(f"Testing: {name} ({url}) [ID: {analysis_id}]")
    print(f"========================================================")
    
    start_time = time.monotonic()
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
    }
    
    try:
        # If rendering is disabled to run fast audits, we can mock/skip render
        if not run_render:
            os.environ["CP_STUBS"] = "render"
        else:
            os.environ["CP_STUBS"] = ""
            
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
            result["status"] = "success"
        else:
            result["status"] = "partial"
            result["error_message"] = "report.json was not generated"
            
    except Exception as exc:
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
        
    result["duration_seconds"] = round(time.monotonic() - start_time, 2)
    print(f"Finished {name} in {result['duration_seconds']}s — Status: {result['status']}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Test ClearPath against popular websites.")
    parser.add_argument("--skip-render", action="store_true", help="Skip video rendering for fast audits")
    parser.add_argument("--sites", nargs="*", help="Specific site names or URLs to test")
    parser.add_argument("--output", default="popular_sites_test_report.json", help="Path to save results JSON")
    args = parser.parse_args()
    
    sites_to_test = DEFAULT_SITES
    if args.sites:
        filtered = []
        for s in args.sites:
            norm_s = "".join(c for c in s.lower() if c.isalnum())
            match = next((item for item in DEFAULT_SITES if "".join(c for c in item["name"].lower() if c.isalnum()) == norm_s), None)
            if match:
                filtered.append(match)
            else:
                filtered.append({"name": s, "url": s if s.startswith("http") else f"https://{s}", "category": "Custom"})
        sites_to_test = filtered

    results = []
    for site in sites_to_test:
        res = test_site(site, run_render=not args.skip_render)
        results.append(res)
        
    # Write JSON results
    out_file = Path(args.output)
    write_json(out_file, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_sites": len(results),
        "results": results
    })
    print(f"\nAll tests completed. Summary written to {out_file}")


if __name__ == "__main__":
    main()
