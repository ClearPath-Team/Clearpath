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
   | [Berkshire Hathaway](https://www.berkshirehathaway.com/) | `site1` | 76 | 9 | 117.363 s | 3.42 s |
   | [Space Jam official 1996 archive](https://www.spacejam.com/1996/) | `site2` | 89 | 4 | 33.974 s | 1.06 s |

   The public targets loaded without cookie dialogs or bot challenges. Berkshire
   illustrates missing page structure/language and definition-list findings;
   Space Jam illustrates missing page structure/language. These structural
   findings have `node_id: null` and `timestamp: null`; the UI correctly labels
   them as absent from the clip. Use the local checkout to demonstrate issue
   timestamp buttons, keyboard-trap detection and active-card highlighting.

2. Install Python/frontend dependencies and Chromium **before** disconnecting.
   For cached playback, the application needs only its local API/frontend and a
   browser supporting H.264/AAC. Verified with Microsoft Edge 156.0.4314.58;
   the bundled Playwright Chromium 130 on this machine lacks those codecs.
   Piper, its voice, FFmpeg and the target websites are not required to replay
   an already cached run.
3. Stage all three caches with the standard-library-only helper:

   ```powershell
   .\.venv\Scripts\python.exe scripts/prepare_demo.py
   $env:CP_STUBS = "empty"
   $env:TTS_ENGINE = "piper"
   .\.venv\Scripts\python.exe scripts/dev.py
   ```

   On Linux/macOS use `.venv/bin/python` and start the application with
   `CP_STUBS=empty TTS_ENGINE=piper .venv/bin/python scripts/dev.py`. These settings
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
   staging destination for verification.
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
references and file integrity, then verifies the staged copies. A modified cache
fails validation rather than silently replacing presentation data. After a new
live capture, refresh the cache and its manifest together; never edit a cached
score or narration independently.

## Offline verification performed

`demo/verification.json` records the browser evidence. A fresh Edge context
blocked every non-loopback HTTP(S) request and disabled service workers. All
three cached dashboards loaded with **zero external requests and zero browser
errors**. Every clip played, accepted a seek and was served with HTTP **206**.
The local checkout's issue timestamp button and active-card background were
verified. The two public pages were tested with native video seeking because
their structural findings have no timestamp buttons.

This is application-level external-network isolation: the workstation's Wi-Fi
adapter was **not** disabled. Before the pitch, the presenter should also perform
a physical Wi-Fi-off rehearsal after installing dependencies. The replay path
uses only localhost; links to original sites, GitHub and WCAG documentation need
internet if clicked. Do not submit a new public-site analysis while offline.

Re-run the staging smoke checks:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_demo.py --verify-only
curl.exe -s -o NUL -w "%{http_code}" -H "Range: bytes=0-100" http://localhost:8000/media/bad-checkout/clip.mp4
```

The second command must print `206`. Repeat for `site1` and `site2`.

To regenerate a full capture while online, use the actual pipeline, not stubs:

```powershell
$env:CP_STUBS = "empty"
$env:TTS_ENGINE = "piper"
.\.venv\Scripts\python.exe -m worker.pipeline bad-checkout http://localhost:8080/bad-checkout.html
.\.venv\Scripts\python.exe -m worker.pipeline site1 https://www.berkshirehathaway.com/
.\.venv\Scripts\python.exe -m worker.pipeline site2 https://www.spacejam.com/1996/
```

On Windows PowerShell 5, assigning an empty string removes the environment
variable, allowing `.env`'s `CP_STUBS=all` to take effect again. The literal
`empty` above explicitly leaves every stage live. Scores/content can change
when public sites change. The CERN World Wide Web page was rejected as a target
after a punctuation-only announcement caused Piper to produce no WAV audio;
no backend algorithms were changed to accommodate a particular demo site.

## Live Presentation Scenario
1. Launch `python scripts/dev.py` before taking the stage.
2. Trigger a live analysis targeting `http://localhost:8080/bad-checkout.html` (runs locally, 100% offline).
3. While the live job processes, open `/a/site1` or `/a/site2` to compare public
   page reports and play their cached video. Switch to `/a/bad-checkout` and click
   a timestamped critical issue to showcase synchronized speech and highlighting.
4. Return to the live analysis tab to reveal the calculated score and detected keyboard trap.

## Contingency Plan (Plan B)
| Failure Point | Action |
|---|---|
| Internet connectivity lost | Rely strictly on `bad-checkout.html` and cached runs in `demo/` |
| Live analysis subprocess crashes | Open the pre-generated run for `bad-checkout.html` |
| Entire laptop fails | Play the recorded screencast video backup from a phone or backup laptop |
