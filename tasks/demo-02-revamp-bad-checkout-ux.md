# Task: [DEMO-02] Modernize & Revamp Demo Checkout Page (bad-checkout.html) for Realism & Better UX

- **Task ID:** `DEMO-02`
- **GitHub Issue:** #31
- **Track:** `Demo` (Demo site and presentation UX)
- **Type:** `Feature`
- **Priority:** `P1 - current milestone`
- **Status:** `Ready`
- **Assignee:** `Unassigned`
- **Branch:** `demo-revamp-bad-checkout`
- **Created Date:** 2026-11-06

---

## 1. Goal
Revamp `test-site/bad-checkout.html` from a barebones 45-line HTML wireframe into an authentic, production-grade Romanian e-commerce checkout page ("PasUșor Sport") featuring modern UX design patterns (stepper navigation, two-column responsive layout, delivery and courier options, payment method selection, rich order summary with item breakdown, trust badges), while strictly preserving all intentional accessibility defects (`html-has-lang`, `button-name`, `image-alt`, `label`, `link-name`, `color-contrast`, `heading-order`, `keyboard-trap`, and non-semantic fake button) and essential DOM selectors, ensuring ClearPath's live offline presentation is both visually compelling and demonstrably accurate.

---

## 2. Context
In the final live presentation and hackathon pitch (`doc/3-integration/demo.md`), ClearPath audits `http://localhost:8080/bad-checkout.html` live on stage and displays the recorded clip (`clip.mp4`) in the web dashboard.

Currently:
- `test-site/bad-checkout.html` is a 45-line minimal HTML prototype with raw inline CSS, plain unstyled input boxes, and an SVG grey rectangle placeholder.
- When recorded in the demonstration video (`clip.mp4`) and showcased in the results dashboard (`/a/{id}`), it looks like a toy test fixture rather than an authentic commercial website, detracting from the credibility and realism of ClearPath's accessibility findings.
- Real-world accessibility violations rarely occur in unstyled wireframes; they occur on polished, visually attractive websites where accessibility was neglected during frontend design.
- Modernizing `bad-checkout.html` into a realistic Romanian e-commerce checkout page (similar to eMAG, Fashion Days, or AboutYou) provides a far more convincing, professional demonstration for judges and users.
- **Strict Constraints:**
  1. **Romanian Localization:** Per `CLAUDE.md` Section 2, the demo site is authored in Romanian and **MUST remain in Romanian**.
  2. **100% Offline Capability:** The page must remain completely self-contained. No external CDN stylesheets, web fonts (e.g. Google Fonts), or external image URLs are allowed. All CSS and SVG graphics must be embedded locally/inline so `python -m http.server 8080` functions flawlessly without Wi-Fi.
  3. **Intentional Flaw Preservation:** The automated pipeline and axe-core audit rely on specific WCAG violations and the keyboard trap on `#promo`. All flaws must be carefully integrated into the new layout.

---

## 3. Scope (Strict Boundary)
The assignee is permitted to modify or create:
- `test-site/bad-checkout.html` (the primary revamped HTML page)
- `contracts/samples/nodes.json`, `events.json`, `issues.json`, `timeline.json`, `report.json` (regenerated mock samples to synchronize with any DOM hierarchy updates)
- `worker/extract/test_extract.py` (update `test_bad_checkout_extraction_is_unchanged` assertions if node count or structure expands)
- `worker/engine/test_audit.py` (verify that axe violation rule checks continue to pass against the revamped page)
- `tasks/demo-02-revamp-bad-checkout-ux.md`
- `tasks/README.md`

**Forbidden:**
- Modifying core extraction algorithms in `worker/extract/extract.py` or `worker/extract/tab_walk.py`.
- Modifying core scoring formulas or rule weights in `worker/engine/report.py`.
- Introducing external network dependencies (fonts, CDNs, external images) that break offline capability.
- Changing the primary language away from Romanian.

---

## 4. Key UX & Visual Specifications

### 4.1. Design System & Aesthetics
- **Canvas & Viewport:** Optimized for standard 1280×720 viewport (the ClearPath recording resolution), centered in a `max-width: 1100px` container.
- **Typography:** Modern clean system font stack (`system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`).
- **Color Palette:** Slate/neutral backgrounds (`#f8fafc`, `#ffffff`), subtle borders (`#e2e8f0`), deep slate header (`#0f172a`), brand accents (emerald green / indigo highlights).
- **Cards & Elevation:** Rounded cards (`border-radius: 12px`), clean borders, and soft shadows (`0 4px 6px -1px rgba(0, 0, 0, 0.05)`).

### 4.2. Header & Store Branding
- **Logo / Brand:** "PasUșor" with slogan "Încălțăminte Sportivă & Lifestyle".
- **Navigation Links:** Categories ("Bărbați", "Femei", "Copii", "Reduceri").
- **Header Actions:**
  - Search link `<a href="#cauta">`: Search SVG icon (*Intentional flaw: missing link name / `aria-label`*).
  - Shopping cart button `<button id="cart">`: Cart SVG icon with notification badge "1" (*Intentional flaw: missing accessible button name / `aria-label`*).

### 4.3. Checkout Stepper / Progress Bar
- Clean visual indicator of the checkout process:
  - `1. Coș de cumpărături` (Completat)
  - `2. Date livrare & Plată` (Activ)
  - `3. Confirmare comandă` (Următorul)

### 4.4. Two-Column Desktop Checkout Layout
- **Left Column: Checkout Form (approx. 60% width)**
  1. **Date de contact & Livrare:**
     - Nume complet: `<label for="name">Nume complet</label><input id="name" required>`
     - Email: `<input id="email" type="email" placeholder="exemplu@email.ro">` (*Intentional flaw: missing `<label for="email">` or `aria-label`*)
     - Telefon: `<label for="phone">Telefon</label><input id="phone" type="tel">`
     - Adresă de livrare: Adresă completă, Oraș, Județ.
  2. **Metodă de livrare:**
     - Selectable options styled as radio cards: "Curier Rapid (Fan Courier) - 15 Lei" vs "Ridicare personală Easybox (Sameday) - Gratuit".
  3. **Metodă de plată:**
     - Selectable options styled as radio cards: "Card bancar online (Visa / Mastercard)" vs "Plată la livrare (Ramburs)".
  4. **Cod promoțional & Reducere:**
     - `<label for="promo">Cod promoțional</label>`
     - `<input id="promo" onkeydown="if (event.key === 'Tab') { event.preventDefault(); }">` (*Intentional flaw: Tab keyboard trap*)
  5. **Muted Helper Information:**
     - `<p class="muted">Livrare gratuită pentru comenzi de peste 200 de lei. Termen estimat de livrare: 24-48 ore lucrătoare.</p>` (*Intentional flaw: low color contrast text on light background, ratio < 4.5:1*).

- **Right Column: Sticky Order Summary (approx. 40% width)**
  1. **Section Heading:** Headings structured with intentional level skip (*Intentional flaw: `<h1>` followed by `<h4>` or heading hierarchy jump*).
  2. **Product Item Card:**
     - Product thumbnail: High-fidelity inline SVG graphic of modern running shoes (*Intentional flaw: `<img>` tag without `alt` attribute*).
     - Product details: "Adidași Alergare PasUșor Pro Runner X", "Mărime: 42", "Culoare: Negru / Neon".
     - Preț: "349,00 Lei".
  3. **Cost Breakdown:**
     - Subtotal produse: 349,00 Lei
     - Cost livrare: 0,00 Lei (Promoție activată)
     - TVA inclus (19%): 55,72 Lei
     - **Total general: 349,00 Lei**
  4. **Primary Checkout CTA Button:**
     - `<div class="fake-btn" onclick="this.textContent = 'Comandă trimisă cu succes!'">Plasează comanda</div>` (*Intentional flaw: fake button created using a `<div>` instead of a semantic `<button>`, inaccessible to keyboard Tab navigation and screen readers*).
  5. **Trust Badges:**
     - Security chips: "🔒 Plată securizată SSL 256-bit", "🚚 Retur gratuit în 30 de zile", "🛡️ Garanție 24 de luni", "📞 Suport clienți: 0800 800 123".

---

## 5. Intentional Accessibility Flaws Matrix

The table below defines the exact intentional accessibility defects that **must be retained** in the revamped page:

| Flaw Category | Element & Selector | WCAG / axe-core Rule | Implementation Detail & Purpose |
|---|---|---|---|
| **Missing Document Language** | `<html>` | `html-has-lang` | Omit `lang="ro"` on root tag so axe detects missing primary language. |
| **Unlabelled Cart Button** | `<button id="cart">` | `button-name` | Icon button contains only SVG; no accessible name or `aria-label`. |
| **Unlabelled Search Link** | `<a href="#cauta">` | `link-name` | Search link contains only SVG circle/icon without accessible text. |
| **Missing Image Alt Text** | `<img>` in cart summary | `image-alt` | Product shoe thumbnail contains no `alt` attribute (`<img src="..." width="..." height="...">`). |
| **Missing Input Label** | `<input id="email">` | `label` | Email input is not associated with any `<label>` or `aria-label`. |
| **Low Contrast Helper Text** | `.muted` class | `color-contrast` | Gray text (e.g. `#c4c4c4` or `#a1a1aa` on `#f8fafc` or `#ffffff`) failing the 4.5:1 minimum contrast ratio. |
| **Heading Hierarchy Jump** | `<h1>` to `<h4>` | `heading-order` | Main title is `<h1>`, immediately followed by `<h4>` for product/order section, skipping `<h2>`/`<h3>`. |
| **Keyboard Focus Trap** | `<input id="promo">` | `keyboard-trap` | Input captures Tab key with `onkeydown="if (event.key === 'Tab') { event.preventDefault(); }"` to trigger trap detection (-15 score penalty). |
| **Non-Semantic CTA Button** | `<div class="fake-btn">` | Semantic button | "Plasează comanda" rendered as `<div>` lacking `role="button"` and `tabindex="0"`, missing from Tab walk. |

---

## 6. Acceptance Criteria
- [ ] **Aesthetic & Realism:** `test-site/bad-checkout.html` appears as a genuine, contemporary Romanian online store with a clean two-column layout, modern typography, card styling, and cohesive branding.
- [ ] **100% Offline & Self-Contained:** Zero external network requests (no CDNs, Google Fonts, or external image URLs). All styles, SVG icons, and product imagery are embedded directly in the HTML file.
- [ ] **Romanian Language:** All visible user interface text, labels, delivery terms, and product descriptions are written in idiomatic Romanian with correct diacritics.
- [ ] **Essential Selectors Preserved:** The core IDs and classes (`#cart`, `#name`, `#email`, `#promo`, `#phone`, `.fake-btn`, `.muted`) remain present in the DOM for downstream tests.
- [ ] **All 8 axe-core Violations Detected:** Running `worker.engine.audit` against the page triggers:
  1. `html-has-lang`
  2. `button-name`
  3. `link-name`
  4. `image-alt`
  5. `label`
  6. `color-contrast`
  7. `heading-order`
  8. `keyboard-trap`
- [ ] **Keyboard Trap Detected:** CDP tab traversal in `worker.extract.tab_walk` halts at `#promo` and flags the trap.
- [ ] **Sample Synchronization:** If the DOM tree structure changes, contract mock files in `contracts/samples/` are updated so offline tests continue to pass.
- [ ] **Test Compatibility:** `worker/extract/test_extract.py` and `worker/engine/test_audit.py` pass without regression.
- [ ] **End-to-End Pipeline Verification:** Executing `python -m worker.pipeline demo_revamp http://localhost:8080/bad-checkout.html` completes all 5 stages cleanly, generating `clip.mp4` with realistic visual highlights.

---

## 7. Validation & Test Commands
```bash
# 1. Start local test HTTP server on port 8080
python -m http.server 8080 --directory test-site &
SERVER_PID=$!

# 2. Verify extraction and AX-tree generation
.venv/bin/python -m worker.extract.extract http://localhost:8080/bad-checkout.html data/dev/nodes.json
.venv/bin/python -c "
from worker.common import read_json
nodes = read_json('data/dev/nodes.json')
assert nodes['focus_trap'] is not None, 'Focus trap on #promo must be detected'
assert nodes['focus_trap']['selector'] == '#promo'
print('Extraction validation PASSED')
"

# 3. Verify axe-core audit captures all required violation rules
.venv/bin/python -m worker.engine.audit http://localhost:8080/bad-checkout.html data/dev/nodes.json
.venv/bin/python -c "
from worker.common import read_json
from worker.engine.audit import run_audit
issues = run_audit('http://localhost:8080/bad-checkout.html', read_json('data/dev/nodes.json'))
rules = {i['rule'] for i in issues}
required = {'html-has-lang', 'button-name', 'link-name', 'image-alt', 'label', 'color-contrast', 'heading-order', 'keyboard-trap'}
assert required <= rules, f'Missing required rules: {required - rules}'
print('Audit validation PASSED: All 8 required rules detected')
"

# 4. Verify full pipeline execution and artifact generation
.venv/bin/python -m worker.pipeline dev_revamp http://localhost:8080/bad-checkout.html
.venv/bin/python -c "
from pathlib import Path
from worker.common import read_json
rep = read_json(Path('data/dev_revamp/report.json'))
assert rep['score'] is not None and rep['score'] < 50, f'Expected failing accessibility score, got {rep[\"score\"]}'
assert Path('data/dev_revamp/clip.mp4').exists(), 'clip.mp4 must be generated'
print('Full pipeline validation PASSED')
"

# 5. Run test suites
.venv/bin/python -m unittest worker/engine/test_audit.py
.venv/bin/python -m unittest worker/extract/test_extract.py

# 6. Clean up background HTTP server
kill $SERVER_PID
```

---

## 8. Dependencies
- Merged `M1-02` (Cookie dismissal and live extraction resilience)
- Merged `M2-02` (Scoring weights reconciliation)
- Merged `M3-02` (Timeline schema alignment)

---

## 9. Out of Scope
- Implementing active server-side form submission endpoints (e.g. actual credit card processing or backend checkout API).
- Converting `test-site/bad-checkout.html` to a frontend framework (must remain pure HTML/CSS/JS for simple local HTTP serving).
- Adding multi-page checkout steps across different HTML files (must remain a self-contained single-page checkout).

---

## 10. Execution Log
- **2026-11-06:** Task specification created as Ready for the Demo Polish milestone.
