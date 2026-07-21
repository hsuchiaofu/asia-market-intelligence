import re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PathTests(unittest.TestCase):
    def test_local_references(self):
        attr=re.compile(r'(?:href|src)="([^"]+)"')
        for page in ROOT.rglob('*.html'):
            if page.parent == ROOT/'templates':
                continue
            for ref in attr.findall(page.read_text(encoding='utf-8')):
                if ref.startswith(('http','#','{{','mailto:','data:')) or ref in ('',): continue
                target=(page.parent/ref.split('#')[0].split('?')[0]).resolve()
                self.assertTrue(target.exists(),f'{page.relative_to(ROOT)} -> {ref}')
    def test_no_absolute_workspace_paths(self):
        for ext in ('*.html','*.js','*.json','*.md','*.yml'):
            for f in ROOT.rglob(ext): self.assertNotIn('C:\\Users\\Joe',f.read_text(encoding='utf-8'))
