#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""智能批量翻译脚本 - 基于内容判断是否需要翻译"""

import MySQLdb, time, json, urllib.request, urllib.parse, sys

DB_CONFIG = {"host": "localhost", "user": "paper_user", "passwd": "paper_db2026", "db": "dongshushu_paper", "charset": "utf8mb4"}

def is_english(text):
    """判断文本是否以英文为主"""
    if not text: return False
    text = text[:500]  # 只检查前500字符
    letters = sum(1 for c in text if c.isalpha())
    if letters < 10: return False  # 太短不判断
    en = sum(1 for c in text if 0 < ord(c) < 128 and c.isalpha())
    return en / letters > 0.7 if letters > 0 else False

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
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    conn = MySQLdb.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT id, title, content FROM article WHERE title_cn IS NULL OR title_cn = '' ORDER BY id LIMIT %s", [n])
    arts = cur.fetchall()
    print("检查 %d 篇..." % len(arts))
    trans_count, skip_count = 0, 0
    for i, (aid, title, content) in enumerate(arts):
        if not is_english(title) and not is_english(content):
            print("[%d] 跳过(非英文): %s..." % (i+1, title[:40]))
            skip_count += 1
            continue
        print("[%d] 翻译: %s..." % (i+1, title[:40]))
        tc = trans(title)
        time.sleep(1)
        cc = trans_long(content) if content else content
        time.sleep(1.5)
        cur.execute("UPDATE article SET title_cn=%s, content_cn=%s WHERE id=%s", (tc[:200], (cc[:5000] if cc else ''), aid))
        conn.commit()
        print("  OK -> %s" % tc[:40])
        trans_count += 1
    cur.close()
    conn.close()
    print("\n完成! 翻译:%d 跳过:%d" % (trans_count, skip_count))
