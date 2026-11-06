# Task: [INTEG-02] Live Popular Websites End-to-End Testing & Resilience Audit

- **Task ID:** `INTEG-02`
- **GitHub Issue:** Pending
- **Track:** `Shared` (Integration, Resilience & End-to-End Quality)
- **Type:** `Test`
- **Priority:** `P1 - current milestone`
- **Status:** `In progress`
- **Assignee:** `@agent`
- **Branch:** `integ-popular-websites-e2e`
- **Created Date:** 2026-11-06

---

## 1. Goal
Execute full end-to-end integration tests of the ClearPath accessibility pipeline against major live public websites (including `google.com`, `amazon.com`, `discord.com`, `emag.com` / `emag.ro`, `wikipedia.org`, `github.com`, `news.ycombinator.com`, etc.) without mock stubs (`CP_STUBS=""`), document pipeline pass/fail behavior, identify failure modes (anti-bot protections, cookie consent overlays, punctuation-only TTS synthesis crashes, CSP restrictions, DOM complexity, and timeouts), and compile actionable remediation findings.

---

## 2. Context
ClearPath is designed to inspect any public website, translate its accessibility tree into spoken announcements via local Piper TTS, highlight focused elements on video via Playwright and ffmpeg, and compute an axe-core WCAG accessibility score.

While initial integration testing (`INTEG-01`) verified the pipeline against the local deterministic `bad-checkout.html` fixture, real-world websites introduce challenging conditions:
1. **Punctuation-Only Text Nodes:** Nodes containing only punctuation (e.g., `"."` after links or breadcrumb dividers) cause Piper TTS to produce zero speech samples, triggering a fatal crash in `wave.py` (`# channels not specified`) during render.
2. **Anti-Bot & Bot Detection Walls:** High-traffic platforms (e.g., Amazon, Discord) often deploy CAPTCHA challenges or anti-scraping walls (Cloudflare, PerimeterX, AWS WAF) when accessed via headless Chromium without user interaction headers.
3. **Cookie / Consent Modals:** Dynamic cookie consent overlays (OneTrust, Didomi, Cookiebot) can capture Tab focus or obstruct the underlying AX-tree if banner dismissal fails or runs before hydration.
4. **Content Security Policy (CSP):** Strict CSP headers (`script-src`) may block inline or external script injection of `axe.min.js`.
5. **Dynamic SPAs & Heavy DOM:** Single-page applications with client-side routing, heavy canvas/WebGL, or hundreds of DOM nodes test the limits of CDP extraction, Tab order traversal, and video rendering timeouts.

---

## 3. Scope (Strict Boundary)
The assignee is permitted to modify or create:
- `scripts/test_popular_sites.py` (automated batch testing runner across popular websites)
- `tasks/integ-02-live-popular-websites-e2e.md` (this task file)
- `tasks/README.md` (task inventory registration)
- Artifact logs in `data/e2e-*` or reports in `.local/`
- Bug fixes in `worker/media/render.py`, `worker/extract/extract.py`, or `worker/engine/audit.py` if directly resolving resilience crashes identified during testing.

**Forbidden:** Modifying core data contracts (`doc/1-foundation/data-contracts.md`, `contracts/selector.js`), altering offline demo test suite (`test-site/bad-checkout.html`), or modifying frontend layout outside of pipeline compatibility.

---

## 4. Acceptance Criteria
- [x] Implement an automated testing script (`scripts/test_popular_sites.py`) capable of testing live public websites with full end-to-end artifact validation.
- [x] Execute tests across a diverse suite of popular domains:
  - Search: `google.com` (Passed, Score: 90)
  - E-Commerce: `amazon.com` (Passed, Score: 0), `emag.com` (Passed, Score: 19), `emag.ro` (CloudFront 410 handled)
  - Web App / SaaS: `discord.com` (Passed with CSP bypass fix, Score: 30)
  - Reference / Content: `en.wikipedia.org` (Passed, Score: 97)
  - Developer Tools: `github.com` (Passed with CSP bypass fix, Score: 100)
  - Minimal / Plain HTML: `news.ycombinator.com` (Passed with Piper punctuation fix, Score: 0)
- [x] Inspect each pipeline stage (Extraction, Announcement Generation, axe-core Audit, Piper Render, Report Assembly) for every target.
- [x] Document all failures, root causes, accessibility scores, and timing benchmarks in a structured findings matrix.
- [x] Identify and implement resilience improvements (`bypass_csp=True` in audit/render, and Piper silence generation for non-alphanumeric text in render).

---

## 5. Validation & Test Commands
```bash
# 1. Run live end-to-end audit across target popular sites
.venv/bin/python scripts/test_popular_sites.py --sites Google Wikipedia HackerNews Amazon Discord eMAG GitHub

# 2. Inspect generated report and individual job directories
ls -la data/e2e-*/
cat popular_sites_test_report.json
```

---

## 6. Dependencies
- Merged `M1-02` (Cookie dismissal & live resilience)
- Merged `M2-02` (Scoring weights)
- Merged `M3-02` (Timeline schema)
- Local Piper voice model (`ro_RO-mihai-medium.onnx`) and `axe.min.js` installed.

---

## 7. Out of Scope
- Solving, clicking through, or bypassing CAPTCHAs and bot challenges (per security/safety guidelines).
- Multi-page deep crawling or automated checkout form submission.

---

## 8. Execution Log
- **2026-11-06:** Task `INTEG-02` created and registered in `tasks/README.md`.
- **2026-11-06:** Developed automated runner `scripts/test_popular_sites.py`.
- **2026-11-06:** Discovered critical Piper TTS crash on symbol/punctuation nodes (`wave.Error: # channels not specified`); resolved by generating clean PCM silence for non-alphanumeric announcements in `worker/media/render.py`.
- **2026-11-06:** Discovered Content Security Policy (CSP) inline script injection blocks on `discord.com` and `github.com`; resolved by enabling `bypass_csp=True` in `worker/engine/audit.py` and `worker/media/render.py`.
- **2026-11-06:** Executed end-to-end testing across 7 live domains; compiled complete findings and resilience recommendations report artifact.
