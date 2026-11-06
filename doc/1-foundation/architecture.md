# Architecture

## Components

```
 ┌──────────┐  POST /api/analyses   ┌──────────┐  spawns subprocess   ┌──────────────────────────┐
 │  web     │ ────────────────────► │  api     │ ───────────────────► │ python -m worker.pipeline│
 │ Next.js  │ ◄──── GET status ──── │ FastAPI  │                      │       {id} {url}         │
 │  :3000   │                       │  :8000   │                      └────────────┬─────────────┘
 └────┬─────┘                       └────┬─────┘                                   │ writes
      │ GET /media/{id}/clip.mp4         │ reads status.json / report.json         ▼
      └──────────────────────────────────┴─────────────────────────────────► data/{id}/
```

- **web** (Next.js): URL submission form, live progress view, and interactive results dashboard.
- **api** (FastAPI): Validates target URLs, creates analyses, spawns the pipeline as a **separate process** (`subprocess.Popen`), and serves status, report, and media assets.
- **pipeline** (`worker/pipeline.py`): Sequentially executes the 5 pipeline stages and outputs all artifacts into `data/{id}/`.
- **No queues or external databases.** Analysis state resides in `data/{id}/status.json`. Each analysis runs as an independent OS process, writing detailed logs to `data/{id}/pipeline.log`.

## Pipeline Flow

Each stage receives and returns Python dictionaries. `pipeline.py` persists results as JSON files.

```python
nodes    = extract(url)                                            # M1  worker/extract/extract.py
events   = build_events(nodes)                                     # M2  worker/engine/events.py
issues   = run_audit(url, nodes)                                   # M2  worker/engine/audit.py
timeline = render_clip(url, nodes, events, out_dir)                # M3  worker/media/render.py (writes clip.mp4)
report   = build_report(analysis_id, url, nodes, issues, timeline) # M2  worker/engine/report.py
```

| Status | Updated by | When |
|---|---|---|
| `queued` | API | Analysis job created |
| `extracting` | pipeline | Before calling `extract` |
| `analyzing` | pipeline | Before calling `build_events` + `run_audit` |
| `rendering` | pipeline | Before calling `render_clip` |
| `done` | pipeline | After writing `report.json` |
| `failed` | pipeline | On unhandled exception, populating `error` |

## Codebase Organization

```
contracts/
├── selector.js                     # Canonical CSS selector function (data-contracts.md)
└── samples/                        # Mock test data: one sample for each contract + clip.mp4
test-site/bad-checkout.html         # Offline demo test site with intentional flaws (Romanian)
worker/
├── common.py                       # Paths, .env configuration, SELECTOR_JS, read_json/write_json
├── extract/   extract.py  tab_walk.py                                         # M1
├── engine/    events.py  audit.py  report.py  recommendations.py              # M2
├── media/     tts.py  record.py  mix.py  render.py                            # M3
└── pipeline.py                                                                # M4
api/main.py                                                                    # M4
web/                                                                           # M4
scripts/       check_env.py  dev.py  fetch_assets.py
data/{id}/     status.json  nodes.json  events.json  issues.json  timeline.json  report.json  clip.mp4  pipeline.log
```

## Technology Stack

| Component | Technology | Role |
|---|---|---|
| Backend Language | Python 3.11 / 3.12 | Unified runtime for both API and worker |
| API Framework | FastAPI + uvicorn | REST endpoints, static media streaming |
| Process Execution | `subprocess.Popen` | Independent analysis processes without external queues |
| Automated Browser | Playwright (Python) + Chromium | Headless browser automation, Tab traversal, screen recording |
| Accessibility Tree | Chrome DevTools Protocol | `Accessibility.getFullAXTree` |
| Accessibility Audit | axe-core 4.10 | Injected directly into the evaluated DOM |
| Speech Synthesis | Piper (`ro_RO-mihai-medium`) | Local, CPU-based offline TTS without API keys |
| Media Processing | ffmpeg / ffprobe | Audio-video overlay mixing, H.264/AAC MP4 export |
| Web Interface | Next.js 14 + Tailwind CSS | Form submission, animated progress, interactive report |
| Storage | Local filesystem, `data/{id}/` | Artifacts and logs per analysis |
