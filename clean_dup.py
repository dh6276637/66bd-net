
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import MySQLdb
from MySQLdb.cursors import DictCursor

DB_CONFIG = {"host": "localhost", "user": "paper_user", "passwd": "paper_db2026", "db": "dongshushu_paper", "charset": "utf8mb4"}

def get_db():
    return MySQLdb.connect(**DB_CONFIG)

def remove_duplicate_content(content):
    if not content:
        return content
    
    paragraphs = content.split('\n\n')
    unique = []
    seen = set()
    
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        normalized = ' '.join(p.split()).lower()
        if len(normalized) < 30:
            if normalized not in seen:
                seen.add(normalized)
                unique.append(p)
            continue
        if normalized not in seen:
            seen.add(normalized)
            unique.append(p)
    
    result = '\n\n'.join(unique)
    return result

def main():
    conn = get_db()
    cur = conn.cursor(DictCursor)
    
    print("=== 清洗重复内容 ===")
    
    # 获取所有文章
    cur.execute("SELECT id, title, content FROM article")
    articles = cur.fetchall()
    
    fixed = 0
    for a in articles:
        if not a['content']:
            continue
        
        # 检测重复
        paras = a['content'].split('\n\n')
        if len(paras) != len(set(paras)):
            new_content = remove_duplicate_content(a['content'])
            if new_content != a['content']:
                cur.execute("UPDATE article SET content=%s WHERE id=%s", (new_content, a['id']))
                fixed += 1
                print(f"  修复 #{a['id']}: {a['title'][:30]}...")
    
    conn.commit()
    print(f"\n修复重复内容: {fixed}篇")
    
    # 统计
    cur.execute("SELECT category, COUNT(*) as cnt FROM article GROUP BY category ORDER BY cnt DESC")
    print("\n文章分布:")
    for cat, cnt in cur.fetchall():
        print(f"  {cat}: {cnt}篇")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
