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
- [x] Extend `scripts/test_popular_sites.py` or author an automated batch configuration for the 9 specified Romanian platforms.
- [x] Run full 5-stage pipeline analyses on each target site:
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
- [x] Handle or document edge bot shields (Cloudflare, AWS WAF, PerimeterX) and cookie consent overlays encountered on Romanian domains.
- [x] Compile a comprehensive markdown audit report summarizing scores, WCAG violation distributions, and video links across the Romanian ecosystem.

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

## 9. Execution Log and Final Evidence

**2026-11-06:** All nine prescribed URLs were executed with `CP_STUBS=` and `TTS_ENGINE=piper`. All nine pipeline runs produced every required artifact. JSON consistency, positive durations, score bounds and audio/video streams were independently checked with the runner verifier and ffprobe. Eight captures contain the target landing-page content. Tazz yielded only a cookie-consent capture and remains unvalidated as a service audit; the task stays **In progress** and issue #44 must remain open.

Initial attempts failed because Chromium did not trust the environment proxy CA. The correction was to import that managed CA into the NSS store and include the same NSS filesystem mapping in the browser invocation. TLS verification was never disabled. Subsequent attempts reached the real pages. No CAPTCHA, authentication or bot-shield bypass was attempted; no purchases, bookings or payments were made.

### Captured results

Scores are ClearPath page-level heuristic results, not percentages of WCAG/legal compliance. A zero means the weighted penalty reached the floor; it is not an independent accessibility verdict on an entire company. The default maximum of 40 narrated announcements was retained (Tazz exposed only seven).

| Platform | Review result | Captured score | Findings C/S/M/m | Clip seconds | Processing seconds | Analysis ID |
| --- | --- | ---: | --- | ---: | ---: | --- |
| Flip.ro | Artifact validation passed | 0 | 0/2/562/0 | 124.572 | 599.44 | `e2e-ro-https---flip-ro-16f6d8e1` |
| Vivre | Artifact validation passed | 96 | 0/0/2/0 | 105.973 | 535.98 | `e2e-ro-https---vivre-ro-83b168ce` |
| Tazz | Consent-only; blocked verification | — | 1/8/0/4 | 19.505 | 282.55 | `e2e-ro-https---tazz-ro-af2322b1` |
| Pago | Artifact validation passed | 93 | 0/1/1/0 | 82.974 | 430.32 | `e2e-ro-https---pago-ro-26f88438` |
| Salt Bank | Artifact validation passed | 0 | 6/11/5/0 | 152.320 | 599.21 | `e2e-ro-https---salt-bank-edbc19f3` |
| Sameday | Artifact validation passed | 0 | 1/34/14/0 | 129.007 | 499.27 | `e2e-ro-https---sameday-ro-805d838d` |
| eJobs | Artifact validation passed | 0 | 1/0/96/0 | 87.223 | 489.12 | `e2e-ro-https---ejobs-ro-5318424a` |
| Elefant.ro | Artifact validation passed | 0 | 2/513/2/0 | 76.890 | 582.86 | `e2e-ro-https---elefant-ro-ae3a1c57` |
| Kinderpedia | Artifact validation passed | 96 | 0/0/2/0 | 140.234 | 503.05 | `e2e-ro-https---kinderpedia-co-2aa47a26` |

### Interpretation and limitations

- **Tazz:** The original run recorded a Wolt-titled document with six accessibility nodes, all belonging to cookie-consent text and controls (seven narrated events including the page announcement). No representative service score is claimed. Independent follow-up HTTP and TLS-verified browser requests returned HTTP 503, with an environment-proxy upstream transport failure. The browser follow-up remained at `https://tazz.ro/`; a redirect to another domain was not established. Revalidate when the full target content is reachable.
- **Flip.ro and Elefant:** Cookiebot content persisted at the beginning of extraction and may dominate the initial narration. Main-page nodes were also present, but consent handling and the recorded video require manual review. Sameday also exposed consent preferences alongside main navigation.
- **Kinderpedia:** The captured landing-page content is English. The requested Romanian narration/recommendation mode was retained; existing English accessible names remain English.
- All captures are single-page, unauthenticated observations. Extraction is capped at 400 nodes; narration at 40 announcements. Findings without corresponding narration may have no timestamp.
- Processing took several minutes per site in this shared CPU environment; this run does **not** establish the product's under-three-minute performance target.
- Captures were reviewed for title, representative node content, artifact consistency and audio/video streams. No claim is made that a real blind user or a real screen reader completed a task.

### Reproduction and artifacts

Run the documented preset in an environment with working browser certificate trust:

```bash
CP_STUBS= TTS_ENGINE=piper .venv/bin/python scripts/test_popular_sites.py --preset romanian --output .local/romanian-audit.json --markdown .local/romanian-audit.md
```

Each analysis ID above identifies `data/<id>/nodes.json`, `events.json`, `issues.json`, `timeline.json`, `report.json`, `status.json` and `clip.mp4`. With the API serving that data directory, videos are available at `/media/<id>/clip.mp4` and JSON/HTML downloads at `/api/analyses/<id>/export?format=json|html`. The captured artifacts are local, gitignored runtime data, not files published by this code PR.

Local evidence manifests: `.local/verified-ro-{0,1,2}.{json,md,log}` and `.local/final-romanian-audit.json`. The consent-only Tazz findings remain in the raw artifact for transparency, but its raw score is excluded from the target-results table.

- **Pull Request:** https://github.com/ClearPath-Team/Clearpath/pull/62
