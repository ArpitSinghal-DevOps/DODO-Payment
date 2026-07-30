import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from app import app


class LedgerApiSecurityTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_transactions_do_not_expose_full_pans(self):
        response = self.client.get("/transactions")

        self.assertEqual(response.status_code, 200)
        transactions = response.get_json()["transactions"]
        self.assertNotIn("pan", transactions[0])
        self.assertEqual(transactions[0]["pan_last4"], "4242")

    def test_fetch_rejects_localhost(self):
        response = self.client.get("/fetch?url=http://127.0.0.1:8080/health")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "URL is not allowed")

    def test_fetch_rejects_non_http_schemes(self):
        response = self.client.get("/fetch?url=file:///etc/passwd")

        self.assertEqual(response.status_code, 400)

    @patch("app.requests.get")
    @patch("app.socket.getaddrinfo")
    def test_fetch_allows_public_http_urls(self, getaddrinfo, requests_get):
        getaddrinfo.return_value = [
            (None, None, None, None, ("93.184.216.34", 443)),
        ]
        requests_get.return_value = Mock(status_code=200, text="ok")

        response = self.client.get("/fetch?url=https://example.com/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status_code": 200, "body": "ok"})
        requests_get.assert_called_once_with("https://example.com/status", timeout=5, allow_redirects=False)


if __name__ == "__main__":
    unittest.main()
