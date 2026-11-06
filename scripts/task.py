#!/usr/bin/env python3
"""ClearPath Task Manager & Anti-Collision CLI

Enforces the project workflow:
- Issues are the authoritative items on the GitHub Project board.
- Pull Requests are registered to their parent issue and MUST NOT appear standalone on the board.
- 5-Stage Lifecycle: Backlog -> Ready -> In progress -> In review -> Done

Usage:
  python scripts/task.py list
  python scripts/task.py check <TASK_ID>
  python scripts/task.py claim <TASK_ID> --assignee <NAME>
  python scripts/task.py release <TASK_ID>
  python scripts/task.py done <TASK_ID> --pr <PR_URL_OR_NUM>
  python scripts/task.py link-pr <TASK_ID> --pr <PR_URL_OR_NUM>
  python scripts/task.py clean-prs [--project "ClearPath Delivery"] [--owner ClearPath-Team]
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"


def get_repo_slug() -> str:
    env_repo = os.environ.get("GITHUB_REPO")
    if env_repo:
        return env_repo
    try:
        slug = subprocess.check_output(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            text=True
        ).strip()
        if slug:
            return slug
    except Exception:
        pass
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        m = re.search(r"github\.com[:/]([^/]+/[^/.]+)", url)
        if m:
            return m.group(1).rstrip(".git")
    except Exception:
        pass
    return "ClearPath-Team/Clearpath"


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
        "pr": "",
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
        m_pr = re.search(r"-\s*\*\*(?:Pull Request|PR):\*\*\s*(.+)", line_str)
        if m_pr:
            raw_pr = m_pr.group(1).strip().strip("*`")
            if raw_pr and "none" not in raw_pr.lower() and "pending" not in raw_pr.lower():
                data["pr"] = raw_pr

    # Also search execution log for PR mentions if not found in header
    if not data["pr"] and "## 8. Execution Log" in content:
        log_section = content.split("## 8. Execution Log", 1)[1]
        m_log_pr = re.search(r"(?:PR opened:|PR:)\s*(https://github\.com/\S+/pull/\d+|#\d+)", log_section)
        if m_log_pr:
            data["pr"] = m_log_pr.group(1).strip()

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


def update_task_header(file_path: Path, new_status: str, new_assignee: str, log_note: str = "", pr_url: str = "") -> None:
    content = file_path.read_text(encoding="utf-8")
    content = re.sub(r"(-\s*\*\*Status:\*\*\s*).*", rf"\g<1>`{new_status}`", content)
    content = re.sub(r"(-\s*\*\*Assignee:\*\*\s*).*", rf"\g<1>`{new_assignee}`", content)
    
    if pr_url:
        # Update or insert PR field in metadata
        if re.search(r"-\s*\*\*(?:Pull Request|PR):\*\*", content):
            content = re.sub(r"(-\s*\*\*(?:Pull Request|PR):\*\*\s*).*", rf"\g<1>{pr_url}", content)
        else:
            # Insert after Branch or Assignee
            if re.search(r"-\s*\*\*Branch:\*\*", content):
                content = re.sub(
                    r"(-\s*\*\*Branch:\*\*[^\n]*\n)",
                    rf"\g<1>- **Pull Request:** {pr_url}\n",
                    content
                )
            else:
                content = re.sub(
                    r"(-\s*\*\*Assignee:\*\*[^\n]*\n)",
                    rf"\g<1>- **Pull Request:** {pr_url}\n",
                    content
                )

    if log_note:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        log_entry = f"\n- **{now}:** {log_note}"
        if "## 8. Execution Log" in content:
            content = content + log_entry
        else:
            content = content + f"\n\n## 8. Execution Log{log_entry}\n"
    file_path.write_text(content, encoding="utf-8")


def normalize_pr(pr_input: str, repo: str) -> tuple[str, str]:
    """Returns (pr_number, pr_url)."""
    pr_clean = pr_input.strip()
    m = re.search(r"/pull/(\d+)", pr_clean)
    if m:
        pr_num = m.group(1)
        return pr_num, f"https://github.com/{repo}/pull/{pr_num}"
    m_num = re.search(r"#?(\d+)", pr_clean)
    if m_num:
        pr_num = m_num.group(1)
        return pr_num, f"https://github.com/{repo}/pull/{pr_num}"
    return "", pr_clean


def set_board_status(issue_num: int, target_status: str, repo: str) -> None:
    """Updates the Issue's Status column on the GitHub Projects v2 board."""
    owner, name = repo.split("/")
    query = """
    query($owner: String!, $name: String!, $number: Int!) {
      repository(owner: $owner, name: $name) {
        issue(number: $number) {
          projectItems(first: 5) {
            nodes {
              id
              project {
                id
                fields(first: 20) {
                  nodes {
                    ... on ProjectV2SingleSelectField {
                      id
                      name
                      options { id name }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    res = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}", "-F", f"owner={owner}", "-F", f"name={name}", "-F", f"number={issue_num}"],
        capture_output=True, text=True
    )
    if res.returncode != 0:
        return
    try:
        data = json.loads(res.stdout)
        items = data.get("data", {}).get("repository", {}).get("issue", {}).get("projectItems", {}).get("nodes", [])
        if not items:
            return
        item = items[0]
        item_id = item["id"]
        project_id = item["project"]["id"]

        status_field = None
        option_id = None
        for f in item["project"].get("fields", {}).get("nodes", []):
            if f.get("name") == "Status":
                status_field = f
                for opt in f.get("options", []):
                    if opt["name"].replace(" ", "").lower() == target_status.replace(" ", "").lower():
                        option_id = opt["id"]
                        break
                break

        if not status_field or not option_id:
            return

        mut = """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $projectId
            itemId: $itemId
            fieldId: $fieldId
            value: { singleSelectOptionId: $optionId }
          }) {
            projectV2Item { id }
          }
        }
        """
        field_id = status_field["id"]
        mres = subprocess.run(
            ["gh", "api", "graphql", "-f", f"query={mut}", "-F", f"projectId={project_id}", "-F", f"itemId={item_id}", "-F", f"fieldId={field_id}", "-F", f"optionId={option_id}"],
            capture_output=True, text=True
        )
        if mres.returncode == 0:
            print(f"[OK] Moved Issue #{issue_num} to '{target_status}' on the Project board.")
    except Exception:
        pass


def link_pr_to_issue_and_register(pr_input: str, task: dict, repo: str) -> None:
    """Links PR to issue on GitHub, comments on issue, and enforces no-standalone-PR board rule."""
    pr_num, pr_url = normalize_pr(pr_input, repo)
    if not pr_num:
        print(f"[!] Could not determine PR number from '{pr_input}'.")
        return

    m_issue = re.search(r"#?(\d+)", task.get("issue", ""))
    if not m_issue:
        print(f"[!] Task '{task['id']}' has no associated GitHub Issue.")
        return
    issue_num = m_issue.group(1)

    print(f"\n--- Registering PR #{pr_num} to Issue #{issue_num} ({repo}) ---")

    # 1. Ensure PR description references 'Closes #<issue_num>'
    try:
        pr_view = subprocess.run(
            ["gh", "pr", "view", pr_num, "--repo", repo, "--json", "body", "-q", ".body"],
            capture_output=True, text=True
        )
        if pr_view.returncode == 0:
            body = pr_view.stdout
            if not re.search(rf"(?:closes|fixes|resolves)\s*#{issue_num}\b", body, re.IGNORECASE):
                new_body = (body.rstrip() + f"\n\nCloses #{issue_num}\n") if body else f"Closes #{issue_num}\n"
                res_edit = subprocess.run(
                    ["gh", "pr", "edit", pr_num, "--repo", repo, "--body", new_body],
                    capture_output=True, text=True
                )
                if res_edit.returncode == 0:
                    print(f"[OK] Added 'Closes #{issue_num}' to PR #{pr_num} body on GitHub.")
            else:
                print(f"[OK] PR #{pr_num} already links to Issue #{issue_num} in description.")
    except Exception as e:
        print(f"[!] Note: Could not verify PR body linking: {e}")

    # 2. Register PR as comment on Issue (avoid duplicate comment)
    try:
        comments_view = subprocess.run(
            ["gh", "issue", "view", issue_num, "--repo", repo, "--json", "comments", "-q", ".comments.[].body"],
            capture_output=True, text=True
        )
        already_commented = False
        if comments_view.returncode == 0 and comments_view.stdout:
            if f"pull/{pr_num}" in comments_view.stdout or pr_url in comments_view.stdout:
                already_commented = True

        if not already_commented:
            comment_body = f"Linked Pull Request: {pr_url}\nStatus: In review"
            res_com = subprocess.run(
                ["gh", "issue", "comment", issue_num, "--repo", repo, "--body", comment_body],
                capture_output=True, text=True
            )
            if res_com.returncode == 0:
                print(f"[OK] Registered PR #{pr_num} comment on GitHub Issue #{issue_num}.")
        else:
            print(f"[OK] PR #{pr_num} is already registered on Issue #{issue_num}.")
    except Exception as e:
        print(f"[!] Note: Could not post comment to issue: {e}")

    # 3. Update Issue status label to 'status:in-review' and move on project board
    try:
        subprocess.run([
            "gh", "issue", "edit", issue_num,
            "--repo", repo,
            "--add-label", "status:in-review",
            "--remove-label", "status:in-progress"
        ], capture_output=True, text=True, check=False)
        print(f"[OK] GitHub Issue #{issue_num} updated to 'status:in-review'.")
        set_board_status(int(issue_num), "In Review", repo)
    except Exception:
        pass

    # 4. Enforce board rule: Check if standalone PR item exists on project board and remove
    owner = repo.split("/")[0]
    try:
        clean_script = ROOT / "scripts" / "clean_project_prs.py"
        if clean_script.exists():
            subprocess.run(
                [sys.executable, str(clean_script), "--owner", owner],
                capture_output=True, text=True, check=False
            )
    except Exception:
        pass


def cmd_list(args):
    tasks = []
    if not TASKS_DIR.exists():
        print("No tasks found.")
        return
    for f in sorted(TASKS_DIR.glob("*.md")):
        if f.name.startswith("README") or f.name.endswith("-prompt.md"):
            continue
        tasks.append(parse_task_file(f))
    
    header = f"{'Task ID':<10} | {'Track':<6} | {'Status':<11} | {'Assignee':<18} | {'Issue':<8} | {'PR':<8} | {'Priority':<16} | {'File'}"
    print(header)
    print("-" * len(header))
    for t in tasks:
        ass = t["assignee"]
        ass_display = "(available)" if ass == "Unassigned" else f"@{ass.lstrip('@')}"
        
        issue_display = t["issue"] if t["issue"] else "-"
        if len(issue_display) > 8:
            m_iss = re.search(r"#?(\d+)", issue_display)
            issue_display = f"#{m_iss.group(1)}" if m_iss else issue_display[:8]

        pr_display = "-"
        if t["pr"]:
            m_pr = re.search(r"/pull/(\d+)|#(\d+)", t["pr"])
            if m_pr:
                pr_display = f"#{m_pr.group(1) or m_pr.group(2)}"
            else:
                pr_display = t["pr"][:8]

        print(f"{t['id']:<10} | {t['track']:<6} | {t['status']:<11} | {ass_display:<18} | {issue_display:<8} | {pr_display:<8} | {t['priority']:<16} | {t['filename']}")


def cmd_check(args):
    t = find_task(args.task_id)
    print(f"Task:     {t['id']} ({t['filename']})")
    print(f"Status:   {t['status']}")
    print(f"Assignee: {t['assignee']}")
    print(f"Issue:    {t['issue']}")
    print(f"PR:       {t['pr'] or '(none)'}")
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
    repo = get_repo_slug()
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
                "--repo", repo,
                "--add-assignee", clean_user,
                "--add-label", "status:in-progress",
                "--remove-label", "status:ready"
            ], capture_output=True, text=True, check=False)
            print(f"[OK] GitHub Issue #{m_num.group(1)} assigned to @{clean_user} on GitHub.")
            set_board_status(int(m_num.group(1)), "In Progress", repo)
        except Exception:
            pass

    # Switch/Create git branch
    branch = t.get("branch")
    if branch:
        res = subprocess.run(["git", "checkout", "-b", branch], capture_output=True, text=True)
        if res.returncode != 0:
            subprocess.run(["git", "checkout", branch], capture_output=True, text=True)
        print(f"[OK] Switched to branch '{branch}'.")
    
    print("\nNext steps for the agent:")
    print("1. Modify ONLY the files listed in the task's Scope section.")
    print("2. Run the task's Validation test commands.")
    print("3. Open a Pull Request referencing 'Closes #" + (m_num.group(1) if m_num else "<issue>") + "'.")
    print("   IMPORTANT: Do NOT add PR as a card to the project board. PRs must only be linked to their parent Issue.")
    print("4. Mark task as In review: python scripts/task.py done " + t['id'] + " --pr <PR_URL>")


def cmd_release(args):
    t = find_task(args.task_id)
    repo = get_repo_slug()
    current_ass = t.get("assignee", "").lstrip("@")
    update_task_header(t["path"], new_status="Ready", new_assignee="Unassigned", log_note="Released back to pool")
    print(f"[OK] Task {t['id']} released. Status set to 'Ready', Assignee cleared.")

    m_num = re.search(r"#?(\d+)", t.get("issue", ""))
    if m_num and current_ass and current_ass != "Unassigned":
        try:
            subprocess.run([
                "gh", "issue", "edit", m_num.group(1),
                "--repo", repo,
                "--remove-assignee", current_ass,
                "--add-label", "status:ready",
                "--remove-label", "status:in-progress"
            ], capture_output=True, text=True, check=False)
            print(f"[OK] GitHub Issue #{m_num.group(1)} unassigned on GitHub.")
            set_board_status(int(m_num.group(1)), "Ready", repo)
        except Exception:
            pass


def cmd_done(args):
    t = find_task(args.task_id)
    repo = get_repo_slug()
    pr_input = args.pr.strip()
    pr_num, pr_url = normalize_pr(pr_input, repo)

    update_task_header(
        t["path"],
        new_status="In review",
        new_assignee=t["assignee"],
        log_note=f"PR opened: {pr_url} (Status -> In review)",
        pr_url=pr_url
    )
    print(f"[OK] Task {t['id']} moved to 'In review'. PR logged: {pr_url}")

    # Register PR to Issue and enforce board policy
    link_pr_to_issue_and_register(pr_input, t, repo)

    print("\nPR is now registered to the issue. Waiting for human review to merge into main and transition to 'Done'.")


def cmd_link_pr(args):
    t = find_task(args.task_id)
    repo = get_repo_slug()
    pr_input = args.pr.strip()
    pr_num, pr_url = normalize_pr(pr_input, repo)

    update_task_header(
        t["path"],
        new_status=t["status"],
        new_assignee=t["assignee"],
        log_note=f"Linked PR: {pr_url}",
        pr_url=pr_url
    )
    link_pr_to_issue_and_register(pr_input, t, repo)


def cmd_clean_prs(args):
    clean_script = ROOT / "scripts" / "clean_project_prs.py"
    if clean_script.exists():
        subprocess.run([sys.executable, str(clean_script), "--project", args.project, "--owner", args.owner])
    else:
        print("Error: scripts/clean_project_prs.py not found.", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="ClearPath Task Anti-Collision Manager")
    sub = parser.add_subparsers(dest="subcommand", required=True)

    sub.add_parser("list", help="List all tasks, assignees, issues, and PRs")
    
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

    p_done = sub.add_parser("done", help="Mark task as In review when PR is opened and register PR on issue")
    p_done.add_argument("task_id", help="Task ID (e.g. M4-01)")
    p_done.add_argument("--pr", required=True, help="PR URL or number")
    p_done.set_defaults(func=cmd_done)

    p_link = sub.add_parser("link-pr", help="Link and register a PR to a task and its GitHub Issue")
    p_link.add_argument("task_id", help="Task ID (e.g. M2-02)")
    p_link.add_argument("--pr", required=True, help="PR URL or number")
    p_link.set_defaults(func=cmd_link_pr)

    p_clean = sub.add_parser("clean-prs", help="Remove standalone PRs from GitHub Projects board")
    p_clean.add_argument("--project", default="ClearPath Delivery", help="GitHub Project title")
    p_clean.add_argument("--owner", default="ClearPath-Team", help="GitHub Project owner")
    p_clean.set_defaults(func=cmd_clean_prs)

    args = parser.parse_args()
    if args.subcommand == "list":
        cmd_list(args)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
