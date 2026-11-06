# Task: [M2-04] Canonical Issue Categorization & Multi-Taxonomy Classification

- **Task ID:** `M2-04`
- **GitHub Issue:** #58
- **Track:** `M2` (Engine, Rules, and Data Contracts)
- **Type:** `Feature`
- **Priority:** `P1 - current milestone`
- **Status:** `In review`
- **Assignee:** @andreiBirsanIoan
- **Branch:** `m2-canonical-categorization`
- **Created Date:** 2026-11-06

---

## 1. Goal
Implement a canonical, backend-driven issue classification taxonomy in `worker/engine/` that organizes accessibility violations into meaningful functional and disability domains (beyond the existing 4-level severity score), tags each violation with its corresponding WCAG principle (POUR), exposes category rollups in `report.json`, and provides the data structure for frontend category-based filtering.

---

## 2. Context
Currently, ClearPath classifies detected accessibility violations solely by:
1. **Severity Impact:** `critical`, `serious`, `moderate`, `minor`
2. **Raw Rule ID:** e.g., `color-contrast`, `button-name`, `keyboard-trap`

While severity is essential for calculating the overall 0–100 score, end users, developers, and compliance officers cannot easily distinguish between different classes of barriers (e.g., contrast issues affecting low-vision users vs. keyboard traps blocking motor-impaired users vs. missing alt text breaking screen readers).

By establishing a **canonical taxonomy on the backend**, issues are classified deterministically at audit time, providing structured groupings for both the UI dashboard and downstream formal report exporters (M4-10).

---

## 3. Canonical Taxonomy Specification

Every issue in `issues.json` and `report.json` must be assigned to exactly one primary **Domain Category** and one **WCAG Principle**:

### A. Domain Categories (`category`)

| Category Key | Display Name (EN) | Display Name (RO) | Target User Group / Impairment | Covered Axe / Engine Rules |
|---|---|---|---|---|
| `visual_contrast` | Contrast & Visual | Contrast și lizibilitate | Low vision, color blindness, cataracts | `color-contrast`, `link-in-text-block` |
| `screen_reader` | Screen Reader & Semantics | Cititoare de ecran și ARIA | Blindness, screen reader navigation | `image-alt`, `button-name`, `link-name`, `label`, `select-name`, `aria-*`, `input-image-alt` |
| `motor_keyboard` | Keyboard & Motor Access | Navigare tastatură și motor | Motor impairments, keyboard-only users | `keyboard-trap`, `nested-interactive`, `aria-hidden-focus` |
| `structure_navigation` | Page Structure & Orientation | Structură și repere de pagină | Cognitive orientation, non-visual navigation | `landmark-one-main`, `region`, `page-has-heading-one`, `heading-order`, `empty-heading`, `html-has-lang`, `document-title` |

### B. WCAG Principles (`wcag_principle`)
- `perceivable`: Information and UI components must be presentable in ways users can perceive.
- `operable`: UI components and navigation must be operable via any input mechanism.
- `understandable`: Information and operation must be predictable and readable.
- `robust`: Content must be reliably interpretable by a wide range of assistive technologies.

---

## 4. Data Contract Updates

### `issues.json` (per-issue schema):
```json
{
  "id": "i1",
  "rule": "color-contrast",
  "severity": "serious",
  "category": "visual_contrast",
  "category_label": { "en": "Contrast & Visual", "ro": "Contrast și lizibilitate" },
  "wcag_principle": "perceivable",
  "node_id": "n12",
  "selector": "#submit-btn",
  "title": "Contrast insuficient între text și fundal",
  "recommendation": "Mărește contrastul textului pentru a atinge raportul minim WCAG de 4.5:1.",
  "help_url": "https://dequeuniversity.com/rules/axe/4.10/color-contrast"
}
```

### `report.json` (aggregated categories rollup):
```json
{
  "counts": { "critical": 2, "serious": 4, "moderate": 3, "minor": 1 },
  "categories": {
    "visual_contrast": 4,
    "screen_reader": 3,
    "motor_keyboard": 1,
    "structure_navigation": 2
  }
}
```

---

## 5. Scope (Strict Boundary)
The assignee is permitted to modify or create:
- `worker/engine/categories.py` (new module: taxonomy definitions, rule mappings, and category helper functions)
- `worker/engine/audit.py` (enrich mapped issues with `category`, `category_label`, and `wcag_principle`)
- `worker/engine/report.py` (aggregate `categories` counts into `report.json`)
- `worker/engine/test_categories.py` (unit tests verifying all rules in `RECOMMENDATIONS` and axe rules map to valid categories)
- `doc/1-foundation/data-contracts.md` (document updated `category` and `categories` fields)
- `contracts/samples/issues.json`, `contracts/samples/report.json` (update contract test fixtures)
- `web/components/` or `web/app/a/[id]/page.tsx` (add Category filter chips/tabs alongside Severity tabs in dashboard)
- `tasks/m2-04-canonical-issue-categorization.md`
- `tasks/README.md`

**Forbidden:** Altering scoring formulas (M2-02 weights), altering selector generation (`contracts/selector.js`), or changing Piper TTS rendering pipeline.

---

## 6. Acceptance Criteria
- [ ] Create `worker/engine/categories.py` mapping 100% of rules in `worker/engine/recommendations.py` plus common axe-core rules and `keyboard-trap` to a valid `category` and `wcag_principle`.
- [ ] `run_audit()` attaches `category`, `category_label` (`en` and `ro`), and `wcag_principle` to every item in `issues.json`.
- [ ] `build_report()` calculates the `categories` count dictionary in `report.json` with counts for all 4 canonical keys.
- [ ] Contract sample fixtures (`contracts/samples/issues.json`, `contracts/samples/report.json`) are updated and pass JSON validation.
- [ ] Unit tests in `worker/engine/test_categories.py` verify that any unknown rule defaults safely to `structure_navigation` without crashing.
- [ ] The web dashboard in `web/` provides a toggle or tabs allowing users to filter issues by Category (Contrast, Screen Reader, Keyboard, Structure).

---

## 7. Validation & Test Commands
```bash
# 1. Run taxonomy unit tests
.venv/bin/python -m unittest worker.engine.test_categories -v

# 2. Run full report generation test
.venv/bin/python -c "
from worker.common import read_json, SAMPLES
from worker.engine.report import build_report

rep = build_report('test', 'https://example.com', read_json(SAMPLES / 'nodes.json'), read_json(SAMPLES / 'issues.json'), read_json(SAMPLES / 'timeline.json'))
assert 'categories' in rep, 'Missing categories in report'
assert all(k in rep['categories'] for k in ['visual_contrast', 'screen_reader', 'motor_keyboard', 'structure_navigation'])
print('CATEGORIZATION TEST PASSED!')
"

# 3. Check web dashboard build
cd web && npm run build && cd ..
```

---

## 8. Dependencies
- Merged `M2-02` (Scoring weights)
- Merged `M2-03` (English & Romanian recommendations)

---

## 9. Out of Scope
- PDF generation or file export (covered in dependent task `M4-10`).
- Machine learning automatic categorization.

---

## 10. Execution Log
- **2026-11-06:** Implemented taxonomy module, audit and report enrichment, bilingual labels, fixtures, deterministic unknown-rule fallback, unit tests and dashboard category filters. Review and full Python/Next.js validation pending.
- **2026-11-06:** Reconciled with the merged redesigned EN/RO dashboard. Category controls follow the website language independently of backend content. Updated live axe contract assertions for taxonomy fields and added legacy-report enrichment coverage. Full Python discovery: 95 passed, one opt-in E2E skipped; production build passes. Scoring weights and score 33 remain unchanged.
