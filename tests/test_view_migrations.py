import sqlite3
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ViewMigrationTests(unittest.TestCase):
    def test_existing_rows_receive_created_timestamp(self):
        db = sqlite3.connect(":memory:")
        db.executescript((ROOT / "migrations/0001_create_page_views.sql").read_text(encoding="utf-8"))
        db.execute(
            "INSERT INTO page_views(path, views, updated_at) VALUES (?, ?, ?)",
            ("/reports/morning/2026-07-22.html", 7, "2026-07-22T00:00:00Z"),
        )
        db.executescript((ROOT / "migrations/0002_add_page_view_created_at.sql").read_text(encoding="utf-8"))
        row = db.execute("SELECT views, created_at, updated_at FROM page_views").fetchone()
        self.assertEqual(row, (7, "2026-07-22T00:00:00Z", "2026-07-22T00:00:00Z"))


if __name__ == "__main__":
    unittest.main()
