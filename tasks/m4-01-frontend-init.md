# Task: [M4-01] Frontend Dashboard Initialization

- **Task ID:** `M4-01`
- **GitHub Issue:** #1 (pending creation/link)
- **Track:** `M4` (API, web, and demo)
- **Type:** `Feature`
- **Priority:** `P0 - blocks delivery`
- **Status:** `Ready`
- **Assignee:** *Unassigned*
- **Branch:** `m4-frontend-init`
- **Created Date:** 2026-11-06

---

## 1. Goal
Initialize the Next.js 14 frontend dashboard inside `web/` featuring a Romanian accessibility UI, URL analysis submission, job status polling against FastAPI (`:8000`), and a synchronized video player paired with an interactive accessibility score breakdown.

---

## 2. Context
The FastAPI backend in `api/main.py` is implemented and operational. It exposes:
- `POST /api/analyses` — Submits a URL for analysis, launches the background pipeline, and returns `{"id": "...", "status": "queued"}`.
- `GET /api/analyses/{id}` — Polls analysis progress (`queued`, `extracting`, `analyzing`, `rendering`, `done`, `failed`). When `done`, returns the full `report.json`.
- `GET /media/{id}/clip.mp4` — Streams the synchronized video with HTTP Range 206 support.

The `web/` directory currently contains only a placeholder `.gitkeep`. A responsive Next.js 14 frontend is needed to complete the demo loop.

---

## 3. Scope (Strict Boundary)
The agent is **only** permitted to create and modify files inside `web/`:
- `web/package.json`
- `web/tsconfig.json`
- `web/tailwind.config.ts`
- `web/next.config.js`
- `web/.env.local`
- `web/app/layout.tsx`
- `web/app/page.tsx`
- `web/app/a/[id]/page.tsx`
- `web/components/*`

**Forbidden:** Modifying `api/`, `worker/`, `contracts/`, or `doc/1-foundation/data-contracts.md`.

---

## 4. Acceptance Criteria
- [ ] Next.js 14 initialized with App Router, TypeScript, and Tailwind CSS.
- [ ] Root layout (`web/app/layout.tsx`) sets `<html lang="ro">` with accessible metadata and clear heading hierarchy.
- [ ] Home page (`/`):
  - Hero section explaining ClearPath in Romanian.
  - URL input defaulting to `http://localhost:8080/bad-checkout.html`.
  - "Analizează pagina" submit button with loading indicator.
  - Submits to `POST /api/analyses` and redirects to `/a/{id}` upon receipt of job UUID.
- [ ] Analysis & Results page (`/a/[id]`):
  - Displays dynamic status badge while job is running (`Se extrage arborele...`, `Se generează audio...`, etc.).
  - Auto-polls `GET /api/analyses/{id}` every 1.5 seconds until `status == "done"` or `"failed"`.
  - When `done`: Displays large circular accessibility score badge (e.g. `28/100`), violation cards categorized by severity (Critic, Grav, Mediu, Minor), and keyboard trap indicator.
  - HTML5 `<video>` player pointing to `http://localhost:8000/media/{id}/clip.mp4`.
  - Clicking any violation or timeline timestamp seeks the video player to that exact timestamp (`player.currentTime = item.timestamp`).

---

## 5. Validation & Test Commands
```bash
# 1. Start the API in background (or separate terminal)
python -m uvicorn api.main:app --port 8000 &

# 2. Start the bad-checkout demo site
python -m http.server 8080 --directory test-site &

# 3. Build and test web application
cd web
npm install
npm run build
npm run dev
# Verify http://localhost:3000 loads cleanly and triggers analysis
```

---

## 6. Dependencies
- Node.js `v20+` or `v26+` (installed)
- Running FastAPI backend on `:8000`

---

## 7. Out of Scope
- User authentication or login.
- Multi-page site crawling.
- Modifying backend endpoints or schemas.

---

## 8. Execution Log (Updated by Assignee)
- **Status Change:** `Backlog` -> `Ready` on 2026-11-06
- **Claimed by:** *None*
- **PR:** *None*
