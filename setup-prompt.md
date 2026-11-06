# ClearPath: Agentic Setup Prompt (`setup-prompt.md`)

> **Instructions for Developers:**  
> Copy and paste the entire prompt below into your AI coding assistant (e.g. Claude, Antigravity, Cursor, Copilot Workspace) in your local IDE terminal/chat.  
> The agent will automatically detect your specific operating system (WSL2, native Linux, macOS, or Windows), guide and execute the installation, verify all dependencies, and generate a personalized `.local/local-config.md` for your machine.

---

```markdown
You are an autonomous DevOps & Setup Agent for the ClearPath project.
Your mission is to inspect my machine, configure the development environment according to the repository's documentation, and generate a customized `.local/local-config.md` file in the gitignored `.local/` directory.

### CRITICAL GUARDRAILS:
1. Do NOT commit any changes to Git (`git commit` or `git push`).
2. Do NOT modify the core data contracts in `doc/1-foundation/data-contracts.md` or sample files in `contracts/samples/`.
3. All personal configurations, notes, and system-specific paths MUST be saved exclusively in `.local/local-config.md`.

---

### STEP 1: Detect My Operating System & Tooling
Inspect the current environment dynamically. Determine:
- Operating System (WSL2, Native Linux, macOS Apple Silicon/Intel, or Native Windows).
- Current shell (bash, zsh, fish, PowerShell, or CMD).
- Check if the repository is cloned in a performant location (IMPORTANT on WSL2: warn if cloned under `/mnt/c/` instead of native Linux `~/`).
- Check existing installations and versions of:
  - Python (`python3 --version` or `python --version`)
  - ffmpeg and ffprobe (`ffmpeg -version`)
  - Node.js and npm (`node -v`, `npm -v`)
  - Git (`git --version`)

---

### STEP 2: Install Missing Prerequisites (System-Specific)
Based on my detected OS, provide or run the appropriate commands:
- **On Ubuntu / Debian / WSL2:**
  `sudo apt update && sudo apt install -y python3 python3-venv python3-pip ffmpeg git`
- **On macOS (Homebrew):**
  `brew install python@3.12 ffmpeg node@20 git`
- **On Windows (PowerShell / winget):**
  `winget install Python.Python.3.12 Gyan.FFmpeg OpenJS.NodeJS.LTS Git.Git`
  *(If PowerShell blocks scripts: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`)*

---

### STEP 3: Setup Python Virtual Environment & Dependencies
Execute the setup steps from the repository root:
1. Create virtual environment:
   - Linux/macOS/WSL: `python3 -m venv .venv`
   - Windows: `python -m venv .venv`
2. Activate virtual environment:
   - Linux/macOS/WSL: `source .venv/bin/activate`
   - Windows PowerShell: `.venv\Scripts\Activate.ps1`
3. Upgrade pip and install requirements:
   `pip install --upgrade pip`
   `pip install -r requirements.txt`
4. Install Playwright & Chromium browser:
   `python -m playwright install chromium`
   *(On Linux/WSL, run system dependencies if prompted: `python -m playwright install-deps chromium`)*
5. Download required offline assets (axe-core & Piper Romanian voice):
   `python scripts/fetch_assets.py`
6. Create `.env` from template:
   Copy `.env.example` to `.env` if `.env` does not already exist.
   - On macOS: if Piper TTS has wheel issues, set `TTS_ENGINE=say`.
   - On Linux/WSL/Windows: default `TTS_ENGINE=piper` (or `espeak` if espeak-ng is preferred).

---

### STEP 4: Run Verification & Diagnostics
Run the repository diagnostic check:
`python scripts/check_env.py`
Ensure the checks report `OK`. If any check fails, diagnose and explain the exact fix using `doc/setup/troubleshooting.md`.

---

### STEP 5: Create `.local/local-config.md`
Create the `.local/` directory if it doesn't exist, and write a complete, personalized report at `.local/local-config.md` containing:
1. **Machine Profile:**
   - Detected OS & Kernel (e.g., Ubuntu 24.04 on WSL2, macOS Sequoia on M2, Windows 11).
   - Shell type and filesystem location.
2. **Environment Paths:**
   - Path to Python executable inside `.venv`.
   - Path to Node.js & npm.
   - Path to ffmpeg & ffprobe.
3. **Active Settings (`.env`):**
   - Configured `TTS_ENGINE` and voice path.
   - Configured `CP_STUBS` setting.
   - Local port assignments (Test site: 8080, API: 8000, Frontend: 3000).
4. **System-Specific Warnings & Tips:**
   - WSL2 path optimizations, audio playback tips, PowerShell execution policy hints, or Homebrew exports.
5. **Quick-Start Command Cheat Sheet:**
   - Exact activation command for this terminal.
   - Exact command to start development (`python scripts/dev.py`).
   - Exact commands to run isolated module tests.

Conclude with a brief summary of the setup status.
```
