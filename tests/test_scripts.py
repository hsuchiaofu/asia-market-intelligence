import subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from site_tools import extract_meta_description,validate_summary
class ScriptTests(unittest.TestCase):
    def test_validator(self):
        r=subprocess.run([sys.executable,str(ROOT/'scripts/validate-site.py')],cwd=ROOT,capture_output=True,text=True); self.assertEqual(r.returncode,0,r.stderr)
    def test_empty_incoming(self):
        r=subprocess.run([sys.executable,str(ROOT/'scripts/import-incoming-reports.py'),'--type','morning'],cwd=ROOT,capture_output=True,text=True); self.assertEqual(r.returncode,0,r.stderr); self.assertIn('No report available for publication',r.stdout)
    def test_add_rejects_bad_type(self):
        r=subprocess.run([sys.executable,str(ROOT/'scripts/add-report.py'),'--type','bad'],cwd=ROOT,capture_output=True,text=True); self.assertNotEqual(r.returncode,0)
    def test_import_summary_requires_valid_meta_description(self):
        summary='亞洲半導體走強，市場風險偏好回升。'
        self.assertEqual(extract_meta_description(f'<meta content="{summary}" name="description">'),summary)
        with self.assertRaisesRegex(ValueError,'meta description'):
            extract_meta_description('<html><head></head><body></body></html>')
        with self.assertRaisesRegex(ValueError,'通用字串'):
            validate_summary('asia-close','2026-08-13','2026-08-13 亞洲股市收盤報')
        self.assertEqual(validate_summary('morning','2026-08-13',summary),summary)
