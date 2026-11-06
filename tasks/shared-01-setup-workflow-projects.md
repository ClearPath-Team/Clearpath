# Task: [SHARED-01] Setup GitHub Projects Board, Labels & Agent Workflows

- **Task ID:** `SHARED-01`
- **GitHub Issue:** #5
- **Track:** `Shared` (Infrastructure and team workflow)
- **Type:** `Documentation`
- **Priority:** `P1 - current milestone`
- **Status:** `Done`
- **Assignee:** `@alexcontz`
- **Branch:** `main`
- **Created Date:** 2026-11-06

---

## 1. Goal
Configure the GitHub Organization Project board (`ClearPath Delivery`), define custom fields and 5-stage lifecycle (`Backlog`, `Ready`, `In progress`, `In review`, `Done`), install declarative labels (`status:*`, `track:*`, `workflow:*`), and establish GitHub Actions CI workflows for automated task synchronization and quality gates.

---

## 2. Context
ClearPath requires an autonomous, multi-agent delivery system with mutual exclusion and anti-collision checks. This setup bridges the gap between GitHub Projects (v2) and local developer environments, recommending GitHub CLI (`gh`) and discouraging brittle MCP servers.

---

## 3. Scope
- `.github/agentic-workflow.yml`
- `.github/labels.yml`
- `.github/workflows/sync-tasks.yml`
- `.github/workflows/ci.yml`
- `scripts/task.py`
- `scripts/sync_tasks_to_github.py`
- `tasks/` registry
- `doc/setup/setup-workflow-projects.md`

---

## 4. Acceptance Criteria
- [x] GitHub Project v2 (`ClearPath Delivery`) created with custom fields (`Status`, `Track`, `Priority`, `Assignee`).
- [x] Standardized 5-stage lifecycle established: `Backlog` -> `Ready` -> `In progress` -> `In review` -> `Done`.
- [x] 23 declarative labels installed in `ClearPath-Team/Clearpath`.
- [x] Initial milestone tasks (`M1-01`, `M2-01`, `M3-01`, `M4-01`) created and synchronized to GitHub Issues.
- [x] GitHub Actions automated workflows installed for CI test validation and task synchronization.
- [x] Anti-collision CLI (`scripts/task.py`) operational.

---

## 5. Validation & Test Commands
```bash
# Verify labels installed
gh label list

# Verify tasks listing and anti-collision CLI
python scripts/task.py list

# Verify GitHub CLI authentication
gh auth status
```

---

## 6. Execution Log
- **2026-11-06:** Board created in `ClearPath-Team`, labels installed, initial issues (#1, #2, #3, #4) synchronized, and CI workflows implemented. Status set to `Done`.
