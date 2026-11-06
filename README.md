# ClearPath

> Making the real web experience of visually impaired users visible and heard.

Starting from a simple link, **ClearPath** analyzes how a website is perceived through assistive technologies (screen readers), runs an automated accessibility audit, and delivers a **synchronized narrated video** that visually and audibly demonstrates the real navigation experience, accompanied by accessibility scores, WCAG violations, and actionable recommendations.

Developed by the **Four The Win** team for **Astra Hack** (November 6–7, 2026).

---

## Table of Contents

1. [What ClearPath Does](#what-clearpath-does)
2. [Architecture & Data Flow](#architecture--data-flow)
3. [System Requirements](#system-requirements)
4. [Complete Step-by-Step Setup Guide](#complete-step-by-step-setup-guide)
5. [Environment Verification](#environment-verification)
6. [Web UI Configuration (Next.js)](#web-ui-configuration-nextjs)
7. [Running in Development Mode](#running-in-development-mode)
8. [Testing Individual Modules](#testing-individual-modules)
9. [Working with Mock Data (CP_STUBS)](#working-with-mock-data-cp_stubs)
10. [Troubleshooting & Common Issues](#troubleshooting--common-issues)
11. [Project Documentation](#project-documentation)

---

## What ClearPath Does

1. **Realistic Screen Reader Simulation:** Launches a headless Chromium browser via Playwright and extracts the full accessibility tree using Chrome DevTools Protocol (`Accessibility.getFullAXTree`).
2. **Sequential Tab Traversal & Trap Detection:** Simulates keyboard `Tab` navigation to reconstruct the focus order and automatically detects keyboard traps (`focus_trap`).
3. **Spoken Announcements:** Converts element roles, states, and accessible names into screen-reader announcements (modeled after NVDA conventions), synthesized locally on CPU with Piper TTS (`ro_RO-mihai-medium.onnx` voice model).
4. **Synchronized Video Recording:** Records live page traversal with an animated yellow high-contrast focus box (`#cp-hl`) following active elements, paired with subtitles (`#cp-cap`).
5. **axe-core Accessibility Audit:** Runs `axe-core 4.10.2` in the browser context to detect WCAG compliance issues, calculating a 0–100 score and providing actionable recommendations.
6. **Interactive Timestamped Results:** Displays a web dashboard where each discovered issue is mapped to its exact timestamp in the narrated video; clicking an issue seeks the player directly to that moment.

---

## Architecture & Data Flow

ClearPath runs **completely locally without Docker or external databases**. Each analysis runs as an isolated Python subprocess (`subprocess.Popen`), storing job artifacts on disk in `data/{id}/`.

```
 ┌──────────────┐   POST /api/analyses   ┌──────────────┐   spawns process   ┌──────────────────────────┐
 │  web         │ ─────────────────────► │  api         │ ─────────────────► │ python -m worker.pipeline│
 │  Next.js 14  │ ◄──── GET status ───── │  FastAPI     │                    │       {id} {url}         │
 │  :3000       │                        │  :8000       │                    └────────────┬─────────────┘
 └──────┬───────┘                        └──────┬───────┘                                 │ writes
        │ GET /media/{id}/clip.mp4              │ reads status / report                   ▼
        └───────────────────────────────────────┴───────────────────────────────► data/{id}/
```

The processing pipeline consists of 5 sequential stages:
```
nodes.json (M1) ──► events.json (M2) ──► issues.json (M2) ──► timeline.json + clip.mp4 (M3) ──► report.json (M2)
```

---

## System Requirements

| Tool | Recommended Version | macOS | Linux (Ubuntu / Debian) | Windows |
|---|---|---|---|---|
| **Python** | 3.11 or 3.12 | `brew install python@3.12` | `sudo apt update && sudo apt install python3 python3-venv python3-pip` | python.org (*check Add Python to PATH*) |
| **ffmpeg & ffprobe** | any recent version | `brew install ffmpeg` | `sudo apt install ffmpeg` | `winget install Gyan.FFmpeg` |
| **Git** | any recent version | included with Xcode CLI | `sudo apt install git` | git-scm.com |
| **Node.js & npm** | 20 LTS | `brew install node@20` | nodesource or `nvm install 20` | nodejs.org or `winget install OpenJS.NodeJS.LTS` |

> [!NOTE]
> Node.js is only required for running the web frontend (Track M4). The backend and worker run strictly in Python.

---

## Complete Step-by-Step Setup Guide

> [!TIP]
> **Automated AI Setup:**  
> If you are using an AI coding assistant (Claude, Antigravity, Cursor, etc.), you can give it the prompt in [`setup-prompt.md`](setup-prompt.md). It will automatically detect your OS (WSL2, Linux, macOS, or Windows), install prerequisites, run verification, and generate a customized `.local/local-config.md`.

Follow the instructions below starting from the root of the project:

### 1. Clone the Repository
```bash
git clone https://github.com/vlad-toderascu/Clearpath.git
cd Clearpath
```

### 2. Create and Activate Python Virtual Environment
* **On Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```
* **On Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```
  *(If PowerShell shows a script execution policy error, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`)*

> [!IMPORTANT]
> Ensure the `.venv` virtual environment is active in every new terminal window before executing any Python command!

### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Playwright & Chromium Browser
```bash
python -m playwright install chromium
```
*If you are on Linux/Ubuntu and installing Playwright for the first time, install system dependencies:*
```bash
python -m playwright install-deps chromium
```

### 5. Download Required Assets (axe-core and Piper Voice)
The setup script downloads `axe.min.js` (v4.10.2) and the Piper voice model (`ro_RO-mihai-medium.onnx` + configuration) into `assets/`:
```bash
python scripts/fetch_assets.py
```

### 6. Configure Environment Variables
Copy the template `.env.example` file to `.env`:
* **On Linux / macOS:**
  ```bash
  cp .env.example .env
  ```
* **On Windows (PowerShell / CMD):**
  ```powershell
  copy .env.example .env
  ```

Default `.env` configuration:
```dotenv
# all | extract,events,audit,render,report | empty (runs full real code)
CP_STUBS=all
# piper (default) | espeak (fallback) | say (macOS only)
TTS_ENGINE=piper
MAX_EVENTS=40
VIDEO_OFFSET=0.0
ALLOWED_HOSTS=localhost,127.0.0.1
KEEP_TMP=0
TEST_URL=http://localhost:8080/bad-checkout.html
```

### 7. Local Developer Scratchpad (`.local/`)
Developers can store personal notes, one-off debug scripts, experimental logs, or local test dumps inside the `.local/` folder. It is ignored by Git (`.gitignore`) to keep repository tracking clean.

---

## Environment Verification

Run the built-in diagnostic script:
```bash
python scripts/check_env.py
```

Expected output:
```text
OK  Python                           3.11.x (or 3.12.x)
OK  worker/common.py + selector.js   selector.js loaded (...)
OK  Playwright + Chromium            130.x
OK  ffmpeg                           /usr/bin/ffmpeg
OK  ffprobe                          /usr/bin/ffprobe
OK  axe-core                         .../assets/axe.min.js
OK  Piper + voice model              0.62s @ 22050 Hz
OK  Node.js                          v20.x (optional for M1-M3)
OK  npm                              10.x  (optional for M1-M3)
```

The first 7 checks **must** report `OK` for the backend and processing pipeline to function properly.

---

## Web UI Configuration (Next.js)

If you are working on the graphical interface (Track M4):

1. **Initialize Next.js in `web/`:**
   If `web/` contains a `.gitkeep` file, remove it first, then run:
   ```bash
   npx create-next-app@14.2.15 web --ts --tailwind --app --eslint --no-src-dir --import-alias "@/*" --use-npm
   ```
2. **Configure API URL:**
   Create `web/.env.local`:
   ```dotenv
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
3. **Set Romanian HTML Language Attribute:**
   In `web/app/layout.tsx`, ensure the root html tag is:
   ```tsx
   <html lang="ro">
   ```
4. **Generate Sample Test Video (for Video Player testing):**
   ```bash
   ffmpeg -y -f lavfi -i testsrc=duration=30:size=1280x720:rate=25 -f lavfi -i sine=frequency=440:duration=30 \
     -shortest -c:v libx264 -preset veryfast -pix_fmt yuv420p -c:a aac contracts/samples/clip.mp4
   ```

---

## Running in Development Mode

### Option A: Unified Single Command (Recommended)
The `dev.py` script starts all services simultaneously in one terminal:
```bash
python scripts/dev.py
```

This starts:
* **Local Test Site:** http://localhost:8080/bad-checkout.html
* **FastAPI Backend:** http://localhost:8000/api/health (Swagger documentation at `/docs`)
* **Next.js Web Frontend:** http://localhost:3000

Press `Ctrl+C` to cleanly terminate all processes.

### Option B: Separate Terminals
To monitor individual service logs separately:
```bash
# Terminal 1 — Offline Test Site (bad-checkout.html)
python -m http.server 8080 -d test-site

# Terminal 2 — FastAPI Backend
python -m uvicorn api.main:app --reload --port 8000

# Terminal 3 — Next.js Frontend
cd web && npm run dev
```

### Running an Analysis Directly from the Terminal
Execute the pipeline on any URL without opening the browser UI:
```bash
python -m worker.pipeline test1 http://localhost:8080/bad-checkout.html
```
Job artifacts and logs will be written to `data/test1/`.

---

## Testing Individual Modules

Each team member can test their module in total isolation from the repository root:

```bash
# Track M1 (AX tree extraction & Tab traversal):
python -m worker.extract.extract http://localhost:8080/bad-checkout.html data/dev/nodes.json

# Track M2 (Generate speech announcements from mock nodes):
python -m worker.engine.events contracts/samples/nodes.json

# Track M2 (Run axe-core audit against the test site):
python -m worker.engine.audit http://localhost:8080/bad-checkout.html contracts/samples/nodes.json

# Track M2 (Assemble final report & calculate score from samples):
python -m worker.engine.report contracts/samples/issues.json contracts/samples/timeline.json contracts/samples/nodes.json

# Track M3 (Render video clip & timeline from samples):
python -m worker.media.render http://localhost:8080/bad-checkout.html contracts/samples/nodes.json contracts/samples/events.json data/dev

# Track M4 (Run pipeline with stubs enabled):
python -m worker.pipeline dev1 http://localhost:8080/bad-checkout.html
```

---

## Working with Mock Data (CP_STUBS)

To enable friction-free parallel development across team members, the pipeline respects the `CP_STUBS` setting in `.env`:

* `CP_STUBS=all` : All stages use mock files from `contracts/samples/` (instantaneous execution; perfect for frontend and API work).
* `CP_STUBS=render,report` : Executes live `extract`, `events`, and `audit`, while using mock samples for `render` and `report`.
* `CP_STUBS=` : Executes live production code for all 5 stages end-to-end.

During integration, stubs are gradually removed following the checklist in `doc/3-integration/integration.md`.

---

## Troubleshooting & Common Issues

| Problem | Likely Cause | Solution |
|---|---|---|
| `ModuleNotFoundError: No module named 'worker'` | Command not executed from the repository root | Always run commands from the root `Clearpath/` directory using `python -m worker....` |
| `Executable doesn't exist` with Playwright | Chromium not installed in the active `.venv` | Activate `.venv` (`source .venv/bin/activate`) and run `python -m playwright install chromium` |
| Missing system libraries for Chromium on Linux | Missing OS-level dependencies | Run `python -m playwright install-deps chromium` (requires `sudo`) |
| `pip install piper-tts` fails | Platform binary compilation issue | Set `TTS_ENGINE=espeak` in `.env` (after installing `espeak-ng` via apt or brew) |
| `fetch_assets.py` voice download error | Hugging Face network block or timeout | Manually download `ro_RO-mihai-medium.onnx` and `.json` to `assets/voices/` (see `doc/setup/troubleshooting.md`) |
| Port `8080`, `8000`, or `3000` is already in use | Another local process is holding the port | Free the port (`lsof -i :8000` or `netstat -ano \| findstr 8000`) or adjust the port in `scripts/dev.py` |
| Video seek/jumping does not work in the browser | HTTP response lacks `Range` header | Ensure FastAPI returns `206 Partial Content` for video chunks (see `doc/2-tracks/m4-app.md`) |

For comprehensive solutions, refer to [`doc/setup/troubleshooting.md`](doc/setup/troubleshooting.md).

---

## Project Documentation

> [!IMPORTANT]
> **Official Baseline Documents:**  
> [`doc/ClearPath-PRD.pdf`](doc/ClearPath-PRD.pdf), [`doc/SETUP.md`](doc/SETUP.md), and [`doc/PRD.md`](doc/PRD.md) are the **top-most official documents and baseline specifications** for ClearPath.

Detailed technical documentation is organized inside [`doc/`](doc/):

* [`CLAUDE.md`](CLAUDE.md) — **Master agent guide** (complete documentation map, track boundaries, and execution rules).
* [`setup-prompt.md`](setup-prompt.md) — **Automated setup prompt** for agentic AIs (WSL2, native Linux, macOS, Windows).
* [`setup-workflow-projects.md`](setup-workflow-projects.md) — **Connecting Agentic AI to GitHub Projects** (v2) and Issues (MCP, CLI, and GitHub Actions).
* [`doc/setup/setup.md`](doc/setup/setup.md) — Complete unified setup guide (local development and baseline Docker stack).
* [`doc/setup/troubleshooting.md`](doc/setup/troubleshooting.md) — In-depth catalog of solutions for setup and runtime issues.
* [`doc/1-foundation/product.md`](doc/1-foundation/product.md) — Product vision, user journey, and MVP feature boundaries.
* [`doc/1-foundation/architecture.md`](doc/1-foundation/architecture.md) — Architecture diagrams, state machines, and technical stack.
* [`doc/1-foundation/data-contracts.md`](doc/1-foundation/data-contracts.md) — **Single source of truth** for JSON data contracts (`nodes.json`, `events.json`, `issues.json`, etc.).
* [`doc/1-foundation/kickoff-checklist.md`](doc/1-foundation/kickoff-checklist.md) — First-hour team synchronization checklist.
* [`doc/2-tracks/`](doc/2-tracks/) — Detailed specifications for each member:
  - [`m1-extract.md`](doc/2-tracks/m1-extract.md) — Accessibility tree, CDP extraction, Tab walking, keyboard traps.
  - [`m2-engine.md`](doc/2-tracks/m2-engine.md) — Screen reader speech rules, axe-core audit, score calculation.
  - [`m3-media.md`](doc/2-tracks/m3-media.md) — Piper TTS voice synthesis, Playwright screen recording with highlights, ffmpeg A/V muxing.
  - [`m4-app.md`](doc/2-tracks/m4-app.md) — FastAPI, Next.js 14, pipeline subprocess orchestration, offline demo setup.
* [`doc/3-integration/integration.md`](doc/3-integration/integration.md) — Midpoint checkpoint and progressive un-stubbing strategy.
* [`doc/3-integration/demo.md`](doc/3-integration/demo.md) — Live presentation scenario and offline contingency plans.
* [`doc/3-integration/definition-of-done.md`](doc/3-integration/definition-of-done.md) — Final MVP acceptance checklist.
* [`doc/rules/repo-rules.md`](doc/rules/repo-rules.md) — Repository rules (branching, file ownership, commit standards).
* [`doc/decisions/decision-log.md`](doc/decisions/decision-log.md) — Architecture Decision Record (ADR) and integration issue tracking.

---

*ClearPath — Making web accessibility visible and heard.*
