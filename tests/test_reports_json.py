import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ReportsJsonTests(unittest.TestCase):
    def test_schema_and_files(self):
        rows=json.loads((ROOT/'data/reports.json').read_text(encoding='utf-8')); self.assertIsInstance(rows,list); ids=set()
        for row in rows:
            self.assertEqual(set(row),{'id','type','title','date','summary','file','updated','status','featured','wordFile'}); self.assertNotIn(row['id'],ids); ids.add(row['id']); self.assertTrue((ROOT/row['file']).is_file())
    def test_sorted(self):
        rows=json.loads((ROOT/'data/reports.json').read_text(encoding='utf-8')); self.assertEqual(rows,sorted(rows,key=lambda x:(x['date'],x['updated']),reverse=True))
