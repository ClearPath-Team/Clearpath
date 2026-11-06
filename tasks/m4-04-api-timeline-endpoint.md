# Task: [M4-04] API Endpoint for Analysis Timeline (transcript data)

- **Task ID:** `M4-04`
- **GitHub Issue:** #33
- **Track:** `M4` (API, web, and demo)
- **Type:** `Feature`
- **Priority:** `P1 - current milestone`
- **Status:** `Ready`
- **Assignee:** Unassigned
- **Branch:** `m4-api-timeline`
- **Created Date:** 2026-11-06

---

## 1. Goal
Serve a finished analysis's `timeline.json` through the API so the redesigned report page (M4-07) can show the "What the user hears" transcript next to the video.

---

## 2. Context
The approved redesign (M4-03, #28, design: https://claude.ai/artifact/FSpXpauSM4zuds3Zs2VHGk) shows every screen-reader announcement with its timestamp and marks the ones linked to an issue. That data already exists in `data/{id}/timeline.json` (schema in `doc/1-foundation/data-contracts.md`, produced by M3's `render_clip`), but `api/main.py` only exposes `/api/health`, `POST /api/analyses`, `GET /api/analyses/{id}` (status + `report.json`) and `/media/{id}/clip.mp4`. `report.json` does not contain the transcript entries.

---

## 3. Scope (Strict Boundary)
The assignee is permitted to modify or create:
- `api/main.py`
- `api/test_main.py` (new or updated tests)
- `doc/2-tracks/m4-app.md` (document the endpoint)
- `tasks/m4-04-api-timeline-endpoint.md`
- `tasks/README.md`

**Forbidden:** Changing the `timeline.json` schema, `doc/1-foundation/data-contracts.md`, `worker/`, or `web/`.

---

## 4. Acceptance Criteria
- [ ] `GET /api/analyses/{id}/timeline` returns `data/{id}/timeline.json` unchanged (`duration`, `clip`, `entries[]` with `seq`, `node_id`, `text`, `start`, `end`) once the analysis status is `done`.
- [ ] Returns `404` with a clear `detail` when the analysis does not exist, and `409` (or `404`) with a clear `detail` while the analysis is not `done`.
- [ ] `analysis_id` is validated so it cannot escape `DATA_DIR` (no path traversal, e.g. `..%2F`), matching how the other endpoints resolve `DATA_DIR / analysis_id`.
- [ ] Works with stubbed (`CP_STUBS=all`) and live pipeline runs.
- [ ] Tests cover: done analysis, unknown id, analysis still running, path traversal attempt.

---

## 5. Validation & Test Commands
```bash
.venv/bin/python -m unittest api.test_main -v

# Manual check with the stubbed pipeline
CP_STUBS=all python scripts/dev.py &
ID=$(curl -s -X POST localhost:8000/api/analyses -H 'Content-Type: application/json' \
      -d '{"url":"http://localhost:8080/bad-checkout.html"}' | python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])')
sleep 5 && curl -s localhost:8000/api/analyses/$ID/timeline | python3 -m json.tool | head
```

---

## 6. Dependencies
- None. Blocks `M4-07`.

---

## 7. Out of Scope
- Changing what the pipeline writes into `timeline.json`.
- Any frontend change (done in `M4-07`).

---

## 8. Execution Log (Updated by Assignee)
- **2026-11-06:** Task created as Ready (split from M4-03).
