# Task: [INTEG-03] Romanian Tech & E-Commerce Ecosystem End-to-End Audit

- **Task ID:** `INTEG-03`
- **GitHub Issue:** #44
- **Track:** `Shared` (Integration, Localization & Live Audit)
- **Type:** `Test`
- **Priority:** `P1 - current milestone`
- **Status:** `In progress`
- **Assignee:** `@andreiBirsanIoan`
- **Branch:** `integ-romanian-tech-audit`
- **Pull Request:** https://github.com/ClearPath-Team/Clearpath/pull/62
- **Created Date:** 2026-11-06

---

## 1. Goal
Execute full end-to-end accessibility evaluations of top Romanian web applications and platforms using ClearPath with zero stubs (`CP_STUBS=""`), utilizing the localized Romanian Piper TTS voice (`ro_RO-mihai-medium.onnx`) and Romanian recommendations in `worker/engine/recommendations.py`. Audit results, WCAG scores, cookie banner resilience, keyboard accessibility, and video narration artifacts must be captured and summarized.

---

## 2. Target Platforms (Romanian Ecosystem)

| Platform | URL | Category / Description | Key Focus Areas |
|---|---|---|---|
| **Flip.ro** | `https://flip.ro` | E-Commerce (Telefoane recondiționate) | Product grid, search filters, cookie consent dialogs |
| **Vivre** | `https://vivre.ro` | E-Commerce (Mobilă și decor) | Image alt attributes, mega-menu navigation, color contrast |
| **Tazz** | `https://tazz.ro` | Food Delivery & Quick Commerce (Web/App) | Dynamic SPA routing, address picker modal, interactive widgets |
| **Pago** | `https://pago.ro` | Fintech & Utility Bill Payments | Form controls, input labels, focus indicators |
| **Salt Bank** | `https://salt.bank` | Digital Neobank (Fintech) | Modern landing animations, accessible landmarks, contrast |
| **Sameday** | `https://sameday.ro` | Logistics & Parcel Tracking | AWBs tracking input, form labels, keyboard navigation |
| **eJobs** | `https://ejobs.ro` | Recruitment & Job Board | Search filters, job card list, heading hierarchy |
| **Elefant.ro** | `https://elefant.ro` | E-Commerce (Cărți, e-book-uri, retail) | Categorized navigation, product search, promotional banners |
| **Kinderpedia** | `https://kinderpedia.co` | EdTech (Platformă școli și părinți) | Multilingual landing, call-to-actions, accessible forms |

---

## 3. Context & Background
With the implementation of live resilience improvements in `M1-02` (cookie banner dismissal) and `INTEG-02` (Content Security Policy bypass and speech normalization for symbols and delimiters), the pipeline is now equipped to evaluate production Romanian web applications.

Because ClearPath synthesizes narration using the Romanian Piper model (`ro_RO-mihai-medium.onnx`) and maps WCAG violations to localized Romanian descriptions (`worker/engine/recommendations.py`), auditing prominent Romanian services provides realistic benchmarks for local assistive technology users and demo presentations.

---

## 4. Scope (Strict Boundary)
The assignee is permitted to modify or create:
- `scripts/test_popular_sites.py` (add Romanian platform preset targets)
- `data/e2e-ro-*/` (analysis artifacts for each Romanian platform)
- `tasks/integ-03-romanian-popular-platforms-audit.md` (this task file)
- `tasks/README.md` (task status progression)
- Resilience bug fixes in `worker/` if novel edge-case crashes are encountered during Romanian site execution.

**Forbidden:** Modifying core data contracts (`doc/1-foundation/data-contracts.md`, `contracts/selector.js`), altering offline demo test suite (`test-site/bad-checkout.html`), or modifying frontend layout outside of pipeline compatibility.

---

## 5. Acceptance Criteria
- [ ] Extend `scripts/test_popular_sites.py` or author an automated batch configuration for the 9 specified Romanian platforms.
- [ ] Run full 5-stage pipeline analyses on each target site:
  - `https://flip.ro`
  - `https://vivre.ro`
  - `https://tazz.ro`
  - `https://pago.ro`
  - `https://salt.bank`
  - `https://sameday.ro`
  - `https://ejobs.ro`
  - `https://elefant.ro`
  - `https://kinderpedia.co`
- [ ] For each platform, verify generation of:
  - `nodes.json` (CDP AX-tree + focus traversal)
  - `events.json` (Romanian announcement texts)
  - `issues.json` (axe-core WCAG violations mapped to selectors)
  - `clip.mp4` (narrated video with yellow highlight overlays)
  - `timeline.json` (synchronized event and issue timestamps)
  - `report.json` (calculated accessibility score 0–100)
- [ ] Handle or document edge bot shields (Cloudflare, AWS WAF, PerimeterX) and cookie consent overlays encountered on Romanian domains.
- [ ] Compile a comprehensive markdown audit report summarizing scores, WCAG violation distributions, and video links across the Romanian ecosystem.

---

## 6. Validation & Test Commands
```bash
# 1. Check task availability
python scripts/task.py check INTEG-03

# 2. Run automated test runner on Romanian target platforms
.venv/bin/python scripts/test_popular_sites.py --sites \
  https://flip.ro \
  https://vivre.ro \
  https://tazz.ro \
  https://pago.ro \
  https://salt.bank \
  https://sameday.ro \
  https://ejobs.ro \
  https://elefant.ro \
  https://kinderpedia.co

# 3. Verify all generated reports
.venv/bin/python -c "
import json
from pathlib import Path

for d in Path('data').glob('e2e-ro-*'):
    rep = d / 'report.json'
    if rep.exists():
        data = json.loads(rep.read_text('utf-8'))
        print(f'{d.name}: score={data.get(\"score\")} duration={data.get(\"duration\")}s issues={len(data.get(\"issues\", []))}')
"
```

---

## 7. Dependencies
- Merged `INTEG-02` (PR #43 - CSP bypass & speech normalization fixes)
- Merged `M1-02` (Cookie consent dismissal & live resilience)
- Local Piper Romanian voice model (`ro_RO-mihai-medium.onnx`) and `axe.min.js`.

---

## 8. Out of Scope
- Automated purchasing, booking, or paying invoices on the live platforms.
- Solving or bypassing CAPTCHAs, bot challenges, or SMS/2FA authentications.

---

## 9. Execution Log
- **2026-11-06:** Implemented reproducible 9-platform Romanian preset, unique run IDs, zero-stub production runner, artifact verification, and JSON/Markdown results manifest. Execution of all nine live sites is **not yet verified** (requires configured local Chromium, ffmpeg, Piper and network). No results, scores, videos or bot-shield outcomes are claimed without collected artifacts.
- **Run:** `python scripts/test_popular_sites.py --preset romanian --output romanian-audit.json --markdown romanian-audit.md`.
- **Completion criteria:** execute all nine live runs without stubs and review generated JSON, Markdown and recorded clips.

### 2026-11-06 live execution evidence

All nine specified targets were attempted with `CP_STUBS=` and `TTS_ENGINE=piper` using Playwright Chromium. Every run failed during extraction with `net::ERR_CERT_AUTHORITY_INVALID`. No site score, issue count or narrated clip is claimed. A second run after importing the managed environment proxy CA into the local NSS store produced the same error. Certificate verification was not disabled.

| Target | Result | Evidence |
| --- | --- | --- |
| https://flip.ro | Blocked at extraction | Chromium certificate authority error; no complete report/video |
| https://vivre.ro | Blocked at extraction | Chromium certificate authority error; no complete report/video |
| https://tazz.ro | Blocked at extraction | Chromium certificate authority error; no complete report/video |
| https://pago.ro | Blocked at extraction | Chromium certificate authority error; no complete report/video |
| https://salt.bank | Blocked at extraction | Chromium certificate authority error; no complete report/video |
| https://sameday.ro | Blocked at extraction | Chromium certificate authority error; no complete report/video |
| https://ejobs.ro | Blocked at extraction | Chromium certificate authority error; no complete report/video |
| https://elefant.ro | Blocked at extraction | Chromium certificate authority error; no complete report/video |
| https://kinderpedia.co | Blocked at extraction | Chromium certificate authority error; no complete report/video |

Local run manifests and logs: `.local/romanian-audit.json`, `.local/romanian-audit.md`, `.local/romanian-run.log`, and `.local/ro-{0,1,2}.{json,md,log}`. Per-run failure states are in gitignored `data/e2e-ro-*/status.json`. This task remains In progress until the full nine-site audit succeeds in a browser with valid managed proxy trust. Do not mark it Done based on the preset implementation alone.


## 8. Execution Log
- **2026-11-06 20:29 UTC:** Linked PR: https://github.com/ClearPath-Team/Clearpath/pull/62

- **Trust-store diagnosis:** The NSS write mapping must be present in the same permission-scoped invocation as browser execution. With that mapping and the managed proxy CA imported, Flip.ro returned verified HTTPS 200. Certificate verification remains enabled. All nine targets are being rerun; verified manifests supersede the initial blocked-at-extraction table above.
