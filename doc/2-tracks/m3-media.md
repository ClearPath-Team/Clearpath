# Track M3: Voice Synthesis & Video Rendering

## Objective
Convert the sequence of events into a synchronized MP4 video clip where each active element is visually highlighted on screen while its announcement is spoken. In addition to `clip.mp4`, produce `timeline.json` recording the precise start and end time of each event.

## Your Files
`worker/media/tts.py`, `worker/media/record.py`, `worker/media/mix.py`, `worker/media/render.py`, `contracts/samples/timeline.json`

## Function Signature
```python
# worker/media/render.py
def render_clip(url: str, nodes: dict, events: dict, out_dir: Path) -> dict:
    """Writes out_dir/clip.mp4 and returns the timeline dictionary (timeline.json contract)."""
```
**Test Inputs:** `samples/nodes.json` + `samples/events.json` + `http://localhost:8080/bad-checkout.html`.

## Implementation Steps

### 1. Speech Synthesis (`tts.py`)
```python
def synthesize_all(events: list, audio_dir: Path) -> dict[int, tuple[Path, float]]:
    """seq -> (wav_path, duration_seconds)"""
```
Select the TTS engine based on `TTS_ENGINE` from `.env`:

- **`piper`** (default): Load the ONNX model **once** in-process:
  ```python
  from piper import PiperVoice
  voice = PiperVoice.load(PIPER_VOICE)
  with wave.open(str(path), "wb") as wf:
      voice.synthesize_wav(text, wf)
  ```
- **`espeak`** (fallback): `subprocess.run(["espeak-ng", "-v", "ro", "-s", "165", "-w", str(path), text], check=True, timeout=30)`
- **`say`** (macOS only): `subprocess.run(["say", "-v", "Ioana", "--file-format=WAVE", "--data-format=LEI16@22050", "-o", str(path), text], check=True, timeout=30)`

Compute duration using Python's `wave` module: `getnframes() / getframerate()`.

Ensure all generated audio files share the exact same format (mono, 16-bit, 22050 Hz). Convert if needed:
```bash
ffmpeg -y -i in.wav -ac 1 -ar 22050 -sample_fmt s16 out.wav
```

### 2. Live Traversal Recording (`record.py`)
```python
ctx = browser.new_context(viewport=VIEWPORT, record_video_dir=str(out_dir / "raw"),
                          record_video_size=VIEWPORT)
page = ctx.new_page()
t0 = time.monotonic()
open_page(page, url)           # identical page settings as M1
```

1. **Inject DOM Overlays** (via `page.evaluate`):
   - `#cp-hl` (bounding box outline): `position:fixed; pointer-events:none; z-index:2147483647; border:4px solid #ffbf00; box-shadow:0 0 0 4px rgba(0,0,0,.6); border-radius:6px; transition:all .15s; display:none`
   - `#cp-cap` (subtitle caption box): `position:fixed; bottom:24px; left:50%; transform:translateX(-50%); z-index:2147483647; background:rgba(0,0,0,.85); color:#fff; font:600 22px system-ui,sans-serif; padding:10px 18px; border-radius:8px; max-width:80%; text-align:center`
2. Wait 1 second. `t_trim = time.monotonic() - t0` represents the video clip trim offset.
3. **Iterate Events:**
   1. If node has `selector` and `visible`: execute `el.scrollIntoView({block: 'center'})`, wait 250ms, measure `getBoundingClientRect()`, and position `#cp-hl` over the element (adding 4px margin, `display:block`). If element is missing or zero-sized, hide `#cp-hl`.
   2. Set event text into `#cp-cap`.
   3. `start = time.monotonic() - t0 - t_trim`, wait `page.wait_for_timeout(int((duration + 0.35) * 1000))`, then `end = start + duration`.
4. **Finalization:** Wait 1 second, save `video_path = page.video.path()`, then call `ctx.close()`. The video file is only finalized once the browser context is closed.

### 3. Audio/Video Mixing (`mix.py`)
1. **Build `voice.wav`** using `wave` and `array` (or `numpy`): create a blank silence buffer spanning `(last_end + 1.0)` seconds, overlaying each event's audio chunk at its calculated `start` offset.
2. **Export Final MP4:**
   ```bash
   ffmpeg -y -ss {t_trim + VIDEO_OFFSET} -i raw.webm -i voice.wav -map 0:v -map 1:a \
          -c:v libx264 -preset veryfast -pix_fmt yuv420p -c:a aac -b:a 128k -shortest clip.mp4
   ```
   `VIDEO_OFFSET` (default `0.0`, configurable via `.env`) aligns video capture with `t0`. Calibrate visually once: if highlight appears before speech, increase offset.
3. **Determine Duration:**
   ```bash
   ffprobe -v error -show_entries format=duration -of csv=p=0 clip.mp4
   ```

### 4. Timeline Construction & Cleanup
- Output `timeline.json` formatted as: `{duration, clip: "clip.mp4", entries: [{seq, node_id, text, start, end}]}`.
- Remove temporary directories `raw/`, `audio/`, and `voice.wav` unless `KEEP_TMP=1`.

### 5. CLI Testing
```bash
python -m worker.media.render <url> nodes.json events.json <out_dir>
```

## Edge Cases
- **Hidden elements, `visible: false` or `selector: null`:** Hide the highlight box, but keep the subtitle caption and speech narration.
- **Dynamic page content** (carousels, animations): Out of scope for MVP.
- **Maximum duration:** If accumulated audio duration exceeds 95 seconds, truncate trailing events and log the cutoff count.

## Acceptance Criteria
- [ ] Speech narration and visual highlights remain synchronized within ±200ms across the clip.
- [ ] Seeking the player to `entries[k].start` aligns accurately with event `k`.
- [ ] Rendered MP4 plays cleanly across Chrome, Firefox, and Safari (H.264/AAC `yuv420p`).
- [ ] Video rendering for `bad-checkout.html` completes in under 90 seconds.
