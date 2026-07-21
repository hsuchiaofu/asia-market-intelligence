#!/usr/bin/env python3
from site_tools import generate_sitemap,load_reports
if __name__=='__main__': generate_sitemap(load_reports()); print('sitemap.xml generated')
