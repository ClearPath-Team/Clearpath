# Troubleshooting & Known Issues

## Installation

| Issue | Solution |
|---|---|
| `python -m playwright install chromium` succeeds, but Chromium fails to start on Linux | Run `python -m playwright install-deps chromium` (requires sudo privileges) |
| `Executable doesn't exist` with Playwright | You did not run `python -m playwright install chromium` inside the **same** active `.venv` |
| `pip install piper-tts` fails | Verify your Python version (3.11 or 3.12). If issues persist: temporarily remove `piper-tts` from `requirements.txt` locally (do not commit) and set `TTS_ENGINE=espeak` (install `espeak-ng`: `brew install espeak-ng` / `sudo apt install espeak-ng`) or `TTS_ENGINE=say` on macOS |
| `fetch_assets.py` cannot download the voice (Hugging Face blocked or 404) | Manually download `ro_RO-mihai-medium.onnx` and `ro_RO-mihai-medium.onnx.json` from https://huggingface.co/rhasspy/piper-voices/tree/main/ro/ro_RO/mihai/medium into `assets/voices/`. Alternatively, switch to `TTS_ENGINE=espeak` or `say` |
| `fetch_assets.py` fails to download axe-core | The script attempts jsdelivr, unpkg, and npm. If all fail: run `npm install axe-core@4.10.2` anywhere and copy `node_modules/axe-core/axe.min.js` to `assets/` |
| `ffmpeg` not found on Windows after `winget` | Close and reopen your terminal. Verify with `ffmpeg -version` |
| PowerShell refuses to activate `.venv` | Execute `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |

## Execution & Runtime

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'worker'` | Run commands from the **root** of the repo with `python -m ...`, not using the relative file path |
| Port 8080, 8000, or 3000 is occupied | Terminate the existing process (`lsof -i :8000` on macOS/Linux, `netstat -ano \| findstr 8000` on Windows) or change the port in `scripts/dev.py` |
| Analysis stays stuck at `queued` | The pipeline subprocess crashed on startup. Inspect `data/{id}/pipeline.log` |
| Analysis status is `failed` | The summary error message is in `data/{id}/status.json`; full trace details are in `data/{id}/pipeline.log` |
| Frontend cannot reach the API (CORS or "failed to fetch") | The API must run on `:8000`, and `web/.env.local` must specify `NEXT_PUBLIC_API_URL=http://localhost:8000`. After editing `.env.local`, restart `npm run dev` |
| Video jumping/seeking to timestamps fails | The API must return HTTP `206 Partial Content` in response to the `Range` header (see `doc/2-tracks/m4-app.md`) |
| On a live website, only a cookie banner is read | Apply the optional Step 9 in `doc/2-tracks/m1-extract.md` to dismiss cookie dialogs, or choose another demo website |
