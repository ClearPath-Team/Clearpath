"""Track M1: Sequential Tab key focus order traversal and keyboard trap detection."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from playwright.sync_api import Error as PlaywrightError

from worker.common import SELECTOR_JS

MAX_TAB_PRESSES = 80


def tab_walk(page, by_selector: dict) -> tuple[list, dict | None]:
    """Simulates pressing Tab repeatedly, recording focus order and detecting focus traps.

    Focus resting on <body> while the document still has focus means the focused
    element was removed from the DOM; Tab continues from its old position, so
    the walk goes on. Focus on <body> without document focus means Tab left the
    page, which ends the walk. Page errors (navigation, crash) stop it early,
    keeping the order collected so far. At most MAX_TAB_PRESSES presses."""
    order, first, repeats, trap = [], None, 0, None
    get_sel = ("(() => { const el = document.activeElement;"
               " if (!el || el === document.body || !el.isConnected)"
               "   return document.hasFocus() ? '' : null;"
               " return (" + SELECTOR_JS + ")(el); })()")

    try:
        page.evaluate("document.activeElement && document.activeElement.blur()")
        for _ in range(MAX_TAB_PRESSES):
            page.keyboard.press("Tab")
            sel = page.evaluate(get_sel)
            if sel is None:
                break
            if sel == "":
                continue
            if order and order[-1]["selector"] == sel:
                repeats += 1
                if repeats >= 2:
                    trap = {"node_id": by_selector.get(sel), "selector": sel}
                    break
                continue
            repeats = 0
            if first is None:
                first = sel
            elif sel == first:
                break
            order.append({"node_id": by_selector.get(sel), "selector": sel})
    except PlaywrightError:
        pass

    return order, trap
