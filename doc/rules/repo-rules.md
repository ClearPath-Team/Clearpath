# Repository Rules & Collaboration Guidelines

## Git Branches
| Branch | Owner | Purpose |
|---|---|---|
| `main` | Team (Integration) | Stable branch; only merges and approved shared changes |
| `m1-extract` | Member 1 | Extraction, CDP, Tab walk, check_env |
| `m2-engine` | Member 2 | Announcement rules, axe audit, report, score |
| `m3-media` | Member 3 | Piper TTS, Playwright video recording, ffmpeg mixing |
| `m4-app` | Member 4 | Pipeline orchestrator, FastAPI backend, Next.js frontend |

Merging into `main` happens at three predefined milestones: end of hour 1 (mock samples), midpoint checkpoint, and final integration. Before merging, always run `git pull origin main` into your branch.

## File Ownership
Each member modifies **only** their assigned files to eliminate merge conflicts.

| Member | Assigned Files |
|---|---|
| M1 | `worker/extract/`, `scripts/check_env.py`, `scripts/fetch_assets.py`, `contracts/samples/nodes.json` |
| M2 | `worker/engine/`, `contracts/samples/events.json`, `issues.json`, `report.json` |
| M3 | `worker/media/`, `contracts/samples/timeline.json` |
| M4 | `worker/pipeline.py`, `api/`, `web/`, `scripts/dev.py`, `demo/`, `contracts/samples/clip.mp4` |
| Shared (Requires Team Consensus) | `contracts/selector.js`, `worker/common.py`, `requirements.txt`, `.env.example`, `test-site/`, `CLAUDE.md`, `README.md`, `doc/1-foundation/` |

Track documentation (`doc/2-tracks/mX-*.md`) can be freely updated by its owner (e.g., adding implementation notes or verified behaviors).

## Contract Modification Procedure
1. Notify the team on chat: explain what needs changing and why.
2. Obtain confirmation from all teammates.
3. Update in a single commit directly on `main`: `doc/1-foundation/data-contracts.md` + the affected sample in `contracts/samples/` + a new entry in `doc/decisions/decision-log.md`.
4. All teammates pull `main` (`git pull origin main`) and adapt their modules.

## New Dependencies
Any new Python package must be added to `requirements.txt` with a pinned version (`package==x.y.z`) and announced to the team, as everyone shares the unified environment. Dependencies inside `web/` belong exclusively to Track M4.

## Commit Guidelines
- Commit message format: `[m1] extract: handle LabelText nodes`. Prefix with `[m1]`/`[m2]`/`[m3]`/`[m4]`, or `[all]` for shared files.
- Commit messages and code comments must be written in **English**.
- Create small, focused commits. Never commit code that breaks service startup.

## Files Excluded from Git
`.env`, `.venv/`, `data/`, `assets/`, `node_modules/`, `.next/`, `raw/`, `.local/` (already present in `.gitignore`). Never commit API keys or sensitive credentials.

## Documentation Placement
- All documentation belongs in `doc/`, inside the appropriate subfolder per the map in `CLAUDE.md`.
- Only `CLAUDE.md` and `README.md` reside in the repository root.
- All documentation files must use `kebab-case.md` naming.

## Language & Localization Policy (Joint English + Romanian)
- **English MUST be used everywhere across the repository:** Code, variables, functions, comments, docstrings, git commit messages, documentation, and agent communications are written in English.
- **The Demo Site is Romanian:** The offline demo website (`test-site/bad-checkout.html`) is authored in Romanian and **MUST remain in Romanian**.
- Correspondingly, screen-reader speech announcement strings (NVDA Romanian patterns) and localized recommendation messages targeting Romanian web pages remain in Romanian.
