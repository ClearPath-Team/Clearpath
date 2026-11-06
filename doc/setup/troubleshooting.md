# Troubleshooting & Known Issues

## Installation

| Issue | Solution |
|---|---|
| `python -m playwright install chromium` succeeds, but Chromium fails to start on Linux | Run `sudo .venv/bin/python -m playwright install-deps chromium` (requires root/sudo; see below) |
| `Executable doesn't exist` with Playwright | You did not run `python -m playwright install chromium` inside the **same** active `.venv` |
| `pip install piper-tts` fails | Verify your Python version (3.11 or 3.12). If issues persist: temporarily remove `piper-tts` from `requirements.txt` locally (do not commit) and set `TTS_ENGINE=espeak` (install `espeak-ng`: `brew install espeak-ng` / `sudo apt install espeak-ng`) or `TTS_ENGINE=say` on macOS |
| `fetch_assets.py` cannot download the voice (Hugging Face blocked or 404) | Manually download `ro_RO-mihai-medium.onnx` and `ro_RO-mihai-medium.onnx.json` from https://huggingface.co/rhasspy/piper-voices/tree/main/ro/ro_RO/mihai/medium into `assets/voices/`. Alternatively, switch to `TTS_ENGINE=espeak` or `say` |
| `fetch_assets.py` fails to download axe-core | The script attempts jsdelivr, unpkg, and npm. If all fail: run `npm install axe-core@4.10.2` anywhere and copy `node_modules/axe-core/axe.min.js` to `assets/` |
| `ffmpeg` not found on Windows after `winget` | Close and reopen your terminal. Verify with `ffmpeg -version` |
| PowerShell refuses to activate `.venv` | Execute `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |

## Playwright host dependencies and test fallbacks

The browser download and OS shared libraries are separate requirements. On
Ubuntu/Debian/WSL, install both from the repository root:

```bash
sudo apt-get update
sudo .venv/bin/python -m playwright install-deps chromium
.venv/bin/python -m playwright install chromium
```

With the virtual environment activated, `sudo playwright install-deps chromium`
also works if sudo can find the same environment's CLI. The explicit interpreter
above avoids sudo PATH differences. For CI or a new container, use the combined
command `.venv/bin/python -m playwright install --with-deps chromium`.
Playwright selects the appropriate apt packages for supported Linux versions,
including the NSS, GTK/ATK, Pango, Cairo and audio libraries. A successful browser
download alone does not install those libraries.

If root/sudo is unavailable, ask the host or container maintainer to install the
dependencies in the same host/container that runs Python. Installation in another
container or shell environment may not fix this runner. Do not run Linux apt
commands on macOS or native Windows. Use these platform prerequisites if Python
is missing, then install Chromium with the project's virtual environment:

```bash
# macOS (Homebrew); install Python only if missing
brew install python@3.12
.venv/bin/python -m playwright install chromium
```

```powershell
# Native Windows; install Python only if missing
winget install --id Python.Python.3.12 --exact
.\.venv\Scripts\python.exe -m playwright install chromium
```

Keep the browser installation and tests under the same user/cache and on an OS
supported by the pinned Playwright version. `python scripts/check_env.py` prints
platform-specific installation commands and exits nonzero if Chromium cannot
launch; it never installs OS packages automatically.

The browser-dependent tests in `test_audit.py` and `test_cli.py` probe Chromium
once per test process and use `unittest.skipIf` with a remediation message for
known missing-browser or shared-library failures. Pure mapping, speech, report
and non-browser CLI tests still run. Audit failures after a successful launch
and unexpected browser crashes remain failures. A green suite with skipped live
tests does **not** certify the environment for live analyses. After installing
dependencies, rerun diagnostics and confirm that the live tests run without skips:

```bash
python scripts/check_env.py
python -m unittest discover -s worker/engine -p 'test_*.py' -v
```

See [Playwright's system dependency installation documentation](https://playwright.dev/python/docs/browsers#install-system-dependencies).

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
