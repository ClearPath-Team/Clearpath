"""Regression tests for M1 live-web resilience (M1-02).

Browser tests use Playwright Chromium on local file:// pages and a local HTTP
server, and are skipped (via scripts.check_env.chromium_skip_reason) when
Chromium or its host libraries are missing. Tab-walk error
handling is also covered without a browser using a fake page.
"""
import shutil
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from playwright.sync_api import Error as PlaywrightError

from scripts.check_env import chromium_skip_reason
from worker.extract import extract as extract_mod
from worker.extract.tab_walk import MAX_TAB_PRESSES, tab_walk

ROOT = Path(__file__).resolve().parents[2]
TEST_SITE = (ROOT / "test-site" / "bad-checkout.html").as_uri()


BANNER_BODY = """
  <div id="cookie-banner" role="dialog" aria-label="Cookie-uri">
    <p>Folosim cookie-uri pentru a îmbunătăți experiența.</p>
    <button onclick="this.closest('#cookie-banner').remove()">Acceptă</button>
  </div>
  <main><h1>Magazin</h1><a href="#produse">Produse</a></main>"""
BANNER_PAGE = ('<!doctype html><html lang="ro"><head><meta charset="utf-8">'
               "<title>Banner</title></head><body>" + BANNER_BODY + "</body></html>")


_SKIP_BROWSER = chromium_skip_reason()


class _FakeKeyboard:
    def __init__(self, page):
        self.page = page

    def press(self, key):
        self.page.presses += 1
        if self.page.fail_on_press and self.page.presses >= self.page.fail_on_press:
            raise PlaywrightError("Target page, context or browser has been closed")


class _FakePage:
    """Returns the next scripted activeElement selector on each evaluate()."""

    def __init__(self, selectors, fail_on_press=None):
        self.selectors = iter(selectors)
        self.presses = 0
        self.fail_on_press = fail_on_press
        self.keyboard = _FakeKeyboard(self)

    def evaluate(self, script):
        if "blur()" in script:
            return None
        return next(self.selectors)


class CookieButtonPatternTests(unittest.TestCase):
    def test_matches_common_consent_labels(self):
        for label in ("Acceptă", "De acord", "Accept", "Accept all", "Agree", "I agree", "OK",
                      "ACCEPT TOATE", "Accept all cookies", "Acceptă cookie-urile",
                      "Permite toate", "Sunt de acord", "  accept  "):
            with self.subTest(label=label):
                self.assertTrue(extract_mod.COOKIE_BUTTON_PATTERN.match(label))

    def test_ignores_longer_labels_that_only_start_with_accept(self):
        for label in ("Acceptă termenii și condițiile", "Accept toate și închide",
                      "OK, mergi la coș", "Comisia Europeană acuză TikTok"):
            with self.subTest(label=label):
                self.assertIsNone(extract_mod.COOKIE_BUTTON_PATTERN.match(label))


class TabWalkGuardTests(unittest.TestCase):
    def test_page_error_mid_walk_keeps_collected_order(self):
        page = _FakePage(["#a", "#b", "#c"], fail_on_press=3)
        order, trap = tab_walk(page, {"#a": "n1", "#b": "n2"})
        self.assertEqual(order, [{"node_id": "n1", "selector": "#a"},
                                 {"node_id": "n2", "selector": "#b"}])
        self.assertIsNone(trap)

    def test_walk_is_capped_at_max_tab_presses(self):
        page = _FakePage(f"#e{i}" for i in range(10 * MAX_TAB_PRESSES))
        order, trap = tab_walk(page, {})
        self.assertEqual(page.presses, MAX_TAB_PRESSES)
        self.assertEqual(len(order), MAX_TAB_PRESSES)
        self.assertIsNone(trap)

    def test_focus_lost_inside_document_does_not_end_walk(self):
        page = _FakePage(["#a", "", "#c", None])
        order, _ = tab_walk(page, {})
        self.assertEqual([o["selector"] for o in order], ["#a", "#c"])

    def test_detached_focus_resets_trap_counter(self):
        page = _FakePage(["#a", "#a", "", "#a", None])
        order, trap = tab_walk(page, {})
        self.assertEqual([o["selector"] for o in order], ["#a"])
        self.assertIsNone(trap)


class _FakeButton:
    def __init__(self, fail=False):
        self.fail = fail
        self.clicked = False

    def is_visible(self):
        return True

    def evaluate(self, script):
        if self.fail:
            raise PlaywrightError("Element is not attached to the DOM")
        return True

    def click(self, timeout):
        self.clicked = True


class _FakeButtons:
    def __init__(self, buttons):
        self.buttons = buttons

    def count(self):
        return len(self.buttons)

    def nth(self, i):
        return self.buttons[i]


class _FakeBannerPage:
    def __init__(self, buttons):
        self.buttons = _FakeButtons(buttons)

    def get_by_role(self, role, name):
        return self.buttons

    def wait_for_timeout(self, ms):
        pass


class DismissCandidateTests(unittest.TestCase):
    def test_detached_candidate_does_not_stop_later_candidates(self):
        detached, real = _FakeButton(fail=True), _FakeButton()
        self.assertTrue(extract_mod._dismiss_cookie_banner(_FakeBannerPage([detached, real])))
        self.assertTrue(real.clicked)


@unittest.skipIf(_SKIP_BROWSER, _SKIP_BROWSER or "")
class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls._pw = sync_playwright().start()
        try:
            cls.browser = cls._pw.chromium.launch(headless=True)
        except Exception:
            # Stop the driver so later classes can still start sync Playwright.
            cls._pw.stop()
            raise
        cls.tmp = Path(tempfile.mkdtemp(prefix="cp-test-extract-"))

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls._pw.stop()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _page_url(self, name, body, title="Test"):
        path = self.tmp / name
        path.write_text(f'<!doctype html><html lang="ro"><head><meta charset="utf-8">'
                        f"<title>{title}</title></head><body>{body}</body></html>",
                        encoding="utf-8")
        return path.as_uri()


@unittest.skipIf(_SKIP_BROWSER, _SKIP_BROWSER or "")
class ExtractRegressionTests(unittest.TestCase):
    """Calls extract() end to end, which starts its own Playwright instance."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cp-test-extract-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_bad_checkout_extraction_is_unchanged(self):
        result = extract_mod.extract(TEST_SITE)

        self.assertEqual(len(result["nodes"]), 19)
        self.assertEqual([n["role"] for n in result["nodes"]], [
            "banner", "text", "navigation", "link", "link", "link", "button", "main",
            "heading", "image", "heading", "text", "text", "heading", "textbox",
            "textbox", "textbox", "textbox", "text"])
        by_selector = {n["selector"]: n for n in result["nodes"]}
        self.assertEqual((by_selector["#cart"]["role"], by_selector["#cart"]["name"]), ("button", ""))
        self.assertEqual(result["focus_trap"], {"node_id": by_selector["#promo"]["id"],
                                                "selector": "#promo"})
        self.assertEqual([f["selector"] for f in result["focus_order"]][3:],
                         ["#cart", "#name", "#email", "#promo"])
        names = [n["name"] for n in result["nodes"]]
        for label in ("Nume complet", "Cod promoțional", "Telefon"):
            self.assertEqual(names.count(label), 1)


    def test_consent_banner_is_dismissed_before_extraction(self):
        path = self.tmp / "banner.html"
        path.write_text(BANNER_PAGE, encoding="utf-8")

        result = extract_mod.extract(path.as_uri())

        names = [n["name"] for n in result["nodes"]]
        self.assertNotIn("Acceptă", names)
        self.assertFalse(any("cookie" in name for name in names))
        self.assertIn("Magazin", names)
        self.assertEqual(result["focus_order"][0]["selector"],
                         "html > body:nth-of-type(1) > main:nth-of-type(1) > a:nth-of-type(1)")


class CookieBannerTests(BrowserTests):
    def test_open_page_dismisses_consent_banner(self):
        url = self._page_url("banner.html", BANNER_BODY)
        page = extract_mod.open_page(self.browser, url)
        try:
            self.assertIsNone(page.query_selector("#cookie-banner"))
        finally:
            page.close()

    def test_generic_ok_button_outside_consent_banner_is_not_clicked(self):
        url = self._page_url("form.html", """
          <form><label>Email <input id="email"></label>
          <button type="button" onclick="document.title = 'clicked'">OK</button></form>""",
                             title="Original")
        page = extract_mod.open_page(self.browser, url)
        try:
            self.assertEqual(page.title(), "Original")
        finally:
            page.close()

    def test_no_banner_costs_little_time(self):
        url = self._page_url("plain.html", "<main><h1>Fără banner</h1></main>")
        page = self.browser.new_page()
        try:
            page.goto(url)
            started = time.monotonic()
            self.assertFalse(extract_mod._dismiss_cookie_banner(page))
            self.assertLess(time.monotonic() - started, 0.5)
        finally:
            page.close()


class _SlowAssetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/slow.png":
            time.sleep(6)
            self.send_response(404)
            self.end_headers()
            return
        body = ('<!doctype html><html><head><title>Lent</title></head><body>'
                '<h1>Conținut</h1><img src="/slow.png" alt=""></body></html>').encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class PageLoadGuardrailTests(BrowserTests):
    def test_slow_asset_falls_back_without_failing_or_renavigating(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), _SlowAssetHandler)
        server.daemon_threads = True
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        url = f"http://127.0.0.1:{server.server_address[1]}/"

        with mock.patch.object(extract_mod, "LOAD_EVENT_GRACE_MS", 500), \
                mock.patch.object(extract_mod, "NETWORKIDLE_GRACE_MS", 500), \
                mock.patch.object(extract_mod, "SETTLE_MS", 100):
            started = time.monotonic()
            page = extract_mod.open_page(self.browser, url)
            elapsed = time.monotonic() - started
        try:
            self.assertEqual(page.title(), "Lent")
            self.assertLess(elapsed, 4)
        finally:
            page.close()

    def test_unreachable_page_raises_descriptive_error(self):
        with self.assertRaisesRegex(RuntimeError, "Failed to load page"):
            extract_mod.open_page(self.browser, "http://127.0.0.1:9/")


class DetachedFocusTests(BrowserTests):
    def test_walk_continues_after_focused_element_removes_itself(self):
        url = self._page_url("detach.html", """
          <a id="a" href="#1">A</a>
          <a id="b" href="#2" onfocus="this.remove()">B</a>
          <a id="c" href="#3">C</a>""")
        page = extract_mod.open_page(self.browser, url)
        try:
            order, trap = tab_walk(page, {})
        finally:
            page.close()
        self.assertEqual([o["selector"] for o in order], ["#a", "#c"])
        self.assertIsNone(trap)


if __name__ == "__main__":
    unittest.main()
