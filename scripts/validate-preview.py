#!/usr/bin/env python3
"""Shared HTTP preview gate for Morning and Asia Closing workflows.

The site validator remains the authority for repository-wide file and content
rules. This script only verifies that the already-built site can be served over
HTTP, decoded as UTF-8, parsed, and linked to its required local resources.
"""

from __future__ import annotations

import argparse
import json
import threading
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = {
    "morning": {
        "name": "Morning Report Workflow",
        "landing": "morning.html",
        "report_type": "morning",
    },
    "asia-close": {
        "name": "Asia Closing Report Workflow",
        "landing": "asia-close.html",
        "report_type": "asia-close",
    },
}
EXPECTED_CONTENT_TYPES = {
    ".css": {"text/css"},
    ".html": {"text/html"},
    ".js": {
        "application/javascript",
        "application/x-javascript",
        "text/javascript",
    },
    ".json": {"application/json"},
    ".svg": {"image/svg+xml"},
    ".webmanifest": {"application/json", "application/manifest+json"},
    ".xml": {
        "application/rss+xml",
        "application/xml",
        "text/xml",
    },
}
TEXT_SUFFIXES = set(EXPECTED_CONTENT_TYPES)


@dataclass
class Failure:
    workflow: str
    url: str
    status: str
    content_type: str
    decoding: str
    expected: str
    actual: str
    failed_file: str
    reason: str
    suggestion: str

    def format(self) -> str:
        fields = (
            ("Workflow", self.workflow),
            ("Validation URL", self.url),
            ("HTTP Status", self.status),
            ("HTTP Content-Type", self.content_type),
            ("Decoding", self.decoding),
            ("Expected Value", self.expected),
            ("Actual Value", self.actual),
            ("Failed File", self.failed_file),
            ("Failure Reason", self.reason),
            ("Suggested Fix", self.suggestion),
        )
        return "\n".join(f"{label}: {value}" for label, value in fields)


class PreviewHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: set[str] = set()
        self.meta_charsets: list[str] = []
        self.local_refs: list[str] = []
        self.report_list_types: list[str] = []
        self.has_search_input = False
        self.has_search_results = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        values = {key.lower(): value for key, value in attrs}
        self.tags.add(tag)
        if tag == "meta" and values.get("charset"):
            self.meta_charsets.append(values["charset"] or "")
        if "data-report-list" in values:
            self.report_list_types.append(values.get("data-type") or "")
        if "data-search" in values:
            self.has_search_input = True
        if "data-search-results" in values:
            self.has_search_results = True

        ref = values.get("src")
        if tag == "link" and "stylesheet" in (values.get("rel") or "").lower():
            ref = values.get("href")
        elif tag == "a":
            ref = values.get("href")
        if ref:
            self.local_refs.append(ref)


@dataclass
class Resource:
    path: str
    status: int
    content_type: str
    decoding: str
    text: str


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        return


def decoding_name(body: bytes) -> str:
    return "utf-8-sig (strict)" if body.startswith(b"\xef\xbb\xbf") else "utf-8 (strict)"


def decode_utf8(body: bytes) -> tuple[str, str]:
    codec = "utf-8-sig" if body.startswith(b"\xef\xbb\xbf") else "utf-8"
    return body.decode(codec, errors="strict"), f"{codec} (strict)"


def content_type_matches(path: str, content_type: str) -> bool:
    suffix = PurePosixPath(urllib.parse.urlsplit(path).path).suffix.lower()
    expected = EXPECTED_CONTENT_TYPES.get(suffix)
    return expected is None or content_type.lower() in expected


def parse_html(text: str) -> PreviewHTMLParser:
    parser = PreviewHTMLParser()
    parser.feed(text)
    parser.close()
    if not {"html", "head", "body"}.issubset(parser.tags):
        missing = sorted({"html", "head", "body"} - parser.tags)
        raise ValueError(f"missing structural elements: {', '.join(missing)}")
    return parser


def same_origin_path(base_url: str, ref: str) -> str | None:
    if not ref or ref.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
        return None
    absolute = urllib.parse.urljoin(base_url, ref)
    base = urllib.parse.urlsplit(base_url)
    target = urllib.parse.urlsplit(absolute)
    if (target.scheme, target.netloc) != (base.scheme, base.netloc):
        return None
    return target.path or "/"


class PreviewValidator:
    def __init__(self, workflow_key: str, report_path: str, base_url: str) -> None:
        self.config = WORKFLOWS[workflow_key]
        self.workflow = self.config["name"]
        self.report_path = report_path.replace("\\", "/").lstrip("/")
        self.base_url = base_url.rstrip("/") + "/"
        self.failures: list[Failure] = []
        self.resources: dict[str, Resource] = {}
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def add_failure(
        self,
        *,
        path: str,
        status: str,
        content_type: str,
        decoding: str,
        expected: str,
        actual: str,
        reason: str,
        suggestion: str,
    ) -> None:
        self.failures.append(
            Failure(
                workflow=self.workflow,
                url=urllib.parse.urljoin(self.base_url, path.lstrip("/")),
                status=status,
                content_type=content_type or "(missing)",
                decoding=decoding,
                expected=expected,
                actual=actual,
                failed_file=path,
                reason=reason,
                suggestion=suggestion,
            )
        )

    def fetch(self, path: str) -> Resource | None:
        path = "/" + path.lstrip("/")
        if path in self.resources:
            return self.resources[path]
        url = urllib.parse.urljoin(self.base_url, path.lstrip("/"))
        try:
            with self.opener.open(url, timeout=10) as response:
                status = response.status
                content_type = response.headers.get_content_type()
                body = response.read()
        except urllib.error.HTTPError as error:
            self.add_failure(
                path=path,
                status=str(error.code),
                content_type=error.headers.get_content_type() if error.headers else "(missing)",
                decoding="not attempted",
                expected="HTTP 200",
                actual=f"HTTP {error.code}",
                reason="The preview server returned a non-success response.",
                suggestion="Confirm the generated file exists at the expected path and rerun the preview.",
            )
            return None
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            self.add_failure(
                path=path,
                status="unavailable",
                content_type="(unavailable)",
                decoding="not attempted",
                expected="A reachable local HTTP response",
                actual=repr(error),
                reason="The local preview server could not be reached.",
                suggestion="Check whether the local port is available and rerun the preview.",
            )
            return None

        if status != 200:
            self.add_failure(
                path=path,
                status=str(status),
                content_type=content_type,
                decoding="not attempted",
                expected="HTTP 200",
                actual=f"HTTP {status}",
                reason="The preview endpoint did not return HTTP 200.",
                suggestion="Fix the route or generated file before publication.",
            )
            return None

        if not content_type_matches(path, content_type):
            suffix = PurePosixPath(path).suffix.lower()
            self.add_failure(
                path=path,
                status=str(status),
                content_type=content_type,
                decoding="not attempted",
                expected=f"One of {sorted(EXPECTED_CONTENT_TYPES.get(suffix, set()))}",
                actual=content_type,
                reason="The response Content-Type is not appropriate for the resource type.",
                suggestion="Correct the server MIME mapping or the referenced file extension.",
            )
            return None

        try:
            text, decoding = decode_utf8(body)
        except UnicodeDecodeError as error:
            self.add_failure(
                path=path,
                status=str(status),
                content_type=content_type,
                decoding=decoding_name(body),
                expected="Response bytes decode successfully as UTF-8",
                actual=f"UnicodeDecodeError at byte {error.start}: {error.reason}",
                reason="The response body is not valid UTF-8.",
                suggestion="Save the source file as UTF-8 and regenerate the publication files.",
            )
            return None

        resource = Resource(path, status, content_type, decoding, text)
        self.resources[path] = resource
        print(
            f"PASS workflow={self.workflow!r} url={url} status={status} "
            f"content-type={content_type!r} decoding={decoding!r}"
        )
        return resource

    def expect_html(self, path: str) -> PreviewHTMLParser | None:
        resource = self.fetch(path)
        if resource is None:
            return None
        try:
            return parse_html(resource.text)
        except (ValueError, TypeError) as error:
            self.add_failure(
                path=path,
                status=str(resource.status),
                content_type=resource.content_type,
                decoding=resource.decoding,
                expected="Parseable HTML containing html, head, and body elements",
                actual=str(error),
                reason="The HTML response could not be parsed into the required document structure.",
                suggestion="Repair the generated HTML structure and rerun validate-site.py.",
            )
            return None

    def expect_json(self, path: str) -> object | None:
        resource = self.fetch(path)
        if resource is None:
            return None
        try:
            return json.loads(resource.text)
        except json.JSONDecodeError as error:
            self.add_failure(
                path=path,
                status=str(resource.status),
                content_type=resource.content_type,
                decoding=resource.decoding,
                expected="Valid JSON",
                actual=f"{error.msg} at line {error.lineno}, column {error.colno}",
                reason="The JSON response is not parseable.",
                suggestion="Regenerate reports.json with the existing rebuild script.",
            )
            return None

    def expect_xml(self, path: str) -> ET.Element | None:
        resource = self.fetch(path)
        if resource is None:
            return None
        try:
            return ET.fromstring(resource.text)
        except ET.ParseError as error:
            self.add_failure(
                path=path,
                status=str(resource.status),
                content_type=resource.content_type,
                decoding=resource.decoding,
                expected="Well-formed XML",
                actual=str(error),
                reason="The XML response is not parseable.",
                suggestion="Regenerate the XML file with the existing rebuild script.",
            )
            return None

    def expect(self, path: str, expected: str, actual: object, condition: bool, suggestion: str) -> None:
        if condition:
            return
        resource = self.resources.get("/" + path.lstrip("/"))
        self.add_failure(
            path=path,
            status=str(resource.status) if resource else "not fetched",
            content_type=resource.content_type if resource else "(unavailable)",
            decoding=resource.decoding if resource else "not attempted",
            expected=expected,
            actual=repr(actual),
            reason="A required structural preview condition was not met.",
            suggestion=suggestion,
        )

    def validate_linked_resources(self, pages: Iterable[tuple[str, PreviewHTMLParser | None]]) -> None:
        checked: set[str] = set()
        for page_path, parser in pages:
            if parser is None:
                continue
            page_url = urllib.parse.urljoin(self.base_url, page_path.lstrip("/"))
            for ref in parser.local_refs:
                path = same_origin_path(page_url, ref)
                if path is None or path in checked:
                    continue
                suffix = PurePosixPath(path).suffix.lower()
                if suffix not in TEXT_SUFFIXES:
                    continue
                checked.add(path)
                resource = self.fetch(path)
                if resource is None:
                    continue
                if suffix == ".html":
                    self.expect_html(path)
                elif suffix in {".xml", ".svg"}:
                    self.expect_xml(path)
                elif suffix == ".json":
                    self.expect_json(path)

    def run(self) -> int:
        index = self.expect_html("/index.html")
        landing_path = "/" + self.config["landing"]
        landing = self.expect_html(landing_path)
        report = self.expect_html("/" + self.report_path)
        archive = self.expect_html("/archive.html")
        reports = self.expect_json("/data/reports.json")
        feed = self.expect_xml("/feed.xml")
        sitemap = self.expect_xml("/sitemap.xml")
        self.fetch("/assets/js/reports.js")
        self.fetch("/assets/js/search.js")
        self.fetch("/service-worker.js")
        self.expect_json("/manifest.webmanifest")

        if landing is not None:
            self.expect(
                landing_path,
                f"A report list bound to type {self.config['report_type']!r}",
                landing.report_list_types,
                self.config["report_type"] in landing.report_list_types,
                "Restore the existing data-report-list binding on the report index.",
            )
        if archive is not None:
            self.expect(
                "/archive.html",
                "Search input and search results containers",
                {
                    "has_search_input": archive.has_search_input,
                    "has_search_results": archive.has_search_results,
                },
                archive.has_search_input and archive.has_search_results,
                "Restore the existing Archive/Search data attributes.",
            )
        if report is not None:
            normalized = {value.strip().lower().replace("_", "-") for value in report.meta_charsets}
            self.expect(
                "/" + self.report_path,
                "A parsed meta charset value of utf-8 or utf8",
                report.meta_charsets,
                bool(normalized & {"utf-8", "utf8"}),
                "Add a valid UTF-8 meta charset declaration to the report head.",
            )
        if isinstance(reports, list):
            matches = [
                row
                for row in reports
                if isinstance(row, dict) and row.get("file") == self.report_path
            ]
            self.expect(
                "/data/reports.json",
                f"Exactly one published {self.config['report_type']!r} record for {self.report_path!r}",
                matches,
                len(matches) == 1
                and matches[0].get("type") == self.config["report_type"]
                and matches[0].get("status") == "published",
                "Regenerate reports.json with the existing rebuild script and verify the report record.",
            )
        if feed is not None:
            links = [(node.text or "").strip().lstrip("/") for node in feed.findall(".//item/link")]
            self.expect(
                "/feed.xml",
                f"An RSS item link equal to {self.report_path!r}",
                links,
                self.report_path in links,
                "Regenerate feed.xml with the existing rebuild script.",
            )
        if sitemap is not None:
            locs = [
                (node.text or "").strip().lstrip("/")
                for node in sitemap.iter()
                if node.tag.rsplit("}", 1)[-1] == "loc"
            ]
            self.expect(
                "/sitemap.xml",
                f"A sitemap loc equal to {self.report_path!r}",
                locs,
                self.report_path in locs,
                "Regenerate sitemap.xml with the existing rebuild script.",
            )

        self.validate_linked_resources(
            (
                ("/index.html", index),
                (landing_path, landing),
                ("/" + self.report_path, report),
                ("/archive.html", archive),
            )
        )

        if self.failures:
            print(f"HTTP Preview failed: {self.workflow}")
            for index, failure in enumerate(self.failures, start=1):
                print(f"\nFailure {index}\n{failure.format()}")
            return 1
        print(
            f"HTTP Preview passed: {self.workflow}; "
            f"{len(self.resources)} HTTP resource(s) validated"
        )
        return 0


def latest_report(root: Path, report_type: str) -> str:
    reports = json.loads((root / "data" / "reports.json").read_text(encoding="utf-8"))
    for report in reports:
        if report.get("type") == report_type and report.get("status") == "published":
            return str(report["file"])
    raise ValueError(f"No published {report_type!r} report exists in data/reports.json")


def validate_report_path(root: Path, report_path: str, report_type: str) -> str:
    normalized = report_path.replace("\\", "/").lstrip("/")
    expected_prefix = f"reports/{report_type}/"
    if not normalized.startswith(expected_prefix) or not normalized.endswith(".html"):
        raise ValueError(f"Report path must match {expected_prefix}*.html")
    resolved = (root / normalized).resolve()
    if root.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError(f"Report file does not exist inside the project: {normalized}")
    return normalized


def run_local(root: Path, workflow_key: str, report_path: str) -> int:
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(root), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{server.server_port}/"
        return PreviewValidator(workflow_key, report_path, base_url).run()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the local HTTP preview")
    parser.add_argument("--workflow", required=True, choices=sorted(WORKFLOWS))
    parser.add_argument("--report", help="Existing report path; defaults to latest published report")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()

    root = args.root.resolve()
    report_type = WORKFLOWS[args.workflow]["report_type"]
    try:
        report_path = args.report or latest_report(root, report_type)
        report_path = validate_report_path(root, report_path, report_type)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        workflow = WORKFLOWS[args.workflow]["name"]
        failure = Failure(
            workflow=workflow,
            url="not started",
            status="not attempted",
            content_type="not attempted",
            decoding="not attempted",
            expected=f"An existing published {report_type!r} report inside the project",
            actual=repr(error),
            failed_file=args.report or "data/reports.json",
            reason="Preview input validation failed.",
            suggestion="Use an existing report path from data/reports.json and rerun the preview.",
        )
        print(f"HTTP Preview failed: {workflow}\n\nFailure 1\n{failure.format()}")
        return 1
    return run_local(root, args.workflow, report_path)


if __name__ == "__main__":
    raise SystemExit(main())
