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
| **`INTEG-01`** | Shared | P0 | `Done` | `@andreiBirsanIoan` | [`integ-01-pipeline-end-to-end-verification.md`](integ-01-pipeline-end-to-end-verification.md) |
| **`DEMO-01`** | M4 | P0 | `Done` | `@AndreiBcs` | [`demo-01-offline-precaching-and-presentation.md`](demo-01-offline-precaching-and-presentation.md) |
| **`M1-02`** | M1 | P1 | `In review` | `@Sergiu1809` | [`m1-02-cookie-dismissal-and-live-resilience.md`](m1-02-cookie-dismissal-and-live-resilience.md) |
| **`M3-03`** | M3 | P1 | `In progress` | `@andreiBirsanIoan` | [`m3-03-romanian-tts-quality-and-subtitles.md`](m3-03-romanian-tts-quality-and-subtitles.md) |
| **`M2-03`** | M2 | P1 | `In review` | `@andreiBirsanIoan` | [`m2-03-english-speech-and-recommendations.md`](m2-03-english-speech-and-recommendations.md) |
| **`M4-03`** | M4 | P1 | `Ready` | *(Unassigned)* | [`m4-03-analysis-language-toggle.md`](m4-03-analysis-language-toggle.md) |
| **`M4-04`** | M4 | P1 | `Ready` | *(Unassigned)* | [`m4-04-website-language-selector-and-analysis-default.md`](m4-04-website-language-selector-and-analysis-default.md) |
| **`DEMO-02`** | Demo | P1 | `In review` | AndreiBcs | [`demo-02-revamp-bad-checkout-ux.md`](demo-02-revamp-bad-checkout-ux.md) |
| **`INTEG-02`** | Shared | P1 | `Done` | `@agent` | [`integ-02-live-popular-websites-e2e.md`](integ-02-live-popular-websites-e2e.md) |
| **`INTEG-03`** | Shared | P1 | `Ready` | *(Unassigned)* | [`integ-03-romanian-popular-platforms-audit.md`](integ-03-romanian-popular-platforms-audit.md) |
| **`M4-08`** | M4 | P1 | `Done` | `@Sergiu1809` | [`m4-08-frontend-visual-redesign.md`](m4-08-frontend-visual-redesign.md) |
| **`M4-09`** | M4 | P1 | `Done` | `@Sergiu1809` | [`m4-09-api-timeline-endpoint.md`](m4-09-api-timeline-endpoint.md) |
| **`M4-05`** | M4 | P1 | `Done` | `@Sergiu1809` | [`m4-05-ui-foundation-and-home.md`](m4-05-ui-foundation-and-home.md) |
| **`M4-06`** | M4 | P1 | `Done` | `@Sergiu1809` | [`m4-06-analysis-progress-and-error-states.md`](m4-06-analysis-progress-and-error-states.md) |
| **`M4-07`** | M4 | P1 | `Done` | `@Sergiu1809` | [`m4-07-report-view.md`](m4-07-report-view.md) |
| **`M2-04`** | M2 | P1 | `Ready` | *(Unassigned)* | [`m2-04-canonical-issue-categorization.md`](m2-04-canonical-issue-categorization.md) |
| **`M4-10`** | M4 | P1 | `Ready` | *(Unassigned)* | [`m4-10-exportable-canonical-audit-reports.md`](m4-10-exportable-canonical-audit-reports.md) |

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
