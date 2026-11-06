# Track M4: API, Web UI, Pipeline Orchestration & Demo

## Objective
Build the user-facing application: URL submission form, live job progress tracking, and the interactive results dashboard. You also orchestrate the full pipeline stages and coordinate offline demo preparation.

## Your Files
`worker/pipeline.py`, `api/main.py`, `web/*`, `contracts/samples/clip.mp4`, `scripts/dev.py`, `demo/`

Build everything with `CP_STUBS=all` initially so you can iterate rapidly without waiting on other modules.

## A. Pipeline Orchestrator (`worker/pipeline.py`)
```python
def run_pipeline(analysis_id: str, url: str) -> None: ...

if __name__ == "__main__":          # python -m worker.pipeline <id> <url>
    run_pipeline(sys.argv[1], sys.argv[2])
```
1. **Status Tracking:** Update `data/{id}/status.json` before each stage (`extracting` → `analyzing` → `rendering` → `done`). On exception, write `failed`, set `error` message, log the traceback, and exit with code 1.
2. **Mock Stubs:** Inspect `CP_STUBS` (`all` or comma-separated list: `extract,events,audit,render,report`). For any active stub stage, load the corresponding file from `contracts/samples/` instead of executing real functions. For `render`, also copy `samples/clip.mp4` into `data/{id}/`. Import real worker modules **inside** the function bodies so stubs run smoothly even before real modules are authored.
3. **Persist Intermediate Artifacts:** Save results for each stage into `data/{id}/`.

## B. Backend API (`api/main.py`)
Starts from the repository root: `python -m uvicorn api.main:app --reload --port 8000`. Can import `worker.common` for `DATA_DIR`, `ROOT`, and JSON helpers.

| Method | Path | Description |
|---|---|---|
| POST | `/api/analyses` | Body `{ "url": "..." }`. Validates URL, generates `id = uuid4().hex[:8]`, writes `status.json` with `queued`, spawns pipeline process, returns `202 { "id": "..." }`. |
| GET | `/api/analyses/{id}` | Returns `{ id, url, status, error, report }`. `report` is `null` until `done`. Returns 404 if not found. |
| GET | `/api/analyses/{id}/timeline` | Returns `data/{id}/timeline.json` unchanged (`duration`, `clip`, `entries[]`) for the report transcript. 404 if the analysis or its timeline does not exist, 409 while it is not `done`. |

All `{id}` path parameters must match `[A-Za-z0-9_-]{1,64}`; anything else returns 404 so a request can never resolve outside `DATA_DIR`.
| GET | `/media/{id}/clip.mp4` | Serves media files via `app.mount("/media", StaticFiles(directory=DATA_DIR))`. |
| GET | `/api/health` | Health check: `{ "ok": true }`. |

- **Spawning the Pipeline:**
  ```python
  log = open(DATA_DIR / id / "pipeline.log", "w")
  subprocess.Popen([sys.executable, "-m", "worker.pipeline", id, url],
                   cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
  ```
  Never wait synchronously for the process. State is polled via `status.json`.
- **URL Validation:**
  - Enforce `http` and `https` schemes only.
  - Resolve DNS host and reject private/loopback IP addresses, except those explicitly allowed in `ALLOWED_HOSTS` (`.env`).
  - Perform `httpx.get(url, timeout=10, follow_redirects=True)`: on status ≥ 400 or network failure, return `422 { "detail": "Pagina nu poate fi accesată" }`.
- **Video Seeking (Byte Range Requests):**
  Verify range request handling with:
  ```bash
  curl -s -o /dev/null -w "%{http_code}" -H "Range: bytes=0-100" http://localhost:8000/media/<id>/clip.mp4
  ```
  Must return `206` (Starlette 0.41 supports `Range`). If `200` is returned, implement a custom range-streaming endpoint.

## C. Web Interface (`web/`, Next.js 14 App Router + Tailwind)
API endpoint is configured via `process.env.NEXT_PUBLIC_API_URL`.

1. **`/` (Home):** Product title, elevator pitch, target URL input field, and "Analizează" (Analyze) button. On submit, issue `POST`, then redirect to `/a/{id}`. Display 422 errors below the input.
2. **`/a/[id]` (Analysis View):** Polls `GET /api/analyses/{id}` every 2 seconds until status is `done` or `failed`.
   - **In Progress:** 4 animated visual milestones (Preparation, Page Extraction, Analysis, Video Generation).
   - **`failed`:** Friendly error notice + "Încearcă din nou" (Retry) action.
   - **`done`:** Comprehensive results view:
     - **Header:** Target URL, overall score displayed in a colored circular badge (≥ 80 green, 50–79 orange, < 50 red), and issue count by severity.
     - **Left Column:** `<video controls>` element with source set to `API_URL + clip_url`.
     - **Right Column:** Filterable list of accessibility issues by severity. Each issue displays severity badge, rule title, and timestamp button (`0:42`) or "Nu apare în clip" (Not in clip) tag.
       - Clicking timestamp: `video.currentTime = timestamp; video.play()`.
       - Clicking issue row: expands recommendation text, CSS selector, and "Detalii" link (`help_url`).
     - During playback, automatically highlight the issue whose `timestamp` is closest to (and ≤) the current `currentTime`.
     - "Copiază linkul" (Copy Link) button copies `window.location.href`.
3. **Self-Accessibility:** As an accessibility tool, our own UI must be accessible: visible focus outlines, labeled inputs, semantic elements, and `<html lang="ro">`.

## D. Offline Demo Coordination
Follow the protocol in `doc/3-integration/demo.md`.

## Acceptance Criteria
- [ ] With `CP_STUBS=all`, the entire user journey works end-to-end: submit → progress → results dashboard → click issue → video seeks to timestamp.
- [ ] Invalid URLs return clear UI validation errors without crashing.
- [ ] Any valid `report.json` displays gracefully (including zero issues or issues with `timestamp: null`).
- [ ] Consecutive analyses execute independently in their own isolated `data/{id}` folders.
