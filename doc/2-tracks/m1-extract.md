# Track M1: Agent & Tree Extraction

## Objective
Receive a URL and produce `nodes.json`: the accessibility tree in natural screen-reader reading order, the sequential Tab focus order, and any detected keyboard trap. Additionally, ensure `scripts/check_env.py` passes reliably across all team laptops.

## Your Files
`worker/extract/extract.py`, `worker/extract/tab_walk.py`, `contracts/samples/nodes.json`, `scripts/check_env.py`, `scripts/fetch_assets.py`

## Inputs and Outputs
- **Input:** URL string
- **Output:** Python dictionary matching the `nodes.json` schema (`doc/1-foundation/data-contracts.md`)

```python
# worker/extract/extract.py
def extract(url: str) -> dict: ...
```

## Implementation Steps

### 1. Opening the Page
Use the Playwright sync API, headless Chromium, and `viewport=VIEWPORT`. Then:
```python
try:
    page.goto(url, wait_until="networkidle", timeout=30000)
except PlaywrightTimeoutError:
    page.goto(url, wait_until="load", timeout=30000)
page.wait_for_timeout(800)
```
Encapsulate this logic into a helper function `open_page(browser, url)`. M2 and M3 can reuse or mirror it so all three modules load pages with identical behavior.

### 2. Accessibility Tree via CDP
```python
cdp = page.context.new_cdp_session(page)
cdp.send("DOM.enable"); cdp.send("Accessibility.enable")
ax = cdp.send("Accessibility.getFullAXTree")["nodes"]
by_id = {n["nodeId"]: n for n in ax}
root = ax[0]   # role.value == "RootWebArea"
```
Relevant fields from each node include `nodeId`, `childIds`, `ignored`, `role.value`, `name.value`, `properties[] {name, value.value}`, `value.value`, and `backendDOMNodeId`.

### 3. Depth-First Traversal in Reading Order
Perform a DFS starting from `root`, traversing `childIds` in order of appearance.

- **`ignored` nodes:** Do not emit, but recurse into their children.
- **Role normalization:** `StaticText` → `text`, `img` → `image`, `searchbox` → `textbox`, `switch` → `checkbox`.
- **Roles outside the contract set** (`generic`, `none`, `paragraph`, `listitem`, `RootWebArea`, etc.): Do not emit, but recurse into their children.
- **`LabelText`:** Do **not** emit and do **not** recurse into its children. The label text is already incorporated into the form control's accessible name; otherwise, the label is read twice. (Verified on the test page).
- **`InlineTextBox`:** Ignore completely.
- **Atomic roles** (`heading`, `link`, `button`, `textbox`, `checkbox`, `radio`, `combobox`, `image`): Emit the node and do **not** descend into its children. Their accessible name already contains child text content.
- **`text` nodes** with empty or whitespace-only names are not emitted.
- **`parent`** represents the `id` of the closest ancestor that was actually emitted, or `null`.
- Halt traversal after 400 emitted nodes.

On `bad-checkout.html`, the emitted order should follow: banner, text "PasUșor", navigation, link "Bărbați", link "Femei", unnamed link, unnamed button, main, heading 1, unnamed image, heading 4, two text nodes, heading 2, textbox "Nume complet", unnamed textbox, textbox "Cod promoțional", textbox "Telefon", text "Plasează comanda".

### 4. Properties Extraction
- From `properties`, extract `level` (check both `prop["name"] == "hierarchicalLevel"` and `"level"`, as modern Chromium DevTools Protocol uses `hierarchicalLevel`), `required`, `checked` (`"true"`/`"false"`/`"mixed"` → `true`/`false`/`"mixed"`), `expanded`, `disabled`, and `focusable`.
- `value` is extracted from `node["value"]["value"]` if present.
- For `list`, `list_size` is the count of `listitem` children in the raw accessibility tree.

### 5. Canonical Selector, Bounding Box, and Visibility
For every emitted node possessing a `backendDOMNodeId`:
```python
JS = ("function(){ let el = this.nodeType === 3 ? this.parentElement : this;"
      " const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);"
      " return { selector: (" + SELECTOR_JS + ")(el),"
      " bbox: { x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height },"
      " visible: r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' }; }")
obj = cdp.send("DOM.resolveNode", {"backendNodeId": bid})["object"]["objectId"]
info = cdp.send("Runtime.callFunctionOn", {"objectId": obj, "functionDeclaration": JS,
                                           "returnByValue": True})["result"]["value"]
```
Wrap this call in a `try/except`. On error, write `selector: null`, `bbox: null`, and `visible: false`.

### 6. Sequential Tab Traversal (`tab_walk.py`)
Runs after tree extraction on the same open page instance.
```python
def tab_walk(page, by_selector: dict) -> tuple[list, dict | None]:
    page.evaluate("document.activeElement && document.activeElement.blur()")
    order, first, repeats, trap = [], None, 0, None
    get_sel = ("(() => { const el = document.activeElement;"
               " if (!el || el === document.body) return null;"
               " return (" + SELECTOR_JS + ")(el); })()")
    for _ in range(80):
        page.keyboard.press("Tab")
        sel = page.evaluate(get_sel)
        if sel is None:
            break                                    # Focus left the document
        if order and order[-1]["selector"] == sel:
            repeats += 1
            if repeats >= 2:                         # Focused same element 3 consecutive times
                trap = {"node_id": by_selector.get(sel), "selector": sel}
                break
            continue
        repeats = 0
        if first is None:
            first = sel
        elif sel == first:
            break                                    # Full focus loop completed
        order.append({"node_id": by_selector.get(sel), "selector": sel})
    return order, trap
```
`by_selector` is a mapping of CSS selector → node ID, constructed from all emitted nodes. On the test page, Tab navigation cycles through the 3 links, `#cart`, `#name`, `#email`, and traps inside `#promo`.

### 7. CLI Testing
```bash
python -m worker.extract.extract <url> [out.json]   # outputs to stdout by default
```

### 8. Environment Diagnostics
Assist teammates until `python scripts/check_env.py` passes cleanly on all development machines. Add any new troubleshooting steps to `doc/setup/troubleshooting.md`.

### 9. Optional: Dismiss Cookie Banners
Before extraction, attempt to dismiss cookie consent dialogs. Query for buttons containing "Accept", "Accept all", "Agree", "I agree", or Romanian equivalents ("Acceptă", "Sunt de acord"), clicking with a 2-second timeout. If none are found, proceed gracefully.

## Edge Cases
- `iframe`: Do not enter iframes; emit elements in the primary document.
- Redirects: `url` in the output preserves the requested URL; `title` is taken from `page.title()`.
- Failed page load: Raise an exception with a descriptive error message.

## Acceptance Criteria
- [ ] On `bad-checkout.html`: `#cart` has `role: button`, `name: ""`. Image has `role: image`, `name: ""`. `#email` has `role: textbox`, `name: ""`. `focus_trap.selector == "#promo"`.
- [ ] "Nume complet", "Cod promoțional", and "Telefon" appear once as textbox names and are not duplicated as standalone text nodes.
- [ ] Every node's selector resolves to its element via `document.querySelector`.
- [ ] Extraction completes in under 30 seconds on average public websites.
- [ ] `check_env.py` passes cleanly on all 4 development laptops.
