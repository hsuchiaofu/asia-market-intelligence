import subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ScriptTests(unittest.TestCase):
    def test_validator(self):
        r=subprocess.run([sys.executable,str(ROOT/'scripts/validate-site.py')],cwd=ROOT,capture_output=True,text=True); self.assertEqual(r.returncode,0,r.stderr)
    def test_empty_incoming(self):
        r=subprocess.run([sys.executable,str(ROOT/'scripts/import-incoming-reports.py'),'--type','morning'],cwd=ROOT,capture_output=True,text=True); self.assertEqual(r.returncode,0,r.stderr); self.assertIn('No report available for publication',r.stdout)
    def test_add_rejects_bad_type(self):
        r=subprocess.run([sys.executable,str(ROOT/'scripts/add-report.py'),'--type','bad'],cwd=ROOT,capture_output=True,text=True); self.assertNotEqual(r.returncode,0)
