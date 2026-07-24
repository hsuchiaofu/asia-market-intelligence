import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validation_paths import is_excluded_path, iter_site_files


class ValidationPathTests(unittest.TestCase):
    def test_windows_and_posix_excluded_components(self):
        excluded_components = (
            ".git",
            ".github",
            ".backups",
            "backup",
            "backups",
            ".tmp",
            "temp",
            "tmp",
            "node_modules",
            "pycache",
            "__pycache__",
            ".codex",
            ".cache",
            "dist",
            "coverage",
        )
        for component in excluded_components:
            for path in (
                f"nested/{component}/report.html",
                rf"nested\{component}\report.html",
            ):
                with self.subTest(path=path):
                    self.assertTrue(is_excluded_path(path))

        included = (
            "reports/asia-close/2026-07-24.html",
            r"reports\morning\2026-07-24.html",
            "assets/js/app.js",
            "data/reports.json",
            "templates/asia-close-report-template.html",
            "functions/api/views.js",
            "reports/backup-analysis.html",
            "assets/tmp-theme.css",
        )
        for path in included:
            with self.subTest(path=path):
                self.assertFalse(is_excluded_path(path))

    def test_recursive_scan_prunes_excluded_directories_but_keeps_public_tree(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            included = (
                root / "reports" / "asia-close" / "report.html",
                root / "templates" / "template.html",
                root / "public" / "nested" / "page.html",
            )
            excluded = (
                root / ".backups" / "report.html",
                root / ".tmp" / "report.html",
                root / "one" / "backup" / "report.html",
                root / "one" / "backups" / "report.html",
                root / "one" / "temp" / "report.html",
                root / "one" / "tmp" / "report.html",
                root / "one" / "node_modules" / "report.html",
            )
            for path in included + excluded:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("<html></html>", encoding="utf-8")

            found = {path.relative_to(root).as_posix() for path in iter_site_files(root, "*.html")}
            self.assertEqual(
                found,
                {
                    "public/nested/page.html",
                    "reports/asia-close/report.html",
                    "templates/template.html",
                },
            )

    def test_public_resource_trees_remain_in_recursive_scans(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            public_files = (
                root / "reports" / "asia-close" / "report.html",
                root / "assets" / "js" / "app.js",
                root / "data" / "reports.json",
                root / "templates" / "template.html",
                root / "functions" / "api" / "views.js",
                root / "index.html",
                root / "archive.html",
                root / "morning.html",
                root / "asia-close.html",
                root / "privacy.html",
            )
            for path in public_files:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("public", encoding="utf-8")

            found = {
                path.relative_to(root).as_posix()
                for path in iter_site_files(root, ("*.html", "*.js", "*.json"))
            }
            self.assertEqual(
                found,
                {path.relative_to(root).as_posix() for path in public_files},
            )


if __name__ == "__main__":
    unittest.main()
