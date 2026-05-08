#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量翻译脚本 v2 - 只翻译真正的英文文章
"""

import MySQLdb
import time
import json
import urllib.request
import urllib.parse
import sys

DB_CONFIG = {"host": "localhost", "user": "paper_user", "passwd": "paper_db2026", "db": "dongshushu_paper", "charset": "utf8mb4"}

# 英文来源列表
ENGLISH_SOURCES = [
    'Michael Larabel', 'Seebug Paper', 'OpenAI博客', 'GitHub Trending',
    'TheHackerNews', 'The Hacker News', 'Dan Goodin', 'Eric Berger',
    'Thomas Macaulay', 'Jess Weatherbed', 'Emma Roth', 'Jay Peters',
    'Jessica Hamzelou', 'Chris Haslam', 'Lily Hay Newman', 'Lisa Martin',
    'Mitchell Clark', 'Allison Matyus', 'Taylor Tier at', 'James Rover',
    'Kenneth Eng', 'Anthony D. May', 'Riyana', 'Haje Jan Kamps',
    'Devin Coldewey', 'Natasha Lomas', 'Catherine H. Craft'
]

def is_english_text(text):
    """判断文本是否以英文为主（英文字母占比>50%）"""
    if not text:
        return False
    letters = sum(1 for c in text if c.isalpha())
    if letters == 0:
        return False
    english_letters = sum(1 for c in text if ord(c) < 128 and c.isalpha())
    return english_letters / letters > 0.5

def translate_to_chinese(text, max_retries=3):
    """使用Google Translate API将英文翻译成中文"""
    if not text or len(text.strip()) == 0:
        return text
    
    # 非英文内容不需要翻译
    if not is_english_text(text):
        return text
    
    for attempt in range(max_retries):
        try:
            # 限制文本长度
            text_to_translate = text[:4500]
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q={urllib.parse.quote(text_to_translate)}"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            if result and len(result) > 0 and result[0]:
                translated_parts = []
                for item in result[0]:
                    if item[0]:
                        translated_parts.append(item[0])
                return ''.join(translated_parts)
        except Exception as e:
            print(f"翻译失败 (尝试 {attempt+1}/{max_retries}): {str(e)[:80]}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    return text

def translate_long_text(text, chunk_size=1800):
    """翻译长文本，分段处理"""
    if not text or len(text) <= chunk_size:
        return translate_to_chinese(text)
    
    paragraphs = text.split('\n\n')
    translated = []
    current_chunk = []
    current_length = 0
    
    for para in paragraphs:
        if current_length + len(para) > chunk_size and current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            translated.append(translate_to_chinese(chunk_text))
            time.sleep(1.2)
            current_chunk = []
            current_length = 0
        
        current_chunk.append(para)
        current_length += len(para)
    
    if current_chunk:
        chunk_text = '\n\n'.join(current_chunk)
        translated.append(translate_to_chinese(chunk_text))
    
    return '\n\n'.join(translated)

def main():
    """主函数"""
    conn = MySQLdb.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        # 查找需要翻译的文章（英文来源 + title_cn为空）
        cur.execute("""
            SELECT id, title, content, source 
            FROM article 
            WHERE (title_cn IS NULL OR title_cn = '') 
              AND source IN (%s)
            ORDER BY id
        """ % ','.join(['%s'] * len(ENGLISH_SOURCES)), ENGLISH_SOURCES)
        
        articles = cur.fetchall()
        total = len(articles)
        print(f"需要翻译的文章数: {total}")
        
        if total == 0:
            print("没有需要翻译的文章")
            return
        
        success_count = 0
        error_count = 0
        
        for i, (article_id, title, content, source) in enumerate(articles):
            try:
                print(f"\n[{i+1}/{total}] 来源: {source}")
                print(f"  原文标题: {title[:60]}...")
                
                # 翻译标题
                if is_english_text(title):
                    title_cn = translate_to_chinese(title)
                    print(f"  译标题: {title_cn[:60]}...")
                else:
                    title_cn = title
                
                time.sleep(1)
                
                # 翻译正文
                if content and len(content) > 50:
                    print(f"  翻译正文 (长度: {len(content)})...")
                    content_cn = translate_long_text(content)
                    print(f"  翻译完成 (译长度: {len(content_cn)})")
                else:
                    content_cn = content
                
                # 更新数据库
                cur.execute("""
                    UPDATE article 
                    SET title_cn = %s, content_cn = %s 
                    WHERE id = %s
                """, (title_cn[:200] if title_cn else '', 
                      content_cn[:5000] if content_cn else '', 
                      article_id))
                conn.commit()
                success_count += 1
                print(f"  ✓ 已更新")
                
                # 间隔
                time.sleep(1.5)
                
            except Exception as e:
                error_count += 1
                print(f"  ✗ 失败: {str(e)[:80]}")
                conn.rollback()
                continue
        
        print(f"\n=== 完成 ===")
        print(f"成功: {success_count}, 失败: {error_count}")
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()

