# Integration

## 1. Midpoint Checkpoint
The goal is early discovery of contract mismatches across tracks, not completing all features.

1. All members merge their respective branches into `main`.
2. Run live extraction, event generation, and audit, keeping `render` and `report` on stubs:
   ```bash
   CP_STUBS=render,report python -m worker.pipeline ck1 http://localhost:8080/bad-checkout.html
   ```
   On Windows PowerShell: `$env:CP_STUBS="render,report"; python -m worker.pipeline ck1 http://localhost:8080/bad-checkout.html`
3. Separately invoke `render_clip` against `data/ck1/nodes.json` and `data/ck1/events.json` (the real outputs from step 2).
4. Log any schema mismatch in `doc/decisions/decision-log.md` under "Integration Issues". The producing track resolves it.

## 2. Progressive Integration (Final 4 Hours)
Disable stubs **progressively** following the pipeline sequence:

| Step | `CP_STUBS` | Validate |
|---|---|---|
| 1 | `events,audit,render,report` | Live `nodes.json` |
| 2 | `audit,render,report` | Live `events.json` |
| 3 | `render,report` | Live `issues.json` |
| 4 | `report` | Live `clip.mp4` + `timeline.json` |
| 5 | (empty) | Complete live pipeline; verify Web results dashboard |

## 3. End-to-End Acceptance Test
- [ ] `bad-checkout.html`: Score is ~28, detects 8 issues, `keyboard-trap` is flagged. The cart button is announced as "Buton" and has an accurate timestamp.
- [ ] Clicking each timestamp seeks to the correct element in the video.
- [ ] Real Site 1: Analysis completes in under 3 minutes.
- [ ] Real Site 2: Analysis completes in under 3 minutes.
- [ ] Invalid URL returns a clear error in the Web UI.
- [ ] Consecutive analyses do not interfere with one another.

## 4. Common Integration Pitfalls

| Symptom | Probable Cause | Fix |
|---|---|---|
| Issues lack `node_id` | Selectors computed differently | Ensure everyone uses `SELECTOR_JS` from `worker/common.py`, never a local variant |
| Same text read twice | Missing rule for `LabelText` or atomic roles | Refer to `doc/2-tracks/m1-extract.md`, step 3 |
| Timestamps constantly offset | Lag at video recording start | Calibrate `VIDEO_OFFSET` in `.env` |
| Video jumping/seeking fails | Server not returning `206` | Refer to `doc/2-tracks/m4-app.md`, section B |
| Job stays in `queued` | Pipeline crashed during import | Inspect `data/{id}/pipeline.log` |
| Cookie banner hides content | Overlay blocking DOM | Implement step 9 in Track M1 or pick another demo site |
