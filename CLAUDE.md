# CLAUDE.md — Agent & Developer Guide

Complete project blueprint for AI coding agents and human contributors for ClearPath.
Read this file at the start of every session.

---

## 1. Project Overview

### What is ClearPath?
**ClearPath** is a web platform that visually and audibly demonstrates how a blind or visually impaired user experiences any public website using assistive technology (screen readers).

### What does it do?
1. **Automated Assistive Traversal:** Takes a public URL and navigates the target page in a Playwright headless Chromium instance (standard 1280×720 viewport).
2. **Accessibility Tree Extraction:** Queries the Chrome DevTools Protocol (`Accessibility.getFullAXTree`), performs depth-first search (DFS) traversal in natural reading order, normalizes ARIA roles, and identifies interactive elements.
3. **Sequential Tab Traversal & Trap Detection:** Simulates pure keyboard `Tab` navigation to reconstruct the browser focus order and detect keyboard traps (`focus_trap`).
4. **Speech Synthesis & Announcements:** Translates element roles, states, and accessible names into screen reader announcements (modeled after NVDA screen reader conventions), synthesized locally on CPU with Piper TTS (`ro_RO-mihai-medium.onnx`), with fallbacks to `espeak-ng` or macOS `say`.
5. **Screen Recording with Visual Highlights:** Records the live page traversal, rendering a synchronized high-contrast bounding box overlay (`#cp-hl`) around the active element alongside subtitles (`#cp-cap`).
6. **Automated axe-core Audit:** Injects `axe-core 4.10.2` to detect WCAG accessibility violations, maps violations to canonical CSS selectors and node IDs, associates actionable recommendations, and calculates an overall score (0–100).
7. **Synchronized Video Mixing:** Combines video footage with synthesized narration audio (`clip.mp4`) and maps each discovered issue to its exact second mark (`timeline.json`).
8. **Interactive Results Web UI:** A Next.js 14 frontend allows users to submit URLs, monitor the 4 pipeline stages in real time, and explore the final report: playing the synchronized narrated clip, filtering issues, and clicking timestamps to jump directly to the moment each problem appears.

**Input:** Public URL  
**Output:** `clip.mp4` (synchronized narrated video with visual focus box) + `report.json` (scored report with issue timeline)

> [!IMPORTANT]
> **Top-Most Official Baseline Documents:**  
> [`doc/ClearPath-PRD.pdf`](doc/ClearPath-PRD.pdf), [`doc/SETUP.md`](doc/SETUP.md), and [`doc/PRD.md`](doc/PRD.md) are the **top-most official documents and serve as the baseline** for the entire project. All architecture, data contracts, and implementation tracks anchor back to them.

---

## 2. Language & Localization Rule (Joint English + Romanian)

> [!IMPORTANT]
> **Joint English + Romanian Repository Policy:**
> - **English MUST be used everywhere across the repository by default:** All documentation, codebase, comments, docstrings, configuration files, git commit messages, architecture blueprints, and AI agent interactions must be in English.
> - **Romanian is reserved exclusively for the demo target website and related localization:** The offline test/demo site (`test-site/bad-checkout.html`) is deliberately authored in Romanian and **MUST remain in Romanian**. Consequently, the screen-reader speech engine rules (NVDA Romanian conventions), Piper Romanian voice model (`ro_RO-mihai-medium.onnx`), and localized user-facing recommendations in `worker/engine/recommendations.py` support Romanian for auditing Romanian web pages.

---

## 3. Repository Structure

```
Clearpath/
├── CLAUDE.md                   # Primary instructions for AI agents and developers (this file)
├── README.md                   # Public project documentation and setup guide
├── setup-prompt.md             # Automated setup prompt for colleagues to run via their AI assistant
├── requirements.txt            # Unified Python dependencies (Playwright, Piper, FastAPI, etc.)
├── .env.example                # Template environment variables (stubs, TTS engine, offset)
├── .gitignore                  # Git exclusions (data/, assets/, .venv/, web/node_modules)
│
├── contracts/                  # Shared data contracts between modules
│   ├── selector.js             # Canonical deterministic CSS selector generator (single source of truth)
│   └── samples/                # Mock/stub JSON contract samples (for parallel development)
│       ├── nodes.json          # Mock accessibility tree & focus order (Track M1)
│       ├── events.json         # Mock screen-reader announcements (Track M2)
│       ├── issues.json         # Mock axe violations + keyboard trap (Track M2)
│       ├── timeline.json       # Mock event timestamp mapping (Track M3)
│       ├── report.json         # Mock assembled report for frontend (Track M2)
│       └── clip.mp4            # Mock sample MP4 video for UI video player testing (Track M4)
│
├── test-site/                  # Offline test site with intentional accessibility flaws
│   └── bad-checkout.html       # Romanian checkout page: missing alt, missing label, bad contrast, trap
│
├── worker/                     # Backend processing engine (pipeline)
│   ├── common.py               # Shared configuration, paths, SELECTOR_JS, JSON helpers
│   ├── pipeline.py             # Pipeline orchestrator managing all 5 stages and stubs (Track M4)
│   ├── extract/                # Track M1: Tree extraction & Tab traversal
│   │   ├── extract.py          # CDP AX tree extraction, role normalization, bbox calculation
│   │   └── tab_walk.py         # Sequential Tab navigation & focus_trap detection
│   ├── engine/                 # Track M2: Narration rules, axe audit & report
│   │   ├── events.py           # Generation of screen-reader announcement texts from nodes.json
│   │   ├── audit.py            # In-browser axe-core 4.10 runner, selector-to-node_id mapping
│   │   ├── recommendations.py  # Romanian localized recommendation templates & titles
│   │   └── report.py           # Accessibility scoring formula (0–100) & report assembly
│   └── media/                  # Track M3: Voice synthesis, video recording & mixing
│       ├── tts.py              # Piper / espeak-ng / say text-to-speech synthesis
│       ├── record.py           # Playwright recording with highlight box & subtitle overlays
│       ├── mix.py              # voice.wav generation and ffmpeg A/V muxing (clip.mp4)
│       └── render.py           # Main render_clip() entrypoint -> clip.mp4 + timeline.json
│
├── api/                        # Track M4: FastAPI backend
│   └── main.py                 # REST API, URL validation, subprocess pipeline execution, /media
│
├── web/                        # Track M4: Next.js 14 frontend (App Router + Tailwind CSS)
│   └── (scaffolded via create-next-app according to doc/setup/setup.md)
│
├── scripts/                    # Helper automation and verification scripts
│   ├── check_env.py            # Environment diagnostic (Python, Chromium, ffmpeg, axe, Piper, Node)
│   ├── dev.py                  # Single-command runner for test-site (:8080), API (:8000), web (:3000)
│   └── fetch_assets.py         # Automated asset downloader for axe.min.js and Piper voice model
│
├── assets/                     # Downloaded local assets (gitignored): axe.min.js, voices/
├── .local/                     # Local developer scratchpad, personal notes, test dumps (gitignored)
├── data/                       # Analysis job runs: data/{id}/... (gitignored)
├── demo/                       # Pre-baked analysis results for offline presentations
└── doc/                        # Comprehensive documentation tree (see map below)
```

---

## 4. Execution Commands & Instructions

### Environment Check & Quick Start
```bash
# 1. Run complete environment verification
python scripts/check_env.py

# 2. Unified development server (starts test-site :8080, API :8000, Web :3000)
python scripts/dev.py

# 3. Direct pipeline execution via CLI (runs full analysis without Web UI)
python -m worker.pipeline dev1 http://localhost:8080/bad-checkout.html
```

### Isolated Module Execution
Each module can be executed and tested independently using samples in `contracts/samples/`:

```bash
# Track M1 — Tree extraction & Tab traversal
python -m worker.extract.extract http://localhost:8080/bad-checkout.html data/dev/nodes.json

# Track M2 — Screen reader announcement generation
python -m worker.engine.events contracts/samples/nodes.json

# Track M2 — axe-core audit
python -m worker.engine.audit http://localhost:8080/bad-checkout.html contracts/samples/nodes.json

# Track M2 — Report assembly and score calculation
python -m worker.engine.report contracts/samples/issues.json contracts/samples/timeline.json contracts/samples/nodes.json

# Track M3 — Video clip rendering and timeline generation
python -m worker.media.render http://localhost:8080/bad-checkout.html contracts/samples/nodes.json contracts/samples/events.json data/dev

# Track M4 — FastAPI standalone server (if not using dev.py)
python -m uvicorn api.main:app --reload --port 8000

# Track M4 — Next.js frontend standalone
cd web && npm run dev
```

### Stub Mode (`CP_STUBS`)
The `CP_STUBS` environment variable in `.env` enables running the pipeline with mock data from `contracts/samples/`:
- `CP_STUBS=all` : Replaces all pipeline steps with mock contract files (ideal for rapid frontend/API iteration).
- `CP_STUBS=render,report` : Runs real `extract`, `events`, and `audit`, while using stubs for `render` and `report`.
- `CP_STUBS=` : Runs all 5 pipeline stages on live code end-to-end.

---

## 5. Documentation Map (`doc/`)

All project documentation resides in `doc/`. Below is the complete directory inventory:

### 5.1. `doc/setup/` — Complete Unified Setup & Troubleshooting (Unnumbered, Up to Date)
* **`doc/setup/setup.md`**  
  *Complete unified setup guide.*  
  Merges the baseline official setup with the active local workflow: Part 1 covers the recommended local development environment without Docker (Python venv, Playwright Chromium, asset downloads with `fetch_assets.py`, Next.js setup, `scripts/dev.py`, and isolated module testing); Part 2 details the official containerized Docker Compose stack.
* **`doc/setup/troubleshooting.md`**  
  *Solutions catalog for common technical issues.*  
  Troubleshooting instructions for: Playwright system dependencies (`install-deps`), `piper-tts` compilation issues, configuring `TTS_ENGINE=espeak` or `say`, manual asset downloading from Hugging Face/npm, port conflicts (8080, 8000, 3000), CORS errors, HTTP `Range 206` video seek support, and cookie banner overlays.

### 5.2. `doc/1-foundation/` — Architecture & Data Contracts
* **`doc/1-foundation/product.md`**  
  *ClearPath Product Definition.*  
  Details product vision, user journey, MVP scope (single page, max 40 announcements / ~90s, Tab walk, axe audit, 0–100 score, synced video UI), and out-of-scope items (multi-page crawling, authentication, cloud storage, LLM recommendations).
* **`doc/1-foundation/architecture.md`**  
  *System Architecture & Data Flow.*  
  Architecture diagram (Web :3000 ↔ API :8000 ↔ Pipeline subprocess ↔ `data/{id}/`), sequential pipeline flow, job lifecycle statuses (`queued`, `extracting`, `analyzing`, `rendering`, `done`, `failed`), codebase organization, and technology stack.
* **`doc/1-foundation/data-contracts.md`**  
  ***Single Source of Truth for JSON Schemas.***  
  Defines schemas for: `nodes.json` (M1), `events.json` (M2), `issues.json` (M2), `timeline.json` (M3), `report.json` (M2 -> M4), and `status.json`. Contains the accessibility scoring formula (100 minus weighted penalty per axe rule, with -15 deduction for `keyboard-trap`), rules for canonical selectors, and mock sample guidelines.
* **`doc/1-foundation/kickoff-checklist.md`**  
  *First-hour synchronization checklist for the 4-person team.*  
  Checklist covering environment verification across all laptops, git branch setup, and creation of initial mock samples in `contracts/samples/` based on `bad-checkout.html`.

### 5.3. `doc/2-tracks/` — Parallel Tracks per Team Member
* **`doc/2-tracks/m1-extract.md`**  
  *Track M1: Agent & Tree Extraction.*  
  Technical specification for page loading (`open_page`), CDP AX tree extraction, role normalization, skipping `LabelText` nodes and atomic children, canonical CSS selector and bounding box (`bbox`) calculation, sequential Tab walking (`tab_walk.py`), `focus_trap` detection, cookie banner handling, and acceptance criteria.
* **`doc/2-tracks/m2-engine.md`**  
  *Track M2: Announcement Engine, Audit & Reporting.*  
  Specification for screen reader announcement text generation (`events.py`), static text condensation, in-browser `axe-core 4.10.2` execution (`audit.py`), violation mapping to `node_id`, localized recommendations (`recommendations.py`), scoring formula implementation, and `report.json` assembly.
* **`doc/2-tracks/m3-media.md`**  
  *Track M3: Voice Synthesis & Video Rendering.*  
  Specification for TTS speech synthesis (`tts.py`) with Piper/espeak/say, Playwright video recording with overlay bounding box (`#cp-hl`) and subtitles (`#cp-cap`), timing synchronization (`record.py`), `voice.wav` generation and ffmpeg H.264/AAC muxing with `VIDEO_OFFSET` calibration (`mix.py`), timeline generation, and temp file cleanup.
* **`doc/2-tracks/m4-app.md`**  
  *Track M4: API, Web UI, Pipeline Orchestration & Demo.*  
  Specification for `pipeline.py` (with `CP_STUBS` support), FastAPI endpoints in `api/main.py` (URL validation, SSRF protection for local private hosts, non-blocking subprocess spawning, static media serving with `Range 206` support), Next.js 14 UI (form, 4-stage progress, interactive video player with timestamp jumping), and offline demo preparation.

### 5.4. `doc/3-integration/` — Integration & Delivery
* **`doc/3-integration/integration.md`**  
  *Step-by-step integration procedure.*  
  Protocol for midpoint checkpoint merge to `main`, hybrid stub testing (`CP_STUBS=render,report`), progressive stub decoupling (steps 1 through 5), end-to-end acceptance testing, and common contract mismatch debugging.
* **`doc/3-integration/demo.md`**  
  *Presentation & live demo protocol.*  
  Offline demo data preparation in `demo/`, live demo scenario on `bad-checkout.html` and 2 chosen real websites, tagging the `demo` release, and fallback contingency plans (Plan B).
* **`doc/3-integration/definition-of-done.md`**  
  *MVP Acceptance Checklist.*  
  Full definition of done: standalone local startup without Docker, complete analysis under 3 minutes, synchronized video narration, clickable timestamps, valid score, and complete offline capability.

### 5.5. `doc/rules/` & `doc/decisions/` — Governance & Architecture History
* **`doc/rules/repo-rules.md`**  
  *Repository Collaboration & Code Rules.*  
  Git branch workflow (`m1-extract`, `m2-engine`, `m3-media`, `m4-app`), file ownership per member, contract change protocol, commit convention (`[mX] subject in english`), dependency management, and documentation placement rules.
* **`doc/decisions/decision-log.md`**  
  *Architecture Decision Record (ADR).*  
  Chronological record of key technical decisions (e.g., dropping Docker/Redis in favor of local Python subprocesses, selecting Piper TTS with voice Mihai, skipping `LabelText` nodes) and open integration tracking table.

### 5.6. Official Baseline Documents
* **`doc/ClearPath-PRD.pdf`**  
  *Original presentation pitch deck and foundational concept specification.*
* **`doc/PRD.md`**  
  *Top-most official baseline PRD.* Full implementation specification covering product definition, algorithms, data contracts, and parallel track roles.
* **`doc/SETUP.md`**  
  *Top-most official baseline setup specification.* Defines the foundational containerized architecture (Docker Compose, Redis, RQ, worker/api Dockerfiles), unified and up-to-date in `doc/setup/setup.md`.

### 5.7. Agentic Workflows & Setup Guides
* **`setup-prompt.md`**  
  *Universal Agentic Setup Prompt.* Prompt designed to be given to an AI coding assistant on any developer machine (WSL2, native Linux, macOS, Windows) to inspect the OS, install missing tools, run `check_env.py`, and generate `.local/local-config.md`.
* **`doc/setup/setup-workflow-projects.md`**  
  *Agentic AI Integration with GitHub Projects & Issues.* Complete reference manual for integrating coding agents with GitHub Projects (v2) and Issues. Recommends GitHub CLI (`gh`) over MCP.
* **`tasks/`**  
  *Authoritative Task Registry.* Markdown specifications for each milestone task (`tasks/mX-YY-slug.md`) containing Goal, Scope, Acceptance Criteria, and Validation commands. Includes universal teammate prompt [`tasks/team-task-prompt.md`](tasks/team-task-prompt.md).

---

## 6. Strict Guidelines for AI Coding Agents

1. **File Boundaries:** Only touch files assigned to your active track. Do not modify files owned by another track without explicit permission:
   - **M1:** `worker/extract/*`, `contracts/samples/nodes.json`, `scripts/check_env.py`, `scripts/fetch_assets.py`
   - **M2:** `worker/engine/*`, `contracts/samples/events.json`, `issues.json`, `report.json`
   - **M3:** `worker/media/*`, `contracts/samples/timeline.json`
   - **M4:** `worker/pipeline.py`, `api/*`, `web/*`, `scripts/dev.py`, `demo/*`, `contracts/samples/clip.mp4`
2. **Data Contract Immutability:** Never alter schemas in `doc/1-foundation/data-contracts.md`, sample files in `contracts/samples/`, or shared definitions in `worker/common.py` without team consensus and explicit instructions.
3. **Canonical CSS Selectors:** Any CSS selector generated in code **must** use the function in `contracts/selector.js` (available as `SELECTOR_JS` from `worker.common`). Never build custom selector generators.
4. **Language Rule:** English is used everywhere in the codebase and documentation. The demo site (`test-site/bad-checkout.html`) and associated screen-reader audio strings/recommendations target Romanian accessibility and stay in Romanian.
5. **Explicit Timeouts:** Always enforce explicit timeouts on browser operations (`goto`, `waitForSelector`), network calls (`httpx`), and subprocesses (`piper`, `ffmpeg`, `axe`). Never allow indefinite hanging.
6. **Documentation Placement:** Keep root clean (`CLAUDE.md` and `README.md` only). All new docs belong in the appropriate `doc/` subdirectory named in `kebab-case.md`.
7. **Local Developer Scratchpad (`.local/`):** Developers and agents should store personal notes, temporary test scripts, scratch work, and debug dumps inside the `.local/` directory, which is gitignored.
8. **No Unprompted Commits:** Never run `git commit` or `git push` unless explicitly commanded by the user.

---

## 7. Multi-Agent Task Workflow & Coordination Protocol

All team members and AI coding assistants operate under the **5-Stage Lifecycle**:
$$\textbf{Backlog} \longrightarrow \textbf{Ready} \longrightarrow \textbf{In progress} \longrightarrow \textbf{In review} \longrightarrow \textbf{Done}$$

### Tooling Strategy: Use GitHub CLI (`gh`), Avoid MCP
- **Strongly Recommended:** Use **GitHub CLI (`gh`)** (`gh auth login`) and the built-in [`scripts/task.py`](scripts/task.py) CLI. It provides zero-overhead, shell-native execution, and powers GitHub Actions CI.
- **Discouraged:** The **MCP server approach** (`@modelcontextprotocol/server-github`) is discouraged for ClearPath because it requires managing local background Node daemons, risks token exposure in plaintext configs, and lacks atomic local file locks.

### Anti-Collision Protocol & Board Rules
- **Board Rule:** Only **GitHub Issues** are items on the GitHub Project board. **Pull Requests must NEVER appear standalone on the board.** Every PR must reference `Closes #<id>` and be registered to its parent issue.
- **Before modifying any code, the AI agent must:**
1. Check task status: `python scripts/task.py check <TASK_ID>`
2. If claimed by another user: **STOP immediately**. Never take or edit an assigned task.
3. If unassigned: Atomically claim it:
   ```bash
   python scripts/task.py claim <TASK_ID> --assignee @your-github-username
   ```
   *(Sets Status to `In progress` on the project board and cuts the dedicated track branch)*.
4. Modify **only** files declared in the task's `Scope`.
5. Execute the exact test commands under `Validation`.
6. Open a PR referencing `Closes #<id>` and register it to the issue:
   ```bash
   python scripts/task.py done <TASK_ID> --pr <PR_URL>
   ```
   *(Registers PR comment on the issue, marks issue as `In review`, and ensures no standalone PR cards exist on the board)*.
7. A peer reviews and merges the PR into `main`. The issue closes and card moves to `Done` automatically. Standalone PRs can be cleaned with `python scripts/task.py clean-prs`.

### Task Generation for Coworkers
Coworkers can generate new tasks without manual script execution:
- **Option A (GitHub Web):** Go to **Issues ➔ New issue ➔ Agent task** and submit.
- **Option B (AI Assistant):** Prompt any AI to draft `tasks/mX-YY-slug.md`. Once pushed to `main`, GitHub Actions (`.github/workflows/sync-tasks.yml`) automatically creates the GitHub Issue and mirrors the link back.
