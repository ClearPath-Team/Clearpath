# Task Management System (`tasks/`)

This directory contains the authoritative version-controlled backlog of tasks for ClearPath, synchronized with GitHub Projects (v2) and GitHub Issues.

---

## Task Files Inventory

| Task ID | Track | Priority | Status | Assignee | Task File |
|---|---|---|---|---|---|
| **`SHARED-01`** | Shared | P1 | `Done` | `@alexcontz` | [`shared-01-setup-workflow-projects.md`](shared-01-setup-workflow-projects.md) |
| **`M1-01`** | M1 | P1 | `Done` | `@Sergiu1809` | [`m1-01-cdp-ax-tree.md`](m1-01-cdp-ax-tree.md) |
| **`M2-01`** | M2 | P1 | `Done` | `@AndreiBcs` | [`m2-01-speech-and-audit.md`](m2-01-speech-and-audit.md) |
| **`M3-01`** | M3 | P1 | `Done` | `@andreiBirsanIoan` | [`m3-01-tts-and-render.md`](m3-01-tts-and-render.md) |
| **`M4-01`** | M4 | P0 | `Done` | `@alexcontz` | [`m4-01-frontend-init.md`](m4-01-frontend-init.md) |
| **`M3-02`** | M3 | P0 | `Done` | `@Sergiu1809` | [`m3-02-timeline-schema-and-piper-path.md`](m3-02-timeline-schema-and-piper-path.md) |
| **`M2-02`** | M2 | P1 | `Done` | `@AndreiBcs` | [`m2-02-reconcile-scoring-weights.md`](m2-02-reconcile-scoring-weights.md) |
| **`SHARED-02`** | Shared | P1 | `Done` | `@AndreiBcs` | [`shared-02-playwright-environment-deps.md`](shared-02-playwright-environment-deps.md) |
| **`M4-02`** | M4 | P0 | `Done` | `@alexcontz` | [`m4-02-frontend-dashboard-fixes.md`](m4-02-frontend-dashboard-fixes.md) |
| **`INTEG-01`** | Shared | P0 | `In review` | `@andreiBirsanIoan` | [`integ-01-pipeline-end-to-end-verification.md`](integ-01-pipeline-end-to-end-verification.md) |
| **`DEMO-01`** | M4 | P0 | `Ready` | *(Unassigned)* | [`demo-01-offline-precaching-and-presentation.md`](demo-01-offline-precaching-and-presentation.md) |
| **`M1-02`** | M1 | P1 | `Ready` | *(Unassigned)* | [`m1-02-cookie-dismissal-and-live-resilience.md`](m1-02-cookie-dismissal-and-live-resilience.md) |
| **`M3-03`** | M3 | P1 | `In progress` | `@andreiBirsanIoan` | [`m3-03-romanian-tts-quality-and-subtitles.md`](m3-03-romanian-tts-quality-and-subtitles.md) |

---

## Task Synchronization Across Branches

When creating a new task file (`tasks/mX-YY-slug.md`) on **any feature branch**:
- **Automatic via CI:** Pushing your branch to GitHub automatically triggers [`.github/workflows/sync-tasks.yml`](../.github/workflows/sync-tasks.yml). GitHub Actions creates the GitHub Issue, writes the `#<issue_number>` into the markdown file, and pushes the commit directly to your feature branch.
- **Manual (Immediate):** You can also run `python scripts/sync_tasks_to_github.py` locally while on your branch to create the issue immediately before committing.

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
   *Registers the PR on the GitHub Issue, updates issue status to `In review`, and ensures no standalone PR cards exist on the project board.*
5. **Clean Standalone PRs from Board (if needed):**
   ```bash
   python scripts/task.py clean-prs
   ```

---

## Agent Instructions Prompt

To start an AI assistant on a task, provide it with the universal prompt located at:
[`tasks/team-task-prompt.md`](team-task-prompt.md)
