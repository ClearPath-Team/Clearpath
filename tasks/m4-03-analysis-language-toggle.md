# Task: [M4-03] Toggleable Analysis Language in URL Submission & End-to-End Flow

- **Task ID:** `M4-03`
- **GitHub Issue:** #36
- **Track:** `M4` (API, web, and orchestration)
- **Type:** `Feature`
- **Priority:** `P1 - current milestone`
- **Status:** `In review`
- **Assignee:** `@andreiBirsanIoan`
- **Branch:** `m4-language-toggle-ui`
- **Created Date:** 2026-11-06

---

## 1. Goal
Add a user-friendly, accessible language toggle (Română 🇷🇴 / English 🇬🇧) to the URL submission form on the Next.js home page, propagate the chosen language through the FastAPI REST endpoint, pass it to the background pipeline orchestrator, and display the language badge in the analysis report dashboard.

---

## 2. Context
With English speech and recommendation capabilities provided by M2-03, the ClearPath user interface needs to allow the user to select whether they want the website audited and narrated in Romanian or English when submitting a URL.

Currently:
- `web/app/page.tsx` only sends `{ url: trimmed }` to `POST /api/analyses`.
- `api/main.py` defines `AnalysisRequest` with only `url: str`.
- `worker/pipeline.py` takes only `sys.argv[1]` (id) and `sys.argv[2]` (url).
- `web/app/a/[id]/page.tsx` displays reports without indicating the analysis language.

This task connects the frontend selector all the way through to the backend analysis pipeline.

---

## 3. Scope (Strict Boundary)
The agent is permitted to modify only the following files:
- `web/app/page.tsx`
- `web/app/a/[id]/page.tsx`
- `api/main.py`
- `worker/pipeline.py`
- `tasks/m4-03-analysis-language-toggle.md`
- `tasks/README.md`

**Forbidden:** Modifying `worker/extract/`, `worker/media/render.py` internal audio logic, or core scoring formulas in `worker/engine/report.py`.

---

## 4. Acceptance Criteria
- [ ] **Frontend Language Toggle (`web/app/page.tsx`):**
  - Displays a clean, keyboard-accessible language selector switch/toggle (e.g. `🇷🇴 Română` / `🇬🇧 English`) near the URL submission bar.
  - Defaults to `Română` (`ro`) to preserve existing default demo behavior.
  - Submits `{ url: trimmed, lang: selectedLang }` to `POST /api/analyses`.
- [ ] **API Endpoint (`api/main.py`):**
  - Updates `AnalysisRequest` schema to support `lang: Literal["ro", "en"] = "ro"`.
  - Rejects invalid language codes with HTTP 422 Unprocessable Entity.
  - Passes `--lang <lang>` (or environment/argument) when spawning `worker.pipeline`.
  - Saves `"lang": lang` in `status.json` and returns it in `GET /api/analyses/{id}`.
- [ ] **Pipeline Orchestrator (`worker/pipeline.py`):**
  - Accepts `--lang` CLI argument (or optional 3rd positional argument), defaulting to `"ro"`.
  - Forwards `lang` into `build_events(nodes, lang=lang)` and `render_clip(..., lang=lang)`.
  - Writes `"lang": lang` into `report.json`.
- [ ] **Report View (`web/app/a/[id]/page.tsx`):**
  - Shows a language badge in the report summary header next to the URL (e.g. `🇷🇴 Română` or `🇬🇧 English`).
- [ ] **Build & Quality:**
  - `cd web && npm run build` completes with zero TypeScript errors or warnings.
  - API handles requests missing the `lang` field gracefully by defaulting to `"ro"`.

---

## 5. Validation & Test Commands
```bash
# 1. Verify Next.js build
cd web
npm run build
cd ..

# 2. Test FastAPI analysis creation with English lang
source .venv/bin/activate
python -c "
from fastapi.testclient import TestClient
from api.main import app
client = TestClient(app)
# Default language test
r1 = client.post('/api/analyses', json={'url': 'http://localhost:8080/bad-checkout.html'})
assert r1.status_code == 202
# Explicit English language test
r2 = client.post('/api/analyses', json={'url': 'http://localhost:8080/bad-checkout.html', 'lang': 'en'})
assert r2.status_code == 202
# Invalid language rejected
r3 = client.post('/api/analyses', json={'url': 'http://localhost:8080/bad-checkout.html', 'lang': 'fr'})
assert r3.status_code == 422
print('API validation PASSED')
"

# 3. Test CLI pipeline with --lang flag
python -m worker.pipeline dev_en http://localhost:8080/bad-checkout.html --lang en
```

---

## 6. Dependencies
- M2-03 (English speech and recommendations)
- M4-02 (Frontend dashboard clean state)

---

## 7. Out of Scope
- Full multi-language translation of the static marketing landing page copy (stays in Romanian).
- Non-English / non-Romanian languages (e.g. French, German).

---

## 8. Execution Log (Updated by Assignee)
- **2026-11-06:** Implemented API request validation, subprocess `--lang`, status propagation, pipeline language handling, report language badge. Website selector and analysis language radio are inherited from M4-04 (#38).
- **Validation pending:** Merge M2-03 (#32) to supply language-aware `build_events`, `run_audit`, `render_clip`; run integrated tests and frontend build before Done.
- **Claimed by:** Unassigned
