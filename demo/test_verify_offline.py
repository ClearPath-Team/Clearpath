"""A failed external connection alone cannot certify physical isolation."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location("verify_offline", Path(__file__).with_name("verify_offline.py"))
offline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(offline)


class PhysicalNetworkCheckTests(unittest.TestCase):
    def test_external_connectivity_rejects_offline_claim(self):
        connection = Mock()
        with patch.object(offline.socket, "create_connection", return_value=connection):
            with self.assertRaisesRegex(RuntimeError, "External TCP connectivity"):
                offline.check_disconnected()
        connection.close.assert_called_once()

    def test_connected_adapter_rejects_claim_even_when_external_probe_fails(self):
        with patch.object(offline.socket, "create_connection", side_effect=OSError("blocked")), \
                patch.object(offline.sys, "platform", "win32"), \
                patch.object(offline.subprocess, "run", return_value=SimpleNamespace(stdout=b"1\r\n")):
            with self.assertRaisesRegex(RuntimeError, "physical adapter"):
                offline.check_disconnected()

    def test_disconnected_adapters_and_failed_external_probe_are_required(self):
        with patch.object(offline.socket, "create_connection", side_effect=OSError("offline")), \
                patch.object(offline.sys, "platform", "win32"), \
                patch.object(offline.subprocess, "run", return_value=SimpleNamespace(stdout=b"0\r\n")):
            offline.check_disconnected()


if __name__ == "__main__":
    unittest.main()
