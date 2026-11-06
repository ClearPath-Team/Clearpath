# Demo Presentation Protocol

During the final 2 hours of the hackathon, feature freezes are strictly observed.

## Preparation
1. Run full analyses on `bad-checkout.html` and 2 chosen real public websites. Copy their `data/{id}` directories into `demo/` and record job IDs below:

   | Site | ID | Score |
   |---|---|---|
   | bad-checkout.html | | |
   | Real Demo Site 1 | | |
   | Real Demo Site 2 | | |

2. Before presenting, copy cached runs from `demo/` back into `data/`. The `/a/{id}` route will serve results with zero internet connectivity.
3. Record a screencast video backup demonstrating the complete flow: URL submit, real-time progress, results view, and timestamp seeking.
4. Tag the final release commit on `main` as `demo` (`git tag demo && git push --tags`). No further code modifications after tagging.

## Live Presentation Scenario
1. Launch `python scripts/dev.py` before taking the stage.
2. Trigger a live analysis targeting `http://localhost:8080/bad-checkout.html` (runs locally, 100% offline).
3. While the live job processes, open the pre-generated results dashboard for Real Demo Site 1. Play the video and click a critical issue to showcase synchronized speech and highlight.
4. Return to the live analysis tab to reveal the calculated score and detected keyboard trap.

## Contingency Plan (Plan B)
| Failure Point | Action |
|---|---|
| Internet connectivity lost | Rely strictly on `bad-checkout.html` and cached runs in `demo/` |
| Live analysis subprocess crashes | Open the pre-generated run for `bad-checkout.html` |
| Entire laptop fails | Play the recorded screencast video backup from a phone or backup laptop |
