# Task: [M4-07] Report View with Synced Video, Transcript and Issues (approved redesign)

- **Task ID:** `M4-07`
- **GitHub Issue:** #37
- **Track:** `M4` (API, web, and demo)
- **Type:** `Feature`
- **Priority:** `P1 - current milestone`
- **Status:** `In progress`
- **Assignee:** `Sergiu1809`
- **Branch:** `m4-report-view`
- **Created Date:** 2026-11-06

---

## 1. Goal
Implement the finished-analysis view of `/a/[id]` to match the "3 · Report" artboard: summary, keyboard-trap banner, narrated video with issue markers, "What the user hears" transcript, and the filterable issue list where "Play from m:ss" seeks the video.

Design (approved, M4-08 / #28): https://claude.ai/artifact/FSpXpauSM4zuds3Zs2VHGk (open "3 · Report" and press Play to try the filters and seeking).

---

## 2. Context
Data sources: `report.json` via `GET /api/analyses/{id}` (score, counts, `focus_trap`, `duration`, `clip_url`, issues with `severity`, `title`, `recommendation`, `selector`, `timestamp`) and `timeline.json` via `GET /api/analyses/{id}/timeline` (added by `M4-09`). Issue titles, recommendations and announcements are produced by the backend in the analysis language (Romanian today; English once M2-03 #32 and M4-03 #36 land) and are shown as-is, wrapped in `lang` set to that language.

---

## 3. Scope (Strict Boundary)
- `web/app/a/[id]/page.tsx`
- `web/components/**` (summary, trap banner, video player, transcript, issue list, severity filter)
- `tasks/m4-07-report-view.md`, `tasks/README.md`

**Forbidden:** `api/`, `worker/`, `contracts/`.

---

## 4. Acceptance Criteria
- [ ] Header: "Accessibility report", the analyzed page title, URL, "Copy link".
- [ ] Summary: score `NN / 100` with a thin bar, counts per severity with their icon shapes (diamond, triangle, filled circle, hollow circle) so severity never relies on color alone.
- [ ] Keyboard-trap banner shown only when `focus_trap` is true, with the trap issue's time and a "Play from m:ss" action.
- [ ] Video: native controls stay keyboard-operable; a scrubber row shows one marker per timestamped issue at `timestamp / duration`.
- [ ] Transcript lists every `timeline.json` entry (`m:ss` + text, `lang` = analysis language), highlights the entry being played (`aria-current`), and marks entries linked to an issue; it scrolls in its own container.
- [ ] Issues: segmented filter All / Critical / Serious / Moderate / Minor with counts, buttons using `aria-pressed`, filtering on `issue.severity`; empty filter shows "No issues at this severity."
- [ ] "Play from m:ss" seeks the video to the issue's `timestamp`, starts playback, and marks the issue card as selected; issues with `timestamp: null` show "Not in the video: this issue affects the whole page."
- [ ] Issue order follows `report.json` (severity, then timestamp); selectors shown in a monospace font, wrapping without horizontal scroll.
- [ ] WCAG 2.1 AA, keyboard-only use of filters, seeking and video, visible focus, `prefers-reduced-motion` respected, works at ~400px; `cd web && npm run build` passes.

---

## 5. Validation & Test Commands
```bash
cd web && npm run build && cd ..
CP_STUBS= python scripts/dev.py
# Analyze http://localhost:8080/bad-checkout.html, then on /a/{id}:
# - click "Play from" on #cart, #email and #promo; the video and transcript must jump there
# - try every severity filter, including one with 0 issues
# - repeat with keyboard only and at ~400px width
```

---

## 6. Dependencies
- `M4-09` (timeline endpoint), `M4-05` (UI foundation).

---

## 7. Out of Scope
- Translating backend-generated content (M2-03 #32) and the language toggle (M4-03 #36).
- Changes to scoring, issue detection or the video itself.

---

## 8. Execution Log (Updated by Assignee)
- **2026-11-06:** Task created as Ready (split from M4-08).

- **2026-11-06 17:45 UTC:** Claimed by @Sergiu1809 (Status -> In progress)