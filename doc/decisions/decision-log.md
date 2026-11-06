# Decision Log (ADR)

Every decision that alters a technology choice, data contract, or core product behavior is logged here: latest entry at the top, including date and rationale.

## Decisions

| Date | Decision | Rationale |
|---|---|---|
| 2026-11-06 | No Docker and no Redis; each analysis runs as an independent Python subprocess spawned by the API | Minimal setup overhead, single-command startup, easier local debugging during a hackathon |
| 2026-11-06 | Single unified Python virtual environment (`requirements.txt`) for both API and worker | Prevents duplicate dependencies and virtual environment divergence |
| 2026-11-06 | Python across the entire backend (FastAPI + Playwright Python) | Single backend programming language; native support for Piper and axe-core evaluation |
| 2026-11-06 | Piper with `ro_RO-mihai-medium` voice, with `espeak` / `say` as fallbacks | Local, offline, high quality, zero API key dependencies |
| 2026-11-06 | Announcements follow Romanian NVDA screen reader conventions | Matches the real assistive experience of blind Romanian users on the web |
| 2026-11-06 | Recommendations generated from curated templates; LLMs kept as optional stretch goal | Zero external network/API rate-limit vulnerabilities during live presentations |
| 2026-11-06 | Single page analysis per run, capped at 40 announcements (~90s video) | Feasible within hackathon constraints; produces concise, digestible video clips |
| 2026-11-06 | `LabelText` nodes in the Chrome AX tree are omitted from reading traversal | Form control labels are already incorporated into accessible names; otherwise text is announced twice (verified on test site) |

## Integration Issues

| Date | Issue | Owner | Status |
|---|---|---|---|
| | | | |
