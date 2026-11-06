# Task: [M4-03] Frontend Visual Redesign (Claude Design mockups -> Next.js)

- **Task ID:** `M4-03`
- **GitHub Issue:** #28
- **Track:** `M4` (API, web, and demo)
- **Type:** `Feature`
- **Priority:** `P1 - current milestone`
- **Status:** `Ready`
- **Assignee:** Unassigned
- **Branch:** `m4-frontend-redesign`
- **Created Date:** 2026-11-06

---

## 1. Goal
Give the ClearPath web UI a deliberate, accessible visual design: produce mockups for the start page (`/`) and the results page (`/a/[id]`) as a Claude Design artifact, get them approved by the team, then implement them in `web/` without changing any behavior or the data contract the UI consumes.

---

## 2. Context
`M4-01` (PR #10) and `M4-02` (PR #19) delivered a working Next.js 14 dashboard: URL submission, 4-stage status polling, synchronized video player with timestamp seeking, score, severity counts and filters. The visuals were built ad hoc (generic indigo/slate palette in `web/tailwind.config.ts`, styling inlined in a ~600-line `web/app/a/[id]/page.tsx`).

ClearPath demonstrates accessibility problems, so its own UI is part of the pitch: it must look intentional and must itself be accessible (contrast, keyboard use, focus visibility, reduced motion).

`web/` is owned by Track M4 (`@alexcontz`). Whoever takes this task coordinates with the M4 owner before merging, per `doc/rules/repo-rules.md`.

### Workflow
1. Create a Claude Design artifact (Design type) with two screens: start page and results page (including loading/progress, error, and "done" states), using real data from `contracts/samples/report.json`.
2. Share the artifact link in this issue; the team reviews and comments on it.
3. Implement the approved design in `web/`, splitting the results page into components under `web/components/`.

---

## 3. Scope (Strict Boundary)
The assignee is permitted to modify or create:
- `web/app/**` (pages, `layout.tsx`, `globals.css`)
- `web/components/**` (new presentational components)
- `web/tailwind.config.ts`
- `web/package.json` / `web/package-lock.json` (only if a new dependency is justified in the PR; pin exact versions)
- `tasks/m4-03-frontend-visual-redesign.md`
- `tasks/README.md`

**Forbidden:** Modifying `api/`, `worker/`, `contracts/`, `doc/1-foundation/data-contracts.md`, or the API request/response shapes the UI relies on.

---

## 4. Acceptance Criteria
- [ ] A Claude Design artifact with the start page and results page (empty, loading/progress, error, done states) is linked in this issue and approved by at least one teammate.
- [ ] `/` and `/a/[id]` match the approved design at desktop (1280px) and phone (~400px) widths, with no horizontal page scroll.
- [ ] All existing behavior is preserved: URL submission and API error messages, 4-stage progress polling, video playback, clicking an issue timestamp seeks the video, severity filters use `issue.severity`, score, counts and `focus_trap` display.
- [ ] Data shapes still follow `doc/1-foundation/data-contracts.md` (`report.json`, `status.json`); no new API calls.
- [ ] The UI meets WCAG 2.1 AA: text contrast >= 4.5:1, every control is reachable and operable by keyboard with a visible focus indicator, the video player and issue list are usable without a mouse, and animations respect `prefers-reduced-motion`.
- [ ] User-facing copy stays in Romanian (consistent with the current UI and the Romanian demo); code, comments and commit messages are in English.
- [ ] `cd web && npm run build` completes with zero errors and zero type errors.

---

## 5. Validation & Test Commands
```bash
# 1. Production build and type check
cd web && npm run build && cd ..

# 2. Full stack with stubbed pipeline (fast UI iteration)
CP_STUBS=all python scripts/dev.py
#    Open http://localhost:3000, analyze http://localhost:8080/bad-checkout.html,
#    check progress -> results, video seek from an issue timestamp, all severity tabs.

# 3. Full stack with the live pipeline
CP_STUBS= python scripts/dev.py
#    Repeat the checks on a live analysis; resize to ~400px and repeat.

# 4. Keyboard pass: Tab through both pages; every control must show focus and work with Enter/Space.
```

---

## 6. Dependencies
- Merged `M4-01` (PR #10) and `M4-02` (PR #19).
- Agreement from the M4 owner (`@alexcontz`) before merge.

---

## 7. Out of Scope
- Backend, pipeline, or contract changes.
- New product features (multi-page crawling, accounts, history of analyses).
- Changing `test-site/bad-checkout.html`.

---

## 8. Execution Log (Updated by Assignee)
- **2026-11-06:** Task created as Ready.
