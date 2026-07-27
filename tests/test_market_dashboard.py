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

    def test_market_dashboard_api_parser(self):
        node = os.environ.get("AMI_NODE") or shutil.which("node")
        if not node:
            self.skipTest("Node.js 不可用")
        result = subprocess.run(
            [node, str(ROOT / "tests/test_market_dashboard_api.mjs")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)

    def test_crypto_and_commodity_cards_are_data_driven(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for asset in ("bitcoin", "ethereum", "gold", "brent"):
            self.assertEqual(html.count(f'data-market-asset="{asset}"'), 1)
        for title in ("美股", "歐洲", "亞洲", "美債", "美元"):
            self.assertIn(f"<h3>{title}</h3><p>尚未更新</p>", html)
        self.assertIn("USD (XAU)", (ROOT / "assets/js/market-dashboard.js").read_text(encoding="utf-8"))
        self.assertIn("USD (Brent)", (ROOT / "assets/js/market-dashboard.js").read_text(encoding="utf-8"))
        self.assertIn("assets/js/market-dashboard.js", html)
        for asset, title in (
            ("gold", "黃金"),
            ("brent", "原油"),
            ("bitcoin", "比特幣"),
            ("ethereum", "以太坊"),
        ):
            self.assertIn(
                f'<article class="card market-card" data-market-asset="{asset}"><h3>{title}</h3>',
                html,
            )
        self.assertNotIn("market-symbol", html)
        self.assertNotIn(".market-symbol", (ROOT / "assets/css/style.css").read_text(encoding="utf-8"))

    def test_csp_allows_only_required_market_api(self):
        headers = (ROOT / "_headers").read_text(encoding="utf-8")
        self.assertIn("connect-src 'self' https://api.coingecko.com", headers)


if __name__ == "__main__":
    unittest.main()
