"""Track M1: Sequential Tab key focus order traversal and keyboard trap detection."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from worker.common import SELECTOR_JS


def tab_walk(page, by_selector: dict) -> tuple[list, dict | None]:
    """Simulates pressing Tab repeatedly, recording focus order and detecting focus traps."""
    page.evaluate("document.activeElement && document.activeElement.blur()")
    order, first, repeats, trap = [], None, 0, None
    get_sel = ("(() => { const el = document.activeElement;"
               " if (!el || el === document.body) return null;"
               " return (" + SELECTOR_JS + ")(el); })()")

    for _ in range(80):
        page.keyboard.press("Tab")
        sel = page.evaluate(get_sel)
        if sel is None:
            break
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

    return order, trap
