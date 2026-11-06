# Demo Presentation Protocol

During the final 2 hours of the hackathon, feature freezes are strictly observed.

## Preparation
1. The following full, unstubbed analyses were captured on **2026-11-06**, using
   local Piper narration and the repository's live extraction, axe audit, render
   and report stages. The public sites were loaded directly; their scores are
   point-in-time observations, not permanent accessibility ratings.

   | Site / source URL | ID | Score | Findings | Clip duration | Measured page load |
   |---|---|---|---|---|---|
   | [Local checkout](http://localhost:8080/bad-checkout.html) | `bad-checkout` | 33 | 9 | 52.595 s | local |
   | [Accessible University, inaccessible training page](https://projects.accesscomputing.uw.edu/au/before.html) | `site1` | 0 | 50 | 49.385 s | 1.99 s |
   | [Drudge Report](https://www.drudgereport.com/) | `site2` | 0 | 64 | 53.978 s | 1.81 s |

   Both public targets have **four critical findings with real timestamps**.
   Accessible University is an intentionally inaccessible fictional university
   used for instruction by the University of Washington, not an assessment of
   its actual university home page. Drudge Report is a snapshot of a live news
   index. Both scores reach the formula's zero floor because of the number of
   findings; they are not hand-adjusted. The captures use event caps of 22 and
   18 respectively so all three clips stay below 90 seconds. Every stage remains
   live. The public targets loaded without cookie dialogs or bot challenges.

2. Install Python/frontend dependencies and Chromium **before** disconnecting.
   For cached playback, the application needs only its local API/frontend and a
   browser supporting H.264/AAC. Verified with Microsoft Edge 156.0.4314.58;
   the bundled Playwright Chromium 130 on this machine lacks those codecs.
   Piper, its voice, FFmpeg and the target websites are not required to replay
   an already cached run.
3. Stage all three caches using the same `DATA_DIR` configuration as the API:

   ```powershell
   .\.venv\Scripts\python.exe scripts/prepare_demo.py
   $env:TTS_ENGINE = "piper"
   .\.venv\Scripts\python.exe -c "import os, runpy; os.environ['CP_STUBS']=''; runpy.run_path('scripts/dev.py', run_name='__main__')"
   ```

   On Linux/macOS use `.venv/bin/python` and start the application with
   `CP_STUBS='' TTS_ENGINE=piper .venv/bin/python scripts/dev.py`. These settings
   also keep a newly submitted local analysis live and offline; `.env` otherwise
   defaults to sample stages. A new analysis still needs the installed browser,
   Piper voice and FFmpeg, unlike cached replay. Open:

   - http://localhost:3000/a/bad-checkout
   - http://localhost:3000/a/site1
   - http://localhost:3000/a/site2

   `python scripts/prepare_demo.py --verify-only` checks the caches without
   copying. Existing different artifacts are rejected; use `--force` only when
   intentionally replacing the seven demo artifacts for these three fixed IDs.
   No other analysis directories are touched. `--data-dir PATH` permits a clean
   staging destination for verification. By default staging imports
   `worker.common.DATA_DIR`, including `.env`; it does not assume `data/` when
   the API is configured to serve another directory.
4. Keep `demo/offline-playback.webm` available as a video backup. It records the
   cached dashboards, playback and seeking; it does not claim to record a new
   URL submission or an entire live analysis. A separate full-pitch recording
   can be made by the presenter.
5. After human review/integration, the release owner may tag the final release
   on `main` as `demo`. This preparation task does not create or push a tag.

## Cache contents and integrity

Each of `demo/bad-checkout/`, `demo/site1/` and `demo/site2/` contains exactly the
seven presentation artifacts: `status.json`, `nodes.json`, `events.json`,
`issues.json`, `clip.mp4`, `timeline.json`, `report.json`. The clips are real
H.264/AAC media, not the placeholder in `contracts/samples/`.

`demo/manifest.json` records source URLs, scores, durations, generation time and
SHA-256/byte counts for every artifact. The staging helper validates all sources
before writing, checks IDs/local media URLs, event/timeline alignment, timestamp
references and file integrity. It compares issue `(id, rule, node_id)` identities,
requires a narrated critical finding in each run and enforces the 90-second cap.
Copied files are verified once under temporary filenames before `os.replace`
publishes them atomically. Existing identical files are not recopied, and staged
files are not redundantly rehashed. A modified cache
fails validation rather than silently replacing presentation data. After a new
live capture, copy the seven artifacts from the configured `DATA_DIR` into each
matching cache directory, then regenerate the manifest without hand-editing hashes:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_demo.py --write-manifest
.\.venv\Scripts\python.exe scripts/prepare_demo.py --verify-only
```

Manifest refresh validates the complete set before atomically publishing it.
Never edit a cached score or narration independently.

## Offline verification performed

`demo/verify_offline.py` records repeatable browser evidence in
`demo/verification.json` and updates the backup video. All three cached dashboards
are checked for critical-issue timestamp button seeking, active-card background,
continued MP4 playback and HTTP **206**, with zero external requests and browser
errors. Service workers are disabled. The new public captures support exactly the
same timestamp demonstration as the local checkout.

The evidence explicitly distinguishes an online smoke check from a physical
network-off rehearsal. To run the latter on Windows, first stop existing dev
services on 3000/8000/8080, then run from an **elevated PowerShell**:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File demo/verify_offline.ps1
```

The wrapper captures active physical adapters, starts an independent 60-second
restoration watchdog, disables the adapters, launches the complete stack through
`scripts/dev.py`, checks external TCP connectivity is unavailable, replays all
three demos, and re-enables the adapters in `finally`. The stack's child processes
are cleaned up. Logs remain under `data/offline-physical-test.*` and
`data/offline-stack.log`. An unsuccessful test is not recorded as a successful
physical rehearsal. This requires a Windows UAC administrator approval.

If UAC is unavailable in the automation session, stop the existing dev services,
turn Wi-Fi off manually in Windows, then run this command in a normal PowerShell
window and turn Wi-Fi back on after it finishes:

```powershell
.\.venv\Scripts\python.exe demo/verify_offline.py --require-disconnected --launch-stack
```

This path does not change adapter settings or need administrator rights. It
verifies both zero connected physical adapters and failed external TCP access
at the start and end. The automatic UAC attempt in this session was cancelled
without changing adapter state, so physical acceptance is still pending.

For a nondisruptive smoke check use `python demo/verify_offline.py --launch-stack`;
this does not claim that the host network is offline. Inspect
`host_network_disconnected`, `stack_started_while_disconnected` and
`physical_adapters_up_at_start_and_end` (must be 0) in the evidence before
approving the physical check. The elevated wrapper additionally records
`physical_adapters_disabled`.
The replay path uses only localhost; links to original sites, GitHub and WCAG
documentation need internet if clicked. Do not submit new public-site jobs offline.

Re-run the staging smoke checks:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_demo.py --verify-only
curl.exe -s -o NUL -w "%{http_code}" -H "Range: bytes=0-100" http://localhost:8000/media/bad-checkout/clip.mp4
```

The second command must print `206`. Repeat for `site1` and `site2`.

To regenerate a full capture while online, use the actual pipeline, not stubs:

```powershell
$env:TTS_ENGINE = "piper"
$env:MAX_EVENTS = "40"
.\.venv\Scripts\python.exe -c "import os; os.environ['CP_STUBS']=''; from worker.pipeline import run_pipeline; run_pipeline('bad-checkout', 'http://localhost:8080/bad-checkout.html')"
$env:MAX_EVENTS = "22"
.\.venv\Scripts\python.exe -c "import os; os.environ['CP_STUBS']=''; from worker.pipeline import run_pipeline; run_pipeline('site1', 'https://projects.accesscomputing.uw.edu/au/before.html')"
$env:MAX_EVENTS = "18"
.\.venv\Scripts\python.exe -c "import os; os.environ['CP_STUBS']=''; from worker.pipeline import run_pipeline; run_pipeline('site2', 'https://www.drudgereport.com/')"
```

On Windows PowerShell 5, assigning an empty string removes the environment
variable, allowing `.env`'s `CP_STUBS=all` to take effect again. The Python commands
above explicitly define a genuinely empty variable in the child process; they do
not rely on undocumented pipeline stage names such as `empty` or `none`. No
pipeline algorithm was changed. Scores/content can change when public sites
change. The CERN World Wide Web page was rejected as a target
after a punctuation-only announcement caused Piper to produce no WAV audio;
no backend algorithms were changed to accommodate a particular demo site.

## Live Presentation Scenario
1. Launch `python scripts/dev.py` before taking the stage.
2. Trigger a live analysis targeting `http://localhost:8080/bad-checkout.html` (runs locally, 100% offline).
3. While the live job processes, open `/a/site1` or `/a/site2`, play its cached
   video and click a timestamped critical issue to demonstrate synchronized
   speech and highlighting. The same interaction is available on `/a/bad-checkout`.
4. Return to the live analysis tab to reveal the calculated score and detected keyboard trap.

## Contingency Plan (Plan B)
| Failure Point | Action |
|---|---|
| Internet connectivity lost | Rely strictly on `bad-checkout.html` and cached runs in `demo/` |
| Live analysis subprocess crashes | Open the pre-generated run for `bad-checkout.html` |
| Entire laptop fails | Play the recorded screencast video backup from a phone or backup laptop |
