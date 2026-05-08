#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import MySQLdb
import urllib.request
import urllib.parse
import json
import time
import re

DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'paper_user',
    'passwd': 'paper_db2026',
    'db': 'dongshushu_paper',
    'charset': 'utf8mb4'
}

def google_translate(text, source_lang='en', target_lang='zh-CN'):
    if not text or len(text.strip()) < 2:
        return text
    try:
        url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=' + source_lang + '&tl=' + target_lang + '&dt=t&q=' + urllib.parse.quote(text[:500])
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data and data[0]:
                return ''.join(item[0] for item in data[0] if item[0])
    except Exception as e:
        print('    翻译API错误: ' + str(e))
    return text

def clean_github_title(title_cn, title):
    if not title_cn:
        return title_cn
    
    prefix = ''
    if title_cn.startswith('【开源项目】'):
        prefix = '【开源项目】'
    elif title_cn.startswith('GitHub热门'):
        prefix = 'GitHub热门: '
    
    content = title_cn.replace(prefix, '')
    content = re.sub(r'⭐\s*Stars?:\s*[\d,]+', '', content)
    content = re.sub(r'语言:\s*\S+', '', content)
    content = re.sub(r'Forks?:\s*[\d,]+', '', content)
    content = re.sub(r'许可证:\s*\S+', '', content)
    content = re.sub(r'星级[：:]\s*[\d,]+', '', content)
    content = re.sub(r'叉子[：:]\s*[\d,]+', '', content)
    content = re.sub(r'项目地址[：:]\s*\S+', '', content)
    content = re.sub(r'\s+[⭐语言许可证叉子].*$', '', content)
    content = content.strip().strip('⭐').strip()
    content = content.rstrip('?').rstrip().strip()
    
    return prefix + content if prefix else content

def main():
    print('=' * 60)
    print('修复文章标题')
    print('=' * 60)
    
    conn = MySQLdb.connect(**DB_CONFIG)
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    
    # Task 1: Clean GitHub titles
    print('\n【任务1】清理GitHub标题...')
    cursor.execute('''SELECT id, title, title_cn, content FROM article 
        WHERE (title_cn LIKE '%Stars%' OR title_cn LIKE '%Forks%' OR title_cn LIKE '%语言%' 
               OR title_cn LIKE '%许可证%' OR title_cn LIKE '%叉子%' OR title_cn LIKE '%项目地址%'
               OR title_cn LIKE '%星级%')
        AND source IN ('GitHub', 'GitHub Trending')
        ''')
    github_articles = cursor.fetchall()
    print('  找到 %d 篇需要清理的GitHub文章' % len(github_articles))
    
    cleaned_count = 0
    for article in github_articles:
        old_title_cn = article['title_cn']
        new_title_cn = clean_github_title(old_title_cn, article['title'])
        
        if not new_title_cn or new_title_cn in ['【开源项目】', 'GitHub热门: ', 'GitHub热门项目: ']:
            project_name = article['title'].replace('GitHub热门项目: ', '').replace('GitHub热门: ', '').strip()
            if '【开源项目】' in old_title_cn:
                new_title_cn = '【开源项目】' + project_name
            else:
                new_title_cn = project_name
        
        content = article.get('content', '') or ''
        desc_match = re.search(r'项目说明[：:]\s*(.+?)(?:\n|$)', content)
        if desc_match:
            desc = desc_match.group(1).strip()
            if desc and desc != '暂无项目描述' and len(desc) < 100:
                if new_title_cn.startswith('【开源项目】'):
                    new_title_cn = new_title_cn + ' - ' + desc
                else:
                    new_title_cn = new_title_cn + ' - ' + desc
        
        if new_title_cn != old_title_cn:
            new_title = clean_github_title(article['title'], article['title'])
            if not new_title:
                new_title = article['title'].split('⭐')[0].strip().split('?')[0].strip()
            
            cursor.execute('UPDATE article SET title_cn = %s, title = %s WHERE id = %s', 
                         (new_title_cn, new_title, article['id']))
            conn.commit()
            cleaned_count += 1
            print('  ✓ ID %d: %s... -> %s...' % (article['id'], old_title_cn[:40], new_title_cn[:40]))
    
    print('  已清理 %d 篇GitHub文章' % cleaned_count)
    
    # Task 2: Translate English titles
    print('\n【任务2】翻译英文标题...')
    all_en_titles = []
    cursor.execute('SELECT id, title, title_cn FROM article WHERE title_cn LIKE \'%科技资讯%\' OR title_cn LIKE \'%开源项目%\'')
    for row in cursor.fetchall():
        title_cn = row['title_cn']
        prefix = ''
        if title_cn.startswith('【科技资讯】'):
            prefix = '【科技资讯】'
        elif title_cn.startswith('【开源项目】'):
            prefix = '【开源项目】'
        
        content_after_prefix = title_cn.replace(prefix, '')
        if content_after_prefix and re.match(r'^[A-Za-z0-9\s\-\–\—:]+$', content_after_prefix):
            all_en_titles.append(row)
    
    print('  找到 %d 篇需要翻译的英文标题' % len(all_en_titles))
    
    translated_count = 0
    for article in all_en_titles:
        title_cn = article['title_cn']
        prefix = ''
        if title_cn.startswith('【科技资讯】'):
            prefix = '【科技资讯】'
        elif title_cn.startswith('【开源项目】'):
            prefix = '【开源项目】'
        
        content_to_translate = title_cn.replace(prefix, '')
        print('  翻译: %s...' % content_to_translate[:50])
        
        translated = google_translate(content_to_translate)
        time.sleep(1.5)
        
        if translated and translated != content_to_translate:
            new_title_cn = prefix + translated
            cursor.execute('UPDATE article SET title_cn = %s WHERE id = %s', 
                         (new_title_cn, article['id']))
            conn.commit()
            translated_count += 1
            print('  ✓ -> %s...' % translated[:50])
        else:
            print('  ✗ 翻译失败或无变化')
    
    print('  已翻译 %d 篇英文标题' % translated_count)
    
    cursor.close()
    conn.close()
    
    print('\n' + '=' * 60)
    print('完成! 清理: %d 篇, 翻译: %d 篇' % (cleaned_count, translated_count))
    print('=' * 60)

if __name__ == '__main__':
    main()
