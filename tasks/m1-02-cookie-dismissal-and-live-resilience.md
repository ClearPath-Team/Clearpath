# Task: [M1-02] Live Web Resilience: Cookie Banner Dismissal & Page Load Guardrails

- **Task ID:** `M1-02`
- **GitHub Issue:** #23
- **Track:** `M1` (Agent & Tree Extraction)
- **Type:** `Feature`
- **Priority:** `P1 - current milestone`
- **Status:** `In review`
- **Assignee:** `@Sergiu1809`
- **Branch:** `m1-cookie-dismissal-resilience`
- **Created Date:** 2026-11-06

---

## 1. Goal
Implement automatic cookie consent banner dismissal and page load guardrails in `worker/extract/extract.py` and `worker/extract/tab_walk.py` (as specified in `doc/2-tracks/m1-extract.md` §9 and `doc/3-integration/integration.md` §4) so that live public websites can be analyzed without modal overlays blocking AX-tree extraction or keyboard focus traversal.

---

## 2. Context
During live site extraction:
1. Many public websites display cookie consent dialogs (e.g. OneTrust, Cookiebot, custom GDPR overlays) that obstruct DOM inspection, intercept Tab focus events, or trap the crawler in modal overlays before it reaches main page content.
2. Step 9 of `doc/2-tracks/m1-extract.md` calls for an opportunistic banner dismissal pass: scanning for buttons with Romanian and English acceptance labels ("Acceptă", "Sunt de acord", "Accept", "Accept all", "Agree", "I agree", "OK") with a short timeout (1–2 seconds), clicking if present, and proceeding gracefully if absent.
3. Slow font loading or third-party tracking scripts can trigger `PlaywrightTimeoutError` on `networkidle`. The page loader must fall back to `"load"` event with an explicit grace period.

---

## 3. Scope (Strict Boundary)
The assignee is permitted to modify or create:
- `worker/extract/extract.py`
- `worker/extract/tab_walk.py`
- `worker/extract/test_extract.py` (new or updated extraction regression tests)
- `tasks/m1-02-cookie-dismissal-and-live-resilience.md`
- `tasks/README.md`

**Forbidden:** Modifying `worker/engine/`, `worker/media/`, `api/`, or `contracts/selector.js`.

---

## 4. Acceptance Criteria
- [ ] `open_page()` helper attempts to dismiss cookie banners using standard multilingual selector patterns ("Acceptă", "De acord", "Accept", "Accept all", "Agree", "I agree", "OK") with a max 2-second timeout without failing if no banner exists.
- [ ] Navigation handles `networkidle` timeouts gracefully, falling back to `"load"` event so slow external assets never crash the extraction stage.
- [ ] Tab traversal in `tab_walk.py` breaks out gracefully if a focus trap exceeds 80 iterations or encounters detached DOM nodes.
- [ ] Extraction on `bad-checkout.html` remains 100% regression-free (identical node count, roles, and `#promo` focus trap detection).
- [ ] Unit tests in `worker/extract/` pass or cleanly skip if headless Chromium dependencies are not installed on the host.

---

## 5. Validation & Test Commands
```bash
# 1. Run extraction against local test site
.venv/bin/python -m worker.extract.extract http://localhost:8080/bad-checkout.html data/test-nodes.json

# 2. Verify extracted structure
.venv/bin/python -c "
from worker.common import read_json
nodes = read_json('data/test-nodes.json')
assert nodes['focus_trap']['selector'] == '#promo'
assert any(n['role'] == 'button' and n['selector'] == '#cart' for n in nodes['nodes'])
print('EXTRACTION RESILIENCE VALIDATED!')
"

# 3. Clean up test file
rm -f data/test-nodes.json
```

---

## 6. Dependencies
- Merged `M1-01` (PR #8)
- Merged `SHARED-02` (PR #18)

---

## 7. Out of Scope
- Interacting with complex multi-step CAPTCHA challenges or login walls.
- Bypassing paywalls or crawling beyond the target single page.

---

## 8. Execution Log
- **2026-11-06:** Task created as Ready for the Live Web Resilience phase.

- **2026-11-06 15:51 UTC:** Claimed by @Sergiu1809 (Status -> In progress)
- **2026-11-06:** PR #25 opened; review feedback from @alexcontz addressed (Status -> In review)
