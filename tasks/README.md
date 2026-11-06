# Task Management System (`tasks/`)

This directory contains the authoritative version-controlled backlog of tasks for ClearPath, synchronized with GitHub Projects (v2) and GitHub Issues.

---

## Task Files Inventory

| Task ID | Track | Priority | Status | Assignee | Task File |
|---|---|---|---|---|---|
| **`SHARED-01`** | Shared | P1 | `Done` | `@alexcontz` | [`shared-01-setup-workflow-projects.md`](shared-01-setup-workflow-projects.md) |
| **`M1-01`** | M1 | P1 | `Ready` | *(Unassigned)* | [`m1-01-cdp-ax-tree.md`](m1-01-cdp-ax-tree.md) |
| **`M2-01`** | M2 | P1 | `Ready` | *(Unassigned)* | [`m2-01-speech-and-audit.md`](m2-01-speech-and-audit.md) |
| **`M3-01`** | M3 | P1 | `Ready` | *(Unassigned)* | [`m3-01-tts-and-render.md`](m3-01-tts-and-render.md) |
| **`M4-01`** | M4 | P0 | `Ready` | *(Unassigned)* | [`m4-01-frontend-init.md`](m4-01-frontend-init.md) |

---

## Anti-Collision Protocol for Multi-Agent Collaboration

The project follows a 5-stage task lifecycle: **`Backlog` ➔ `Ready` ➔ `In progress` ➔ `In review` ➔ `Done`**.

To prevent two AI agents or team members from working on the same task simultaneously:

1. **Check Task Availability:**
   ```bash
   python scripts/task.py check <TASK_ID>
   ```
2. **Claim Task Atomically:**
   ```bash
   python scripts/task.py claim <TASK_ID> --assignee <YOUR_NAME>
   ```
   *Sets status to `In progress`, records assignee, and checks out the track branch.*
3. **Verify All Tasks:**
   ```bash
   python scripts/task.py list
   ```
4. **Mark as Ready for Review (`In review`):**
   ```bash
   python scripts/task.py done <TASK_ID> --pr <PR_URL>
   ```

---

## Agent Instructions Prompt

To start an AI assistant on a task, provide it with the universal prompt located at:
[`tasks/team-task-prompt.md`](team-task-prompt.md)
