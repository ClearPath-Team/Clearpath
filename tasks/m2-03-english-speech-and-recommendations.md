# Task: [M2-03] English Screen Reader Speech Rules, Recommendations & Voice Synthesis

- **Task ID:** `M2-03`
- **GitHub Issue:** #32
- **Track:** `M2` (Announcement engine, audit, and reporting)
- **Type:** `Feature`
- **Priority:** `P1 - current milestone`
- **Status:** `In review`
- **Assignee:** `@andreiBirsanIoan`
- **Branch:** `m2-english-speech-rules`
- **Created Date:** 2026-11-06

---

## 1. Goal
Implement bilingual English screen reader announcement rules modeled after NVDA English conventions, English WCAG recommendation templates, and English TTS voice configuration in the backend engine, allowing the pipeline to analyze pages and generate narrated demonstration clips in English when requested.

---

## 2. Context
Currently:
- `worker/engine/events.py` hardcodes Romanian screen reader announcements (`titlu nivel 1`, `buton`, `casetă de editare, necompletat`, `reper antet`).
- `worker/engine/recommendations.py` provides Romanian translations for axe-core violation rules.
- `worker/media/render.py` defaults to Romanian Piper voice (`ro_RO-mihai-medium.onnx`) and Romanian diacritic normalization.

When auditing English websites or presenting to international audiences, ClearPath should support generating screen reader announcements and issue recommendations in English, following official NVDA English screen reader speech patterns (e.g. `Submit, button`, `Main navigation, landmark`, `Search, edit box`).

---

## 3. Scope (Strict Boundary)
The agent is permitted to modify only the following files:
- `worker/engine/events.py`
- `worker/engine/audit.py`
- `worker/engine/recommendations.py`
- `worker/media/render.py`
- `scripts/fetch_assets.py`
- `worker/engine/test_events.py`
- `worker/engine/test_audit.py`
- `worker/media/test_render.py`
- `tasks/m2-03-english-speech-and-recommendations.md`
- `tasks/README.md`

**Forbidden:** Modifying `worker/extract/`, `api/`, `web/`, or core schemas in `doc/1-foundation/data-contracts.md`.

---

## 4. Acceptance Criteria
- [x] `worker/engine/events.py`:
  - `build_events(nodes, lang="ro")` accepts an optional `lang` parameter (`"ro"` or `"en"`), defaulting to `"ro"`.
  - When `lang == "en"`:
    - `heading` with `level=N` ➔ `heading level N`
    - `button` ➔ `button`
    - `link` ➔ `link`
    - `textbox` / `input` ➔ `edit, blank` or `edit, contains {value}`
    - `checkbox` ➔ `check box, checked` or `check box, not checked`
    - `radio` ➔ `radio button, selected` or `radio button, not selected`
    - `combobox` ➔ `combo box`
    - `image` without name ➔ `graphic unlabelled` (or `graphic {name}`)
    - Landmarks: `banner` ➔ `banner landmark`, `navigation` ➔ `navigation landmark`, `main` ➔ `main landmark`, etc.
    - State flags: `required` ➔ `required`, `disabled` ➔ `unavailable`
  - When `lang == "ro"` (or omitted): Produces identical Romanian announcements matching the baseline tests.
  - Result JSON retains `"lang": "en"` or `"lang": "ro"`.
- [x] `worker/engine/audit.py` & `worker/engine/recommendations.py`:
  - `run_audit(url, nodes, lang="ro")` accepts `lang`.
  - When `lang == "en"`, uses axe-core's native English `help` and `description` strings, or curated English recommendation strings.
  - When `lang == "ro"`, continues to use the curated Romanian `RECOMMENDATIONS` table.
- [x] `worker/media/render.py`:
  - Accepts `lang` parameter.
  - When `lang == "en"`:
    - If `TTS_ENGINE=edge-tts`, defaults voice to `en-US-ChristopherNeural` or `en-US-AriaNeural`.
    - If `TTS_ENGINE=piper`, resolves an English voice model (e.g. `assets/voices/en_US-lessac-medium.onnx` or path configured via `PIPER_MODEL_EN`).
- [x] `scripts/fetch_assets.py`:
  - Adds optional `--lang` or downloads the English Piper voice model (`en_US-lessac-medium`) if requested.
- [ ] **Backward Compatibility & Regression:**
  - All 63 existing unit tests pass without errors (`python -m unittest discover -s worker`).
  - New unit tests added in `worker/engine/test_events.py` verifying English translations for all supported roles and states.

---

## 5. Validation & Test Commands
```bash
# 1. Run all worker unit tests including new English test cases
source .venv/bin/activate
python -m unittest discover -s worker -v

# 2. Test English speech generation via CLI
python -m worker.engine.events contracts/samples/nodes.json --lang en

# 3. Test backward compatibility: Romanian speech generation remains default
python -m worker.engine.events contracts/samples/nodes.json
```

---

## 6. Dependencies
- Merged M2-01 and M2-02 in `main`.
- `contracts/samples/nodes.json`

---

## 7. Out of Scope
- Frontend UI language selector widget (handled in M4-03).
- Modifying DOM tree extraction in `worker/extract/` (language-agnostic).

---

## 8. Execution Log (Updated by Assignee)
- **2026-11-06:** Added bilingual announcement roles, English axe-core remediation support, language-dependent Piper/edge TTS voices, optional English model asset download, and focused regression tests.
- **Validation pending:** Full worker test suite and real English Piper render must be run on a machine with installed voice/model and Playwright. Do not mark Done before acceptance.
- **Claimed by:** @andreiBirsanIoan

- **2026-11-06 validation:** Downloaded en_US-lessac-medium and ran the real five-stage English pipeline over a local HTTP fixture with four announcements and zero stubs. MP4 duration: 10.745 seconds; ffprobe confirmed audio and video streams. Added a durable real English Piper render regression using an HTTP fixture. All 26 focused engine/voice/render tests passed. Full worker discovery was also executed: 86 tests, 1 failure, 8 errors, 1 skip. Eight errors involve file:// fixtures rejected by managed Chromium policy; the live audit test also missed expected contrast findings in this environment. Full-suite acceptance remains pending; no blanket all-tests-pass claim.
