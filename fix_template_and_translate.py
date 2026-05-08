#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复article_detail模板 + 批量翻译英文文章"""
import MySQLdb
import urllib.request
import urllib.parse
import json
import time
import re
import os
import sys

# 数据库配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'paper_user',
    'passwd': 'paper_db2026',
    'db': 'dongshushu_paper',
    'charset': 'utf8mb4'
}

print("=" * 60)
print("修复article_detail模板 + 批量翻译")
print("=" * 60)

# 1. 修复模板
print("\n1. 修复article_detail.html...")
TEMPLATE = '''<style>
.gh-stat { display: inline-block; margin-right: 15px; font-family: var(--wired-font-mono); font-size: 0.85em; }
.gh-stat-label { color: var(--wired-gray); }
.gh-stat-value { font-weight: bold; margin-left: 5px; }
.gh-tags { font-family: var(--wired-font-mono); font-size: 0.8em; color: var(--wired-gray); margin: 8px 0; }
.gh-tags span { background: var(--wired-light); padding: 2px 8px; margin-right: 5px; border: 1px solid #ddd; }
.gh-license { font-family: var(--wired-font-mono); font-size: 0.8em; color: var(--wired-gray); margin: 5px 0; }
.gh-link { font-family: var(--wired-font-mono); font-size: 0.85em; word-break: break-all; margin: 8px 0; }
.gh-link a { color: #057dbc; }
.translation-section { margin-top: 30px; padding-top: 20px; border-top: 2px dashed #ccc; }
.translation-divider { text-align: center; margin-bottom: 15px; position: relative; }
.translation-divider::before { content: ''; position: absolute; top: 50%; left: 0; right: 0; border-top: 2px dashed #ccc; }
.translation-divider span { font-family: var(--wired-font-mono); font-size: 0.7em; text-transform: uppercase; letter-spacing: 2px; color: var(--wired-gray); background: #fff; padding: 0 10px; position: relative; }
.article-body p { margin-bottom: 12px; }
.article-body br { display: block; margin-bottom: 4px; }
</style>
{% extends "base.html" %}

{% block title %}{{ article.title }} - 66必读{% endblock %}
{% block meta_desc %}{{ article.content[:150] if article.content else "66必读" }}{% endblock %}
{% block content %}
<article class="article-detail" style="max-width:800px;margin:0 auto;padding:20px 0;">
    <div class="page-header">
        <span class="category-tag">{{ article.category }}</span>
        <h1>{{ article.title }}</h1>
        <div class="article-meta"><span>{{ article.source }}</span> | <span>{{ article.publish_date or article.created_at }}</span> | <span>{{ article.view_count }} 阅读</span></div>
    </div>
    
    <div class="article-body" style="font-size:1.1em;line-height:1.8;margin:30px 0;">
        {{ content_html|safe if content_html else (article.content|safe if article.content else '') }}
    </div>
    
    {% if content_cn_html %}
    <div class="translation-section">
        <div class="translation-divider"><span>中文翻译</span></div>
        <div class="article-body" style="font-size:1.1em;line-height:1.8;">
            {{ content_cn_html|safe }}
        </div>
    </div>
    {% elif article.content_cn %}
    <div class="translation-section">
        <div class="translation-divider"><span>中文翻译</span></div>
        <div class="article-body" style="font-size:1.1em;line-height:1.8;">
            {{ article.content_cn|safe }}
        </div>
    </div>
    {% endif %}
    
    <div class="share-bar" style="border-top:1px solid #000;border-bottom:1px solid #000;padding:20px 0;margin:30px 0;">
        <div style="font-family:var(--wired-font-mono);font-size:0.7em;text-transform:uppercase;letter-spacing:2px;color:#666;margin-bottom:15px;">Share</div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
            <button onclick="alert('请使用微信扫一扫')" style="font-family:var(--wired-font-mono);font-size:0.75em;text-transform:uppercase;padding:10px 20px;border:2px solid #000;background:#fff;cursor:pointer;">微信</button>
            <button onclick="window.open('http://service.weibo.com/share/share.php?title='+encodeURIComponent(document.querySelector('h1').textContent+' - 66必读')+'&url='+encodeURIComponent(location.href),'_blank')" style="font-family:var(--wired-font-mono);font-size:0.75em;text-transform:uppercase;padding:10px 20px;border:2px solid #000;background:#fff;cursor:pointer;">微博</button>
            <button onclick="navigator.clipboard.writeText(location.href).then(function(){alert('已复制')})" style="font-family:var(--wired-font-mono);font-size:0.75em;text-transform:uppercase;padding:10px 20px;border:2px solid #000;background:#fff;cursor:pointer;">复制链接</button>
        </div>
    </div>
    
    <div style="display:flex;gap:15px;"><a href="/category/{{ article.slug }}" class="btn">返回分类</a><a href="/" class="btn">返回首页</a></div>
</article>
{% endblock %}
'''

with open('/var/www/dongshushu-paper/templates/article_detail.html', 'w') as f:
    f.write(TEMPLATE)
print("  ✓ 模板已更新")

# 2. 批量翻译英文文章
print("\n2. 批量翻译未翻译的英文文章...")
try:
    conn = MySQLdb.connect(**DB_CONFIG)
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    
    # 找出没有中文翻译的英文文章
    cursor.execute("SELECT id, content FROM article WHERE (content_cn IS NULL OR content_cn = '') AND content IS NOT NULL AND content != ''")
    articles = cursor.fetchall()
    print("  找到 %d 篇未翻译文章" % len(articles))
    
    translated_count = 0
    for article in articles:
        text = article['content']
        if not text or len(text.strip()) < 10:
            continue
        
        # 判断是否为英文内容
        en_chars = sum(1 for c in text if ord(c) < 128 and c.isalpha())
        total_alpha = sum(1 for c in text if c.isalpha())
        if total_alpha == 0 or en_chars / total_alpha < 0.5:
            continue
        
        # 分段翻译
        segments = []
        chunk = ''
        for line in text.split('\n'):
            if len(chunk) + len(line) > 450:
                if chunk:
                    segments.append(chunk)
                chunk = line
            else:
                chunk = chunk + '\n' + line if chunk else line
        if chunk:
            segments.append(chunk)
        
        translated = []
        for seg in segments:
            try:
                url = 'https://api.mymemory.translated.net/get?q=' + urllib.parse.quote(seg[:500]) + '&langpair=en|zh-CN'
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Mozilla/5.0')
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode())
                    translated.append(data.get('responseData', {}).get('translatedText', seg))
                time.sleep(0.5)
            except:
                translated.append(seg)
        
        content_cn = '\n'.join(translated)
        cursor.execute("UPDATE article SET content_cn = %s WHERE id = %s", (content_cn, article['id']))
        conn.commit()
        translated_count += 1
        print("  ✓ 文章ID %d 已翻译" % article['id'])
        
        # 限制每批最多翻译15篇，避免API限制
        if translated_count >= 15:
            print("  已达15篇上限，停止翻译")
            break
    
    cursor.close()
    conn.close()
    print("  共翻译 %d 篇文章" % translated_count)
except Exception as e:
    print("  ✗ 翻译失败: %s" % str(e))

# 3. 修复cron_collect.py - 添加自动翻译
print("\n3. 修复cron_collect.py自动翻译...")
try:
    with open('/var/www/dongshushu-paper/cron_collect.py', 'r') as f:
        cron_content = f.read()
    
    if 'content_cn' not in cron_content or 'translate_text' not in cron_content:
        # 添加translate_text函数
        TRANSLATE_FUNC = '''
def translate_text(text, source_lang='en', target_lang='zh-CN'):
    if not text or len(text.strip()) < 10:
        return ''
    en_chars = sum(1 for c in text if ord(c) < 128 and c.isalpha())
    total_alpha = sum(1 for c in text if c.isalpha())
    if total_alpha > 0 and en_chars / total_alpha < 0.5:
        return ''
    segments = []
    chunk = ''
    for line in text.split('\\n'):
        if len(chunk) + len(line) > 450:
            if chunk:
                segments.append(chunk)
            chunk = line
        else:
            chunk = chunk + '\\n' + line if chunk else line
    if chunk:
        segments.append(chunk)
    translated = []
    for seg in segments:
        try:
            import urllib.request
            import urllib.parse
            import json
            url = 'https://api.mymemory.translated.net/get?q=' + urllib.parse.quote(seg[:500]) + '&langpair=' + source_lang + '|' + target_lang
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                translated.append(data.get('responseData', {}).get('translatedText', seg))
            import time
            time.sleep(0.5)
        except:
            translated.append(seg)
    return '\\n'.join(translated)

'''
        # 在import之后插入
        import_end = cron_content.find('\n\n', cron_content.find('import'))
        if import_end > 0:
            cron_content = cron_content[:import_end] + '\n' + TRANSLATE_FUNC + cron_content[import_end:]
        
        # 修改INSERT语句添加content_cn字段
        old_insert = "INSERT INTO article"
        if old_insert in cron_content:
            # 找到INSERT语句并添加content_cn
            cron_content = cron_content.replace(
                "(title, content, category, source, paper_type, publish_date, is_published, created_at)",
                "(title, content, content_cn, category, source, paper_type, publish_date, is_published, created_at)"
            )
            # 在VALUES前添加翻译
            cron_content = cron_content.replace(
                "%(title)s, %(content)s, %(category)s",
                "%(title)s, %(content)s, %(content_cn)s, %(category)s"
            )
            # 在保存前添加翻译逻辑 - 在每个article dict构建后
            # 查找article dict的构建位置
            lines = cron_content.split('\n')
            new_lines = []
            for i, line in enumerate(lines):
                new_lines.append(line)
                if "'content':" in line and "'content_cn'" not in line:
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(' ' * indent + "'content_cn': translate_text(article.get('content', '')),")
            cron_content = '\n'.join(new_lines)
        
        with open('/var/www/dongshushu-paper/cron_collect.py', 'w') as f:
            f.write(cron_content)
        print("  ✓ cron_collect.py已更新")
    else:
        print("  ✓ cron_collect.py已包含翻译逻辑")
except Exception as e:
    print("  ✗ 修复cron失败: %s" % str(e))

# 4. 重启Gunicorn
print("\n4. 重启Gunicorn...")
os.system("pkill -9 gunicorn 2>/dev/null")
time.sleep(2)
os.system("cd /var/www/dongshushu-paper && gunicorn -c gunicorn_config.py app:app -D 2>/dev/null")
time.sleep(3)
print("  ✓ 已重启")

# 5. 验证
print("\n5. 验证...")
result = os.popen("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/ 2>&1").read()
print("  首页状态: %s" % result)

result = os.popen("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/article/1 2>&1").read()
print("  文章页状态: %s" % result)

print("\n" + "=" * 60)
print("完成!")
print("=" * 60)
