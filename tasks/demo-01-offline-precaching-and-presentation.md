# Task: [DEMO-01] Real Demo Sites Analysis, Offline Pre-Caching & Presentation Preparation

- **Task ID:** `DEMO-01`
- **GitHub Issue:** #21
- **Track:** `M4` (API, web, and demo coordination)
- **Type:** `Feature`
- **Priority:** `P0 - blocks delivery`
- **Status:** `Ready`
- **Assignee:** Unassigned
- **Branch:** `demo-precaching-preparation`
- **Created Date:** 2026-11-06

---

## 1. Goal
Execute full end-to-end analyses on `bad-checkout.html` and 2 chosen real public websites, pre-cache all generated artifacts into `demo/`, document target URLs, IDs, and scores in `doc/3-integration/demo.md`, and verify that the application operates 100% offline with zero internet access according to the presentation contingency plan.

---

## 2. Context
In the final hackathon phase (`doc/3-integration/demo.md`), presentation resilience is paramount:
1. Wi-Fi loss during live pitch is a high-risk failure point. Pre-cached runs in `demo/` ensure that copying them into `data/` allows the `/a/{id}` results dashboard and video player to function flawlessly offline.
2. The team must select 2 real public websites with demonstrable accessibility findings (e.g. missing image alt attributes, contrast failures, unlabeled buttons), fast loading times (< 5 seconds), and minimal cookie/bot protection.
3. Interactive video seeking (`video.currentTime = timestamp; video.play()`) and active card highlighting must be validated in a real browser session.

---

## 3. Scope (Strict Boundary)
The assignee is permitted to modify or create:
- `demo/` (create pre-cached run directories `demo/bad-checkout/`, `demo/site1/`, `demo/site2/`)
- `scripts/prepare_demo.py` (convenience helper to copy `demo/` directories to `data/` and verify integrity)
- `doc/3-integration/demo.md` (fill in real site table, job IDs, and scores)
- `tasks/demo-01-offline-precaching-and-presentation.md`
- `tasks/README.md`

**Forbidden:** Modifying core backend algorithms, extraction logic, or scoring formulas.

---

## 4. Acceptance Criteria
- [ ] 2 real public demo websites are selected and documented in `doc/3-integration/demo.md`.
- [ ] Full analyses are completed for `bad-checkout.html` and both real websites.
- [ ] `demo/` contains the complete run directories with all required artifacts (`status.json`, `nodes.json`, `events.json`, `issues.json`, `clip.mp4`, `timeline.json`, `report.json`).
- [ ] A convenience script `scripts/prepare_demo.py` is provided to stage demo runs into `data/` before presentation.
- [ ] With system networking/Wi-Fi disabled, launching `scripts/dev.py` and navigating to `/a/<id>` displays the results dashboard, plays the video clip, and seeks correctly on timestamp button click.

---

## 5. Validation & Test Commands
```bash
# 1. Run demo staging script
.venv/bin/python scripts/prepare_demo.py

# 2. Verify all demo directories have report.json and clip.mp4
test -f demo/bad-checkout/report.json && test -f demo/bad-checkout/clip.mp4
test -f demo/site1/report.json && test -f demo/site1/clip.mp4
test -f demo/site2/report.json && test -f demo/site2/clip.mp4

# 3. Verify video range response returns HTTP 206
curl -s -o /dev/null -w "%{http_code}" -H "Range: bytes=0-100" http://localhost:8000/media/bad-checkout/clip.mp4
```

---

## 6. Dependencies
- Merged `M4-02` (PR #19)
- Completed `INTEG-01` (full pipeline execution verified)

---

## 7. Out of Scope
- Adding new UI features not specified in `doc/2-tracks/m4-app.md`.
- Modifying `test-site/bad-checkout.html`.

---

## 8. Execution Log
- **2026-11-06:** Task created as Ready for the Demo Preparation phase.
