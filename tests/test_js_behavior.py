import os,shutil,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class JavaScriptBehaviorTests(unittest.TestCase):
    def test_frontend_and_api_behavior(self):
        node=os.environ.get('AMI_NODE') or shutil.which('node')
        if not node: self.skipTest('Node.js 不可用')
        version=subprocess.run([node,'--version'],capture_output=True,text=True).stdout.strip().lstrip('v').split('.')[0]
        if not version.isdigit() or int(version)<18: self.skipTest('需要 Node.js 18 或更新版本')
        result=subprocess.run([node,str(ROOT/'tests/test_frontend_behavior.mjs')],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
