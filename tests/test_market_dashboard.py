import os
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MarketDashboardTests(unittest.TestCase):
    def test_market_dashboard_behavior(self):
        node = os.environ.get("AMI_NODE") or shutil.which("node")
        if not node:
            self.skipTest("Node.js 不可用")
        result = subprocess.run(
            [node, str(ROOT / "tests/test_market_dashboard.mjs")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)

    def test_only_crypto_cards_are_data_driven(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertEqual(html.count('data-market-asset="bitcoin"'), 1)
        self.assertEqual(html.count('data-market-asset="ethereum"'), 1)
        for title in ("美股", "歐洲", "亞洲", "美債", "美元", "原油", "黃金"):
            self.assertIn(f"<h3>{title}</h3><p>尚未更新</p>", html)
        self.assertIn("assets/js/market-dashboard.js", html)

    def test_csp_allows_only_required_market_api(self):
        headers = (ROOT / "_headers").read_text(encoding="utf-8")
        self.assertIn("connect-src 'self' https://api.coingecko.com", headers)


if __name__ == "__main__":
    unittest.main()
