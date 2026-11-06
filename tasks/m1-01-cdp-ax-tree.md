# Task: [M1-01] Playwright CDP AX-Tree & Keyboard Tab Traversal

- **Task ID:** `M1-01`
- **GitHub Issue:** #1
- **Track:** `M1` (Extraction and keyboard traversal)
- **Type:** `Feature`
- **Priority:** `P1 - current milestone`
- **Status:** `Ready`
- **Assignee:** *Unassigned*
- **Branch:** `m1-cdp-ax-tree`
- **Created Date:** 2026-11-06

---

## 1. Goal
Implement live Playwright CDP accessibility tree extraction and sequential keyboard `Tab` traversal inside `worker/extract/`, producing a validated `nodes.json` conforming to `doc/1-foundation/data-contracts.md`.

---

## 2. Context
Currently `worker/extract/extract.py` and `worker/extract/tab_walk.py` are skeletons that copy mock files when `CP_STUBS=all`.
For live analysis without stubs (`CP_STUBS=`), Track M1 must:
1. Connect via Chrome DevTools Protocol (`Accessibility.getFullAXTree`).
2. Run sequential `Tab` key presses, tracking `activeElement` changes, bounding client rects, and computed accessible names.
3. Detect keyboard traps (`focus_trap`) when focus cycles continuously between 2 or fewer elements or stays trapped on an element for more than 3 consecutive Tab presses.
4. Generate canonical CSS selectors using `worker.common.SELECTOR_JS`.

---

## 3. Scope (Strict Boundary)
The agent is **only** permitted to modify files in `worker/extract/`:
- `worker/extract/extract.py`
- `worker/extract/tab_walk.py`

**Forbidden:** Modifying `worker/engine/`, `worker/media/`, `api/`, `web/`, or core contracts.

---

## 4. Acceptance Criteria
- [ ] Connects to Playwright Chromium and initiates CDP session: `client = page.context.new_cdp_session(page)`.
- [ ] Invokes `Accessibility.getFullAXTree` and filters non-semantic nodes (ignoring `role == "LabelText"` or hidden nodes per `doc/decisions/decision-log.md`).
- [ ] Performs sequential keyboard `Tab` navigation up to a maximum of 40 events (configurable via `MAX_EVENTS`).
- [ ] Calculates canonical CSS selector for each focused element using `worker.common.SELECTOR_JS`.
- [ ] Correctly identifies keyboard traps on `#promo` on `test-site/bad-checkout.html` and flags `"focus_trap": true`.
- [ ] Writes `nodes.json` strictly formatted according to the schema in `doc/1-foundation/data-contracts.md`.

---

## 5. Validation & Test Commands
```bash
# 1. Ensure test-site is running
python -m http.server 8080 --directory test-site &

# 2. Run extraction module standalone
python -m worker.extract.extract http://localhost:8080/bad-checkout.html data/dev/nodes.json

# 3. Validate JSON output schema
node -e "
const d = JSON.parse(fs.readFileSync('data/dev/nodes.json'));
assert(Array.isArray(d.nodes), 'nodes array missing');
assert(d.nodes.length > 0, 'nodes array empty');
assert(d.has_trap === true, 'keyboard trap not detected');
console.log('M1-01 validation PASSED. Extracted ' + d.nodes.length + ' nodes.');
"
```

---

## 6. Dependencies
- Playwright Chromium installed with host dependencies (`sudo playwright install-deps`).
- Local test site running on `localhost:8080`.

---

## 7. Out of Scope
- TTS announcement generation (M2 responsibility).
- Video recording or canvas rendering (M3 responsibility).

---

## 8. Execution Log (Updated by Assignee)
- **Status Change:** `Backlog` -> `Ready` on 2026-11-06
- **Claimed by:** *None*
- **PR:** *None*
