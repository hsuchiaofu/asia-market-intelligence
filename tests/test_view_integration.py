import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ViewIntegrationTests(unittest.TestCase):
    def test_list_and_report_pages_have_view_hooks(self):
        self.assertIn("data-report-list", (ROOT / "index.html").read_text(encoding="utf-8"))
        self.assertIn("data-search-results", (ROOT / "archive.html").read_text(encoding="utf-8"))
        reports_js = (ROOT / "assets/js/reports.js").read_text(encoding="utf-8")
        self.assertIn("data-view-id", reports_js)
        self.assertIn("/api/views/batch", reports_js)

        reports = json.loads((ROOT / "data/reports.json").read_text(encoding="utf-8"))
        for report in reports:
            page = (ROOT / report["file"]).read_text(encoding="utf-8")
            self.assertIn("data-view-count", page, report["file"])
            self.assertIn("assets/js/views.js", page, report["file"])

    def test_future_reports_use_convention_without_code_changes(self):
        views_js = (ROOT / "assets/js/views.js").read_text(encoding="utf-8")
        reports_js = (ROOT / "assets/js/reports.js").read_text(encoding="utf-8")
        self.assertIn("morning|asia-close", views_js)
        self.assertNotIn("2026-07-23", views_js)
        self.assertNotIn("2026-07-23", reports_js)


if __name__ == "__main__":
    unittest.main()
