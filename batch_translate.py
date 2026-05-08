#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量翻译脚本 - 翻译数据库中未翻译的文章
"""

import MySQLdb
import time
import json
import urllib.request
import urllib.parse
import sys

DB_CONFIG = {"host": "localhost", "user": "paper_user", "passwd": "paper_db2026", "db": "dongshushu_paper", "charset": "utf8mb4"}

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
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q={urllib.parse.quote(text[:5000])}"
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

def batch_translate(batch_size=10):
    """批量翻译文章"""
    conn = MySQLdb.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        # 统计待翻译数量
        cur.execute("SELECT COUNT(*) FROM article WHERE (title_cn IS NULL OR title_cn = '' OR title_cn = title) OR (content_cn IS NULL OR content_cn = '' OR content_cn = content)")
        total = cur.fetchone()[0]
        print(f"待翻译文章总数: {total}")
        
        if total == 0:
            print("没有需要翻译的文章")
            return
        
        # 分批处理
        offset = 0
        translated_count = 0
        error_count = 0
        
        while True:
            # 获取待翻译的文章
            cur.execute("""
                SELECT id, title, content, title_cn, content_cn 
                FROM article 
                WHERE (title_cn IS NULL OR title_cn = '' OR title_cn = title) 
                   OR (content_cn IS NULL OR content_cn = '' OR content_cn = content)
                LIMIT %s OFFSET %s
            """, (batch_size, offset))
            
            articles = cur.fetchall()
            if not articles:
                break
            
            for article_id, title, content, title_cn, content_cn in articles:
                try:
                    needs_title_translate = not title_cn or title_cn == '' or title_cn == title
                    needs_content_translate = not content_cn or content_cn == '' or content_cn == content
                    
                    new_title_cn = title_cn if not needs_title_translate else None
                    new_content_cn = content_cn if not needs_content_translate else None
                    
                    # 翻译标题
                    if needs_title_translate and title:
                        print(f"翻译标题 [{article_id}]: {title[:40]}...")
                        new_title_cn = translate_to_chinese(title)
                        time.sleep(1)
                    
                    # 翻译正文
                    if needs_content_translate and content:
                        print(f"翻译正文 [{article_id}]...")
                        new_content_cn = translate_long_text(content)
                        time.sleep(1.5)
                    
                    # 更新数据库
                    if new_title_cn is not None or new_content_cn is not None:
                        update_sql = "UPDATE article SET "
                        update_params = []
                        if new_title_cn is not None:
                            update_sql += "title_cn = %s, "
                            update_params.append(new_title_cn[:200] if new_title_cn else '')
                        if new_content_cn is not None:
                            update_sql += "content_cn = %s, "
                            update_params.append(new_content_cn[:5000] if new_content_cn else '')
                        
                        update_sql = update_sql.rstrip(', ') + " WHERE id = %s"
                        update_params.append(article_id)
                        
                        cur.execute(update_sql, update_params)
                        conn.commit()
                        translated_count += 1
                        print(f"✓ 已更新 [{article_id}]")
                    
                    # 进度
                    offset += 1
                    if translated_count % 10 == 0:
                        print(f"\n=== 进度: {translated_count}/{total} ===\n")
                    
                except Exception as e:
                    error_count += 1
                    print(f"✗ 处理失败 [{article_id}]: {str(e)[:80]}")
                    conn.rollback()
                    continue
            
            # 批次间隔
            time.sleep(1)
        
        print(f"\n=== 翻译完成 ===")
        print(f"成功翻译: {translated_count}")
        print(f"失败: {error_count}")
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("=== 批量翻译脚本启动 ===")
    batch_translate()

