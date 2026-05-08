#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清洗数据库中的URL暴露问题
1. 移除 "Article URL:" 和 "Comments URL:" 等原始URL
2. 清理其他采集时遗留的原始数据格式
"""

import MySQLdb
import re

DB_CONFIG = {"host": "localhost", "user": "paper_user", "passwd": "paper_db2026", "db": "dongshushu_paper", "charset": "utf8mb4"}

def clean_content(content):
    """清洗文章内容，移除原始URL暴露"""
    if not content:
        return content
    
    # 移除 "Article URL: https://..." 格式
    content = re.sub(r'Article URL:\s*https?://\S+', '', content, flags=re.IGNORECASE)
    
    # 移除 "Comments URL: https://..." 格式
    content = re.sub(r'Comments URL:\s*https?://\S+', '', content, flags=re.IGNORECASE)
    
    # 移除 "HN URL: https://..." 格式
    content = re.sub(r'HN URL:\s*https?://\S+', '', content, flags=re.IGNORECASE)
    
    # 移除 "URL: https://..." 格式
    content = re.sub(r'URL:\s*https?://\S+', '', content, flags=re.IGNORECASE)
    
    # 移除 "Source: https://..." 格式
    content = re.sub(r'Source:\s*https?://\S+', '', content, flags=re.IGNORECASE)
    
    # 移除独立的URL行（仅包含URL的行）
    content = re.sub(r'^https?://\S+\s*$', '', content, flags=re.MULTILINE)
    
    # 清理多余的空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content.strip()

def main():
    conn = MySQLdb.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # 查找包含原始URL的文章
    cur.execute("SELECT id, title, content FROM article WHERE content LIKE '%Article URL:%' OR content LIKE '%Comments URL:%' OR content LIKE '%HN URL:%'")
    articles = cur.fetchall()
    
    if not articles:
        print("没有发现需要清洗的文章")
        return
    
    print(f"发现 {len(articles)} 篇需要清洗的文章")
    
    updated = 0
    for article_id, title, content in articles:
        cleaned = clean_content(content)
        if cleaned != content:
            cur.execute("UPDATE article SET content = %s WHERE id = %s", (cleaned, article_id))
            updated += 1
            print(f"清洗文章 #{article_id}: {title[:50]}...")
    
    conn.commit()
    print(f"完成！已更新 {updated} 篇文章")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
