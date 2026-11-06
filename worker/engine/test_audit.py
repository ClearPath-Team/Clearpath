"""Audit mapping regressions and a real browser check against the offline demo."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import threading
import unittest
from unittest.mock import Mock, patch

from playwright.sync_api import Error as PlaywrightError
from scripts.check_env import chromium_install_hint, chromium_skip_reason

from worker.common import ROOT, SAMPLES, read_json
from worker.engine.audit import _map_violations, run_audit
from worker.engine.recommendations import RECOMMENDATIONS

CHROMIUM_SKIP_REASON = chromium_skip_reason()


def violation(rule, targets, impact="serious"):
    return {"id": rule, "impact": impact, "help": "Fallback title",
            "description": "Fallback recommendation", "helpUrl": "https://example.com/help",
            "nodes": [{"target": target} for target in targets]}


class AuditMappingTests(unittest.TestCase):
    def test_canonical_ancestor_mapping_dedup_and_fallback(self):
        page = Mock()
        page.evaluate.side_effect = lambda script, target: {
            ".child": ["#parent > span:nth-of-type(1)", "#parent", "html"],
            "#unmapped": ["#unmapped", "html"], "#removed": [],
        }[target]
        nodes = {"nodes": [{"id": "n0", "order": 0, "selector": "#parent"}]}
        results = _map_violations(page, [
            violation("button-name", [[".child"], [".child"], ["#removed"]], "critical"),
            violation("unknown-rule", [["#unmapped"]]),
        ], nodes)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["node_id"], "n0")
        self.assertEqual(results[0]["selector"], "#parent > span:nth-of-type(1)")
        self.assertEqual(results[1]["title"], "Fallback title")
        self.assertEqual(results[1]["recommendation"], "Fallback recommendation")
        self.assertIsNone(results[1]["node_id"])

    def test_frame_and_shadow_targets_are_skipped(self):
        page = Mock()
        results = _map_violations(page, [violation("label", [[], [["#host", "input"]], ["iframe", "input"]])], {})
        self.assertEqual(results, [])
        page.evaluate.assert_not_called()

    def test_trap_supports_contract_object_and_legacy_boolean(self):
        for trap in (True, {"node_id": "n1", "selector": "#trap"}):
            with self.subTest(trap=trap):
                result = _map_violations(Mock(), [], {"focus_trap": trap})
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]["rule"], "keyboard-trap")
                self.assertEqual(result[0]["severity"], "critical")
                self.assertIsNone(result[0]["help_url"])

    def test_all_required_rules_have_romanian_recommendations(self):
        required = {"button-name", "link-name", "image-alt", "input-image-alt", "label", "select-name",
                    "color-contrast", "html-has-lang", "document-title", "heading-order", "empty-heading",
                    "page-has-heading-one", "landmark-one-main", "region", "list", "listitem",
                    "aria-hidden-focus", "nested-interactive", "frame-title", "duplicate-id-aria"}
        self.assertTrue(required <= RECOMMENDATIONS.keys())
        self.assertTrue(all(title and recommendation for title, recommendation in RECOMMENDATIONS.values()))


class BrowserEnvironmentTests(unittest.TestCase):
    def tearDown(self):
        chromium_skip_reason.cache_clear()

    def test_missing_host_libraries_produce_cached_skip_reason(self):
        chromium_skip_reason.cache_clear()
        with patch("scripts.check_env.chromium", side_effect=PlaywrightError(
                "BrowserType.launch: Host system is missing dependencies to run browsers.")) as launch:
            reason = chromium_skip_reason()
            self.assertIn("Chromium unavailable", reason)
            self.assertIn("-m playwright install", reason)
            self.assertEqual(chromium_skip_reason(), reason)
            launch.assert_called_once()

    def test_missing_browser_binary_produces_skip_reason(self):
        chromium_skip_reason.cache_clear()
        with patch("scripts.check_env.chromium", side_effect=PlaywrightError("Executable doesn't exist at /cache/chromium")):
            self.assertIn("install chromium", chromium_skip_reason())

    def test_unexpected_browser_error_is_not_hidden(self):
        chromium_skip_reason.cache_clear()
        with patch("scripts.check_env.chromium", side_effect=PlaywrightError("unexpected browser crash")):
            with self.assertRaisesRegex(PlaywrightError, "unexpected browser crash"):
                chromium_skip_reason()

    def test_available_browser_runs_live_tests(self):
        chromium_skip_reason.cache_clear()
        with patch("scripts.check_env.chromium", return_value="130.0"):
            self.assertIsNone(chromium_skip_reason())

    def test_platform_instructions_use_current_interpreter(self):
        for platform, command in (("linux", "sudo apt-get update"), ("darwin", "brew install python@3.12"),
                                  ("win32", "winget install --id Python.Python.3.12 --exact")):
            with self.subTest(platform=platform), patch("scripts.check_env.sys.platform", platform):
                hint = chromium_install_hint()
                self.assertIn(command, hint)
                self.assertIn("-m playwright install chromium", hint)
                if platform == "linux":
                    self.assertIn("-m playwright install-deps chromium", hint)


@unittest.skipIf(CHROMIUM_SKIP_REASON is not None, CHROMIUM_SKIP_REASON or "")
class LiveAuditTests(unittest.TestCase):
    def test_demo_uses_real_axe_and_maps_at_least_five_nodes(self):
        handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT / "test-site"))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            source = read_json(SAMPLES / "nodes.json")
            issues = run_audit(f"http://127.0.0.1:{server.server_port}/bad-checkout.html", source)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        rules = {issue["rule"] for issue in issues}
        self.assertTrue({"button-name", "image-alt", "label", "link-name", "html-has-lang",
                         "color-contrast", "heading-order", "keyboard-trap"} <= rules)
        valid_ids = {node["id"] for node in source["nodes"]}
        linked = [issue for issue in issues if issue["node_id"] is not None]
        self.assertGreaterEqual(len(linked), 5)
        self.assertTrue(all(issue["node_id"] in valid_ids for issue in linked))
        selectors = {issue["rule"]: issue["selector"] for issue in issues}
        self.assertEqual(selectors["button-name"], "#cart")
        self.assertEqual(selectors["image-alt"], "#product-image")
        self.assertEqual(selectors["label"], "#email")
        self.assertEqual(selectors["keyboard-trap"], "#promo")
        contrast = [i for i in issues if i["rule"] == "color-contrast"]
        self.assertEqual(len(contrast), 2)
        by_id = {n["id"]: n for n in source["nodes"]}
        self.assertTrue(all(by_id[i["node_id"]]["selector"] == i["selector"] for i in linked))
        self.assertEqual([issue["id"] for issue in issues], [f"i{i}" for i in range(1, len(issues) + 1)])
        self.assertEqual(len({(issue["rule"], issue["selector"]) for issue in issues}), len(issues))
        self.assertEqual(set(issues[0]), {"id", "rule", "severity", "node_id", "selector", "title", "recommendation", "help_url"})


if __name__ == "__main__":
    unittest.main()
