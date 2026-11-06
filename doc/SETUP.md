# ClearPath: Setup Specification (Official Baseline)

> [!IMPORTANT]
> **Top-Most Official Baseline Document:**  
> This file, alongside [`doc/ClearPath-PRD.pdf`](ClearPath-PRD.pdf) and [`doc/PRD.md`](PRD.md), represents the **top-most official documentation and foundational baseline** for the ClearPath project.  
> The complete, up-to-date, unified setup guide covering both this baseline containerized architecture and the streamlined local Python development workflow is located in [`doc/setup/setup.md`](setup/setup.md).

---

## 0. Requirements

| Tool | Version | Purpose |
|---|---|---|
| Git | any | all members |
| Docker Desktop (with Compose v2) | recent | runs the entire stack in containers |
| Node.js | 20 LTS | creating Next.js project (step 5), optional afterwards |
| Python | 3.10 or 3.11 | only if running worker without Docker (section 10) |

On Windows: Docker Desktop with WSL2, cloning the repo **inside WSL** (e.g. `~/clearpath`), not in `C:\`.

## 1. Repo Structure

```bash
mkdir clearpath && cd clearpath && git init -b main
mkdir -p contracts/samples test-site assets worker/extract worker/engine worker/media api demo scripts
touch worker/__init__.py worker/extract/__init__.py worker/engine/__init__.py worker/media/__init__.py
cp /path/to/PRD.md /path/to/SETUP.md .
```

### .gitignore
```gitignore
data/
assets/
.env
__pycache__/
*.pyc
.venv/
node_modules/
.next/
raw/
.local/
```

### .env.example
```dotenv
# Stages replaced with mock data from contracts/samples/ (all, empty, or list: extract,events,audit,render,report)
CP_STUBS=all
# piper or espeak (fallback if Piper fails)
TTS_ENGINE=piper
MAX_EVENTS=40
# video sync correction in seconds (see PRD 2.3)
VIDEO_OFFSET=0.0
# allowed hosts even if private (local test page)
ALLOWED_HOSTS=testsite,localhost
KEEP_TMP=0
```

## 2. docker-compose.yml

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

## 3. Worker Dockerfile & Requirements

### worker/requirements.txt
```text
playwright==1.48.0
rq==1.16.2
redis==5.0.8
piper-tts==1.2.0
numpy==1.26.4
```

### worker/Dockerfile
```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg espeak-ng curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# axe-core + Romanian voice for Piper
RUN mkdir -p /opt/assets/voices \
 && curl -fsSL -o /opt/assets/axe.min.js https://cdn.jsdelivr.net/npm/axe-core@4.10.2/axe.min.js \
 && curl -fsSL -o /opt/assets/voices/ro_RO-mihai-medium.onnx \
      https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ro/ro_RO/mihai/medium/ro_RO-mihai-medium.onnx \
 && curl -fsSL -o /opt/assets/voices/ro_RO-mihai-medium.onnx.json \
      https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ro/ro_RO/mihai/medium/ro_RO-mihai-medium.onnx.json

WORKDIR /app
```

## 4. API Dockerfile & Requirements

### api/requirements.txt
```text
fastapi==0.115.5
uvicorn[standard]==0.32.1
httpx==0.27.2
rq==1.16.2
redis==5.0.8
```

### api/Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

## 5. Startup Commands (Docker Compose)

```bash
docker compose up --build
```
- API health check: `curl localhost:8000/api/health`
- Frontend: http://localhost:3000
- Test site: http://localhost:8080/bad-checkout.html

---

*See [`doc/setup/setup.md`](setup/setup.md) for the active, merged, full setup instructions.*
