# Hour 1 Checklist

All 4 team members work through this checklist together before starting parallel development tracks.

## Entire Team
- [ ] GitHub repository created, all 4 members have access and have cloned it.
- [ ] Each member has completed `doc/setup/setup.md`, and `python scripts/check_env.py` shows `OK` on the first 7 checks.
- [ ] `python scripts/dev.py` launches and http://localhost:8080/bad-checkout.html opens in the browser.
- [ ] The team has reviewed `doc/1-foundation/data-contracts.md` and agreed on all JSON schemas.
- [ ] Selected 1–2 real demo websites: visible accessibility issues, fast load times, and no aggressive cookie barriers.
- [ ] Each member has created their dedicated branch (see `doc/rules/repo-rules.md`).

## Individual Member Deliverables (Pushed to `main` before hour 1 ends)
- [ ] **M1:** `contracts/samples/nodes.json`
- [ ] **M2:** `contracts/samples/events.json`, `issues.json`, `report.json`
- [ ] **M3:** `contracts/samples/timeline.json`
- [ ] **M4:** `contracts/samples/clip.mp4`, Next.js scaffold in `web/`

## Fast Sample Generation Strategy
M1 authors `nodes.json` manually based on `bad-checkout.html` using the reading order of elements on the page. Other members derive their samples from it: M2 creates events and issues matching the same `node_id` entries, and M3 creates the timeline using the corresponding `seq` values. Values do not need to be mathematically exact, but they must be internally consistent.
