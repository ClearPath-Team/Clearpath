# Task: [M2-01] Screen Reader Speech Rules, axe-core Runner & Report Generation

- **Task ID:** `M2-01`
- **GitHub Issue:** #2
- **Track:** `M2` (Announcement engine, audit, and reporting)
- **Type:** `Feature`
- **Priority:** `P1 - current milestone`
- **Status:** `Done`
- **Assignee:** `@AndreiBcs`
- **Branch:** `m2-speech-audit`
- **Created Date:** 2026-11-06

---

## 1. Goal
Implement live NVDA-style Romanian screen reader announcement generation, in-browser axe-core 4.10.2 audit execution, and final report assembly with deterministic scoring according to `doc/1-foundation/data-contracts.md`.

---

## 2. Context
Track M2 bridges the raw accessibility tree (`nodes.json`) and WCAG audit into human-meaningful announcements (`events.json`) and final metrics (`report.json`).
Currently, `worker/engine/events.py`, `worker/engine/audit.py`, and `worker/engine/report.py` are stub implementations.
For `bad-checkout.html`:
- The score MUST compute to exactly `28/100`.
- The Romanian announcements must model NVDA conventions (e.g. `buton`, `casetă de editare`, `titlu nivel 1`).
- Recommendations must be mapped deterministically using `worker/engine/recommendations.py`.

---

## 3. Scope (Strict Boundary)
The agent is **only** permitted to modify files in `worker/engine/`:
- `worker/engine/events.py`
- `worker/engine/audit.py`
- `worker/engine/report.py`
- `worker/engine/recommendations.py`

**Forbidden:** Modifying `worker/extract/`, `worker/media/`, `api/`, `web/`, or core contracts.

---

## 4. Acceptance Criteria
- [ ] `events.py`:
  - Translates element roles into Romanian screen reader equivalents:
    - `heading` with `level=1` ➔ `titlu nivel 1`
    - `button` ➔ `buton`
    - `textbox` / `input` ➔ `casetă de editare`
    - `combobox` ➔ `casetă combinată`
  - Correctly reports state flags: `necompletat`, `obligatoriu`, `bifat` / `nebifat`.
  - Generates speech string matching NVDA pattern: `"{name}, {role_ro}, {state_ro}"`.
- [ ] `audit.py`:
  - Injects `assets/axe.min.js` into the Playwright page context.
  - Executes `axe.run()` and transforms violations into `issues.json` conforming to contract schema.
  - Adds synthetic `keyboard-trap` issue if `nodes.json` flagged `focus_trap: true`.
- [ ] `report.py`:
  - Calculates score using formula: `100 - SUM(weight * occurrences)`, where:
    - `critical` = 10 deduction
    - `serious` = 5 deduction
    - `moderate` = 2 deduction
    - `minor` = 1 deduction
    - `keyboard-trap` = 15 deduction
  - For `test-site/bad-checkout.html`, computes exact score of `28`.

---

## 5. Validation & Test Commands
```bash
# 1. Test event speech generation
python -m worker.engine.events contracts/samples/nodes.json data/dev/events.json

# 2. Test axe-core audit against running test site
python -m worker.engine.audit http://localhost:8080/bad-checkout.html contracts/samples/nodes.json data/dev/issues.json

# 3. Test report assembly and score calculation
python -m worker.engine.report contracts/samples/issues.json contracts/samples/timeline.json contracts/samples/nodes.json data/dev/report.json

# 4. Verify score output is 28
node -e "
const r = JSON.parse(fs.readFileSync('data/dev/report.json'));
assert.strictEqual(r.summary.score, 28, 'Score expected 28 but got ' + r.summary.score);
console.log('M2-01 validation PASSED. Score: ' + r.summary.score);
"
```

---

## 6. Dependencies
- `assets/axe.min.js` (already present)
- Valid `nodes.json` (from contracts/samples or M1)

---

## 7. Out of Scope
- Audio synthesis with Piper (M3 responsibility).
- Front-end React rendering (M4 responsibility).

---

## 8. Execution Log (Updated by Assignee)
- **Status Change:** `Backlog` -> `Ready` on 2026-11-06
- **Claimed by:** `@AndreiBcs`
- **PR:** https://github.com/ClearPath-Team/Clearpath/pull/7

- **2026-11-06 13:03 UTC:** Claimed by @AndreiBcs (Status -> In progress)
- **2026-11-06 13:40 UTC:** PR #7 merged into main (Status -> Done)

