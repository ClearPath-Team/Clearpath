#!/usr/bin/env python3
"""ClearPath Task Manager & Anti-Collision CLI

Usage:
  python scripts/task.py list
  python scripts/task.py check <TASK_ID>
  python scripts/task.py claim <TASK_ID> --assignee <NAME>
  python scripts/task.py release <TASK_ID>
  python scripts/task.py done <TASK_ID> --pr <PR_URL_OR_NUM>
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"


def parse_task_file(file_path: Path) -> dict:
    content = file_path.read_text(encoding="utf-8")
    data = {
        "path": file_path,
        "filename": file_path.name,
        "id": "",
        "issue": "",
        "track": "",
        "type": "",
        "priority": "",
        "status": "Ready",
        "assignee": "Unassigned",
        "branch": "",
    }
    for line in content.splitlines():
        line_str = line.strip()
        m_id = re.search(r"-\s*\*\*Task ID:\*\*\s*`?([^`\n]+)`?", line_str)
        if m_id:
            data["id"] = m_id.group(1).strip()
        m_issue = re.search(r"-\s*\*\*GitHub Issue:\*\*\s*(.+)", line_str)
        if m_issue:
            data["issue"] = m_issue.group(1).strip()
        m_track = re.search(r"-\s*\*\*Track:\*\*\s*`?([^`\n]+)`?", line_str)
        if m_track:
            data["track"] = m_track.group(1).strip()
        m_pri = re.search(r"-\s*\*\*Priority:\*\*\s*`?([^`\n]+)`?", line_str)
        if m_pri:
            data["priority"] = m_pri.group(1).strip()
        m_status = re.search(r"-\s*\*\*Status:\*\*\s*`?([^`\n]+)`?", line_str)
        if m_status:
            data["status"] = m_status.group(1).strip()
        m_ass = re.search(r"-\s*\*\*Assignee:\*\*\s*(.+)", line_str)
        if m_ass:
            raw_ass = m_ass.group(1).strip().strip("*`")
            data["assignee"] = raw_ass if raw_ass else "Unassigned"
        m_branch = re.search(r"-\s*\*\*Branch:\*\*\s*`?([^`\n]+)`?", line_str)
        if m_branch:
            data["branch"] = m_branch.group(1).strip()
    return data


def find_task(task_id: str) -> dict:
    if not TASKS_DIR.exists():
        print(f"Error: {TASKS_DIR} does not exist", file=sys.stderr)
        sys.exit(1)
    target = task_id.strip().upper()
    for f in sorted(TASKS_DIR.glob("*.md")):
        if f.name.startswith("README") or f.name.endswith("-prompt.md"):
            continue
        t = parse_task_file(f)
        if t["id"].upper() == target or f.stem.upper() == target or target in f.name.upper():
            return t
    print(f"Error: Task '{task_id}' not found in {TASKS_DIR}", file=sys.stderr)
    sys.exit(1)


def update_task_header(file_path: Path, new_status: str, new_assignee: str, log_note: str = "") -> None:
    content = file_path.read_text(encoding="utf-8")
    content = re.sub(r"(-\s*\*\*Status:\*\*\s*).*", rf"\g<1>`{new_status}`", content)
    content = re.sub(r"(-\s*\*\*Assignee:\*\*\s*).*", rf"\g<1>`{new_assignee}`", content)
    
    if log_note:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        log_entry = f"\n- **{now}:** {log_note}"
        if "## 8. Execution Log" in content:
            content = content + log_entry
        else:
            content = content + f"\n\n## 8. Execution Log{log_entry}\n"
    file_path.write_text(content, encoding="utf-8")


def cmd_list(args):
    tasks = []
    if not TASKS_DIR.exists():
        print("No tasks found.")
        return
    for f in sorted(TASKS_DIR.glob("*.md")):
        if f.name.startswith("README") or f.name.endswith("-prompt.md"):
            continue
        tasks.append(parse_task_file(f))
    
    header = f"{'Task ID':<10} | {'Track':<6} | {'Status':<10} | {'Assignee':<20} | {'Priority':<20} | {'File'}"
    print(header)
    print("-" * len(header))
    for t in tasks:
        ass = t["assignee"]
        if ass == "Unassigned":
            ass_display = "(available)"
        else:
            ass_display = f"@{ass.lstrip('@')}"
        print(f"{t['id']:<10} | {t['track']:<6} | {t['status']:<10} | {ass_display:<20} | {t['priority']:<20} | {t['filename']}")


def cmd_check(args):
    t = find_task(args.task_id)
    print(f"Task: {t['id']} ({t['filename']})")
    print(f"Status:   {t['status']}")
    print(f"Assignee: {t['assignee']}")
    print(f"Branch:   {t['branch']}")
    if t["assignee"] != "Unassigned":
        print(f"==> LOCKED: Already claimed by @{t['assignee']}. Other agents must NOT take this task.")
        sys.exit(2)
    else:
        print("==> AVAILABLE: Task is unassigned and ready to claim.")
        sys.exit(0)


def cmd_claim(args):
    t = find_task(args.task_id)
    assignee = args.assignee.strip()
    if not assignee:
        print("Error: --assignee is required", file=sys.stderr)
        sys.exit(1)

    # ANTI-COLLISION CHECK
    current_ass = t["assignee"]
    if current_ass not in ("Unassigned", "", None) and current_ass != assignee:
        print(f"COLLISION DETECTED: Task '{t['id']}' is already assigned to @{current_ass}!", file=sys.stderr)
        print(f"Status: {t['status']}. AI agents MUST NOT overwrite an active task.", file=sys.stderr)
        sys.exit(1)

    update_task_header(t["path"], new_status="In progress", new_assignee=assignee, log_note=f"Claimed by @{assignee} (Status -> In progress)")
    print(f"[OK] Task {t['id']} claimed by @{assignee}. Status set to 'In progress'.")
    
    # Sync with GitHub if gh CLI is available and task is linked to an issue
    m_num = re.search(r"#?(\d+)", t.get("issue", ""))
    if m_num:
        clean_user = assignee.lstrip("@")
        try:
            subprocess.run([
                "gh", "issue", "edit", m_num.group(1),
                "--add-assignee", clean_user,
                "--add-label", "status:in-progress",
                "--remove-label", "status:ready"
            ], capture_output=True, text=True, check=False)
            print(f"[OK] GitHub Issue #{m_num.group(1)} assigned to @{clean_user} on GitHub.")
        except Exception:
            pass

    # Switch/Create git branch
    branch = t.get("branch")
    if branch:
        res = subprocess.run(["git", "checkout", "-b", branch], capture_output=True, text=True)
        if res.returncode != 0:
            # Branch may already exist
            subprocess.run(["git", "checkout", branch], capture_output=True, text=True)
        print(f"[OK] Switched to branch '{branch}'.")
    
    print("\nNext steps for the agent:")
    print("1. Modify ONLY the files listed in the task's Scope section.")
    print("2. Run the task's Validation commands.")
    print("3. Open PR and mark task as In review: python scripts/task.py done " + t['id'] + " --pr <PR_URL>")


def cmd_release(args):
    t = find_task(args.task_id)
    current_ass = t.get("assignee", "").lstrip("@")
    update_task_header(t["path"], new_status="Ready", new_assignee="Unassigned", log_note="Released back to pool")
    print(f"[OK] Task {t['id']} released. Status set to 'Ready', Assignee cleared.")

    m_num = re.search(r"#?(\d+)", t.get("issue", ""))
    if m_num and current_ass and current_ass != "Unassigned":
        try:
            subprocess.run([
                "gh", "issue", "edit", m_num.group(1),
                "--remove-assignee", current_ass,
                "--add-label", "status:ready",
                "--remove-label", "status:in-progress"
            ], capture_output=True, text=True, check=False)
            print(f"[OK] GitHub Issue #{m_num.group(1)} unassigned on GitHub.")
        except Exception:
            pass


def cmd_done(args):
    t = find_task(args.task_id)
    pr = args.pr.strip()
    update_task_header(t["path"], new_status="In review", new_assignee=t["assignee"], log_note=f"PR opened: {pr} (Status -> In review)")
    print(f"[OK] Task {t['id']} moved to 'In review'. PR logged: {pr}")

    m_num = re.search(r"#?(\d+)", t.get("issue", ""))
    if m_num:
        try:
            subprocess.run([
                "gh", "issue", "edit", m_num.group(1),
                "--add-label", "status:in-review",
                "--remove-label", "status:in-progress"
            ], capture_output=True, text=True, check=False)
            print(f"[OK] GitHub Issue #{m_num.group(1)} marked 'status:in-review' on GitHub.")
        except Exception:
            pass

    print("Waiting for human review to merge into main and transition to 'Done'.")


def main():
    parser = argparse.ArgumentParser(description="ClearPath Task Anti-Collision Manager")
    sub = parser.add_subparsers(dest="subcommand", required=True)

    sub.add_parser("list", help="List all tasks and assignees")
    
    p_check = sub.add_parser("check", help="Check if a task is available")
    p_check.add_argument("task_id", help="Task ID (e.g. M4-01)")
    p_check.set_defaults(func=cmd_check)

    p_claim = sub.add_parser("claim", help="Claim a task with anti-collision check")
    p_claim.add_argument("task_id", help="Task ID (e.g. M4-01)")
    p_claim.add_argument("--assignee", required=True, help="GitHub username or agent name")
    p_claim.set_defaults(func=cmd_claim)

    p_rel = sub.add_parser("release", help="Release a claimed task back to pool")
    p_rel.add_argument("task_id", help="Task ID (e.g. M4-01)")
    p_rel.set_defaults(func=cmd_release)

    p_done = sub.add_parser("done", help="Mark task as In review when PR is opened")
    p_done.add_argument("task_id", help="Task ID (e.g. M4-01)")
    p_done.add_argument("--pr", required=True, help="PR URL or number")
    p_done.set_defaults(func=cmd_done)

    args = parser.parse_args()
    if args.subcommand == "list":
        cmd_list(args)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
