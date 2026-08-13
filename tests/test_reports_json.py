import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from site_tools import extract_meta_description,validate_summary
class ReportsJsonTests(unittest.TestCase):
    def test_schema_and_files(self):
        rows=json.loads((ROOT/'data/reports.json').read_text(encoding='utf-8')); self.assertIsInstance(rows,list); ids=set()
        for row in rows:
            self.assertEqual(set(row),{'id','type','title','date','summary','file','updated','status','featured','wordFile'}); self.assertNotIn(row['id'],ids); ids.add(row['id']); self.assertTrue((ROOT/row['file']).is_file())
    def test_sorted(self):
        rows=json.loads((ROOT/'data/reports.json').read_text(encoding='utf-8')); self.assertEqual(rows,sorted(rows,key=lambda x:(x['date'],x['updated']),reverse=True))
    def test_latest_summaries_match_report_metadata(self):
        rows=json.loads((ROOT/'data/reports.json').read_text(encoding='utf-8'))
        for report_type in ('morning','asia-close'):
            row=next(row for row in rows if row['type']==report_type and row['status']=='published')
            with self.subTest(report=row['id']):
                summary=validate_summary(row['type'],row['date'],row['summary'])
                html=(ROOT/row['file']).read_text(encoding='utf-8')
                self.assertEqual(summary,extract_meta_description(html))
