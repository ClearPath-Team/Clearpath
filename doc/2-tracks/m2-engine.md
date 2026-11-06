# Track M2: Announcement Engine, Audit & Reporting

## Objective
Build three core functions: convert extracted nodes into spoken screen reader text (`events.json`), execute the in-browser accessibility audit with axe-core (`issues.json`), and assemble the final report including calculated accessibility score and timestamp mappings (`report.json`).

## Your Files
`worker/engine/events.py`, `worker/engine/audit.py`, `worker/engine/report.py`, `worker/engine/recommendations.py`, `contracts/samples/events.json`, `contracts/samples/issues.json`, `contracts/samples/report.json`

## Function Signatures
```python
# worker/engine/events.py
def build_events(nodes: dict) -> dict: ...
# worker/engine/audit.py
def run_audit(url: str, nodes: dict) -> list[dict]: ...
# worker/engine/report.py
def build_report(analysis_id: str, url: str, nodes: dict, issues: list, timeline: dict) -> dict: ...
```

## A. Announcement Engine (`events.py`)
Develop against `contracts/samples/nodes.json`.

1. **First event** is always `Pagina {title}` (or localized title), with `node_id: null`.
2. **Node Speech Translation**, iterating nodes in `order`. Omit missing attributes:

| Role | Announcement Pattern (Romanian screen-reader conventions) |
|---|---|
| heading | `Titlu nivel {level}, {name}` |
| link | `Link, {name}`; if unnamed: `Link` |
| button | `Buton, {name}`; if unnamed: `Buton` |
| textbox | `{name}, câmp de editare[, obligatoriu][, conține {value}]`; if unnamed: `Câmp de editare[, obligatoriu]` |
| checkbox | `{name}, casetă de bifare, bifată` / `nebifată` |
| radio | `{name}, buton radio, selectat` / `neselectat` |
| combobox | `{name}, listă derulantă[, {value}]` |
| image | `Imagine, {name}`; if unnamed: `Imagine fără descriere` |
| list | `Listă cu {list_size} elemente` |
| banner | `Reper antet` |
| navigation | `Reper navigare` |
| main | `Reper conținut principal` |
| contentinfo | `Reper subsol` |
| search | `Reper căutare` |
| form | `Reper formular` |
| region | `Regiune, {name}` |
| complementary | `Reper complementar` |
| text | Text content truncated to 12 words (appending `...` if truncated) |

   - If `states.disabled` is true, append `, indisponibil`.
   - If `states.expanded` is true, append `, extins`; if false, append `, restrâns`.
3. **Static Text Condensation:** Consecutive `text` nodes sharing the same `parent` are merged into a single event and truncated to 12 words. `node_id` is assigned from the first node in the sequence. After 2 consecutive `text` events, subsequent `text` nodes are skipped until another role appears.
4. **Event Capping:** Cap at `MAX_EVENTS` (40). Ensure unnamed interactive elements (`button`, `link`, `image`, `textbox`) among the first 80 nodes are not discarded by replacing trailing static text events with these nodes, maintaining relative reading order.
5. **Renumbering:** Reassign `seq` starting from 0 sequentially.

## B. Accessibility Audit (`audit.py`)
Develop against `http://localhost:8080/bad-checkout.html`.

1. Open the page matching M1 settings (`open_page`), using a dedicated browser context.
2. Inject axe-core and run violations audit:
   ```python
   page.add_script_tag(path=AXE_PATH)
   results = page.evaluate("async () => await axe.run(document, { resultTypes: ['violations'] })")
   ```
3. For each `violation` and each item in `violation["nodes"]`:
   - `target = node["target"][0]`. If not a string (iframe or shadow DOM), skip it.
   - Calculate canonical CSS selector chain:
     ```python
     chain = page.evaluate("(t) => { let el = document.querySelector(t); const out = [];"
                           " for (let i = 0; el && i < 6; i++, el = el.parentElement)"
                           " out.push((" + SELECTOR_JS + ")(el)); return out; }", target)
     ```
   - `selector = chain[0]`. `node_id` is set to the first selector in `chain` that matches a node in `nodes`, otherwise `null`.
   - Deduplicate to retain a single issue per (`rule`, `selector`) pair.
4. Map titles and recommendations using `recommendations.py`. Include Romanian templates for common WCAG rules:
   `button-name`, `link-name`, `image-alt`, `input-image-alt`, `label`, `select-name`, `color-contrast`, `html-has-lang`, `document-title`, `heading-order`, `empty-heading`, `page-has-heading-one`, `landmark-one-main`, `region`, `list`, `listitem`, `aria-hidden-focus`, `nested-interactive`, `frame-title`, `duplicate-id-aria`. For unmapped rules, fall back to `violation["help"]` and `violation["description"]`. Set `help_url = violation["helpUrl"]`.
5. If `nodes["focus_trap"]` is not `null`, inject a synthetic `keyboard-trap` issue (`critical`, `help_url: null`):
   - Title: "Capcană de tastatură: utilizatorul nu mai poate ieși cu Tab"
   - Recommendation: "Nu intercepta tasta Tab. Utilizatorul trebuie să poată ajunge la elementul următor fără mouse."
6. Sort issues by severity and number IDs sequentially: `i1`, `i2`, ...

On `bad-checkout.html`, axe detects: `button-name` (#cart), `image-alt` (img), `label` (#email), `link-name` (search link), `html-has-lang`, `color-contrast` (light gray text and fake button), and `heading-order` (h4), plus `keyboard-trap`.

## C. Report Assembly (`report.py`)
Develop against `samples/issues.json` + `samples/timeline.json` + `samples/nodes.json`.

1. Compute `timestamp` for each issue following the contract rule (earliest `start` time in timeline matching `node_id`).
2. Calculate `counts`, `score` (formula from `doc/1-foundation/data-contracts.md`), `focus_trap` boolean, `clip_url = f"/media/{analysis_id}/clip.mp4"`, and `duration`.
3. Order issues by severity (`critical`, `serious`, `moderate`, `minor`), then by `timestamp` ascending (placing `null` at the end).

## CLI Testing
```bash
python -m worker.engine.events nodes.json
python -m worker.engine.audit <url> nodes.json
python -m worker.engine.report issues.json timeline.json nodes.json
```

## Acceptance Criteria
- [ ] On `samples/nodes.json`: Unnamed button yields `Buton`, unnamed image yields `Imagine fără descriere`, unlabeled input yields `Câmp de editare`.
- [ ] On `bad-checkout.html`: The audit returns the expected WCAG rules + `keyboard-trap`, with at least 5 linked to valid `node_id`s.
- [ ] A dedicated test (`worker/engine/test_report.py`) verifies the scoring formula against test data. Expected score for `bad-checkout.html` is approximately 28.
- [ ] All user-facing issue titles and recommendations are clearly phrased.
