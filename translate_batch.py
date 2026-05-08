#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import MySQLdb, time, json, urllib.request, urllib.parse, sys

DB_CONFIG = {"host": "localhost", "user": "paper_user", "passwd": "paper_db2026", "db": "dongshushu_paper", "charset": "utf8mb4"}

ENGLISH_SOURCES = ['Michael Larabel', 'Seebug Paper', 'OpenAI博客', 'GitHub Trending',
    'TheHackerNews', 'Dan Goodin', 'Eric Berger', 'Thomas Macaulay', 
    'Jess Weatherbed', 'Emma Roth', 'Jay Peters', 'Jessica Hamzelou']

def is_en(t):
    if not t: return False
    l = sum(1 for c in t if c.isalpha())
    if l == 0: return False
    return sum(1 for c in t if 0 < ord(c) < 128 and c.isalpha()) / l > 0.5

def trans(t):
    if not t or not is_en(t): return t
    try:
        u = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q=" + urllib.parse.quote(t[:4500])
        req = urllib.request.Request(u)
        req.add_header('User-Agent', 'Mozilla/5.0')
        r = json.loads(urllib.request.urlopen(req, timeout=15).read())
        return ''.join(i[0] for i in r[0] if i[0])
    except Exception as e:
        print("ERR:" + str(e)[:50])
        return t

def trans_long(t):
    if not t or len(t) <= 1800: return trans(t)
    ps = t.split('\n\n')
    r, c, l = [], [], 0
    for p in ps:
        if l + len(p) > 1800 and c:
            r.append(trans('\n\n'.join(c)))
            time.sleep(1.2)
            c, l = [], 0
        c.append(p)
        l += len(p)
    if c: r.append(trans('\n\n'.join(c)))
    return '\n\n'.join(r)

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    conn = MySQLdb.connect(**DB_CONFIG)
    cur = conn.cursor()
    ph = ','.join(['%s'] * len(ENGLISH_SOURCES))
    cur.execute("SELECT id, title, content FROM article WHERE (title_cn IS NULL OR title_cn = '') AND source IN (" + ph + ") ORDER BY id LIMIT %s", ENGLISH_SOURCES + [n])
    arts = cur.fetchall()
    print("翻译 %d 篇" % len(arts))
    for i, (aid, title, content) in enumerate(arts):
        print("[%d] %s..." % (i+1, title[:40]))
        tc = trans(title)
        time.sleep(1)
        cc = trans_long(content) if content else content
        time.sleep(1.5)
        cur.execute("UPDATE article SET title_cn=%s, content_cn=%s WHERE id=%s", (tc[:200], (cc[:5000] if cc else ''), aid))
        conn.commit()
        print("  OK")
    cur.close()
    conn.close()
    print("完成!")
