# ClearPath: Complete Setup Guide

> [!IMPORTANT]
> **Official Baseline Reference:**  
> [`doc/ClearPath-PRD.pdf`](../ClearPath-PRD.pdf), [`doc/SETUP.md`](../SETUP.md), and [`doc/PRD.md`](../PRD.md) are the **top-most official documents and serve as the baseline** for the entire ClearPath project.  
> This setup document provides the unified, up-to-date guide covering both the **recommended local workflow** (fast iteration without containers) and the **official baseline containerized architecture** (Docker Compose).

---

## Table of Contents

1. [Prerequisites & System Requirements](#1-prerequisites--system-requirements)
2. [Track A: Recommended Local Setup (Fastest for Development)](#2-track-a-recommended-local-setup-fastest-for-development)
   - [2.1 Repository & Python Environment](#21-repository--python-environment)
   - [2.2 Playwright & Offline Assets](#22-playwright--offline-assets)
   - [2.3 Environment Configuration (.env)](#23-environment-configuration-env)
   - [2.4 Environment Verification](#24-environment-verification)
   - [2.5 Frontend Initialization (Next.js)](#25-frontend-initialization-nextjs)
   - [2.6 Starting the Local Dev Server](#26-starting-the-local-dev-server)
   - [2.7 Isolated Module Execution](#27-isolated-module-execution)
3. [Track B: Containerized Architecture (Official Docker Baseline)](#3-track-b-containerized-architecture-official-docker-baseline)
   - [3.1 Docker Compose Specification](#31-docker-compose-specification)
   - [3.2 Worker Service & Dockerfile](#32-worker-service--dockerfile)
   - [3.3 API Service & Dockerfile](#33-api-service--dockerfile)
   - [3.4 Starting with Docker Compose](#34-starting-with-docker-compose)
   - [3.5 Verification of Containerized Stack](#35-verification-of-containerized-stack)
4. [Developer Scratchpad (.local/)](#4-developer-scratchpad-local)
5. [Git Branches & Collaboration](#5-git-branches--collaboration)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Prerequisites & System Requirements

| Tool | Recommended Version | macOS | Linux (Ubuntu / Debian) | Windows |
|---|---|---|---|---|
| **Python** | 3.11 or 3.12 | `brew install python@3.12` | `sudo apt install python3 python3-venv python3-pip` | python.org (*Add Python to PATH*) |
| **ffmpeg & ffprobe** | Recent | `brew install ffmpeg` | `sudo apt install ffmpeg` | `winget install Gyan.FFmpeg` |
| **Node.js & npm** | 20 LTS | `brew install node@20` | nodesource or `nvm install 20` | nodejs.org |
| **Git** | Recent | Included | `sudo apt install git` | git-scm.com |
| **Docker Desktop** | Compose v2 | Optional (for Docker stack) | Optional (for Docker stack) | WSL2 backend (*clone in WSL*) |

> [!NOTE]
> On Windows when using Docker: Ensure Docker Desktop is configured with the WSL2 backend, and clone the repository **inside WSL** (e.g. `~/clearpath`), not under `/mnt/c/`, to prevent severe I/O degradation.

---

## 2. Track A: Recommended Local Setup (Fastest for Development)

In this mode, all services run directly on the host machine via terminal sessions. Analysis jobs run as lightweight Python subprocesses (`subprocess.Popen`), requiring no Redis server or Docker daemon.

### 2.1 Repository & Python Environment
```bash
git clone https://github.com/vlad-toderascu/Clearpath.git
cd Clearpath

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate              # Windows PowerShell: .venv\Scripts\Activate.ps1

# Upgrade pip and install unified requirements
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.2 Playwright & Offline Assets
```bash
# Install Chromium browser binary
python -m playwright install chromium

# On Linux (first-time install only): install OS libraries
python -m playwright install-deps chromium

# Download axe-core (v4.10.2) and Piper Romanian voice model into assets/
python scripts/fetch_assets.py
```

### 2.3 Environment Configuration (.env)
```bash
cp .env.example .env                   # Windows: copy .env.example .env
```

Key environment settings in `.env`:
```dotenv
# all | extract,events,audit,render,report | empty (runs full live code)
CP_STUBS=all
# piper (default) | espeak (fallback) | say (macOS only)
TTS_ENGINE=piper
MAX_EVENTS=40
VIDEO_OFFSET=0.0
ALLOWED_HOSTS=localhost,127.0.0.1
KEEP_TMP=0
TEST_URL=http://localhost:8080/bad-checkout.html
```

### 2.4 Environment Verification
Run the diagnostic script:
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
OK  Piper + Romanian voice           0.62s @ 22050 Hz
OK  Node.js                          v20.x
OK  npm                              10.x
```
The first 7 lines **must** report `OK` for the processing pipeline to operate.

### 2.5 Frontend Initialization (Next.js)
If working on Track M4 (UI):
1. Remove `web/.gitkeep` if present, then scaffold Next.js:
   ```bash
   npx create-next-app@14.2.15 web --ts --tailwind --app --eslint --no-src-dir --import-alias "@/*" --use-npm
   ```
2. Create `web/.env.local`:
   ```dotenv
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
3. In `web/app/layout.tsx`, ensure the html tag specifies:
   ```tsx
   <html lang="ro">
   ```
4. Generate the mock test video for UI player verification:
   ```bash
   ffmpeg -y -f lavfi -i testsrc=duration=30:size=1280x720:rate=25 -f lavfi -i sine=frequency=440:duration=30 \
     -shortest -c:v libx264 -preset veryfast -pix_fmt yuv420p -c:a aac contracts/samples/clip.mp4
   ```

### 2.6 Starting the Local Dev Server
Single unified command starts all three dev services:
```bash
python scripts/dev.py
```
- **Offline Test Site:** http://localhost:8080/bad-checkout.html
- **FastAPI API:** http://localhost:8000/api/health (Swagger: `/docs`)
- **Next.js Web Frontend:** http://localhost:3000

Press `Ctrl+C` to terminate all processes.

### 2.7 Isolated Module Execution
Test individual modules without starting the full stack:
```bash
# Member 1: Tree extraction & Tab traversal
python -m worker.extract.extract http://localhost:8080/bad-checkout.html data/dev/nodes.json

# Member 2: Screen reader announcements
python -m worker.engine.events contracts/samples/nodes.json

# Member 2: axe-core audit against test page
python -m worker.engine.audit http://localhost:8080/bad-checkout.html contracts/samples/nodes.json

# Member 2: Report assembly and scoring
python -m worker.engine.report contracts/samples/issues.json contracts/samples/timeline.json contracts/samples/nodes.json

# Member 3: Video rendering & timeline generation
python -m worker.media.render http://localhost:8080/bad-checkout.html contracts/samples/nodes.json contracts/samples/events.json data/dev

# Member 4: Full pipeline with stubs
python -m worker.pipeline dev1 http://localhost:8080/bad-checkout.html
```

---

## 3. Track B: Containerized Architecture (Official Docker Baseline)

The baseline official architecture described in [`doc/SETUP.md`](../SETUP.md) runs the pipeline using Docker Compose, Redis 7, and RQ (Redis Queue).

### 3.1 Docker Compose Specification (`docker-compose.yml`)

```yaml
services:
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  api:
    build: ./api
    env_file: .env
    environment:
      DATA_DIR: /app/data
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./api:/app
      - ./data:/app/data
    ports: ["8000:8000"]
    depends_on: [redis]

  worker:
    build: ./worker
    env_file: .env
    environment:
      DATA_DIR: /app/data
      REDIS_URL: redis://redis:6379/0
      PYTHONPATH: /app
      AXE_PATH: /opt/assets/axe.min.js
      PIPER_VOICE: /opt/assets/voices/ro_RO-mihai-medium.onnx
    volumes:
      - .:/app
    working_dir: /app
    shm_size: "1gb"
    command: rq worker clearpath --url redis://redis:6379/0
    depends_on: [redis, testsite]

  testsite:
    image: python:3.11-slim
    working_dir: /site
    volumes:
      - ./test-site:/site:ro
    command: python -m http.server 8080
    ports: ["8080:8080"]

  web:
    image: node:20-alpine
    working_dir: /web
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    volumes:
      - ./web:/web
      - /web/node_modules
    command: sh -c "npm install && npm run dev -- -H 0.0.0.0 -p 3000"
    ports: ["3000:3000"]
    depends_on: [api]
```

### 3.2 Worker Service & Dockerfile

**`worker/requirements.txt`:**
```text
playwright==1.48.0
rq==1.16.2
redis==5.0.8
piper-tts==1.2.0
numpy==1.26.4
```

**`worker/Dockerfile`:**
```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg espeak-ng curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# axe-core + Romanian voice model for Piper
RUN mkdir -p /opt/assets/voices \
 && curl -fsSL -o /opt/assets/axe.min.js https://cdn.jsdelivr.net/npm/axe-core@4.10.2/axe.min.js \
 && curl -fsSL -o /opt/assets/voices/ro_RO-mihai-medium.onnx \
      https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ro/ro_RO/mihai/medium/ro_RO-mihai-medium.onnx \
 && curl -fsSL -o /opt/assets/voices/ro_RO-mihai-medium.onnx.json \
      https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ro/ro_RO/mihai/medium/ro_RO-mihai-medium.onnx.json

WORKDIR /app
```

### 3.3 API Service & Dockerfile

**`api/requirements.txt`:**
```text
fastapi==0.115.5
uvicorn[standard]==0.32.1
httpx==0.27.2
rq==1.16.2
redis==5.0.8
```

**`api/Dockerfile`:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 3.4 Starting with Docker Compose
```bash
cp .env.example .env
docker compose up --build
```

### 3.5 Verification of Containerized Stack
| Check | Expected Result |
|---|---|
| `curl localhost:8000/api/health` | `{"ok":true}` |
| http://localhost:3000 | Next.js home page |
| http://localhost:8080/bad-checkout.html | Offline demo test site |
| `docker compose run --rm worker python -c "import playwright; print('ok')"` | `ok` |
| `docker compose run --rm worker espeak-ng -v ro -w /tmp/e.wav "Buton"` | Clean exit without errors |

---

## 4. Developer Scratchpad (`.local/`)

Developers and agents can place personal scratch files, notes, one-off test scripts, or local test runs in the `.local/` directory. It is explicitly ignored by Git (`.gitignore`) to keep repository tracking clean.

---

## 5. Git Branches & Collaboration

```bash
git checkout -b m1-extract   # Member 1
git checkout -b m2-engine    # Member 2
git checkout -b m3-media     # Member 3
git checkout -b m4-app       # Member 4
```
- Each developer modifies **only** their assigned files (`doc/rules/repo-rules.md`).
- Merge into `main` happens at designated checkpoints: hour 1 (mock samples), midpoint, and final integration.

---

## 6. Troubleshooting

For solutions to common errors (Playwright missing native dependencies, Piper TTS compilation, Hugging Face voice downloads, occupied ports, or video seek issues), consult [`doc/setup/troubleshooting.md`](troubleshooting.md).
