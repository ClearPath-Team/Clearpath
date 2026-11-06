"""Validate cached demo artifacts and stage them for offline presentation.

Run from any directory: python scripts/prepare_demo.py
No browser, TTS engine or network connection needed for staging.
"""
import argparse
import hashlib
import json
import math
import os
import shutil
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_IDS = ("bad-checkout", "site1", "site2")
REQUIRED = ("status.json", "nodes.json", "events.json", "issues.json",
            "clip.mp4", "timeline.json", "report.json")


def digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def default_data_dir():
    # Read the same .env and DATA_DIR definition as the API. Import lazily so
    # explicit --data-dir/--verify-only usage does not need application imports.
    sys.path.insert(0, str(ROOT))
    from worker.common import DATA_DIR
    path = Path(DATA_DIR)
    return path if path.is_absolute() else ROOT / path


def validate_run(directory, record, *, verify_hashes=True):
    """Check hashes, playback metadata and cross-file references before copying."""
    run_id = directory.name
    if directory.is_symlink():
        raise ValueError(f"{run_id}: cache directory must not be a symlink")
    for name in REQUIRED:
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"{run_id}: missing or unsafe artifact {name}")
        expected = record["files"][name]
        if path.stat().st_size != expected["bytes"] or (verify_hashes and digest(path) != expected["sha256"]):
            raise ValueError(f"{run_id}: integrity check failed for {name}")
    status = read_json(directory / "status.json")
    report = read_json(directory / "report.json")
    nodes = read_json(directory / "nodes.json")
    events = read_json(directory / "events.json")["events"]
    timeline = read_json(directory / "timeline.json")
    issues = read_json(directory / "issues.json")
    if status["status"] != "done" or status.get("error") is not None:
        raise ValueError(f"{run_id}: analysis is not complete")
    if status["id"] != run_id or report["id"] != run_id:
        raise ValueError(f"{run_id}: cached IDs do not match their directory")
    if not (status["url"] == report["url"] == nodes["url"] == record["url"]):
        raise ValueError(f"{run_id}: source URL mismatch")
    if report["clip_url"] != f"/media/{run_id}/clip.mp4" or timeline["clip"] != "clip.mp4":
        raise ValueError(f"{run_id}: invalid local clip reference")
    duration = timeline["duration"]
    if not isinstance(duration, (float, int)) or not math.isfinite(duration) or duration <= 0:
        raise ValueError(f"{run_id}: invalid video duration")
    if duration > 90:
        raise ValueError(f"{run_id}: clip exceeds the 90-second presentation bound")
    if report["duration"] != duration or report["score"] != record["score"]:
        raise ValueError(f"{run_id}: report metrics mismatch")
    if not events or len(events) != len(timeline["entries"]):
        raise ValueError(f"{run_id}: timeline must contain one entry per event")
    node_ids = {node["id"] for node in nodes["nodes"]}
    starts = {}
    previous_end = 0
    for seq, (event, entry) in enumerate(zip(events, timeline["entries"])):
        if (entry["seq"] != seq or event["seq"] != seq
                or entry["node_id"] != event["node_id"] or entry["text"] != event["text"].strip()):
            raise ValueError(f"{run_id}: mismatched event/timeline entry {seq}")
        start, end = entry["start"], entry["end"]
        if not (math.isfinite(start) and math.isfinite(end)
                and previous_end <= start < end <= duration + 0.1):
            raise ValueError(f"{run_id}: invalid timeline interval {seq}")
        previous_end = end
        node_id = entry["node_id"]
        if node_id is not None:
            if node_id not in node_ids:
                raise ValueError(f"{run_id}: unknown node {node_id}")
            starts[node_id] = min(starts.get(node_id, start), start)
    identity = lambda issue: (issue["id"], issue["rule"], issue["node_id"])
    if Counter(map(identity, issues)) != Counter(map(identity, report["issues"])):
        raise ValueError(f"{run_id}: issue identities do not match")
    for issue in report["issues"]:
        if issue["node_id"] is not None and issue["node_id"] not in node_ids:
            raise ValueError(f"{run_id}: unknown issue node")
        if issue["timestamp"] != starts.get(issue["node_id"]):
            raise ValueError(f"{run_id}: incorrect issue timestamp")
    if not any(issue["severity"] == "critical" and issue["timestamp"] is not None
               for issue in report["issues"]):
        raise ValueError(f"{run_id}: no narrated critical issue for the timestamp demonstration")
    with (directory / "clip.mp4").open("rb") as stream:
        header = stream.read(12)
    if b"ftyp" not in header or (directory / "clip.mp4").stat().st_size < 1024:
        raise ValueError(f"{run_id}: clip is not a playable MP4 artifact")
    return report


def atomic_copy(source, target, expected):
    """Verify the copied file once before exposing it at the live filename."""
    fd, name = tempfile.mkstemp(prefix=f".{target.name}-", dir=target.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        shutil.copy2(source, temporary)
        if temporary.stat().st_size != expected["bytes"] or digest(temporary) != expected["sha256"]:
            raise ValueError(f"Copied artifact failed integrity verification: {source}")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def write_manifest(demo_dir):
    """Explicitly refresh hashes and metadata after new complete captures."""
    manifest = {"version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
                "runs": {}}
    for run_id in RUN_IDS:
        directory = demo_dir / run_id
        report = read_json(directory / "report.json")
        record = {"url": report["url"], "score": report["score"],
                  "issues": len(report["issues"]), "duration": report["duration"],
                  "event_count": len(read_json(directory / "events.json")["events"]),
                  "timestamped_critical_issues": sum(i["severity"] == "critical" and i["timestamp"] is not None
                                                     for i in report["issues"]),
                  "files": {name: {"bytes": (directory / name).stat().st_size,
                                   "sha256": digest(directory / name)} for name in REQUIRED}}
        validate_run(directory, record, verify_hashes=False)
        manifest["runs"][run_id] = record
    fd, name = tempfile.mkstemp(prefix=".manifest-", dir=demo_dir)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(manifest, stream, indent=2)
            stream.write("\n")
        os.replace(temporary, demo_dir / "manifest.json")
    finally:
        temporary.unlink(missing_ok=True)
    return manifest


def prepare(demo_dir, data_dir, *, verify_only=False, force=False):
    manifest = read_json(demo_dir / "manifest.json")
    if manifest["version"] != 1 or set(manifest["runs"]) != set(RUN_IDS):
        raise ValueError("Manifest must describe exactly bad-checkout, site1 and site2")
    # Validate every source and destination before staging any run.
    reports = {run_id: validate_run(demo_dir / run_id, manifest["runs"][run_id])
               for run_id in RUN_IDS}
    if not verify_only:
        copies = []
        for run_id in RUN_IDS:
            destination = data_dir / run_id
            if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
                raise ValueError(f"Unsafe destination: {destination}")
            for name in REQUIRED:
                path = destination / name
                if path.is_symlink():
                    raise ValueError(f"Unsafe destination: {path}")
                expected = manifest["runs"][run_id]["files"][name]
                if path.exists():
                    if not path.is_file():
                        raise ValueError(f"Unsafe destination: {path}")
                    if not force:
                        if digest(path) != expected["sha256"]:
                            raise ValueError(f"Existing artifact differs: {path}. Use --force to replace demo artifacts.")
                        continue
                copies.append((run_id, name))
        # Publish report/status last; every individual file replacement is atomic.
        copies.sort(key=lambda item: (item[1] == "status.json", item[1] == "report.json"))
        for run_id, name in copies:
            destination = data_dir / run_id
            destination.mkdir(parents=True, exist_ok=True)
            source = demo_dir / run_id / name
            target = destination / name
            if source.resolve() != target.resolve():
                atomic_copy(source, target, manifest["runs"][run_id]["files"][name])
        for run_id in RUN_IDS:
            # Changed files were hashed before atomic replacement; unchanged
            # destinations were hashed during preflight. Do not hash them again.
            validate_run(data_dir / run_id, manifest["runs"][run_id], verify_hashes=False)
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo-dir", type=Path, default=ROOT / "demo")
    parser.add_argument("--data-dir", type=Path, help="Defaults to worker.common.DATA_DIR, including .env")
    parser.add_argument("--write-manifest", action="store_true", help="Refresh manifest from complete caches, then exit without staging")
    parser.add_argument("--verify-only", action="store_true", help="Verify caches without copying")
    parser.add_argument("--force", action="store_true", help="Replace differing artifacts in the three demo destinations")
    args = parser.parse_args()
    try:
        if args.write_manifest:
            write_manifest(args.demo_dir.resolve())
            print("Demo manifest refreshed and validated.")
            return 0
        data_dir = args.data_dir or (ROOT / "data" if args.verify_only else default_data_dir())
        reports = prepare(args.demo_dir.resolve(), data_dir.resolve(),
                          verify_only=args.verify_only, force=args.force)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Demo preparation failed: {error}\n")
    for run_id, report in reports.items():
        print(f"OK {run_id}: score={report['score']}, issues={len(report['issues'])}, duration={report['duration']}s")
        if not args.verify_only:
            print(f"  http://localhost:3000/a/{run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
