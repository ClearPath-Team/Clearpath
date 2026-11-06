# Task: [M4-05] UI Foundation and Home Page (approved redesign)

- **Task ID:** `M4-05`
- **GitHub Issue:** #34
- **Track:** `M4` (API, web, and demo)
- **Type:** `Feature`
- **Priority:** `P1 - current milestone`
- **Status:** `Ready`
- **Assignee:** Unassigned
- **Branch:** `m4-ui-foundation-home`
- **Created Date:** 2026-11-06

---

## 1. Goal
Set up the shared visual foundation of the approved redesign in `web/` and implement the home page (`/`) to match the "1 · Home" artboard.

Design (approved, M4-08 / #28): https://claude.ai/artifact/FSpXpauSM4zuds3Zs2VHGk

---

## 2. Context
The redesign is minimal and Apple-like: white surfaces, near-black text, one blue accent, near-square corners, 1px hairlines instead of shadows. Interface copy is in English; Romanian content produced by the backend is shown as-is with `lang="ro"`.

### Design tokens (put them in `web/tailwind.config.ts`, not hard-coded per component)
| Token | Value | Use |
|---|---|---|
| text | `#1D1D1F` | primary text |
| text-secondary | `#6E6E73` | secondary text (4.98:1 on white, 4.63:1 on `#F5F5F7`) |
| text-tertiary | `#424245` | body on gray, unselected controls |
| surface | `#F5F5F7` | gray sections and panels |
| hairline | `#D2D2D7` | 1px borders and dividers |
| accent | `#0076DF` | primary buttons, selected states, score (4.51:1 on white: only on white or as a background under white text, never as text on gray) |
| link | `#0066CC` | inline links |
| critical | `#D70015` on `#FDECEE`, diamond icon | severity |
| serious | `#B25000` on `#FDF1E6`, triangle icon | severity |
| moderate | `#4B49D0` on `#EFEFFD`, filled circle | severity |
| minor | `#5E5E63` on `#F1F1F3`, hollow circle | severity |

- Corner radius at most 4px everywhere, except small severity dots and video scrubber markers (round).
- No soft drop shadows; separate with 1px `#D2D2D7` lines.
- Font stack: `-apple-system, BlinkMacSystemFont, 'SF Pro Text', Inter, 'Segoe UI', sans-serif`. Do not fetch fonts at runtime (the demo must work offline, see DEMO-01); use Inter only if self-hosted from `web/`.

---

## 3. Scope (Strict Boundary)
- `web/tailwind.config.ts`, `web/app/globals.css`, `web/app/layout.tsx`
- `web/app/page.tsx`
- `web/components/**` (new shared components: header, buttons, severity badge)
- `web/lib/strings.ts` (interface copy)
- `tasks/m4-05-ui-foundation-and-home.md`, `tasks/README.md`

**Forbidden:** `api/`, `worker/`, `contracts/`, and changing the request/response shapes the UI uses.

---

## 4. Acceptance Criteria
- [ ] Tokens above are defined once in Tailwind config and used by components; the old indigo/slate palette is removed.
- [ ] Interface strings live in one module (e.g. `web/lib/strings.ts`, English only) so M4-04 (#38, website language selector) can add Romanian without touching components.
- [ ] `layout.tsx` sets `<html lang="en">`, the font stack, white background, and a shared header ("ClearPath" wordmark, "How it works", "Sample report" links).
- [ ] `/` matches the Home artboard: centered hero, URL form (labelled input + "Analyze"), report preview block, "Three steps. One link." section, limits note.
- [ ] Existing behavior is unchanged: POST to `/api/analyses`, redirect to `/a/{id}`, API `detail` errors shown under the input with `aria-invalid` and `aria-describedby`.
- [ ] WCAG 2.1 AA: contrast per the token notes, visible keyboard focus on every control, 44px minimum touch targets, works at ~400px width without horizontal scroll.
- [ ] `cd web && npm run build` passes with zero errors.

---

## 5. Validation & Test Commands
```bash
cd web && npm run build && cd ..
CP_STUBS=all python scripts/dev.py
# Open http://localhost:3000: compare with the Home artboard at 1280px and ~400px,
# Tab through every control, submit a valid URL and a private-network URL (error state).
```

---

## 6. Dependencies
- Approved design in M4-08 (#28). Blocks `M4-06` and `M4-07` (shared foundation).

---

## 7. Out of Scope
- `/a/[id]` pages (`M4-06`, `M4-07`).
- The analysis language toggle (M4-03, #36) and website language selector (M4-04, #38); they build on these components afterwards.

---

## 8. Execution Log (Updated by Assignee)
- **2026-11-06:** Task created as Ready (split from M4-08).
