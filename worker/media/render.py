"""M3: Piper narration, synchronized highlighted browser frames and MP4 rendering.

Run: python -m worker.media.render URL NODES_JSON EVENTS_JSON OUTPUT_DIR
Requires piper (CLI), ffmpeg, ffprobe, Playwright Chromium and a Romanian voice.
"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from worker.common import SAMPLES, read_json

PAUSE_SECONDS = 0.3
FPS = 12


def _run(args, *, input_text=None):
    try:
       return subprocess.run(
    args,
    input=input_text,
    text=True,
    encoding="utf-8",
    capture_output=True,
    check=True
)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Missing executable: {args[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Command failed: {args[0]}: {exc.stderr[-2000:]}") from exc


def _duration(path):
    with wave.open(str(path), "rb") as wav:
        return wav.getnframes() / wav.getframerate()


# Short enough that no announcement can be lost; absorbs AAC frame (~21ms) and
# last-video-frame rounding in the muxed clip.
CLIP_END_SLACK_SECONDS = 0.1
MAX_CLIP_EXCESS_SECONDS = 1.0


def _probed_duration(probe_stdout: str) -> float:
    """Extracts format.duration from `ffprobe -of json` output, rejecting any
    response that doesn't have the expected structure and types."""
    try:
        data = json.loads(probe_stdout)
    except (TypeError, ValueError):
        raise RuntimeError("ffprobe returned non-JSON output for clip.mp4") from None
    if not isinstance(data, dict) or not isinstance(data.get("format"), dict):
        raise RuntimeError("ffprobe JSON for clip.mp4 has no 'format' object")
    raw = data["format"].get("duration")
    if isinstance(raw, bool) or not isinstance(raw, (str, int, float)):
        raise RuntimeError(f"ffprobe reported no usable duration for clip.mp4: {raw!r}")
    try:
        probed = float(raw)
    except ValueError:
        raise RuntimeError(f"ffprobe reported a non-numeric clip duration: {raw!r}") from None
    if not math.isfinite(probed) or probed <= 0:
        raise RuntimeError(f"ffprobe reported an invalid clip duration: {raw!r}")
    return probed


def _validate_clip_duration(probe_stdout: str, last_event_end: float) -> float:
    """Returns the rendered clip's real duration, raising if clip.mp4 is broken.

    The clip must cover the end of the final announcement, otherwise issue
    timestamps could point past the end of the video. A clip far longer than
    the narration also signals a bad mux. Never substitutes a synthetic value."""
    probed = _probed_duration(probe_stdout)
    if probed + CLIP_END_SLACK_SECONDS < last_event_end:
        raise RuntimeError(
            f"clip.mp4 is truncated: {probed:.3f}s but the last announcement ends at "
            f"{last_event_end:.3f}s")
    if probed - last_event_end > MAX_CLIP_EXCESS_SECONDS:
        raise RuntimeError(
            f"clip.mp4 is {probed:.3f}s, more than {MAX_CLIP_EXCESS_SECONDS}s longer than "
            f"the narration ({last_event_end:.3f}s); render is inconsistent")
    return round(probed, 3)


def _voice_path():
    return Path(os.environ.get("PIPER_MODEL", str(ROOT / "assets/voices/ro_RO-mihai-medium.onnx")))


def _piper_bin() -> str:
    """Resolves the piper executable, falling back to the current venv's bin
    directory when it isn't on PATH (e.g. background subprocesses spawned
    without .venv/bin set). Cross-platform: tries the .exe suffix on Windows."""
    found = shutil.which("piper")
    if found:
        return found
    exe_name = "piper.exe" if os.name == "nt" else "piper"
    candidate = Path(sys.executable).parent / exe_name
    if candidate.is_file():
        return str(candidate)
    raise RuntimeError(f"Missing executable: piper (checked PATH and {candidate})")


def _synthesize(text, output):
    engine = os.environ.get("TTS_ENGINE", "piper").lower()
    if engine != "piper":
        raise RuntimeError(f"Unsupported TTS_ENGINE={engine!r}; configure piper")
    model = _voice_path()
    if not model.is_file():
        raise RuntimeError(f"Piper model not found: {model}")
    _run([_piper_bin(), "--model", str(model), "--output_file", str(output)],
         input_text=text)
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("Piper did not generate audio")
    return _duration(output)


def _draw_overlay(page, node, text):
    # DOM-only overlays: never click, type, or submit on the audited website.
    page.evaluate("""(payload) => {
      let hl = document.getElementById('cp-hl');
      if (!hl) {
        hl = document.createElement('div'); hl.id = 'cp-hl';
        document.documentElement.appendChild(hl);
      }
      Object.assign(hl.style, {
        position:'fixed', pointerEvents:'none', zIndex:'2147483646',
        border:'3px solid #FFD700', boxSizing:'border-box',
        background:'rgba(255,215,0,.10)', display:'none'
      });
      let cap = document.getElementById('cp-cap');
      if (!cap) {
        cap = document.createElement('div'); cap.id = 'cp-cap';
        document.documentElement.appendChild(cap);
      }
      Object.assign(cap.style, {
        position:'fixed', bottom:'16px', left:'10%', width:'80%',
        padding:'12px 16px', boxSizing:'border-box', textAlign:'center',
        background:'rgba(0,0,0,.88)', color:'#fff', font:'bold 24px Arial',
        borderRadius:'8px', zIndex:'2147483647', pointerEvents:'none'
      });
      cap.textContent = payload.text;
      const node = payload.node;
      if (!node) return;
      let rect = null;
      try {
        const el = node.selector ? document.querySelector(node.selector) : null;
        if (el) {
          el.scrollIntoView({block:'nearest', inline:'nearest'});
          rect = el.getBoundingClientRect();
        }
      } catch (_) {}
      if (!rect && node.bbox) {
        const b = node.bbox;
        rect = {x:b.x - window.scrollX, y:b.y - window.scrollY,
                width:b.w, height:b.h};
      }
      if (rect && rect.width > 0 && rect.height > 0) {
        Object.assign(hl.style, {
          display:'block', left:rect.x+'px', top:rect.y+'px',
          width:rect.width+'px', height:rect.height+'px'
        });
      }
    }""", {"node": node, "text": text})


def _concat_file(paths, output):
    # ffmpeg concat demuxer paths must be quoted; temp paths are local.
    with output.open("w", encoding="utf-8") as file:
        for path in paths:
            escaped = str(path.resolve()).replace("'", "'\\''")
            file.write("file '" + escaped + "'\n")


def render_clip(url: str, nodes: dict, events: dict, out_dir: Path) -> dict:
    """Produce clip.mp4 and timeline.json; raise on missing dependencies."""
    from playwright.sync_api import sync_playwright

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe must be installed and on PATH")
    items = events.get("events", [])
    if not isinstance(items, list) or not items:
        raise ValueError("events.json must contain a non-empty events array")
    node_by_id = {n["id"]: n for n in nodes.get("nodes", [])}
    viewport = nodes.get("viewport", {"width": 1280, "height": 720})
    timeline = []
    with tempfile.TemporaryDirectory(prefix="clearpath-m3-") as temp:
        temp = Path(temp)
        audio_files, frame_files, durations = [], [], []
        current = 0.0
        for index, event in enumerate(items):
            spoken = str(event.get("text", "")).strip()
            if not spoken:
                raise ValueError(f"Empty announcement at index {index}")
            wav = temp / f"voice_{index:04d}.wav"
            duration = _synthesize(spoken, wav)
            audio_files.append(wav)
            seq = event.get("seq", index)
            timeline.append({
                "seq": seq,
                "node_id": event.get("node_id"),
                "text": spoken,
                "start": round(current, 3),
                "end": round(current + duration, 3),
            })
            durations.append(duration + (PAUSE_SECONDS if index < len(items)-1 else 0))
            current += durations[-1]

        # Normalize audio before concatenation; avoids mismatched Piper WAV formats.
        normalized = []
        for i, wav in enumerate(audio_files):
            pcm = temp / f"pcm_{i:04d}.wav"
            _run(["ffmpeg", "-y", "-v", "error", "-i", str(wav),
                  "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(pcm)])
            normalized.append(pcm)
        silence = temp / "pause.wav"
        _run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
              "-i", "anullsrc=r=48000:cl=mono", "-t", str(PAUSE_SECONDS),
              "-c:a", "pcm_s16le", str(silence)])
        segments = []
        for i, wav in enumerate(normalized):
            segments.append(wav)
            if i < len(normalized)-1:
                segments.append(silence)
        audio_list = temp / "audio.txt"
        _concat_file(segments, audio_list)
        audio = temp / "narration.wav"
        _run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
              "-i", str(audio_list), "-c:a", "pcm_s16le", str(audio)])

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={
                    "width": int(viewport.get("width", 1280)),
                    "height": int(viewport.get("height", 720)),
                }, device_scale_factor=1)
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                for i, event in enumerate(items):
                    _draw_overlay(page, node_by_id.get(event.get("node_id")),
                                  str(event["text"]))
                    page.wait_for_timeout(80)
                    frame = temp / f"frame_{i:04d}.png"
                    page.screenshot(path=str(frame))
                    frame_files.append(frame)
            finally:
                browser.close()

        # One browser screenshot per event; ffmpeg holds each frame for its
        # narration duration. This is a narrated walkthrough, not live interaction.
        frame_list = temp / "frames.txt"
        with frame_list.open("w", encoding="utf-8") as file:
            for frame, duration in zip(frame_files, durations):
                escaped = str(frame.resolve()).replace("'", "'\\''")
                file.write(f"file '{escaped}'\n")
                file.write(f"duration {duration:.6f}\n")
            last = str(frame_files[-1].resolve()).replace("'", "'\\''")
            file.write(f"file '{last}'\n")
        clip = out_dir / "clip.mp4"
        _run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
              "-i", str(frame_list), "-i", str(audio),
              "-map", "0:v:0", "-map", "1:a:0",
              "-fps_mode", "vfr", "-c:v", "libx264",
              "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
              "-movflags", "+faststart", "-shortest", str(clip)])
        probe = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size",
              "-of", "json", str(clip)])
        clip_duration = _validate_clip_duration(probe.stdout, timeline[-1]["end"])
    result = {"duration": clip_duration, "clip": "clip.mp4", "entries": timeline}
    (out_dir / "timeline.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080/bad-checkout.html"
    nodes_path = sys.argv[2] if len(sys.argv) > 2 else str(SAMPLES / "nodes.json")
    events_path = sys.argv[3] if len(sys.argv) > 3 else str(SAMPLES / "events.json")
    out = Path(sys.argv[4]) if len(sys.argv) > 4 else Path("data/dev")
    print(json.dumps(render_clip(url, read_json(nodes_path),
                                 read_json(events_path), out),
                     indent=2, ensure_ascii=False))
