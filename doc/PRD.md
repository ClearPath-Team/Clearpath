# ClearPath: Implementation PRD (MVP)

> Four The Win Team · Astra Hack, November 6–7, 2026  
> **Top-Most Official Baseline Document:** This document, alongside `doc/ClearPath-PRD.pdf` and `doc/SETUP.md`, serves as the top-most official documentation and foundational baseline for the ClearPath project.

## Document Structure

The document is divided into 3 chronological parts:

| Part | When | Who | Outcome |
|---|---|---|---|
| **Part 1: Foundation** | Hour 1 | All 4 together | Repo, data contracts, shared files, test data |
| **Part 2: Parallel Tracks** | Hour 1 until integration | Independent tracks | 4 decoupled modules running on mock data |
| **Part 3: Integration & Delivery** | Midpoint checkpoint + last 4 hours | All 4 | End-to-end working application & live demo |

**Instructions for AI IDE Agents:**
1. Read **Part 1** completely. Data contracts cannot be altered without team consensus.
2. In **Part 2**, read only the section dedicated to your track. Touch only files in "Your Files".
3. **Part 3** applies when the team enters integration.
4. The local environment (dependencies, test site) is documented in `doc/setup/setup.md`.

---

# PART 1: FOUNDATION (Hour 1, All Together)

## 1.1 Product

ClearPath is a web application that demonstrates how a blind user navigates a website with a screen reader. A user enters a webpage URL. An agent launches the page in Chromium and traverses it like a screen reader: element-by-element, then via pure Tab key navigation. From this traversal, a narrated video is generated featuring the active element visually highlighted with synchronized spoken announcements. In parallel, an automated accessibility audit (axe-core) flags accessibility violations. Each violation is mapped to the exact second in the video where it occurs. The final result delivers the video, an organized list of issues, an accessibility score (0–100), and actionable recommendations.

**Input:** Public URL. **Output:** `clip.mp4` + `report.json`, displayed in an interactive dashboard.

### MVP Scope
- Single page analysis per run (no authentication on analyzed site).
- Video of at most ~90 seconds (maximum 40 announcements).
- Pure Tab traversal with keyboard trap detection.
- axe-core audit, numeric score, actionable recommendations.
- Interactive results dashboard with player, navigable issue list, and shareable link.

### Out of Scope
User accounts, saved history, multi-page user journeys, live comparisons with desktop NVDA, cloud storage, real-time LLM recommendations.

## 1.2 Architecture

```
 ┌──────────┐   POST /api/analyses   ┌──────────┐   enqueue / spawn   ┌──────────────────────────┐
 │  web     │ ─────────────────────► │  api     │ ──────────────────► │ python -m worker.pipeline│
 │ Next.js  │ ◄───── GET status ──── │ FastAPI  │                     │       {id} {url}         │
 └────┬─────┘                        └────┬─────┘                     └────────────┬─────────────┘
      │ GET /media/{id}/clip.mp4          │ reads status/report                    │
      └───────────────────────────────────┤                                        ▼
                                          └───────────────────────────────► data/{id}/
```

The pipeline runs a sequence of functions, receiving and returning Python dictionaries:
```python
nodes    = extract(url)                                      # Member 1
events   = build_events(nodes)                               # Member 2
issues   = run_audit(url, nodes)                             # Member 2
timeline = render_clip(url, nodes, events, out_dir)          # Member 3 (writes clip.mp4)
report   = build_report(analysis_id, url, nodes, issues, timeline)   # Member 2
```

Analysis state is persisted in `data/{id}/status.json`.

## 1.3 Repository Structure

```
clearpath/
├── CLAUDE.md, README.md
├── contracts/
│   ├── selector.js                 # Shared CSS selector generator (1.6)
│   └── samples/                    # Mock sample data for each contract
│       ├── nodes.json  events.json  issues.json  timeline.json  report.json
│       └── clip.mp4                # Short sample MP4 video
├── test-site/
│   └── bad-checkout.html           # Offline demo site with intentional flaws (Romanian)
├── assets/                         # axe.min.js, Piper voice models (downloaded, gitignored)
├── worker/
│   ├── common.py                   # Paths, JSON read/write, SELECTOR_JS
│   ├── extract/   extract.py   tab_walk.py          # Member 1
│   ├── engine/    events.py  audit.py  report.py  recommendations.py  # Member 2
│   ├── media/     tts.py  record.py  mix.py  render.py               # Member 3
│   └── pipeline.py                                              # Member 4
├── api/
│   └── main.py                                                  # Member 4
├── web/                                                         # Member 4 (Next.js)
└── data/                           # Generated job runs, gitignored
```

## 1.4 Data Contracts

Entities are linked via `node_id`. DOM association is established via `selector` generated by `contracts/selector.js`.

> **Source of Truth Notice:** While this PRD defines baseline requirements, [`doc/1-foundation/data-contracts.md`](1-foundation/data-contracts.md) serves as the authoritative, mathematically aligned specification for inter-module JSON contracts.

### nodes.json (Produced by Member 1)
```json
{
  "url": "http://localhost:8080/bad-checkout.html",
  "title": "Finalizează comanda",
  "viewport": { "width": 1280, "height": 720 },
  "nodes": [
    {
      "id": "n12",
      "order": 12,
      "role": "button",
      "name": "",
      "level": null,
      "states": { "required": false, "checked": null, "expanded": null, "disabled": false },
      "value": null,
      "list_size": null,
      "focusable": true,
      "parent": "n1",
      "selector": "#cart",
      "bbox": { "x": 1040, "y": 22, "w": 32, "h": 32 },
      "visible": true
    }
  ],
  "focus_order": [
    { "node_id": "n3", "selector": "html > body:nth-of-type(1) > header:nth-of-type(1) > nav:nth-of-type(1) > a:nth-of-type(1)" },
    { "node_id": "n12", "selector": "#cart" }
  ],
  "focus_trap": { "node_id": "n18", "selector": "#promo" }
}
```

Rules:
- `id` follows format `n{order}`. `order` is 0-indexed linear reading order without gaps.
- `role` is normalized: `heading`, `link`, `button`, `textbox`, `checkbox`, `radio`, `combobox`, `image`, `list`, `banner`, `navigation`, `main`, `contentinfo`, `region`, `form`, `search`, `complementary`, `text`.
- `bbox` in CSS document coordinates or `null`.
- `focus_trap` is `null` or `{ "node_id": "n18" | null, "selector": "..." }`.

### events.json (Produced by Member 2)
```json
{
  "lang": "ro",
  "events": [
    { "seq": 0, "node_id": null,  "text": "Pagina Finalizează comanda" },
    { "seq": 1, "node_id": "n13", "text": "Titlu nivel 1, Finalizează comanda" },
    { "seq": 2, "node_id": "n12", "text": "Buton" }
  ]
}
```

### issues.json (Produced by Member 2)
```json
[
  {
    "id": "i1",
    "rule": "button-name",
    "severity": "critical",
    "node_id": "n12",
    "selector": "#cart",
    "title": "Butonul nu are nume accesibil",
    "recommendation": "Adaugă un text vizibil sau un atribut aria-label care descrie acțiunea butonului.",
    "help_url": "https://dequeuniversity.com/rules/axe/4.10/button-name"
  }
]
```

### timeline.json (Produced by Member 3)
```json
{
  "duration": 84.2,
  "clip": "clip.mp4",
  "entries": [
    { "seq": 0, "node_id": null,  "text": "Pagina Finalizează comanda", "start": 1.0,  "end": 2.6 },
    { "seq": 2, "node_id": "n12", "text": "Buton",                      "start": 9.8,  "end": 10.4 }
  ]
}
```

### report.json (Produced by Member 2)
```json
{
  "id": "a7f3c2d1",
  "url": "http://localhost:8080/bad-checkout.html",
  "title": "Finalizează comanda",
  "score": 28,
  "counts": { "critical": 4, "serious": 4, "moderate": 1, "minor": 0 },
  "clip_url": "/media/a7f3c2d1/clip.mp4",
  "duration": 84.2,
  "focus_trap": true,
  "issues": [ { "id": "i1", "timestamp": 9.8 } ]
}
```

### Scoring Formula
```
score = 100
for each axe rule: penalty = min(20, sum of weights of violations)
    weights: critical = 10, serious = 6, moderate = 3, minor = 1
score -= sum of penalties
if keyboard-trap exists: score -= 15
score = max(0, round(score))
```

---

# PART 2: PARALLEL TRACKS

## 2.1 Member 1: Agent & Tree Extraction
- Produce `nodes.json` from URL via CDP `Accessibility.getFullAXTree`.
- Implement DFS traversal, role normalization, and atomic role child-suppression.
- Implement sequential Tab traversal in `tab_walk.py` and detect `focus_trap`.
- CLI test: `python -m worker.extract.extract <url> [out.json]`.

## 2.2 Member 2: Announcement Engine, Audit & Reporting
- Generate speech announcements (`events.py`) mapped to screen reader speech patterns.
- Run `axe-core 4.10` via browser injection (`audit.py`), deduplicating by `(rule, selector)`.
- Assemble final `report.json` with calculated score and timeline mappings (`report.py`).
- CLI test: `python -m worker.engine.events nodes.json`, `python -m worker.engine.audit <url> nodes.json`.

## 2.3 Member 3: Voice Synthesis & Video Rendering
- Synthesize audio chunks with Piper TTS (`tts.py`).
- Record Playwright session with highlight overlay `#cp-hl` and captions `#cp-cap` (`record.py`).
- Mix audio and video into `clip.mp4` using ffmpeg (`mix.py`).
- CLI test: `python -m worker.media.render <url> nodes.json events.json <out_dir>`.

## 2.4 Member 4: API, Web UI, Orchestration & Demo
- Build `worker/pipeline.py` with mock stub support (`CP_STUBS`).
- Build FastAPI backend in `api/main.py`.
- Build Next.js 14 frontend in `web/` with interactive video seek.
- Prepare offline demo assets in `demo/`.

---

# PART 3: INTEGRATION & DELIVERY

- Midpoint checkpoint: merge to `main`, run `CP_STUBS=render,report` on `bad-checkout.html`.
- Progressively remove stubs (1 through 5).
- Verify end-to-end acceptance tests.
- Offline demo presentation execution.
