# Task: [M3-02] Fix timeline.json Schema Mismatch and Piper Path Resolution

- **Task ID:** `M3-02`
- **GitHub Issue:** #12
- **Track:** `M3` (TTS, recording, and media rendering)
- **Type:** `Bug`
- **Priority:** `P0 - blocks delivery`
- **Status:** `Ready`
- **Assignee:** Unassigned
- **Branch:** `m3-fix-timeline-schema`
- **Created Date:** 2026-11-06

---

## 1. Goal
Fix the breaking contract mismatch in `worker/media/render.py` where `timeline.json` is generated with an invalid top-level schema (`{"timeline": [...]}` instead of `{"duration": ..., "clip": ..., "entries": [...]}`) causing downstream pipeline crashes (`KeyError: 'duration'`), and resolve the `piper` executable path robustly for virtual environments.

---

## 2. Context
During midpoint integration testing across merged milestone tracks (M1–M4), running `worker.pipeline` without stubs triggered a fatal error in `worker/engine/report.py`:
```python
File "worker/engine/report.py", line 43, in build_report
    "clip_url": f"/media/{analysis_id}/clip.mp4", "duration": timeline["duration"],
                                                              ~~~~~~~~^^^^^^^^^^^^
KeyError: 'duration'
```

### Root Causes
1. **Schema Mismatch in `worker/media/render.py`:**
   Lines 147–152 and 215–218 output:
   ```json
   {
     "timeline": [
       {
         "node_id": "n1",
         "event_id": 0,
         "start_sec": 3.0,
         "end_sec": 3.7
       }
     ]
   }
   ```
   However, the canonical contract (`doc/1-foundation/data-contracts.md` and `contracts/samples/timeline.json`) specifies:
   ```json
   {
     "duration": 30.0,
     "clip": "clip.mp4",
     "entries": [
       {
         "seq": 0,
         "node_id": "n1",
         "text": "PasUșor",
         "start": 3.0,
         "end": 3.7
       }
     ]
   }
   ```
   Because `duration` is missing, `report.py` crashes. Because `entries` is missing, `report.py` cannot map issue timestamps (`starts.get(node_id)`).

2. **`piper` CLI Binary Path Resolution:**
   Line 57 executes `subprocess.run(["piper", ...])` directly. When python is launched from `.venv/bin/python` without `.venv/bin` in the shell `$PATH` (e.g. background subprocesses spawned by `api/main.py`), `shutil.which("piper")` is `None` and raises `RuntimeError: Missing executable: piper`.

---

## 3. Scope (Strict Boundary)
The agent is **only** permitted to modify files in:
- `worker/media/render.py`
- `worker/media/test_render.py` (optional new unit test)

**Forbidden:** Modifying `worker/extract/`, `worker/engine/`, `api/`, `web/`, or core contracts.

---

## 4. Acceptance Criteria
- [ ] `render_clip()` returns and writes a dictionary matching `contracts/samples/timeline.json`:
  - `"duration"`: float (total audio/clip duration in seconds, rounded to 3 decimal places)
  - `"clip"`: string `"clip.mp4"`
  - `"entries"`: list of event objects
- [ ] Each entry in `"entries"` contains:
  - `"seq"`: integer sequence index (0, 1, 2, ...)
  - `"node_id"`: string node identifier (`"n0"`, `"n1"`, ...) or `null`
  - `"text"`: string spoken announcement text
  - `"start"`: float start offset in seconds
  - `"end"`: float end offset in seconds
- [ ] Piper executable is resolved via `shutil.which("piper") or str(Path(sys.executable).parent / "piper")` (or `PiperVoice` SDK) so execution never fails inside virtual environments.
- [ ] `render_clip()` output can be passed directly to `build_report()` in `worker/engine/report.py` without raising `KeyError` or missing timestamps.

---

## 5. Validation & Test Commands
```bash
# 1. Test render_clip against samples directly
.venv/bin/python -c "
from worker.common import SAMPLES, read_json
from worker.media.render import render_clip
from worker.engine.report import build_report
from pathlib import Path

nodes = read_json(SAMPLES / 'nodes.json')
events = read_json(SAMPLES / 'events.json')
issues = read_json(SAMPLES / 'issues.json')

# Test timeline schema
tl = render_clip('http://localhost:8080/bad-checkout.html', nodes, events, Path('data/test-m3-fix'))
assert 'duration' in tl, 'duration missing'
assert 'clip' in tl, 'clip missing'
assert 'entries' in tl, 'entries missing'
assert isinstance(tl['entries'], list), 'entries is not a list'
assert tl['entries'][0].get('text'), 'text missing from entry'
assert 'start' in tl['entries'][0], 'start missing from entry'

# Test downstream report assembler integration
rep = build_report('test-m3', 'http://localhost:8080/bad-checkout.html', nodes, issues, tl)
assert rep['duration'] == tl['duration']
print('SUCCESS: timeline.json schema and build_report integration verified!')
"

# 2. Run pipeline with extract and audit stubbed
CP_STUBS=extract,audit .venv/bin/python -m worker.pipeline test-m3-pipe http://localhost:8080/bad-checkout.html
```

---

## 6. Dependencies
- `contracts/samples/timeline.json`
- `contracts/samples/events.json`
- `contracts/samples/nodes.json`

---

## 7. Out of Scope
- Modifying speech rules in `worker/engine/events.py`.
- Changing video styling or CSS highlight selectors.

---

## 8. Execution Log
- **2026-11-06:** Task created as Ready based on midpoint integration findings.
