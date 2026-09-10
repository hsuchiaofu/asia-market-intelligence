#!/usr/bin/env python3
import argparse, re, sys
from pathlib import Path
from site_tools import ROOT,add_report,extract_h1,extract_meta_description,validate_source
def main():
    p=argparse.ArgumentParser(description='新增 Asia Market Intelligence 正式報告')
    p.add_argument('--type',required=True,choices=['morning','asia-close']); p.add_argument('--date',required=True)
    p.add_argument('--title'); p.add_argument('--summary'); p.add_argument('--source')
    p.add_argument('--existing-html',metavar='PATH',help='直接註冊既有正式 UTF-8 HTML，從 H1 與 meta description 讀取 metadata')
    p.add_argument('--replace',action='store_true')
    a=p.parse_args()
    try:
        if a.existing_html:
            if a.source or a.title is not None or a.summary is not None: raise ValueError('existing-html 模式不得同時提供 source、title 或 summary')
            source=Path(a.existing_html).resolve(); expected=(ROOT/'reports'/a.type/f'{a.date}.html').resolve()
            if source!=expected: raise ValueError('existing-html 必須指向相符 type/date 的正式報告路徑')
            text=validate_source(source); title=extract_h1(text); summary=extract_meta_description(text)
            if '\ufffd' in title or re.search(r'\?{2,}',title): raise ValueError('Validation Failed: H1 含無效字元')
            item=add_report(a.type,a.date,title,summary,source,a.replace,in_place=True)
        else:
            if not a.source or a.title is None or a.summary is None: raise ValueError('一般模式必須提供 source、title 與 summary')
            item=add_report(a.type,a.date,a.title,a.summary,a.source,a.replace)
        print(f'Published {item["id"]}')
    except Exception as e: print(f'Error: {e}',file=sys.stderr); return 1
    return 0
if __name__=='__main__': raise SystemExit(main())
