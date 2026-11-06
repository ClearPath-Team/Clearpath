# ClearPath — Quick Start & How-To Guide

This guide explains how to start, access, and test ClearPath on your local machine (WSL2 / Linux / macOS).

---

## 1. Quick Start (Running the Application)

ClearPath consists of 3 local lightweight services running concurrently:
1. **Target Demo Site** (`:8080`) — Mock e-commerce site with intentional accessibility flaws.
2. **FastAPI Backend** (`:8000`) — Orchestrates background analysis pipelines and streams media.
3. **Next.js Web Frontend** (`:3000`) — Interactive accessibility dashboard in Romanian.

### Terminal 1: Start the Target Demo Site
```bash
.venv/bin/python -m http.server 8080 --directory test-site
```
*Accessible at:* `http://localhost:8080/bad-checkout.html`

### Terminal 2: Start the FastAPI Backend
To run with mock sample data (instant response without heavy GPU/TTS dependencies):
```bash
CP_STUBS=all .venv/bin/python -m uvicorn api.main:app --port 8000 --reload
```
To run fully live (once M1/M2/M3 runtime dependencies are installed):
```bash
.venv/bin/python -m uvicorn api.main:app --port 8000 --reload
```
*API docs at:* `http://localhost:8000/docs` | *Health check:* `http://localhost:8000/api/health`

### Terminal 3: Start the Next.js Frontend
```bash
cd web
npm run dev
```
*Dashboard accessible at:* **`http://localhost:3000`**

---

## 2. Testing via the Browser (Interactive Flow)

1. Open your browser and navigate to:
   👉 **`http://localhost:3000`**

2. **Submit an Analysis**:
   - The URL input is pre-filled with `http://localhost:8080/bad-checkout.html`.
   - Click the blue **"Analizează pagina"** button.
   - The frontend calls `POST /api/analyses` and redirects you to `/a/[id]`.

3. **In-Progress Polling**:
   - The UI polls `GET /api/analyses/[id]` every 1.5 seconds.
   - Watch the 4-step progress tracker:
     - 1. *Inițializare job*
     - 2. *Extragere arbore de accesibilitate* (`extracting`)
     - 3. *Analiză reguli WCAG & axe-core* (`analyzing`)
     - 4. *Randare clip video narat* (`rendering`)

4. **Results Dashboard (`done`)**:
   - **Accessibility Score**: Large colored circular badge (e.g. `28 / 100` or `33 / 100`).
   - **Keyboard Trap Alert**: Prominent alert badge (*"Capcană de tastatură detectată"*).
   - **Narrated Video Player**: Streams `/media/[id]/clip.mp4` with HTTP Range 206 support.
   - **Severity Filtering**: Filter issues by clicking *Toate*, *Critice*, *Grave*, *Medii*, or *Minore*.
   - **Video Seek Synchronization**: Click any timestamp button (e.g. `0:08`, `0:12`, `0:20`) on an issue card to jump to that moment in the video. The currently active issue is highlighted automatically during playback.
   - **Remediation Details**: Click *"Vezi recomandare"* on any card to view Romanian remediation guidance and the canonical CSS selector.

---

## 3. Automated End-to-End Verification (Terminal)

You can run an automated end-to-end check without opening a browser:

```bash
.venv/bin/python -c "
import subprocess, time, httpx, sys, os

site = subprocess.Popen([sys.executable, '-m', 'http.server', '8080', '--directory', 'test-site'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
api = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'api.main:app', '--port', '8000'], env=dict(os.environ, CP_STUBS='all'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
web = subprocess.Popen(['npm', 'run', 'start', '--', '-p', '3000'], cwd='web', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(3)
try:
    # 1. Health check
    h = httpx.get('http://localhost:8000/api/health')
    print('1. Backend API (8000):', 'OK' if h.status_code == 200 else 'FAIL')

    # 2. Web Home check
    wh = httpx.get('http://localhost:3000/')
    print('2. Frontend Web (3000):', 'OK' if wh.status_code == 200 else 'FAIL')

    # 3. Submit analysis
    resp = httpx.post('http://localhost:8000/api/analyses', json={'url': 'http://localhost:8080/bad-checkout.html'})
    aid = resp.json()['id']
    print(f'3. Submit Analysis ID={aid}:', 'OK' if resp.status_code == 202 else 'FAIL')

    # 4. Poll until done
    for _ in range(10):
        time.sleep(1)
        st = httpx.get(f'http://localhost:8000/api/analyses/{aid}').json()
        if st.get('status') == 'done':
            print(f'4. Analysis Complete! Score: {st[\"report\"].get(\"score\")}, Issues: {len(st[\"report\"].get(\"issues\", []))}')
            break

    # 5. Media range check
    media = httpx.get(f'http://localhost:8000/media/{aid}/clip.mp4', headers={'Range': 'bytes=0-100'})
    print('5. Video Streaming (206 Range):', 'OK' if media.status_code == 206 else f'Status {media.status_code}')
finally:
    web.terminate()
    api.terminate()
    site.terminate()
"
```

---

## 4. Troubleshooting & Helpful Tips

- **Next.js Webpack Chunk Error (`Cannot find module './138.js'`)**:
  This happens if `npm run dev` was running while a production build (`npm run build`) was triggered.
  *Fix:* Stop the dev server (`Ctrl + C`), delete `.next`, and restart:
  ```bash
  rm -rf web/.next
  cd web && npm run dev
  ```

- **Video Error: "No video with supported format found"**:
  Ensure the backend is running and `clip.mp4` exists in `data/{analysis_id}/clip.mp4`. When testing with `CP_STUBS=all`, the backend copies the sample video. If testing live, ensure `ffmpeg` is installed in your `$PATH`.

- **Checking Ports**:
  ```bash
  # Check if ports 3000, 8000, or 8080 are currently listening:
  ss -tulpn | grep -E "3000|8000|8080"
  ```
