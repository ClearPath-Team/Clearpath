# Task: [M2-02] Reconcile Accessibility Scoring Weights and Contract Documentation

- **Task ID:** `M2-02`
- **GitHub Issue:** #11
- **Track:** `M2` (Announcement engine, audit, and reporting)
- **Type:** `Bug`
- **Priority:** `P1 - current milestone`
- **Status:** `Ready`
- **Assignee:** Unassigned
- **Branch:** `m2-fix-scoring-weights`
- **Created Date:** 2026-11-06

---

## 1. Goal
Resolve the inconsistency between the implemented scoring weights in `worker/engine/report.py` (which yields score `38` using weights `10/5/2/1`) and the authoritative contract documentation in `doc/1-foundation/data-contracts.md` / sample data in `contracts/samples/report.json` (which defines weights `10/6/3/1` yielding score `28`).

---

## 2. Context
During Track M2 implementation, the author added this docstring to `calculate_score` in `worker/engine/report.py`:
```python
"""Apply issue #2 weights (10/5/2/1), plus a single independent trap penalty.

This issue-specific scoring policy was explicitly selected over the older
contract formula (10/6/3/1 with per-rule caps). The supplied issues score 38.
"""
```

However, the repository baseline documents still enforce score `28`:
- `doc/1-foundation/data-contracts.md`: `critical = 10, serious = 6, moderate = 3, minor = 1` -> `score: 28`
- `contracts/samples/report.json`: `"score": 28`
- `doc/3-integration/integration.md`: `bad-checkout.html: Score is ~28`
- `doc/PRD.md`: `score: 28`

This creates a mismatch between contract samples used for mock frontend development and live calculation.

### Resolution Options (Requires Consensus)
- **Option A (Preserve Baseline Contract):** Revert weights in `worker/engine/report.py` to `{"critical": 10, "serious": 6, "moderate": 3, "minor": 1}`, update `test_report.py` assertion to expect `28`.
- **Option B (Adopt Issue #2 Policy):** Keep `weights = {"critical": 10, "serious": 5, "moderate": 2, "minor": 1}` in `report.py`, update `doc/1-foundation/data-contracts.md`, update `contracts/samples/report.json` to score `38`, update `doc/3-integration/integration.md`, and record the formal decision in `doc/decisions/decision-log.md`.

---

## 3. Scope
Depending on team consensus:
- `worker/engine/report.py`
- `worker/engine/test_report.py`
- `doc/decisions/decision-log.md`
- `doc/1-foundation/data-contracts.md` (if Option B is selected)
- `contracts/samples/report.json` (if Option B is selected)

---

## 4. Acceptance Criteria
- [ ] Scoring weights and formulas across code, unit tests, contract documentation, and sample JSON are in 100% agreement.
- [ ] `worker/engine/test_report.py` passes all unit tests without failing assertions.
- [ ] An ADR entry is added to `doc/decisions/decision-log.md` under "Integration Issues" formally recording the agreed scoring weights and rationale.
- [ ] End-to-end integration checklist in `doc/3-integration/integration.md` specifies the agreed expected score.

---

## 5. Validation & Test Commands
```bash
# 1. Run report unit tests
.venv/bin/python -m unittest worker/engine/test_report.py

# 2. Verify score calculation matches sample or updated baseline
.venv/bin/python -c "
from worker.common import SAMPLES, read_json
from worker.engine.report import calculate_score, build_report

issues = read_json(SAMPLES / 'issues.json')
timeline = read_json(SAMPLES / 'timeline.json')
nodes = read_json(SAMPLES / 'nodes.json')

score = calculate_score(issues)
rep = build_report('test', 'http://localhost:8080/bad-checkout.html', nodes, issues, timeline)
print(f'Calculated Score: {score}, Report Score: {rep[\"score\"]}')
"
```

---

## 6. Dependencies
- Team decision on Option A (score 28) vs Option B (score 38).

---

## 7. Out of Scope
- Changing axe-core violation detection logic or recommendations.
- Changing event announcements or TTS audio.

---

## 8. Execution Log
- **2026-11-06:** Task created as Ready based on midpoint integration findings.
