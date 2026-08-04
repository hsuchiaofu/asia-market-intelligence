import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-preview.py"
SPEC = importlib.util.spec_from_file_location("validate_preview", SCRIPT)
validate_preview = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validate_preview
SPEC.loader.exec_module(validate_preview)


class PreviewValidatorTests(unittest.TestCase):
    def run_latest_preview(self, workflow):
        config = validate_preview.WORKFLOWS[workflow]
        reports = json.loads((ROOT / "data" / "reports.json").read_text(encoding="utf-8"))
        report_path = validate_preview.latest_report(ROOT, config["report_type"])
        matches = [
            report
            for report in reports
            if report.get("file") == report_path
            and report.get("type") == config["report_type"]
        ]

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].get("status"), "published")
        self.assertTrue((ROOT / report_path).is_file())

        latest_feed_files = {
            report.get("file")
            for report in reports[:20]
            if report.get("status") == "published"
        }
        if report_path in latest_feed_files:
            feed_links = {
                (node.text or "").strip().lstrip("/")
                for node in ET.parse(ROOT / "feed.xml").findall(".//item/link")
            }
            self.assertIn(report_path, feed_links)

        sitemap_locs = {
            (node.text or "").strip().lstrip("/")
            for node in ET.parse(ROOT / "sitemap.xml").iter()
            if node.tag.rsplit("}", 1)[-1] == "loc"
        }
        self.assertIn(report_path, sitemap_locs)

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--workflow",
                workflow,
                "--report",
                report_path,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"HTTP Preview passed: {config['name']}", result.stdout)

    def test_strict_utf8_decode(self):
        text, decoding = validate_preview.decode_utf8("café €".encode("utf-8"))
        self.assertEqual(text, "café €")
        self.assertEqual(decoding, "utf-8 (strict)")
        with self.assertRaises(UnicodeDecodeError):
            validate_preview.decode_utf8(b"\xff")

    def test_content_type_validation_is_structural(self):
        self.assertTrue(validate_preview.content_type_matches("/report.HTML", "text/html"))
        self.assertTrue(validate_preview.content_type_matches("/data.json", "application/json"))
        self.assertTrue(
            validate_preview.content_type_matches(
                "/manifest.webmanifest", "application/manifest+json"
            )
        )
        self.assertTrue(validate_preview.content_type_matches("/search.js", "text/javascript"))
        self.assertFalse(validate_preview.content_type_matches("/report.html", "text/plain"))

    def test_html_parser_accepts_case_insensitive_charset_value(self):
        parser = validate_preview.parse_html(
            '<!doctype html><html><head><meta charset="UTF_8"></head><body></body></html>'
        )
        normalized = {value.lower().replace("_", "-") for value in parser.meta_charsets}
        self.assertIn("utf-8", normalized)

    def test_failure_output_contains_complete_diagnostics(self):
        rendered = validate_preview.Failure(
            workflow="Morning Report Workflow",
            url="http://127.0.0.1/report.html",
            status="200",
            content_type="text/html",
            decoding="utf-8 (strict)",
            expected="Parseable HTML",
            actual="missing body",
            failed_file="/report.html",
            reason="Invalid document structure",
            suggestion="Repair the HTML",
        ).format()
        for label in (
            "Workflow:",
            "Validation URL:",
            "HTTP Status:",
            "HTTP Content-Type:",
            "Decoding:",
            "Expected Value:",
            "Actual Value:",
            "Failed File:",
            "Failure Reason:",
            "Suggested Fix:",
        ):
            self.assertIn(label, rendered)

    def test_excluded_paths_are_never_requested_for_either_workflow(self):
        class RecordingOpener:
            def __init__(self):
                self.calls = []

            def open(self, url, timeout):
                self.calls.append((url, timeout))
                raise AssertionError("Excluded preview paths must not be requested")

        for workflow in ("morning", "asia-close"):
            with self.subTest(workflow=workflow):
                validator = validate_preview.PreviewValidator(
                    workflow,
                    f"reports/{workflow}/latest.html",
                    "http://127.0.0.1:8000/",
                )
                opener = RecordingOpener()
                validator.opener = opener
                self.assertIsNone(validator.fetch("/nested/.backups/report.html"))
                self.assertIsNone(validator.fetch(r"\nested\tmp\report.html"))
                self.assertEqual(opener.calls, [])
                self.assertEqual(len(validator.failures), 2)
                self.assertTrue(
                    all(failure.status == "not requested" for failure in validator.failures)
                )

    def test_preview_input_rejects_excluded_report_path_before_server_start(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            report = root / "reports" / "asia-close" / ".backups" / "report.html"
            report.parent.mkdir(parents=True)
            report.write_text("<html></html>", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "excluded directory component"):
                validate_preview.validate_report_path(
                    root,
                    "reports/asia-close/.backups/report.html",
                    "asia-close",
                )

    def test_morning_preview(self):
        self.run_latest_preview("morning")

    def test_asia_close_preview(self):
        self.run_latest_preview("asia-close")


if __name__ == "__main__":
    unittest.main()
