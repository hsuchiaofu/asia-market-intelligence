#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
from site_tools import ROOT,load_reports
def main():
    errors=[]; reports=load_reports(); seen=set()
    required=['index.html','morning.html','asia-close.html','archive.html','popular.html','about.html','privacy.html','offline.html','404.html','feed.xml','sitemap.xml','manifest.webmanifest','service-worker.js','_headers','robots.txt']
    for name in required:
        if not (ROOT/name).is_file(): errors.append(f'缺少 {name}')
    for f in ROOT.rglob('*.html'):
        text=f.read_text(encoding='utf-8'); low=text.lower()
        if '<html lang="zh-hant"' not in low: errors.append(f'{f.relative_to(ROOT)} 缺少 lang=zh-Hant')
        if '<meta charset="utf-8"' not in low: errors.append(f'{f.relative_to(ROOT)} 缺少 UTF-8 charset')
    for r in reports:
        for k in ('id','type','title','date','summary','file','updated','status','featured','wordFile'):
            if k not in r: errors.append(f'{r.get("id","?")} 缺少 {k}')
        if r.get('id') in seen: errors.append(f'重複 id：{r["id"]}')
        seen.add(r.get('id'))
        if not (ROOT/r.get('file','')).is_file(): errors.append(f'找不到報告：{r.get("file")}')
    secret=re.compile(r'(api[_-]?key|token|secret)\s*[:=]\s*["\'][^"\']{12,}',re.I)
    for f in list(ROOT.rglob('*.js'))+list(ROOT.rglob('*.json'))+list(ROOT.rglob('*.yml')):
        if secret.search(f.read_text(encoding='utf-8')): errors.append(f'疑似秘密：{f.relative_to(ROOT)}')
    if errors:
        print('\n'.join('ERROR '+x for x in errors),file=sys.stderr); return 1
    print(f'Validation passed: {len(reports)} published report(s)'); return 0
if __name__=='__main__': raise SystemExit(main())
