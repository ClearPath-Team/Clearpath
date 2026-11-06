"""Exercise actual CLI processes with the legacy Windows stdout encoding."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import subprocess
import sys
import threading
import unittest

from worker.common import ROOT


class CliEncodingTests(unittest.TestCase):
    def run_cli(self, module, *arguments):
        result = subprocess.run(
            [sys.executable, "-m", module, *arguments], cwd=ROOT,
            env={**os.environ, "PYTHONIOENCODING": "cp1252"},
            capture_output=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
        return json.loads(result.stdout.decode("utf-8"))

    def test_events_stdout_is_utf8_even_with_cp1252_environment(self):
        result = self.run_cli("worker.engine.events", "contracts/samples/nodes.json")
        self.assertEqual(result["events"][0]["text"], "Pagina Finalizează comanda")
        self.assertIn("imagine fără descriere", [event["text"] for event in result["events"]])

    def test_report_stdout_is_utf8_even_with_cp1252_environment(self):
        result = self.run_cli("worker.engine.report", "contracts/samples/issues.json",
                              "contracts/samples/timeline.json", "contracts/samples/nodes.json")
        self.assertEqual(result["title"], "Finalizează comanda")
        self.assertEqual(result["score"], 38)

    def test_audit_stdout_is_utf8_even_with_cp1252_environment(self):
        handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT / "test-site"))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            result = self.run_cli("worker.engine.audit",
                                  f"http://127.0.0.1:{server.server_port}/bad-checkout.html",
                                  "contracts/samples/nodes.json")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        labels = [issue for issue in result if issue["rule"] == "label"]
        self.assertEqual(labels[0]["title"], "Câmpul de formular nu are etichetă")


if __name__ == "__main__":
    unittest.main()
