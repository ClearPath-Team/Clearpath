# Task: [DEMO-01] Real Demo Sites Analysis, Offline Pre-Caching & Presentation Preparation

- **Task ID:** `DEMO-01`
- **GitHub Issue:** #21
- **Track:** `M4` (API, web, and demo coordination)
- **Type:** `Feature`
- **Priority:** `P0 - blocks delivery`
- **Status:** `In progress`
- **Assignee:** `@AndreiBcs`
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
- [x] 2 real public demo websites are selected and documented in `doc/3-integration/demo.md`.
- [x] Full analyses are completed for `bad-checkout.html` and both real websites.
- [x] `demo/` contains the complete run directories with all required artifacts (`status.json`, `nodes.json`, `events.json`, `issues.json`, `clip.mp4`, `timeline.json`, `report.json`).
- [x] A convenience script `scripts/prepare_demo.py` is provided to stage demo runs into `data/` before presentation.
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
- **2026-11-06:** Prepared on `demo-precaching-preparation` by `@AndreiBcs`. Three fully live Piper runs cached: `bad-checkout` (33, 9 issues), `site1` / Berkshire Hathaway (76, 9 issues), `site2` / Space Jam archive (89, 4 issues). No extraction, audit, scoring or media algorithms modified.
- **2026-11-06:** Added manifest SHA-256 integrity checks and staging helper. Verified fresh staging, repeat staging, destination collision protection, explicit replacement and rejection of tampered artifacts before writes.
- **2026-11-06:** Offline application rehearsal uses Edge with all non-loopback HTTP(S) blocked and service workers disabled. Results, MP4 playback, 206 ranges and seeking are verified; issue timestamp highlighting is verified on `bad-checkout`. Physical Wi-Fi-off rehearsal remains a presenter check (the unchecked acceptance item above), rather than a claim that the host network adapter was disabled. Evidence and a video backup are included in `demo/`.
- **2026-11-06:** Worker regression suite passed: 38 tests, zero skips, including real Piper/Chromium/FFmpeg rendering. All three cached MP4 files were independently probed as H.264 video plus AAC audio; cache integrity verification passed.
- **2026-11-06, PR #26 review revision:** Superseded the original public captures with Accessible University (`site1`: 0, 50 findings, 49.385 s) and Drudge Report (`site2`: 0, 64 findings, 53.978 s). Each now contains four narrated critical findings with genuine timestamps. Event caps are 22 and 18; every stage remains live and all clips are under 90 seconds.
- **2026-11-06, PR #26 review revision:** Default staging now shares the API's `DATA_DIR`; issue identities are checked; copied files are verified once before atomic replacement; `--write-manifest` provides repeatable refreshes. Ten staging regression tests passed. Added reproducible stack/playback verification and an elevated physical-network test with immediate restoration plus an independent 60-second watchdog. Physical acceptance remains unchecked until that elevated test succeeds.
- **2026-11-06, PR #26 review revision:** The full stack starts through `scripts/dev.py` and all three critical timestamp buttons, playback and highlights pass. UAC was cancelled without adapter changes; the user reports no visible UAC dialog. Physical acceptance and merge are held pending a manual Wi-Fi-off run. Added a non-admin verification path and three tests preventing an online/connected host from being reported as physically offline. Status returned to In progress until this criterion is met.
