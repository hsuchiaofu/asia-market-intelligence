import importlib.util, subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from site_tools import extract_h1,extract_meta_description,validate_summary
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

    def test_existing_html_registration_reads_utf8_metadata_without_cli_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'reports'/'asia-close'/'2026-09-10.html'; source.parent.mkdir(parents=True)
            source.write_text('<!doctype html><html><head><meta name="description" content="測試摘要。"></head><body><h1>測試收盤報</h1><p>本網站內容僅供一般資訊與研究參考</p><p>'+'測試內容。'*100+'</p></body></html>',encoding='utf-8')
            spec=importlib.util.spec_from_file_location('add_report_cli',ROOT/'scripts'/'add-report.py'); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
            published=[]; module.ROOT=root; module.add_report=lambda *args,**kwargs: published.append((args,kwargs)) or {'id':'asia-close-2026-09-10'}
            old_argv=sys.argv; sys.argv=['add-report.py','--type','asia-close','--date','2026-09-10','--existing-html',str(source)]
            try: self.assertEqual(module.main(),0)
            finally: sys.argv=old_argv
            self.assertEqual(published[0][0][2:4],('測試收盤報','測試摘要。'))
            self.assertTrue(published[0][1]['in_place'])

    def test_extract_h1_requires_one_nonempty_heading(self):
        self.assertEqual(extract_h1('<h1>亞洲收盤報</h1>'),'亞洲收盤報')
        with self.assertRaisesRegex(ValueError,'唯一且非空白的 H1'): extract_h1('<h1></h1>')
        with self.assertRaisesRegex(ValueError,'唯一且非空白的 H1'): extract_h1('<h1>A</h1><h1>B</h1>')
