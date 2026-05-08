
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清洗文章数据 - 去除重复内容和模板套话摘要"""

import MySQLdb
import re
from collections import Counter

DB_CONFIG = {"host": "localhost", "user": "paper_user", "passwd": "paper_db2026", "db": "dongshushu_paper", "charset": "utf8mb4"}

def get_db():
    return MySQLdb.connect(**DB_CONFIG)

def remove_duplicate_content(content):
    """去除重复内容 - 检测并合并重复段落"""
    if not content:
        return content
    
    # 按段落分割
    paragraphs = content.split('\n\n')
    unique_paragraphs = []
    seen = set()
    
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        
        # 归一化：去除多余空格、转小写
        normalized = ' '.join(p.split()).lower()
        
        # 跳过太短的段落
        if len(normalized) < 50:
            # 如果是链接或代码块，保留
            if p.startswith('http') or p.startswith('🔗') or p.startswith('#'):
                if normalized not in seen:
                    seen.add(normalized)
                    unique_paragraphs.append(p)
            continue
        
        # 检查是否重复
        if normalized not in seen:
            seen.add(normalized)
            unique_paragraphs.append(p)
        else:
            print(f"  发现重复段落，已去除")
    
    return '\n\n'.join(unique_paragraphs)

def clean_summary(summary, content):
    """清洗摘要 - 去掉模板套话，使用真实内容"""
    # 检测是否是模板套话
    template_patterns = [
        r'^本文报道了.*最新动态',
        r'^.*是近期热门话题',
        r'^关于.*的报道引起了.*关注',
    ]
    
    for pattern in template_patterns:
        if re.match(pattern, summary or ''):
            # 用真实内容替换
            if content:
                # 提取content前150字
                clean_content = re.sub(r'<[^>]+>', '', content)
                clean_content = ' '.join(clean_content.split())
                if len(clean_content) > 150:
                    summary = clean_content[:150].rstrip() + '...'
                else:
                    summary = clean_content
            else:
                summary = ''
            break
    
    return summary

def main():
    conn = get_db()
    cur = conn.cursor()
    
    print("开始清洗数据...")
    
    # 1. 删除V2EX来源的文章
    cur.execute("DELETE FROM article WHERE source = 'V2EX' OR source LIKE '%v2ex%'")
    deleted_v2ex = cur.rowcount
    print(f"删除V2EX文章: {deleted_v2ex}篇")
    
    # 2. 删除使用模板套话的文章
    cur.execute("DELETE FROM article WHERE content LIKE '%本文报道了%' OR content LIKE '%是近期热门话题%' OR content LIKE '%引起了业界关注%'")
    deleted_template = cur.rowcount
    print(f"删除模板套话文章: {deleted_template}篇")
    
    conn.commit()
    
    # 3. 修复剩余文章的重复内容和摘要
    cur.execute("SELECT id, title, content, summary FROM article WHERE 1=1")
    articles = cur.fetchall()
    
    fixed_count = 0
    for article_id, title, content, summary in articles:
        needs_update = False
        new_content = content
        new_summary = summary
        
        # 检查并修复重复内容
        if content and content.count('\n\n') > 5:
            # 检测重复
            paragraphs = content.split('\n\n')
            if len(paragraphs) != len(set(paragraphs)):
                new_content = remove_duplicate_content(content)
                if new_content != content:
                    needs_update = True
                    print(f"  修复文章 #{article_id} 的重复内容")
        
        # 修复摘要
        if summary:
            new_summary = clean_summary(summary, content)
            if new_summary != summary:
                needs_update = True
                print(f"  修复文章 #{article_id} 的摘要")
        
        if needs_update:
            cur.execute("UPDATE article SET content=%s, summary=%s WHERE id=%s", 
                       (new_content, new_summary, article_id))
            fixed_count += 1
    
    conn.commit()
    print(f"\n修复完成! 共修复 {fixed_count} 篇文章")
    
    cur.close()
    conn.close()
    
    # 打印统计
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT category, COUNT(*) as cnt FROM article GROUP BY category ORDER BY cnt DESC")
    print("\n当前文章分布:")
    for cat, cnt in cur.fetchall():
        print(f"  {cat}: {cnt}篇")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
