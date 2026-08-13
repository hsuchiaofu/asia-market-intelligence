#!/usr/bin/env python3
"""Asia Market Intelligence 發布共用工具。"""
from __future__ import annotations
import json, re, shutil
from datetime import date, datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; REPORTS=DATA/'reports.json'
VALID_TYPES={'morning':'全球新聞晨報','asia-close':'亞洲股市收盤報'}
FORBIDDEN=('TODO','PLACEHOLDER','SAMPLE ONLY')

class _MetaDescriptionParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.descriptions=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()!='meta': return
        values={str(key).lower():value for key,value in attrs}
        if (values.get('name') or '').strip().lower()=='description':
            self.descriptions.append((values.get('content') or '').strip())

def extract_meta_description(text:str):
    parser=_MetaDescriptionParser(); parser.feed(text); parser.close()
    descriptions=[value for value in parser.descriptions if value]
    if len(descriptions)!=1: raise ValueError('Validation Failed: HTML 必須包含唯一且非空白的 meta description')
    return descriptions[0]

def validate_summary(kind,day,summary):
    value=re.sub(r'\s+',' ',str(summary)).strip()
    if not value: raise ValueError('Validation Failed: 報告摘要不可空白')
    if value==f'{day} {VALID_TYPES[kind]}': raise ValueError('Validation Failed: 報告摘要不得使用日期加報告類型的通用字串')
    if '\ufffd' in value or re.search(r'\?{2,}',value): raise ValueError('Validation Failed: 報告摘要含無效字元')
    if not re.search(r'[\u3400-\u4dbf\u4e00-\u9fff]',value): raise ValueError('Validation Failed: 報告摘要必須包含有效中文內容')
    return value

def load_config(): return json.loads((DATA/'site-config.json').read_text(encoding='utf-8'))
def load_reports():
    data=json.loads(REPORTS.read_text(encoding='utf-8'))
    if not isinstance(data,list): raise ValueError('reports.json 必須是陣列')
    return data
def validate_source(path:Path):
    try: text=path.read_text(encoding='utf-8')
    except UnicodeDecodeError as e: raise ValueError('來源必須是 UTF-8') from e
    if path.suffix.lower()!='.html' or len(text.strip())<500: raise ValueError('HTML 報告內容過短或格式錯誤')
    low=text.lower()
    for token in ('<!doctype html','<html','<head','<body','</html>'):
        if token not in low: raise ValueError(f'缺少必要 HTML 結構：{token}')
    if any(x.lower() in low for x in FORBIDDEN): raise ValueError('正式報告含禁止的預留文字')
    if '本網站內容僅供一般資訊與研究參考' not in text: raise ValueError('正式報告缺少免責聲明')
    return text
def backup(path:Path):
    if path.exists():
        stamp=datetime.now().strftime('%Y%m%d%H%M%S'); dest=ROOT/'.backups'/stamp/path.relative_to(ROOT); dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(path,dest)
def rebuild(reports=None):
    reports=reports if reports is not None else load_reports(); reports.sort(key=lambda x:(x['date'],x['updated']),reverse=True)
    REPORTS.write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    generate_sitemap(reports); generate_feed(reports)
def generate_sitemap(reports):
    cfg=load_config(); base=cfg.get('baseUrl','').rstrip('/'); pages=['','morning.html','asia-close.html','archive.html','popular.html','about.html','privacy.html']+[x['file'] for x in reports]
    locs='\n'.join(f'  <url><loc>{escape(base+"/"+p if base else p or "index.html")}</loc></url>' for p in pages)
    (ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+locs+'\n</urlset>\n',encoding='utf-8')
def generate_feed(reports):
    cfg=load_config(); base=cfg.get('baseUrl','').rstrip('/'); items=[]
    for x in reports[:20]:
        link=base+'/'+x['file'] if base else x['file']; pub=datetime.fromisoformat(x['updated']).astimezone(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
        items.append(f'<item><title>{escape(x["title"])}</title><link>{escape(link)}</link><guid>{escape(link)}</guid><description>{escape(x["summary"])}</description><category>{escape(VALID_TYPES[x["type"]])}</category><pubDate>{pub}</pubDate></item>')
    xml='<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Asia Market Intelligence</title><description>全球市場晨報與亞洲股市收盤研究</description><link>'+escape(base or '')+'</link>'+''.join(items)+'</channel></rss>\n'
    (ROOT/'feed.xml').write_text(xml,encoding='utf-8')
def add_report(kind,day,title,summary,source,allow_replace=False):
    if kind not in VALID_TYPES: raise ValueError('type 必須是 morning 或 asia-close')
    try: date.fromisoformat(day)
    except ValueError as e: raise ValueError('日期必須是 YYYY-MM-DD') from e
    if not title.strip(): raise ValueError('標題不可空白')
    summary=validate_summary(kind,day,summary)
    source=Path(source).resolve(); text=validate_source(source)
    if summary!=extract_meta_description(text): raise ValueError('Validation Failed: summary 必須與 HTML meta description 一致')
    reports=load_reports(); rid=f'{kind}-{day}'
    existing=next((x for x in reports if x['id']==rid),None)
    if existing and not allow_replace: raise ValueError(f'報告已存在：{rid}')
    dest=ROOT/'reports'/kind/f'{day}.html'; dest.parent.mkdir(parents=True,exist_ok=True); backup(dest); backup(REPORTS); shutil.copy2(source,dest)
    now=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
    item={'id':rid,'type':kind,'title':title.strip(),'date':day,'summary':summary.strip(),'file':dest.relative_to(ROOT).as_posix(),'updated':now,'status':'published','featured':False,'wordFile':''}
    if existing: reports[reports.index(existing)]=item
    else: reports.append(item)
    rebuild(reports); return item
