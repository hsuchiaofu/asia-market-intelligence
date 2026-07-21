#!/usr/bin/env python3
import argparse, sys
from site_tools import add_report
def main():
    p=argparse.ArgumentParser(description='新增 Asia Market Intelligence 正式報告'); p.add_argument('--type',required=True,choices=['morning','asia-close']); p.add_argument('--date',required=True); p.add_argument('--title',required=True); p.add_argument('--summary',required=True); p.add_argument('--source',required=True); p.add_argument('--replace',action='store_true')
    a=p.parse_args()
    try: item=add_report(a.type,a.date,a.title,a.summary,a.source,a.replace); print(f'Published {item["id"]}')
    except Exception as e: print(f'Error: {e}',file=sys.stderr); return 1
    return 0
if __name__=='__main__': raise SystemExit(main())
