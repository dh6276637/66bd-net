#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests, time, pymysql, re, base64

DB = {'host':'localhost','user':'paper_user','password':'paper_db2026','database':'dongshushu_paper','charset':'utf8mb4'}
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def extract(title):
    for p in [r'GitHub热门项目:\s*(.+)', r'GitHub热门:\s*(.+)', r'^(.+)$']:
        m = re.search(p, title.strip())
        if m:
            n = m.group(1).strip()
            if n and 'GitHub' not in n:
                return n
    return None

def search(name):
    try:
        r = requests.get(f"https://api.github.com/search/repositories?q={name}+in:name&sort=stars&order=desc", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            for i in r.json().get('items', []):
                if i['name'].lower() == name.lower():
                    return i
            if r.json().get('items'):
                return r.json()['items'][0]
    except: pass
    return None

conn = pymysql.connect(**DB)
try:
    with conn.cursor() as cur:
        cur.execute("SELECT id, title FROM article WHERE source='GitHub Trending' AND (url IS NULL OR url='')")
        for aid, title in cur.fetchall():
            name = extract(title)
            if not name: continue
            repo = search(name)
            if not repo: continue
            print(f"Updating {aid}: {title[:30]} -> {repo['html_url']}")
            cur.execute("UPDATE article SET url=%s WHERE id=%s", (repo['html_url'], aid))
            conn.commit()
            time.sleep(1)
finally:
    conn.close()
