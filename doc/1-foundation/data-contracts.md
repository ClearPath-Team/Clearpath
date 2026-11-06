# Data Contracts

> **Single Source of Truth** for data formats exchanged between modules. A contract may only be modified following the procedure in `doc/rules/repo-rules.md`.

All entities are linked via `node_id`. The association with the real DOM is established via `selector`, generated **exclusively** with `contracts/selector.js`. The function is deterministic: the same element always produces the identical selector across any component.

| File | Produced by | Consumed by | Test Sample |
|---|---|---|---|
| `nodes.json` | M1 `extract` | M2, M3 | `contracts/samples/nodes.json` |
| `events.json` | M2 `build_events` | M3 | `contracts/samples/events.json` |
| `issues.json` | M2 `run_audit` | M2 `build_report` | `contracts/samples/issues.json` |
| `timeline.json` | M3 `render_clip` | M2 `build_report` | `contracts/samples/timeline.json` |
| `report.json` | M2 `build_report` | API, Frontend | `contracts/samples/report.json` |
| `status.json` | API + pipeline | API, Frontend | (no sample required) |
| `clip.mp4` | M3 `render_clip` | Frontend | `contracts/samples/clip.mp4` |

## nodes.json

```json
{
  "url": "http://localhost:8080/bad-checkout.html",
  "title": "Finalizează comanda",
  "viewport": { "width": 1280, "height": 720 },
  "nodes": [
    {
      "id": "n12",
      "order": 12,
      "role": "button",
      "name": "",
      "level": null,
      "states": { "required": false, "checked": null, "expanded": null, "disabled": false },
      "value": null,
      "list_size": null,
      "focusable": true,
      "parent": "n1",
      "selector": "#cart",
      "bbox": { "x": 1040, "y": 22, "w": 32, "h": 32 },
      "visible": true
    }
  ],
  "focus_order": [
    { "node_id": "n3", "selector": "html > body:nth-of-type(1) > header:nth-of-type(1) > nav:nth-of-type(1) > a:nth-of-type(1)" },
    { "node_id": "n12", "selector": "#cart" }
  ],
  "focus_trap": null
}
```

- `id` = `n{order}`. `order` represents linear reading order, starting at 0 with no gaps.
- `role` must take a normalized value: `heading`, `link`, `button`, `textbox`, `checkbox`, `radio`, `combobox`, `image`, `list`, `banner`, `navigation`, `main`, `contentinfo`, `region`, `form`, `search`, `complementary`, `text`.
- `level` is populated only for `heading` (1–6). `list_size` is populated only for `list`.
- `states.checked` can be `true`, `false`, `"mixed"`, or `null`.
- `bbox` uses document coordinates (including scroll offsets) in CSS pixels, or `null`.
- `focus_trap` is `null` or `{ "node_id": "n18" | null, "selector": "#promo" }`.

## events.json

```json
{
  "lang": "ro",
  "events": [
    { "seq": 0, "node_id": null,  "text": "Pagina Finalizează comanda" },
    { "seq": 1, "node_id": "n13", "text": "Titlu nivel 1, Finalizează comanda" },
    { "seq": 2, "node_id": "n12", "text": "Buton" }
  ]
}
```

- `seq` starts at 0 with no gaps. The list contains at most `MAX_EVENTS` (40) events.
- `node_id` is `null` only for the introductory page title announcement.

## issues.json

```json
[
  {
    "id": "i1",
    "rule": "button-name",
    "severity": "critical",
    "node_id": "n12",
    "selector": "#cart",
    "title": "Butonul nu are nume accesibil",
    "recommendation": "Adaugă un text vizibil sau un atribut aria-label care descrie acțiunea butonului.",
    "help_url": "https://dequeuniversity.com/rules/axe/4.10/button-name"
  }
]
```

- `severity` takes values `critical`, `serious`, `moderate`, or `minor` (matching axe `impact` levels).
- `rule` is the axe rule identifier. The only custom rule is `keyboard-trap` (which has `help_url: null`).
- `node_id` is `null` if the violation could not be mapped to an accessibility tree node.

## timeline.json

```json
{
  "duration": 84.2,
  "clip": "clip.mp4",
  "entries": [
    { "seq": 0, "node_id": null,  "text": "Pagina Finalizează comanda", "start": 1.0, "end": 2.6 },
    { "seq": 2, "node_id": "n12", "text": "Buton",                      "start": 9.8, "end": 10.4 }
  ]
}
```

- Contains exactly one entry per event. `start` and `end` are measured in seconds from the beginning of `clip.mp4`.

## report.json

```json
{
  "id": "a7f3c2d1",
  "url": "http://localhost:8080/bad-checkout.html",
  "title": "Finalizează comanda",
  "score": 38,
  "counts": { "critical": 4, "serious": 3, "moderate": 1, "minor": 0 },
  "clip_url": "/media/a7f3c2d1/clip.mp4",
  "duration": 84.2,
  "focus_trap": true,
  "issues": [ { "...": "fields from issues.json", "timestamp": 9.8 } ]
}
```

- `timestamp` is the `start` second of the first timeline entry with matching `node_id`. It is `null` if the element is not featured in the video.
- Issues are ordered by severity (`critical`, `serious`, `moderate`, `minor`), then by `timestamp` (placing `null` entries last).

## status.json

```json
{ "id": "a7f3c2d1", "url": "...", "status": "rendering", "error": null, "updated_at": "2026-11-06T14:02:11Z" }
```

- `status` can be `queued`, `extracting`, `analyzing`, `rendering`, `done`, or `failed`.
- `error` is a short summary string populated only when `status` is `failed`.

## Scoring Formula

```
score = 100
for each issue except keyboard-trap:
    score -= weight[issue.severity]
    weights: critical = 10, serious = 5, moderate = 2, minor = 1
if keyboard-trap exists in issues or nodes.focus_trap is flagged:
    score -= 15    (once, independently of trap severity or count)
score = max(0, round(score))
```

There is no per-rule cap. A keyboard trap is excluded from severity deductions,
so its penalty is never counted twice. The `counts` still include every issue,
including the synthetic critical `keyboard-trap` finding.

The eight findings in `contracts/samples/issues.json` produce score **38**:
`100 - (3 * 10) - (3 * 5) - (1 * 2) - 15 = 38`. The live demo has an additional
serious `color-contrast` finding and scores **33** with nine findings. Live scores
are calculated from detected findings, not fixed to a page URL.

This policy supersedes the previous 10/6/3/1 weights and per-rule cap; see
[M2-02 in the decision log](../decisions/decision-log.md#integration-issues).

## Shared Files

### contracts/selector.js

Contains a single anonymous arrow function without a trailing semicolon, injected as text into pages. Accepts a DOM element or text node and returns a deterministic unique CSS selector: `#id` if unique, otherwise a hierarchical `tag:nth-of-type(n)` chain.

Usage in Python:
```python
from worker.common import SELECTOR_JS
# On a live element with Playwright:
sel = page.evaluate("(" + SELECTOR_JS + ")(document.activeElement)")
# Inside a CDP Runtime.callFunctionOn context where `this` is the node:
fn = "function(){ return (" + SELECTOR_JS + ")(this); }"
```

### worker/common.py

Reads `.env` and exports: `ROOT`, `DATA_DIR`, `SAMPLES`, `SELECTOR_JS`, `AXE_PATH`, `PIPER_VOICE`, `TTS_ENGINE`, `VIEWPORT` (1280×720), `MAX_EVENTS`, `VIDEO_OFFSET`, `KEEP_TMP`, `TEST_URL`, `read_json()`, `write_json()`, `now_iso()`. Never duplicate these utilities across modules.

### contracts/samples/

Every team member creates their contract mock test sample in hour 1. Samples should feature 8–12 nodes or events matching `test-site/bad-checkout.html`. Must contain at least one `critical` issue with a valid `timestamp` and at least one with `timestamp: null`. The mock `clip.mp4` is generated with the ffmpeg command from `doc/setup/setup.md`, step 7.
