# Task: [M4-02] Fix Frontend Dashboard Review Findings from PR #10

- **Task ID:** `M4-02`
- **GitHub Issue:** #17
- **Track:** `M4` (API, web, and demo)
- **Type:** `Bug`
- **Priority:** `P0 - blocks delivery`
- **Status:** `Done`
- **Assignee:** `@alexcontz`
- **Branch:** `m4-fix-frontend-dashboard`
- **Created Date:** 2026-11-06

---

## 1. Goal
Address post-merge code review findings on PR #10 ([M4-01] Next.js 14 Frontend Dashboard Initialization): fix broken severity filter tabs on the results page, relocate root `HOWTO.md` to `doc/setup/howto.md`, replace the non-existent Tailwind color class `bg-slate-850`, remove unused `clsx` and `tailwind-merge` dependencies, drop dead speculative `summary` contract fallback code, and ignore/untrack `web/.env.local` while maintaining `web/.env.example`.

---

## 2. Context
Following the merge of PR #10, colleague Sergiu conducted a post-merge code review identifying 6 findings:
1. **Broken Severity Filter Tabs (`web/app/a/[id]/page.tsx:178`):** The filter tabs check `issue.impact`, but the backend contract (`worker/engine/report.py`, `doc/1-foundation/data-contracts.md`) only emits `severity`. Every non-"all" filter silently returned zero results.
2. **`HOWTO.md` at Repo Root:** `CLAUDE.md` §6 mandates that repo root contains only `CLAUDE.md` and `README.md`. Root `HOWTO.md` must be relocated to `doc/setup/howto.md`.
3. **Non-Existent Tailwind Class `bg-slate-850` (`web/app/a/[id]/page.tsx:499`):** Default Tailwind slate scale has no 850 shade. The active issue card lost its background highlight and relied only on border/ring.
4. **Unused Dependencies (`web/package.json`):** `clsx` and `tailwind-merge` were installed but never imported anywhere in `web/app`.
5. **Dead Speculative `summary` Fallback (`web/app/a/[id]/page.tsx:55`):** `AnalysisReport` interface and result dashboard computations fell back to `report.summary?.score`, etc., but the canonical contract emits flat top-level fields.
6. **Tracked `.env.local` (`web/.env.local`):** Committed per-developer local overrides to git without a `.gitignore` exclusion.

---

## 3. Scope (Strict Boundary)
The agent is permitted to modify only the following files:
- `tasks/m4-02-frontend-dashboard-fixes.md`
- `tasks/README.md`
- `web/app/a/[id]/page.tsx`
- `web/package.json`
- `web/package-lock.json`
- `web/tailwind.config.ts`
- `web/.gitignore`
- `web/.env.local` (untracked from git tracking)
- `HOWTO.md` (moved to `doc/setup/howto.md`)

**Forbidden:** Modifying `api/`, `worker/`, `contracts/`, or `doc/1-foundation/data-contracts.md`.

---

## 4. Acceptance Criteria
- [x] Severity filter tabs on `/a/[id]` check `issue.severity` (with fallback to `issue.impact`), correctly filtering issues by severity ("critical", "serious", "moderate", "minor").
- [x] `HOWTO.md` is removed from repository root and relocated to `doc/setup/howto.md`.
- [x] Active issue card highlight uses valid Tailwind styling (`bg-slate-800` and `slate.850` theme extension) so the background highlight renders properly.
- [x] Unused dependencies `clsx` and `tailwind-merge` are removed from `web/package.json` and `web/package-lock.json`.
- [x] Dead speculative `summary` fallback fields are removed from `AnalysisReport` and consumer logic in `web/app/a/[id]/page.tsx`, adhering to `doc/1-foundation/data-contracts.md`.
- [x] `web/.gitignore` excludes `.env*.local`; `web/.env.local` is untracked from git; `web/.env.example` remains tracked as the configuration template.
- [x] Production build (`cd web && npm run build`) completes cleanly with zero errors.

---

## 5. Validation & Test Commands
```bash
# 1. Verify Next.js production build and type check
cd web
npm run build

# 2. Verify root doc cleanliness
test ! -f ../HOWTO.md && test -f ../doc/setup/howto.md

# 3. Verify task CLI
cd ..
.venv/bin/python scripts/task.py check M4-02
```

---

## 6. Dependencies
- Node.js `v20+` or `v26+`
- Merged PR #10 on `main`

---

## 7. Out of Scope
- Backend API or worker changes.
- Modifying `test-site/bad-checkout.html`.

---

## 8. Execution Log (Updated by Assignee)
- **Status Change:** `Backlog` -> `Ready` on 2026-11-06
- **Claimed by:** `@alexcontz` (Status -> `In progress`)
- **PR:** https://github.com/ClearPath-Team/Clearpath/pull/19

- **2026-11-06 14:53 UTC:** PR opened: https://github.com/ClearPath-Team/Clearpath/pull/19 (Status -> In review)
- **2026-11-06 15:05 UTC:** PR #19 merged into main, Issue #17 closed (Status -> Done)
