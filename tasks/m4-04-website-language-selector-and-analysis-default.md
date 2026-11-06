# Task: [M4-04] Website Language Selector (English Main / Romanian Secondary) & Initial Analysis Language Default

- **Task ID:** `M4-04`
- **GitHub Issue:** #38
- **Track:** `M4` (API, web, and orchestration)
- **Type:** `Feature`
- **Priority:** `P1 - current milestone`
- **Status:** `In review`
- **Assignee:** `@andreiBirsanIoan`
- **Branch:** `m4-website-language-selector`
- **Created Date:** 2026-11-06

---

## 1. Goal
Implement a website-wide language selector for the ClearPath frontend with English (`en`) as the primary/main language and Romanian (`ro`) as the secondary language, internationalizing the user interface copy, and automatically synchronizing the initial default language selection for the analysis form on the user's first analysis based on the selected website language.

---

## 2. Context
Per the project guidelines (`CLAUDE.md` §2), English is the primary standard across the repository, while Romanian was initially implemented to demonstrate accessibility testing on the local Romanian test site (`bad-checkout.html`). Currently:
- The entire website layout (`web/app/layout.tsx`), landing page (`web/app/page.tsx`), and report views (`web/app/a/[id]/page.tsx`) are authored exclusively in Romanian (`<html lang="ro">`).
- Task M4-03 introduces an analysis language toggle for URL submissions (`POST /api/analyses` with `lang: "ro" | "en"`), but explicitly leaves the website marketing copy and UI shell out of scope.
- To accommodate international audiences, evaluators, and judges, the website itself needs a persistent language switcher with English as the main default and Romanian as the secondary option.
- When an end user visits ClearPath, the analysis language selector on the submission form should automatically default to match the user's active website language selection for their first analysis (e.g. English UI defaults to English analysis narration; Romanian UI defaults to Romanian analysis narration), while still allowing the user to override the analysis language independently before submission.

---

## 3. Scope (Strict Boundary)
The agent is permitted to modify only the following files:
- `web/app/layout.tsx`
- `web/app/page.tsx`
- `web/app/a/[id]/page.tsx`
- `web/components/**` (e.g. `web/components/LanguageSelector.tsx`, layout components)
- `web/lib/**` or `web/locales/**` (e.g. dictionary / translation definitions for `en` and `ro`)
- `tasks/m4-04-website-language-selector-and-analysis-default.md`
- `tasks/README.md`

**Forbidden:** Modifying `worker/extract/`, `worker/media/`, `worker/engine/`, or backend contracts in `contracts/`.

---

## 4. Acceptance Criteria
- [x] **Website Language Switcher (`web/components/LanguageSelector.tsx` or Header):**
  - Add an accessible, visible language switcher toggle/dropdown in the main header navigation (`web/app/layout.tsx`).
  - Set **English (`en`)** as the primary / default language for the website.
  - Provide **Romanian (`ro`)** as the secondary language option.
  - Dynamically updates `<html lang="en">` or `<html lang="ro">` attributes for screen readers and SEO.
  - Persists the selected website language in client storage (`localStorage` / cookies) so user preference is remembered across refreshes and page transitions.
- [x] **UI Internationalization (i18n):**
  - Create a lightweight, type-safe localization dictionary/provider (e.g. `web/lib/i18n.ts` or `web/locales/`) supporting English and Romanian translations.
  - Translate the following core website sections:
    - Header navigation ("New Analysis", "GitHub", skip to main content).
    - Landing page hero title, subtitle, badges, and features summary.
    - URL input placeholder, submit button text, and validation/error banners.
    - Report dashboard UI labels (score card, status badges, severity filter tabs, issues list, video playback guidance, timestamp instructions).
    - Footer attribution text.
- [x] **Analysis Language Default Synchronization (First Analysis):**
  - When a user loads the landing page (`/`), the analysis language toggle defaults to the currently selected website language (`en` if website is English, `ro` if website is Romanian).
  - If the user changes the website language before touching the analysis toggle, the analysis language selection dynamically updates to match.
  - If the user explicitly selects a different analysis language (manual override), preserve their manual choice for the submission.
  - When submitting the URL, the form sends `{ url: trimmed, lang: selectedAnalysisLang }` to `POST /api/analyses`.
- [ ] **Accessibility & Code Quality:**
  - The language selector is fully keyboard-accessible (Tab navigation, Enter/Space activation) with proper `aria-label`, `role`, and focus rings.
  - Next.js production build (`cd web && npm run build`) compiles cleanly with zero TypeScript errors or ESLint warnings.

---

## 5. Validation & Test Commands
```bash
# 1. Verify Next.js build and TypeScript compilation
cd web
npm run build
cd ..

# 2. Verify task CLI status
.venv/bin/python scripts/task.py check M4-04

# 3. Verify task listing
.venv/bin/python scripts/task.py list
```

---

## 6. Dependencies
- M4-01 (Frontend init)
- M4-02 (Frontend dashboard fixes)
- M4-03 (Toggleable Analysis Language in URL submission)

---

## 7. Out of Scope
- Translating the content of external third-party audited target websites (they are audited in their authored language or the selected analysis language).
- Adding additional languages beyond English and Romanian for the MVP.

---

## 8. Execution Log (Updated by Assignee)
- **2026-11-06:** Implementation proposed on `m4-website-language-selector`: typed EN/RO translations, persistent header selector, document language updates, localized landing/report, synchronized analysis default with manual override. Next.js build and integrated backend flow not yet verified.
- **Dependency:** M4-03 (#36) must merge for the API to actually consume `lang`. The current `main` ignores the extra JSON property.
- **Status Change:** `Ready` -> `In review`
- **Claimed by:** Unassigned
