import re,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'scripts'
if str(SCRIPTS) not in sys.path: sys.path.insert(0,str(SCRIPTS))
from validation_paths import iter_site_files

ATTR=re.compile(r'(?:href|src)="([^"]+)"')
BASE=re.compile(r'<base\b[^>]*\bhref="([^"]+)"',re.I)
def missing_local_references(root):
    missing=[]
    for page in iter_site_files(root,'*.html'):
        relative=page.relative_to(root)
        if relative.parts and relative.parts[0] in ('templates','incoming'):
            continue
        text=page.read_text(encoding='utf-8'); base=page.parent; match=BASE.search(text)
        if match:
            base_ref=match.group(1).split('#')[0].split('?')[0]
            if base_ref and not base_ref.startswith(('http','//')):
                target=(page.parent/base_ref).resolve()
                base=target if base_ref.endswith(('/','\\')) else target.parent
        for ref in ATTR.findall(text):
            if ref.startswith(('http','#','{{','mailto:','tel:','data:','javascript:','//')) or not ref:
                continue
            target=(base/ref.split('#')[0].split('?')[0]).resolve()
            if not target.exists(): missing.append((relative,ref))
    return missing

class PathTests(unittest.TestCase):
    def test_local_references(self):
        self.assertEqual(
            missing_local_references(ROOT),
            [],
            "Formal HTML contains missing local references",
        )

    def test_formal_html_missing_css_js_and_link_are_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            page=root/'reports'/'asia-close'/'broken.html'
            page.parent.mkdir(parents=True)
            page.write_text(
                '<html><head><link rel="stylesheet" href="../../assets/missing.css">'
                '</head><body><script src="../../assets/missing.js"></script>'
                '<a href="../../missing.html">missing</a></body></html>',
                encoding='utf-8',
            )
            self.assertEqual(
                {ref for _,ref in missing_local_references(root)},
                {
                    '../../assets/missing.css',
                    '../../assets/missing.js',
                    '../../missing.html',
                },
            )

    def test_base_href_resolves_local_references(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            page=root/'prototype'/'review.html'
            asset=root/'assets'/'app.js'
            page.parent.mkdir(parents=True)
            asset.parent.mkdir(parents=True)
            asset.write_text('',encoding='utf-8')
            page.write_text(
                '<html><head><base href="../"></head>'
                '<body><script src="assets/app.js"></script></body></html>',
                encoding='utf-8',
            )
            self.assertEqual(missing_local_references(root),[])

    def test_no_absolute_workspace_paths(self):
        for ext in ('*.html','*.js','*.json','*.md','*.yml'):
            for f in iter_site_files(ROOT,ext):
                self.assertNotIn('C:\\Users\\Joe',f.read_text(encoding='utf-8'))
