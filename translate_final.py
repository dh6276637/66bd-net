#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完善翻译脚本 - 中文文章也设置title_cn"""

import MySQLdb, time, json, urllib.request, urllib.parse, sys

DB_CONFIG = {"host": "localhost", "user": "paper_user", "passwd": "paper_db2026", "db": "dongshushu_paper", "charset": "utf8mb4"}

def is_english(t):
    if not t: return False
    t = t[:500]
    l = sum(1 for c in t if c.isalpha())
    if l < 10: return False
    return sum(1 for c in t if 0 < ord(c) < 128 and c.isalpha()) / l > 0.7

def trans(t):
    if not t or not is_english(t): return t
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
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    conn = MySQLdb.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT id, title, content FROM article WHERE title_cn IS NULL OR title_cn = '' ORDER BY id LIMIT %s", [n])
    arts = cur.fetchall()
    print("处理 %d 篇..." % len(arts))
    for i, (aid, title, content) in enumerate(arts):
        if is_english(title):
            print("[%d] 翻译: %s..." % (i+1, title[:40]))
            tc = trans(title)
            time.sleep(1)
            cc = trans_long(content) if content else content
            time.sleep(1.5)
            print("  -> %s" % tc[:40])
        else:
            print("[%d] 复制: %s..." % (i+1, title[:40]))
            tc = title
            cc = content
        cur.execute("UPDATE article SET title_cn=%s, content_cn=%s WHERE id=%s", 
                   (tc[:200], (cc[:5000] if cc else ''), aid))
        conn.commit()
    cur.close()
    conn.close()
    print("\n完成!")
