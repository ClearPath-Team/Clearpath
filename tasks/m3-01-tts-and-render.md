# Task: [M3-01] Piper Voice Synthesis, Video Recording & Timeline Generation

- **Task ID:** `M3-01`
- **GitHub Issue:** #3
- **Track:** `M3` (TTS, recording, and media rendering)
- **Type:** `Feature`
- **Priority:** `P1 - current milestone`
- **Status:** `Ready`
- **Assignee:** `@andreiBirsanIoan`
- **Branch:** `m3-tts-render`
- **Created Date:** 2026-11-06

---

## 1. Goal
Implement live Romanian voice synthesis with Piper TTS (`ro_RO-mihai-medium.onnx`), browser video recording with animated yellow highlight box (`#cp-hl`) and subtitles (`#cp-cap`), and ffmpeg muxing to produce `clip.mp4` and `timeline.json`.

---

## 2. Context
Track M3 turns abstract accessibility events into a synchronized sensory video.
Currently `worker/media/render.py` is a stub copying `contracts/samples/clip.mp4` and `timeline.json`.
For live generation:
- For each announcement in `events.json`, Piper synthesizes a WAV audio segment.
- Exact durations and start/end offsets are tracked in `timeline.json`.
- The browser page is animated with high-contrast yellow outline (`#cp-hl`, 3px solid #FFD700) matching each element's bounding rect while subtitles display the Romanian announcement text (`#cp-cap`).
- Playwright records screen or canvas frames.
- ffmpeg combines the concatenated audio track with video frames into an H.264/AAC MP4 playable in HTML5 video players.

---

## 3. Scope (Strict Boundary)
The agent is **only** permitted to modify files in `worker/media/`:
- `worker/media/render.py`

**Forbidden:** Modifying `worker/extract/`, `worker/engine/`, `api/`, `web/`, or core contracts.

---

## 4. Acceptance Criteria
- [ ] Synthesizes all events using `assets/voices/ro_RO-mihai-medium.onnx` (or fallback engine configured in `TTS_ENGINE`).
- [ ] Concatenates individual audio clips with 300ms pause between announcements.
- [ ] Generates `timeline.json` recording `node_id`, `event_id`, `start_sec`, and `end_sec` for each item.
- [ ] Injects high-contrast visual focus frame `#cp-hl` and subtitle bar `#cp-cap` during video capture.
- [ ] Invokes `ffmpeg` to produce a web-compatible `clip.mp4` (`yuv420p`, `libx264`, `aac`, with `+faststart` flag).
- [ ] `clip.mp4` can be probed with `ffprobe` and played in standard browsers.

---

## 5. Validation & Test Commands
```bash
# 1. Ensure test-site is running
python -m http.server 8080 --directory test-site &

# 2. Run media rendering module
python -m worker.media.render http://localhost:8080/bad-checkout.html contracts/samples/nodes.json contracts/samples/events.json data/dev

# 3. Validate video and timeline output
node -e "
const tl = JSON.parse(fs.readFileSync('data/dev/timeline.json'));
assert(Array.isArray(tl.timeline), 'timeline array missing');
assert(tl.timeline.length > 0, 'timeline is empty');
console.log('Timeline validated with ' + tl.timeline.length + ' synchronized events.');
"

# 4. Verify MP4 validity
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 data/dev/clip.mp4
```

---

## 6. Dependencies
- `assets/voices/ro_RO-mihai-medium.onnx`
- `ffmpeg` & `ffprobe` (in PATH)

---

## 7. Out of Scope
- Modifying speech texts (M2 responsibility).
- Web player styling (M4 responsibility).

---

## 8. Execution Log (Updated by Assignee)
- **Status Change:** `Backlog` -> `Ready` on 2026-11-06
- **Claimed by:** *None*
- **PR:** *None*
