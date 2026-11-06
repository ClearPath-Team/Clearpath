# Task: [M4-10] Exportable Professional Audit Reports with Categorized Findings (PDF/HTML/JSON)

- **Task ID:** `M4-10`
- **GitHub Issue:** #59
- **Track:** `M4` (API, Web Dashboard, and Formal Reporting)
- **Type:** `Feature`
- **Priority:** `P1 - current milestone`
- **Status:** `In review`
- **Assignee:** `andreiBirsanIoan`
- **Branch:** `m4-exportable-audit-reports`
- **Pull Request:** https://github.com/ClearPath-Team/Clearpath/pull/62
- **Created Date:** 2026-11-06

---

## 1. Goal
Build an export engine and downloadable professional accessibility audit report generator (standalone printable HTML / PDF-ready document and structured JSON export) that formats ClearPath analysis findings into an authoritative, legitimate compliance audit document organized by the canonical finding categories established in `M2-04`.

---

## 2. Context
While ClearPath provides an interactive Next.js web studio with video playback, organizations, QA teams, accessibility consultants, and corporate clients require **formal, exportable compliance artifacts** that can be:
1. Shared with non-technical stakeholders and leadership as an official accessibility review.
2. Archived in Jira, GitHub, or audit compliance repositories.
3. Printed or saved as a clean, professional PDF without web UI clutter.

To look and feel legitimate, authoritative, and canonical, the exported report must not simply be a raw list of code errors; it must group findings into clear functional sections (Contrast & Low Vision, Screen Reader & ARIA, Keyboard & Motor Navigation, Page Structure), explain the real-world user impact for each group, and include verification metadata (audit timestamp, engine versions, and WCAG 2.1 AA conformance rating).

---

## 3. Report Architecture & Visual Structure

The exported document must be rendered via a clean, self-contained HTML template with print-optimized CSS (`@media print` supporting native browser "Save as PDF"):

### Section 1: Executive Audit Header & Certification Metadata
- **Target URL & Title:** Target website with direct link.
- **Audit Timestamp:** ISO 8601 timestamp and local audit time.
- **Evaluation Engine Signature:** ClearPath v1.0, Playwright Chromium, axe-core 4.10.2, Piper Neural Voice.
- **Overall Accessibility Score:** Large circular/badge score (0–100) with color coding (Green: 90+, Amber: 50–89, Red: <50).
- **Executive Summary:** Quick summary text indicating primary areas of non-compliance and keyboard trap status.

### Section 2: Categorized Findings Breakdown (Powered by M2-04)
Grouped sections for each of the 4 canonical categories:
1. **Contrast & Visual Accessibility:** Impact on low vision/color blindness, contrast violation count, affected selectors, and ratio remedies.
2. **Screen Reader & Semantics:** Impact on blind users, missing accessible names (`button-name`, `image-alt`), missing form labels, and ARIA violations.
3. **Keyboard & Motor Navigation:** Keyboard traps, Tab focus traversal integrity, and nested interactives.
4. **Page Structure & Cognitive Orientation:** Landmarks, heading outline hierarchy, and document language tags.

Each category section includes:
- Summary of impact on specific user disabilities.
- Category status badge (**Compliant**, **Needs Attention**, or **Critical Barriers**).
- Itemized violation cards with:
  - Exact video timestamp (e.g. `00:14.3`).
  - Severity badge (`critical`, `serious`, `moderate`, `minor`).
  - Target DOM selector (`selector.js` canonical string).
  - Remediation recommendation (plain Romanian or English).
  - Deque University / WCAG reference citation link.

### Section 3: Narrated Traversal Transcript Summary
- Table listing the sequential screen-reader announcements, timestamps, and active element bounding boxes recorded in `timeline.json`.

---

## 4. Scope (Strict Boundary)
The assignee is permitted to modify or create:
- `api/export.py` or `worker/engine/export.py` (HTML report template and JSON export generator)
- `api/main.py` (add `GET /api/analyses/{id}/export` endpoint supporting `format=html` and `format=json`)
- `api/test_export.py` (automated tests for export generation and validation)
- `web/components/ExportReportButton.tsx` (dropdown or button on the results page)
- `web/app/a/[id]/page.tsx` (integrate the Export button into the header/studio actions)
- `tasks/m4-10-exportable-canonical-audit-reports.md`
- `tasks/README.md`

**Forbidden:** Modifying core data contracts (`contracts/`), changing scoring formulas, or altering video rendering.

---

## 5. Acceptance Criteria
- [x] Implement `generate_html_report(report_data)` generating a standalone, self-contained HTML file (embedded CSS, zero external CDN dependencies) optimized for print and PDF generation (`@media print`).
- [x] Add `GET /api/analyses/{id}/export?format=html|json` in `api/main.py`:
  - Returns `text/html` with `Content-Disposition: attachment; filename="clearpath-audit-{id}.html"` when `format=html`.
  - Returns canonical `application/json` download when `format=json`.
  - Returns `404` if the analysis is not found, and `409` if still in progress.
- [x] The exported report groups all findings by the 4 canonical categories from `M2-04` with executive explanations.
- [x] Include an "Export Report" button in the Next.js analysis view (`web/app/a/[id]/page.tsx`) triggering report download or print dialog.
- [x] All unit and integration tests in `api/test_export.py` pass cleanly.

---

## 6. Validation & Test Commands
```bash
# 1. Run export API test suite
.venv/bin/python -m unittest api.test_export -v

# 2. Test export endpoint against a sample analysis
.venv/bin/python -c "
import urllib.request
from worker.common import DATA_DIR

# Verify sample report HTML generation
from api.export import generate_html_report
from worker.common import read_json, SAMPLES
sample_rep = read_json(SAMPLES / 'report.json')
html = generate_html_report(sample_rep)
assert '<title>' in html and 'Contrast & Visual' in html or 'Contrast' in html
assert 'clearpath' in html.lower()
print('EXPORT HTML GENERATION PASSED!')
"

# 3. Check web dashboard build
cd web && npm run build && cd ..
```

---

## 7. Dependencies
- **Requires `M2-04`** (Canonical Issue Categorization & Multi-Taxonomy Classification)
- Merged `M4-02` (Frontend dashboard fixes)

---

## 8. Out of Scope
- Requiring server-side headless Chrome PDF print daemons (client-side browser print or self-contained HTML provides 100% portable PDF export without heavy binary dependencies).
- Paid compliance certification signatures.

---

## 9. Execution Log
- **2026-11-06:** Task `M4-10` created as Ready in backlog (depends on M2-04).


- **2026-11-06:** Claimed by @andreiBirsanIoan. Implemented standalone printable HTML, canonical JSON download, categorized findings, escaped untrusted page content, transcript/bounding-box evidence, completion timestamps and bilingual export controls. HTML is PDF-ready through browser Print/Save as PDF; no server PDF engine added.
- **Validation:** 19 export/existing API tests passed; Next.js production build passed. Canonical source JSON is preserved. Missing historical engine metadata is labelled not recorded; no engine versions or certification claims are invented. No automated findings is used instead of a claim of compliance.
- **Limitations:** Legacy runs may lack transcript, bounding boxes, timestamp or engine provenance. Available evidence is exported and missing values are explicitly marked.


## 8. Execution Log
- **2026-11-06 20:29 UTC:** PR opened: https://github.com/ClearPath-Team/Clearpath/pull/62 (Status -> In review)
