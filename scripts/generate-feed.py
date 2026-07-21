#!/usr/bin/env python3
from site_tools import generate_feed,load_reports
if __name__=='__main__': generate_feed(load_reports()); print('feed.xml generated')
