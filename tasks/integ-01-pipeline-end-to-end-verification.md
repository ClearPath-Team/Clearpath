# Task: [INTEG-01] End-to-End Pipeline Integration & Acceptance Verification

- **Task ID:** `INTEG-01`
- **GitHub Issue:** #22
- **Track:** `Shared` (Integration and pipeline orchestration)
- **Type:** `Feature`
- **Priority:** `P0 - blocks delivery`
- **Status:** `In review`
- **Assignee:** `@andreiBirsanIoan`
- **Branch:** `integ-e2e-verification`
- **Created Date:** 2026-11-06

---

## 1. Goal
Execute the progressive stub elimination checklist on `bad-checkout.html` according to `doc/3-integration/integration.md`, verify that the un-stubbed live pipeline generates all 5 canonical artifacts without errors, assert that the calculated accessibility score is 33 with a keyboard trap penalty of 15, and author an automated end-to-end integration test runner in `worker/test_pipeline.py`.

---

## 2. Context
All core track milestones (M1–M4) along with contract reconciliations (M2-02 scoring weights, M3-02 timeline schema, M4-02 frontend dashboard fixes, SHARED-02 browser dependency fallbacks) are now merged into `main`.

Before entering final demo preparations, the team must verify that the pipeline runs end-to-end with zero stubs (`CP_STUBS=""`):
1. **Extraction (M1):** CDP AX-tree and Tab walk emit valid `nodes.json` with detected keyboard trap on `#promo`.
2. **Analysis (M2):** Speech events emit valid `events.json`, axe-core audit produces `issues.json`, and `report.json` correctly calculates the accessibility score (33 for 9 axe issues + 1 trap penalty).
3. **Render (M3):** `clip.mp4` renders with Piper Romanian voice narration and highlighted bounding boxes, writing `timeline.json` with canonical `{duration, clip, entries[]}`.
4. **Report (M2/M4):** `build_report()` bundles all data cleanly into `report.json` without `KeyError` or NaN values.

---

## 3. Scope (Strict Boundary)
The assignee is permitted to modify or create:
- `worker/pipeline.py` (only bug fixes for pipeline stage handoffs, if any)
- `worker/test_pipeline.py` (new automated end-to-end integration test suite)
- `doc/3-integration/integration.md` (check off completed acceptance criteria)
- `tasks/integ-01-pipeline-end-to-end-verification.md`
- `tasks/README.md`

**Forbidden:** Altering core contracts (`doc/1-foundation/data-contracts.md`, `contracts/selector.js`), changing scoring formulas, or modifying frontend code.

---

## 4. Acceptance Criteria
- [ ] Running `CP_STUBS="" python -m worker.pipeline ck-live http://localhost:8080/bad-checkout.html` completes cleanly without exceptions and exits with code 0.
- [ ] `data/ck-live/` contains all 7 files: `status.json` (`status: "done"`), `nodes.json`, `events.json`, `issues.json`, `clip.mp4`, `timeline.json`, and `report.json`.
- [ ] `report.json` score matches the ADR M2-02 specification: exactly **33** (9 axe-core issues + 1 keyboard trap).
- [ ] Cart button is announced with role "buton" and has a valid timestamp in `timeline.json` and `report.json`.
- [ ] An automated test suite in `worker/test_pipeline.py` validates pipeline stage handoffs with both mocked and live runners (skipping live browser launch gracefully if host browser dependencies are absent, per SHARED-02).

---

## 5. Validation & Test Commands

```bash
python -m unittest worker.test_pipeline.MockedPipelineTests -v
CP_RUN_LIVE_E2E=1 python -m unittest worker.test_pipeline.LivePipelineTests -v
```

PowerShell: `$env:CP_RUN_LIVE_E2E="1"; python -m unittest worker.test_pipeline.LivePipelineTests -v`.

The live runner starts the demo HTTP server and uses an isolated temporary output directory. It validates the current report fields `counts` and `focus_trap` (not obsolete `issues_count` / `trap`). Browser and media prerequisites must be installed; a skip is not a passing acceptance result. The live test has **not** been executed by this PR author in the connected environment.

---

## 6. Dependencies
- Merged `M3-02` (PR #16)
- Merged `M2-02` (PR #14)
- Local HTTP server serving `test-site/bad-checkout.html`

---

## 7. Out of Scope
- Frontend UI visual redesigns.
- Custom scraping rules for non-demo websites.

---

## 8. Execution Log
- **2026-11-06:** Task created as Ready for the Integration phase.

- **2026-11-06:** Added mocked handoff regression tests and opt-in live acceptance runner. Live verification pending; acceptance checkboxes intentionally remain unchecked.
