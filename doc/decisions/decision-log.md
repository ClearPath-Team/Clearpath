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
| 2026-11-06 | M3-02 / #12: canonical timeline.json schema {duration, clip, entries} and venv piper path | M3 | Resolved (via PR #16) |
| 2026-11-06 | SHARED-02 / #13: Playwright host OS dependencies and graceful headless test fallbacks | Shared | Resolved (via PR #18) |
| 2026-11-06 | M4-02 / #17: fix frontend dashboard severity filter, CSS highlights and untrack .env.local | M4 | Resolved (via PR #19) |
| 2026-11-06 | M2-02 / #11: reconcile implemented scoring, contract documentation and sample report | M2 | Adopted (via PR #14); details below |

### M2-02: One scoring policy for live and sample reports

- **Decision:** Adopt Option B from [issue #11](https://github.com/ClearPath-Team/Clearpath/issues/11), retaining the policy explicitly selected during M2-01: deduct **10/5/2/1** for each critical/serious/moderate/minor axe finding, with **no per-rule cap**. Deduct **15 once** when a keyboard trap is present in issues or flagged in nodes. Exclude keyboard-trap issues from severity deductions and clamp the result at zero.
- **Rationale:** Keep the selected and tested live behavior while eliminating conflicting formulas and stale mock scores. The prior 10/6/3/1 weights with a per-rule cap and the illustrative score of 28 are superseded in the editable contract and PRD. This entry records the selected policy; shared documentation changes remain subject to PR review.
- **Sample arithmetic:** Three axe critical findings, three serious findings, one moderate finding and one trap yield `100 - 30 - 15 - 2 - 15 = 38`. Counts still include the synthetic critical trap: critical 4, serious 3, moderate 1, minor 0.
- **Live distinction:** The current axe-core 4.10.2 demo audit has an extra serious contrast finding: nine findings score **33**. Scores depend on actual findings, not a fixed target of 28 or 38 for a URL.
- **Affected artifacts:** `worker/engine/report.py`, its regression tests, `contracts/samples/report.json`, `doc/1-foundation/data-contracts.md`, `doc/PRD.md`, Track M2 acceptance criteria and the end-to-end integration checklist. Existing archived PDF material is superseded for scoring by this decision and the editable scoring contract.
- **Regression protection:** Tests compare calculated and generated report scores with the sample, verify each severity weight, apply a trap penalty only once, and ensure repeated violations have no per-rule cap. No schema fields, detection rules, announcements or TTS behavior change.
