"""Track M1: Accessibility tree extraction via Chrome DevTools Protocol (CDP)."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from worker.common import SELECTOR_JS, VIEWPORT
from worker.extract.tab_walk import tab_walk

# Role names already matching the contract's normalized set (doc/1-foundation/data-contracts.md).
CONTRACT_ROLES = {
    "heading", "link", "button", "textbox", "checkbox", "radio", "combobox", "image",
    "list", "banner", "navigation", "main", "contentinfo", "region", "form", "search",
    "complementary", "text",
}
# Raw CDP AX role -> normalized contract role.
ROLE_MAP = {"StaticText": "text", "img": "image", "searchbox": "textbox", "switch": "checkbox"}
# Roles whose accessible name already contains their child text content: emit, do not descend.
ATOMIC_ROLES = {"heading", "link", "button", "textbox", "checkbox", "radio", "combobox", "image"}
# Roles never emitted, never recursed into.
SKIP_SUBTREE_ROLES = {"LabelText", "InlineTextBox"}
MAX_NODES = 400

COOKIE_BUTTON_TEXTS = ["Accept all", "Accept", "Agree", "I agree", "Acceptă", "Sunt de acord"]

# Resolves the canonical selector, document-coordinate bbox, and visibility for a DOM node.
RESOLVE_JS = (
    "function(){ let el = this.nodeType === 3 ? this.parentElement : this;"
    " const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);"
    " return { selector: (" + SELECTOR_JS + ")(el),"
    " bbox: { x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height },"
    " visible: r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' }; }"
)


def open_page(browser, url: str):
    """Opens `url` in a new page with the standard viewport, falling back from
    networkidle to load on timeout (shared behavior across M1/M2/M3)."""
    page = browser.new_page(viewport=VIEWPORT)
    try:
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
        except PlaywrightTimeoutError:
            page.goto(url, wait_until="load", timeout=30000)
    except Exception as exc:
        page.close()
        raise RuntimeError(f"Failed to load page at {url}: {exc}") from exc
    page.wait_for_timeout(800)
    return page


def _dismiss_cookie_banner(page) -> None:
    for text in COOKIE_BUTTON_TEXTS:
        try:
            page.get_by_role("button", name=text, exact=False).first.click(timeout=2000)
            return
        except Exception:
            continue


def _prop(node: dict, name: str):
    for p in node.get("properties") or []:
        if p.get("name") == name:
            return (p.get("value") or {}).get("value")
    return None


def _bool_prop(node: dict, name: str, default: bool = False) -> bool:
    v = _prop(node, name)
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    return str(v).lower() == "true"


def _checked_prop(node: dict):
    v = _prop(node, "checked")
    if v is None:
        return None
    if v is True or v == "true":
        return True
    if v is False or v == "false":
        return False
    if v == "mixed":
        return "mixed"
    return None


def _resolve_selector_bbox(cdp, backend_node_id):
    if backend_node_id is None:
        return None, None, False
    try:
        object_id = cdp.send("DOM.resolveNode", {"backendNodeId": backend_node_id})["object"]["objectId"]
        value = cdp.send("Runtime.callFunctionOn", {
            "objectId": object_id,
            "functionDeclaration": RESOLVE_JS,
            "returnByValue": True,
        })["result"]["value"]
        return value["selector"], value["bbox"], value["visible"]
    except Exception:
        return None, None, False


def _extract_tree(cdp, by_id: dict, root_id: str) -> list:
    """Depth-first traversal of the CDP accessibility tree in natural reading order."""
    emitted: list = []

    def dfs(node_id: str, parent_emitted_id):
        if len(emitted) >= MAX_NODES:
            return
        node = by_id.get(node_id)
        if node is None:
            return

        raw_role = (node.get("role") or {}).get("value")
        if raw_role in SKIP_SUBTREE_ROLES:
            return  # Do not emit, do not recurse (e.g. label text already in accessible name).

        norm_role = ROLE_MAP.get(raw_role, raw_role)
        ignored = bool(node.get("ignored", False))
        name = (node.get("name") or {}).get("value") or ""

        emit = (not ignored) and (norm_role in CONTRACT_ROLES)
        if emit and norm_role == "text" and not name.strip():
            emit = False

        this_id = None
        if emit:
            order = len(emitted)
            this_id = f"n{order}"

            level = None
            if norm_role == "heading":
                raw_level = _prop(node, "hierarchicalLevel")
                if raw_level is None:
                    raw_level = _prop(node, "level")
                level = int(raw_level) if raw_level is not None else None

            list_size = None
            if norm_role == "list":
                list_size = sum(
                    1 for cid in node.get("childIds", [])
                    if (by_id.get(cid, {}).get("role") or {}).get("value") == "listitem"
                )

            value = (node.get("value") or {}).get("value")
            expanded_raw = _prop(node, "expanded")
            selector, bbox, visible = _resolve_selector_bbox(cdp, node.get("backendDOMNodeId"))

            emitted.append({
                "id": this_id,
                "order": order,
                "role": norm_role,
                "name": name,
                "level": level,
                "states": {
                    "required": _bool_prop(node, "required"),
                    "checked": _checked_prop(node),
                    "expanded": bool(expanded_raw) if expanded_raw is not None else None,
                    "disabled": _bool_prop(node, "disabled"),
                },
                "value": value,
                "list_size": list_size,
                "focusable": _bool_prop(node, "focusable"),
                "parent": parent_emitted_id,
                "selector": selector,
                "bbox": bbox,
                "visible": visible,
            })

        if emit and norm_role in ATOMIC_ROLES:
            return  # Accessible name already contains child text content; do not descend.

        next_parent = this_id if this_id else parent_emitted_id
        for child_id in node.get("childIds", []):
            if len(emitted) >= MAX_NODES:
                break
            dfs(child_id, next_parent)

    dfs(root_id, None)
    return emitted


def extract(url: str) -> dict:
    """Extracts accessibility tree, bounding boxes, and Tab order for the given URL.
    Note: CDP Accessibility.AXNode properties check both 'hierarchicalLevel' and 'level' for headings.
    """
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = open_page(browser, url)
            _dismiss_cookie_banner(page)
            title = page.title()

            cdp = page.context.new_cdp_session(page)
            cdp.send("DOM.enable")
            cdp.send("Accessibility.enable")
            ax_nodes = cdp.send("Accessibility.getFullAXTree")["nodes"]
            by_id = {n["nodeId"]: n for n in ax_nodes}
            root = next(
                (n for n in ax_nodes if (n.get("role") or {}).get("value") == "RootWebArea"),
                ax_nodes[0],
            )

            emitted = _extract_tree(cdp, by_id, root["nodeId"])
            by_selector = {n["selector"]: n["id"] for n in emitted if n.get("selector")}
            focus_order, focus_trap = tab_walk(page, by_selector)

            return {
                "url": url,
                "title": title,
                "viewport": VIEWPORT,
                "nodes": emitted,
                "focus_order": focus_order,
                "focus_trap": focus_trap,
            }
        finally:
            browser.close()


if __name__ == "__main__":
    import json
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080/bad-checkout.html"
    res = extract(url)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        print(json.dumps(res, indent=2, ensure_ascii=False))
