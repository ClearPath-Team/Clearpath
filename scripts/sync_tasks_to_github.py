#!/usr/bin/env python3
"""Syncs tasks from doc/tasks/*.md to GitHub Issues using the GitHub REST API or gh CLI.

Usage:
  # With GitHub CLI:
  python scripts/sync_tasks_to_github.py

  # With Personal Access Token:
  GITHUB_TOKEN=ghp_... GITHUB_REPO=Sergiu1809/Clearpath python scripts/sync_tasks_to_github.py
"""
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"


def get_repo_slug() -> str:
    env_repo = os.environ.get("GITHUB_REPO")
    if env_repo:
        return env_repo
    try:
        slug = subprocess.check_output(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], text=True).strip()
        if slug:
            return slug
    except Exception:
        pass
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        # Handles git@github.com:owner/repo.git or https://github.com/owner/repo.git
        m = re.search(r"github\.com[:/]([^/]+/[^/.]+)", url)
        if m:
            return m.group(1)
    except Exception:
        pass
    return "ClearPath-Team/Clearpath"


def sync_task(file_path: Path, repo: str, token: str) -> None:
    content = file_path.read_text(encoding="utf-8")
    
    # Check if already linked to GitHub Issue
    issue_line = ""
    for line in content.splitlines():
        if "**GitHub Issue:**" in line:
            issue_line = line
            break
    m_issue = re.search(r"-\s*\*\*GitHub Issue:\*\*\s*#?(\d+)", content)
    if m_issue and "pending" not in issue_line.lower():
        issue_num = m_issue.group(1)
        # Check if PR is recorded in task and ensure it is registered on the issue
        m_pr = re.search(r"-\s*\*\*(?:Pull Request|PR):\*\*\s*(https://github\.com/\S+/pull/\d+|#\d+)", content)
        if not m_pr:
            m_pr = re.search(r"(?:PR opened:|PR:)\s*(https://github\.com/\S+/pull/\d+|#\d+)", content)
        if m_pr:
            pr_val = m_pr.group(1).strip()
            try:
                comments_view = subprocess.run(
                    ["gh", "issue", "view", issue_num, "--repo", repo, "--json", "comments", "-q", ".comments.[].body"],
                    capture_output=True, text=True
                )
                if comments_view.returncode == 0 and pr_val not in (comments_view.stdout or ""):
                    subprocess.run(
                        ["gh", "issue", "comment", issue_num, "--repo", repo, "--body", f"Linked Pull Request: {pr_val}"],
                        capture_output=True, text=True, check=False
                    )
                    print(f"-> Registered PR {pr_val} on Issue #{issue_num}")
            except Exception:
                pass
        print(f"Skipping {file_path.name}: already linked to issue #{issue_num}")
        return

    # Extract Title and Track
    m_id = re.search(r"-\s*\*\*Task ID:\*\*\s*`?([^`\n]+)`?", content)
    task_id = m_id.group(1).strip() if m_id else file_path.stem
    m_title = re.search(r"^#\s*Task:\s*(.+)$", content, re.MULTILINE)
    title = m_title.group(1).strip() if m_title else f"[{task_id}] {file_path.stem}"
    
    m_track = re.search(r"-\s*\*\*Track:\*\*\s*`?([^`\n]+)`?", content)
    track = m_track.group(1).lower().strip() if m_track else ""
    
    labels = ["status:ready"]
    if track:
        labels.append(f"track:{track}")

    print(f"Creating GitHub Issue for {task_id}: '{title}'...")

    # Method 1: Use gh CLI if available
    gh = subprocess.run(["which", "gh"], capture_output=True, text=True)
    if gh.returncode == 0:
        res = subprocess.run(
            ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", content, "--label", ",".join(labels)],
            capture_output=True, text=True
        )
        if res.returncode == 0:
            issue_url = res.stdout.strip()
            num_match = re.search(r"/issues/(\d+)", issue_url)
            issue_num = num_match.group(1) if num_match else issue_url
            print(f"-> Created Issue #{issue_num} ({issue_url})")
            # Update task file with issue link
            new_content = re.sub(r"(-\s*\*\*GitHub Issue:\*\*\s*).*", rf"\g<1>#{issue_num}", content)
            file_path.write_text(new_content, encoding="utf-8")
            return
        else:
            print(f"gh CLI error: {res.stderr.strip()}", file=sys.stderr)

    # Method 2: Use GitHub REST API with GITHUB_TOKEN
    if not token:
        print(f"Cannot create remote issue for {task_id}: neither 'gh' CLI nor GITHUB_TOKEN is available.")
        print(f"To sync, run: GITHUB_TOKEN=ghp_... python scripts/sync_tasks_to_github.py")
        return

    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ClearPath-Task-Sync"
    }
    payload = json.dumps({"title": title, "body": content, "labels": labels}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            issue_num = data.get("number")
            html_url = data.get("html_url")
            print(f"-> Created Issue #{issue_num} ({html_url})")
            new_content = re.sub(r"(-\s*\*\*GitHub Issue:\*\*\s*).*", rf"\g<1>#{issue_num}", content)
            file_path.write_text(new_content, encoding="utf-8")
    except urllib.error.HTTPError as e:
        print(f"GitHub API Error: {e.code} {e.read().decode('utf-8')}", file=sys.stderr)


def main():
    repo = get_repo_slug()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    print(f"Syncing tasks to GitHub Repository: {repo}")

    for f in sorted(TASKS_DIR.glob("*.md")):
        if f.name.startswith("README") or f.name.endswith("-prompt.md"):
            continue
        sync_task(f, repo, token)


if __name__ == "__main__":
    main()
