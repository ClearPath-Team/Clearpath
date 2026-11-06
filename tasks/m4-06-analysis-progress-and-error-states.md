# Task: [M4-06] Analysis Progress and Error States (approved redesign)

- **Task ID:** `M4-06`
- **GitHub Issue:** #35
- **Track:** `M4` (API, web, and demo)
- **Type:** `Feature`
- **Priority:** `P1 - current milestone`
- **Status:** `In progress`
- **Assignee:** `Sergiu1809`
- **Branch:** `m4-analysis-states`
- **Created Date:** 2026-11-06

---

## 1. Goal
Implement the in-progress and failure states of `/a/[id]` to match the "2 · Analysis in progress" and "4 · Error and empty states" artboards.

Design (approved, M4-08 / #28): https://claude.ai/artifact/FSpXpauSM4zuds3Zs2VHGk

---

## 2. Context
`web/app/a/[id]/page.tsx` already polls `GET /api/analyses/{id}` and renders a 4-stage progress view and a failure view. This task restyles them with the M4-05 foundation and extracts them into components, without changing the polling logic.

Stage mapping (from `status.json`): `queued`/`extracting` -> "Preparing the session" and "Accessibility tree"; `analyzing` -> "Screen reader and WCAG audit"; `rendering` -> "Narrated video"; `done` -> report (M4-07); `failed` -> failure view.

---

## 3. Scope (Strict Boundary)
- `web/app/a/[id]/page.tsx`
- `web/components/**` (progress list, failure panel, video error panel)
- `tasks/m4-06-analysis-progress-and-error-states.md`, `tasks/README.md`

**Forbidden:** `api/`, `worker/`, `contracts/`.

---

## 4. Acceptance Criteria
- [ ] Progress view: title "Listening to your page.", analyzed URL, thin progress bar with `role="progressbar"` and `aria-valuetext` ("Step N of 4"), four steps with Done / In progress / Up next states, current step marked `aria-current="step"`, "Copy link" button and the "usually under 3 minutes" note.
- [ ] Status changes are announced to screen readers (polite live region) without re-announcing the whole page on each poll.
- [ ] Failure view: "The analysis couldn't be completed", the backend `error` text shown as-is (it may be Romanian or English), "New analysis" and "Try again" actions.
- [ ] Video error panel ("The video couldn't be played") shown when the clip fails to load, with the rest of the report still usable.
- [ ] Polling behavior and timings are unchanged; unknown ids still show the existing not-found handling.
- [ ] WCAG 2.1 AA, keyboard focus visible, works at ~400px; `cd web && npm run build` passes.

---

## 5. Validation & Test Commands
```bash
cd web && npm run build && cd ..
CP_STUBS= python scripts/dev.py
# Start an analysis and watch the steps advance; then analyze https://does-not-exist.invalid/
# to see the failure view. Check both with a screen reader or the browser accessibility tree.
```

---

## 6. Dependencies
- `M4-05` (UI foundation).

---

## 7. Out of Scope
- The finished report view (`M4-07`).

---

## 8. Execution Log (Updated by Assignee)
- **2026-11-06:** Task created as Ready (split from M4-08).

- **2026-11-06 17:42 UTC:** Claimed by @Sergiu1809 (Status -> In progress)