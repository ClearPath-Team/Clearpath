"""Track M2: Accessibility audit running axe-core 4.10 inside the evaluated webpage."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

from worker.common import AXE_PATH, SELECTOR_JS, SAMPLES, VIEWPORT, read_json, write_json
from worker.engine.recommendations import RECOMMENDATIONS, EN_RECOMMENDATIONS
from worker.engine.categories import enrich_issue

SEVERITY_ORDER = {"critical": 0, "serious": 1, "moderate": 2, "minor": 3}


def _map_violations(page, violations: list, nodes: dict, lang: str = "ro") -> list[dict]:
    """Resolve axe targets through the shared selector generator and nearest ancestors."""
    if lang not in ("ro", "en"):
        raise ValueError(f"Unsupported audit language: {lang}")
    by_selector = {}
    for node in sorted(nodes.get("nodes", []), key=lambda item: item["order"]):
        by_selector.setdefault(node.get("selector"), node["id"])
    issues = []
    seen = set()
    for violation in violations:
        rule = violation["id"]
        title, recommendation = (RECOMMENDATIONS.get(
            rule, (violation["help"], violation["description"])) if lang == "ro" else
            EN_RECOMMENDATIONS.get(rule, (violation["help"], violation["description"])))
        for item in violation["nodes"]:
            targets = item.get("target") or []
            # Multiple selectors refer to iframe paths; nested arrays refer to shadow DOM.
            if len(targets) != 1 or not isinstance(targets[0], str):
                continue
            chain = page.evaluate(
                "(target) => { let el; try { el = document.querySelector(target); }"
                " catch { return []; } const chain = [];"
                " for (let i = 0; el && i < 6; i++, el = el.parentElement)"
                " chain.push((" + SELECTOR_JS + ")(el)); return chain; }", targets[0])
            if not chain or (rule, chain[0]) in seen:
                continue
            seen.add((rule, chain[0]))
            severity = item.get("impact") or violation.get("impact") or "moderate"
            issues.append({
                "rule": rule, "severity": severity,
                "node_id": next((by_selector[selector] for selector in chain if selector in by_selector), None),
                "selector": chain[0], "title": title, "recommendation": recommendation,
                "help_url": violation.get("helpUrl"),
            })
    trap = nodes.get("focus_trap")
    if trap:
        trap_data = trap if isinstance(trap, dict) else {}
        title, recommendation = (RECOMMENDATIONS if lang == "ro" else EN_RECOMMENDATIONS)["keyboard-trap"]
        issues.append({
            "rule": "keyboard-trap", "severity": "critical",
            "node_id": trap_data.get("node_id") or by_selector.get(trap_data.get("selector")),
            "selector": trap_data.get("selector"), "title": title,
            "recommendation": recommendation, "help_url": None,
        })
    issues.sort(key=lambda issue: (SEVERITY_ORDER[issue["severity"]], issue["rule"], issue["selector"] or ""))
    return [{"id": f"i{index}", **issue} for index, issue in enumerate(issues, start=1)]


def run_audit(url: str, nodes: dict, lang: str = "ro") -> list[dict]:
    """Runs axe-core on the page, resolves canonical selectors, and maps issues to node_ids."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            context = browser.new_context(viewport=VIEWPORT, bypass_csp=True)
            try:
                page = context.new_page()
                try:
                    page.goto(url, wait_until="networkidle", timeout=30000)
                except PlaywrightTimeoutError:
                    page.goto(url, wait_until="load", timeout=30000)
                page.wait_for_timeout(800)
                page.add_script_tag(path=AXE_PATH)
                results = page.evaluate("async () => await axe.run(document, {resultTypes: ['violations']})")
                return [enrich_issue(issue) for issue in _map_violations(page, results["violations"], nodes, lang=lang)]
            finally:
                context.close()
        finally:
            browser.close()


if __name__ == "__main__":
    import json
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080/bad-checkout.html"
    nodes_path = sys.argv[2] if len(sys.argv) > 2 else str(SAMPLES / "nodes.json")
    result = run_audit(url, read_json(nodes_path))
    if len(sys.argv) > 3:
        write_json(Path(sys.argv[3]), result)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps(result, indent=2, ensure_ascii=False))
