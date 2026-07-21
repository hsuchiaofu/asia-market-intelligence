#!/usr/bin/env python3
import argparse,re,shutil,sys
from datetime import date
from pathlib import Path
from site_tools import ROOT,add_report,VALID_TYPES
def main():
    p=argparse.ArgumentParser(); p.add_argument('--type',choices=VALID_TYPES); p.add_argument('--allow-past',action='store_true'); a=p.parse_args(); found=ok=failed=0
    kinds=[a.type] if a.type else list(VALID_TYPES)
    for kind in kinds:
        folder=ROOT/'incoming'/kind
        for source in sorted(folder.glob('*.html')):
            found+=1; m=re.search(r'(\d{4}-\d{2}-\d{2})',source.name)
            try:
                if not m: raise ValueError('檔名找不到 YYYY-MM-DD 日期')
                day=m.group(1)
                if date.fromisoformat(day)<date.today() and not a.allow_past: raise ValueError('拒絕發布過期檔案；手動確認可加 --allow-past')
                add_report(kind,day,VALID_TYPES[kind],f'{day} {VALID_TYPES[kind]}',source)
                dest=ROOT/'incoming'/'processed'/kind; dest.mkdir(parents=True,exist_ok=True); shutil.move(str(source),dest/source.name); ok+=1
            except Exception as e:
                dest=ROOT/'incoming'/'failed'/kind; dest.mkdir(parents=True,exist_ok=True); shutil.move(str(source),dest/source.name); failed+=1; print(f'Failed {source.name}: {e}',file=sys.stderr)
    if not found: print('No report available for publication')
    else: print(f'Imported: {ok}; Failed: {failed}')
    return 1 if failed else 0
if __name__=='__main__': raise SystemExit(main())
