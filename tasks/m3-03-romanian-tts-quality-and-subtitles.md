# Task: [M3-03] Enhance Romanian Voice Synthesis Quality and Subtitle Diacritics

- **Task ID:** `M3-03`
- **GitHub Issue:** #9
- **Track:** `M3` (TTS, recording, and media rendering)
- **Type:** `Feature`
- **Priority:** `P1 - current milestone`
- **Status:** `In progress`
- **Assignee:** `@andreiBirsanIoan`
- **Branch:** `feature/m3-romanian-tts`
- **Pull Request:** https://github.com/ClearPath-Team/Clearpath/pull/15
- **Created Date:** 2026-11-06

---

## 1. Goal
Finalize Romanian text-to-speech voice synthesis improvements in `worker/media/render.py` (resolving Issue #9 and PR #15), ensuring proper UTF-8 handling of Romanian diacritics (ă, â, î, ș, ț) in narration audio and video overlay subtitles, while maintaining Piper (`TTS_ENGINE=piper`) as the offline-first default and providing Edge-TTS (`TTS_ENGINE=edge-tts`) as an optional high-fidelity alternative.

---

## 2. Context
During media rendering testing:
1. Issue #9 noted that Romanian diacritics and screen reader pronunciation could be enhanced for clearer live presentation demonstrations.
2. PR #15 was opened by Andrei Bîrsan adding optional Edge-TTS voice support (`ro-RO-EmilNeural`).
3. Code review on PR #15 identified requirements:
   - Piper must remain the default engine (`TTS_ENGINE=piper`) to honor the 100% offline hackathon design rule (`doc/1-foundation/architecture.md`).
   - Edge-TTS must be strictly opt-in (`TTS_ENGINE=edge-tts`) with `edge-tts` pinned in `requirements.txt`.
   - Temporary binary files (such as `.mp3` tests) must not be checked into the repository root.
   - Video overlay subtitles and timeline synchronization must preserve Romanian diacritics without Mojibake encoding artifacts on both Linux and Windows.

---

## 3. Scope (Strict Boundary)
The assignee is permitted to modify or create:
- `worker/media/render.py`
- `worker/media/test_render.py`
- `requirements.txt`
- `.env.example`
- `tasks/m3-03-romanian-tts-quality-and-subtitles.md`
- `tasks/README.md`

**Forbidden:** Altering core contracts (`doc/1-foundation/data-contracts.md`), modifying `worker/extract/`, or changing `worker/engine/`.

---

## 4. Acceptance Criteria
- [x] Piper remains the default TTS engine (`TTS_ENGINE=piper` or unset) and synthesizes Romanian speech using `assets/ro_RO-mihai-medium.onnx` without requiring internet connectivity.
- [x] When `TTS_ENGINE=edge-tts` is configured, speech synthesis invokes `edge-tts` with voice `ro-RO-EmilNeural` and transcodes to standard PCM WAV audio compatible with FFmpeg concatenation.
- [x] Subtitles and spoken text preserve Romanian diacritics (ă, â, î, ș, ț) in UTF-8 without question marks or replacement characters.
- [x] Generated `clip.mp4` and `timeline.json` conform strictly to the canonical contract and pass `worker/media/test_render.py`.
- [ ] PR #15 is approved and merged into `main`, closing Issue #9.

---

## 5. Validation & Test Commands
```bash
# 1. Verify requirements installation
pip install -r requirements.txt

# 2. Run media test suite
.venv/bin/python -m unittest discover -s worker/media -p 'test_*.py'

# 3. Test Piper synthesis with diacritics
.venv/bin/python -c "
from worker.media.render import _synthesize
from pathlib import Path
out = Path('data/test-diacritics.wav')
_synthesize('Testăm diacriticele românești: ă, â, î, ș, ț.', out)
assert out.exists() and out.stat().st_size > 0
print('PIPER ROMANIAN DIACRITICS VALIDATED!')
out.unlink(missing_ok=True)
"
```

---

## 6. Dependencies
- Merged `M3-02` (PR #16)
- Piper model in `assets/`

---

## 7. Out of Scope
- Adding multi-lingual TTS engines beyond Romanian.
- Modifying `web/` video player controls.

---

## 8. Execution Log (Updated by Assignee)
- **2026-11-06:** Issue #9 opened on GitHub.
- **2026-11-06 14:31 UTC:** PR #15 opened from `feature/m3-romanian-tts` (Status -> In progress).
- **2026-11-06 15:13 UTC:** Updated PR #15 with commit 43036f1 adding optional Edge-TTS and removing test MP3 (Status -> In review).
- **2026-11-06 16:00 UTC:** Finalized PR #15 changes: unified virtualenv binary resolver for Piper and Edge-TTS, added Romanian diacritic normalization (NFC and comma-below), added intermediate MP3 cleanup and offline error handling, and added 10 new unit tests. Rebased onto main canonical timeline schema.
