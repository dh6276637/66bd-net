#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彻底清洗文章内容中的URL暴露问题
"""
import MySQLdb
import re

DB_CONFIG = {"host": "localhost", "user": "paper_user", "passwd": "paper_db2026", "db": "dongshushu_paper", "charset": "utf8mb4"}

def clean_content(content):
    """清洗文章内容"""
    if not content:
        return content
    
    # 移除 "Article URL: https://..." 格式及其后续内容直到换行
    content = re.sub(r'Article URL:\s*https?://\S+', '', content, flags=re.IGNORECASE)
    
    # 移除 "Comments URL: https://..." 格式
    content = re.sub(r'Comments URL:\s*https?://\S+', '', content, flags=re.IGNORECASE)
    
    # 移除 "HN URL: https://..." 格式
    content = re.sub(r'HN URL:\s*https?://\S+', '', content, flags=re.IGNORECASE)
    
    # 移除 "URL: https://..." 格式
    content = re.sub(r'URL:\s*https?://\S+', '', content, flags=re.IGNORECASE)
    
    # 移除 "Source: https://..." 格式
    content = re.sub(r'Source:\s*https?://\S+', '', content, flags=re.IGNORECASE)
    
    # 移除 "Points: XXX" 格式（采集时的统计信息）
    content = re.sub(r'Points:\s*\d+', '', content, flags=re.IGNORECASE)
    
    # 移除 "# Comments: XXX" 格式
    content = re.sub(r'#\s*Comments:\s*\d+', '', content, flags=re.IGNORECASE)
    
    # 移除独立的URL行
    content = re.sub(r'^https?://\S+\s*$', '', content, flags=re.MULTILINE)
    
    # 清理URL旁边多余的空格和标点
    content = re.sub(r'\s{2,}', ' ', content)
    
    # 清理多余的空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content.strip()

def main():
    conn = MySQLdb.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # 查找所有文章
    cur.execute("SELECT id, title, content FROM article")
    articles = cur.fetchall()
    
    print(f"检查 {len(articles)} 篇文章...")
    
    updated = 0
    for article_id, title, content in articles:
        if not content:
            continue
        
        cleaned = clean_content(content)
        if cleaned != content:
            cur.execute("UPDATE article SET content = %s WHERE id = %s", (cleaned, article_id))
            updated += 1
    
    conn.commit()
    print(f"完成！已更新 {updated} 篇文章的内容")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
