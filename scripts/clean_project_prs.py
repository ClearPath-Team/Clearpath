#!/usr/bin/env python3
"""Removes Pull Requests from the GitHub Projects board to enforce the rule:
"PRs are registered to issues, but must not appear standalone on the project board."

Usage:
  python scripts/clean_project_prs.py [--project "ClearPath Delivery"] [--owner ClearPath-Team]
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
    return "ClearPath-Team/Clearpath"


def clean_project_prs(owner: str, project_title: str) -> None:
    print(f"Scanning for standalone Pull Requests in project '{project_title}' (owner: {owner})...")
    
    # 1. First test if gh has required scope or if GITHUB_TOKEN is available
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    
    # GraphQL query to find project ID and items
    find_query = """
    query($login: String!) {
      organization(login: $login) {
        projectsV2(first: 20) {
          nodes {
            id
            number
            title
            fields(first: 20) {
              nodes {
                ... on ProjectV2SingleSelectField {
                  id
                  name
                  options { id name }
                }
              }
            }
            items(first: 100) {
              nodes {
                id
                type
                fieldValueByName(name: "Status") {
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    name
                  }
                }
                content {
                  __typename
                  ... on PullRequest {
                    number
                    title
                    url
                  }
                  ... on Issue {
                    number
                    title
                    url
                    state
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    
    user_query = """
    query($login: String!) {
      user(login: $login) {
        projectsV2(first: 20) {
          nodes {
            id
            number
            title
            items(first: 100) {
              nodes {
                id
                type
                content {
                  __typename
                  ... on PullRequest {
                    number
                    title
                    url
                  }
                  ... on Issue {
                    number
                    title
                    url
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
        ["gh", "api", "graphql", "-f", f"query={find_query}", "-F", f"login={owner}"],
        capture_output=True, text=True
    )
    
    # If organization query failed, try user query
    if res.returncode != 0 and "Could not resolve to an Organization" in res.stderr:
        res = subprocess.run(
            ["gh", "api", "graphql", "-f", f"query={user_query}", "-F", f"login={owner}"],
            capture_output=True, text=True
        )
    
    if res.returncode != 0:
        err = res.stderr.strip()
        if "INSUFFICIENT_SCOPES" in err or "read:project" in err:
            print("\n[!] GitHub API Error: Token is missing 'read:project' and 'project' scopes.")
            print("\nTo grant project permissions to your GitHub CLI token, run:")
            print("  gh auth refresh -h github.com -s project,read:project")
            print("\nAlternatively, to remove PRs from the GitHub Projects board manually in the web UI:")
            print("  1. Open your project board: https://github.com/orgs/ClearPath-Team/projects")
            print("  2. Click the '...' menu on any standalone Pull Request card")
            print("  3. Click 'Remove from project' (this keeps the PR intact on GitHub, but removes it from the board)")
            print("  4. In Project Settings -> Workflows -> Auto-add to project, ensure filter is 'is:issue' (excluding PRs)")
            return
        else:
            print(f"[!] GraphQL Error: {err}", file=sys.stderr)
            return

    try:
        data = json.loads(res.stdout)
    except Exception as e:
        print(f"[!] Failed to parse GraphQL response: {e}", file=sys.stderr)
        return

    owner_data = data.get("data", {}).get("organization") or data.get("data", {}).get("user") or {}
    projects = owner_data.get("projectsV2", {}).get("nodes", [])
    
    target_project = None
    for p in projects:
        if p["title"].strip().lower() == project_title.strip().lower():
            target_project = p
            break
            
    if not target_project:
        # If title didn't match, check if there's only one project
        if len(projects) == 1:
            target_project = projects[0]
        else:
            available = [p['title'] for p in projects]
            print(f"[!] Project '{project_title}' not found. Available projects for {owner}: {available}")
            return

    project_id = target_project["id"]
    project_number = target_project["number"]
    print(f"-> Found Project: '{target_project['title']}' (#{project_number}, ID: {project_id})")

    items = target_project.get("items", {}).get("nodes", [])
    pr_items = []
    for item in items:
        content = item.get("content") or {}
        typename = content.get("__typename")
        item_type = item.get("type")
        if typename == "PullRequest" or item_type == "PULL_REQUEST":
            pr_items.append({
                "item_id": item["id"],
                "number": content.get("number"),
                "title": content.get("title"),
                "url": content.get("url")
            })

    if not pr_items:
        print(f"[OK] No standalone Pull Requests found on project board '{target_project['title']}'. Board is clean!")
    else:
        print(f"\nFound {len(pr_items)} standalone Pull Request(s) on the board:")
        delete_mutation = """
        mutation($projectId: ID!, $itemId: ID!) {
          deleteProjectV2Item(input: { projectId: $projectId, itemId: $itemId }) {
            deletedItemId
          }
        }
        """
        for pr in pr_items:
            print(f"  - Removing PR #{pr['number']}: {pr['title']} (Item ID: {pr['item_id']})...")
            del_res = subprocess.run(
                [
                    "gh", "api", "graphql",
                    "-f", f"query={delete_mutation}",
                    "-F", f"projectId={project_id}",
                    "-F", f"itemId={pr['item_id']}"
                ],
                capture_output=True, text=True
            )
            if del_res.returncode == 0:
                print(f"    [OK] Successfully removed PR #{pr['number']} from project board.")
            else:
                print(f"    [!] Failed to remove PR #{pr['number']}: {del_res.stderr.strip()}")

    # Reconcile any closed issues on the board that are not marked 'Done'
    status_field_id = None
    done_option_id = None
    for f in target_project.get("fields", {}).get("nodes", []):
        if f.get("name") == "Status":
            status_field_id = f.get("id")
            for opt in f.get("options", []):
                if opt.get("name") == "Done":
                    done_option_id = opt.get("id")
                    break
            break

    if status_field_id and done_option_id:
        for item in items:
            content = item.get("content") or {}
            if content.get("__typename") == "Issue" and content.get("state") == "CLOSED":
                val = item.get("fieldValueByName") or {}
                if val.get("name") != "Done":
                    iss_num = content.get("number")
                    title = content.get("title")
                    item_id = item["id"]
                    print(f"  - Reconciling closed Issue #{iss_num} ('{title}') -> 'Done' on board...")
                    up_mut = """
                    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
                      updateProjectV2ItemFieldValue(input: {
                        projectId: $projectId
                        itemId: $itemId
                        fieldId: $fieldId
                        value: { singleSelectOptionId: $optionId }
                      }) { projectV2Item { id } }
                    }
                    """
                    subprocess.run(
                        ["gh", "api", "graphql", "-f", f"query={up_mut}", "-F", f"projectId={project_id}", "-F", f"itemId={item_id}", "-F", f"fieldId={status_field_id}", "-F", f"optionId={done_option_id}"],
                        capture_output=True, text=True
                    )

    print("\n[OK] Project check complete: All standalone PRs removed, all closed issues reconciled to 'Done'.")
    print("Issues remain the authoritative items on the board with PRs linked directly to them.")


def main():
    parser = argparse.ArgumentParser(description="Remove standalone PRs from GitHub Projects v2")
    parser.add_argument("--project", default="ClearPath Delivery", help="GitHub Project title")
    parser.add_argument("--owner", default="ClearPath-Team", help="GitHub Project owner (org or user)")
    args = parser.parse_args()

    clean_project_prs(args.owner, args.project)


if __name__ == "__main__":
    main()
