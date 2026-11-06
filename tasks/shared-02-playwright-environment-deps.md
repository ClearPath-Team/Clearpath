# Task: [SHARED-02] Playwright Host Environment Setup & Graceful Test Fallbacks

- **Task ID:** `SHARED-02`
- **GitHub Issue:** #13
- **Track:** `Shared` (Infrastructure and team workflow)
- **Type:** `Chore`
- **Priority:** `P1 - current milestone`
- **Status:** `Done`
- **Assignee:** `@AndreiBcs`
- **Branch:** `shared-playwright-deps`
- **Pull Request:** https://github.com/ClearPath-Team/Clearpath/pull/18
- **Created Date:** 2026-11-06

---

## 1. Goal
Ensure developers and CI environments can run live Playwright browser audits and AX-tree extraction reliably by automating dependency installation, enhancing environment diagnostics in `scripts/check_env.py`, and adding graceful test fallbacks for headless runner environments.

---

## 2. Context
During midpoint integration testing on Linux, running `test_audit.py`, `test_cli.py`, and `extract.py` failed with:
```
playwright._impl._errors.Error: BrowserType.launch: 
Host system is missing dependencies to run browsers.
Please install them with: sudo playwright install-deps
```
Missing packages include `libnss3`, `libnspr4`, `libatk1.0-0`, `libatk-bridge2.0-0`, `libcups2`, `libxkbcommon0`, `libxdamage1`, `libpango-1.0-0`, `libcairo2`, `libasound2`, and `libatspi2.0-0`.

While CI runs `sudo apt-get install` in `.github/workflows/ci.yml`, local environments or container subshells often lack these shared libraries or sudo privileges, preventing unit test execution even when Playwright itself is installed in `.venv`.

---

## 3. Scope
- `scripts/check_env.py`
- `worker/engine/test_audit.py`
- `worker/engine/test_cli.py`
- `doc/setup/troubleshooting.md`
- `setup-prompt.md`

**Forbidden:** Modifying shared contracts (`doc/1-foundation/data-contracts.md`, `contracts/selector.js`).

---

## 4. Acceptance Criteria
- [x] `scripts/check_env.py` provides exact apt/brew/winget commands when Chromium launch fails due to missing OS libraries.
- [x] Unit tests requiring live Chromium launch (`test_audit.py` and `test_cli.py`) check browser launchability and skip gracefully with an informative message (`unittest.skipIf`) instead of failing hard with missing shared library exceptions.
- [x] Setup documentation in `doc/setup/troubleshooting.md` and `setup-prompt.md` includes explicit instructions for installing Playwright system dependencies on Ubuntu/Debian/WSL (`sudo playwright install-deps chromium`).

---

## 5. Validation & Test Commands
```bash
# 1. Run environment diagnostics
.venv/bin/python scripts/check_env.py

# 2. Run unit test suite - should pass or cleanly skip without crashing
.venv/bin/python -m unittest discover -s worker/engine -p 'test_*.py'
```

---

## 6. Dependencies
- None.

---

## 7. Out of Scope
- Rewriting Playwright CDP extraction logic in `worker/extract/extract.py`.

---

## 8. Execution Log (Updated by Assignee)
- **Status Change:** `Backlog` -> `Ready` on 2026-11-06
- **Claimed by:** `@AndreiBcs`
- **PR:** https://github.com/ClearPath-Team/Clearpath/pull/18

- **2026-11-06 14:47 UTC:** Claimed by @AndreiBcs (Status -> In progress)
- **2026-11-06 14:50 UTC:** PR opened: https://github.com/ClearPath-Team/Clearpath/pull/18 (Status -> In review)
- **2026-11-06 15:27 UTC:** PR #18 merged into main, Issue #13 closed (Status -> Done)
