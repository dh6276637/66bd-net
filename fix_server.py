#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接在服务器上执行的修复脚本
"""
import MySQLdb
import urllib.request
import urllib.parse
import json
import time
import re
import sys
import os

print("="*60)
print("开始修复66必读网站...")
print("="*60)

# 备份函数
def backup_file(path):
    if os.path.exists(path):
        bak = path + '.bak.' + time.strftime('%Y%m%d%H%M%S')
        with open(path, 'r') as f:
            content = f.read()
        with open(bak, 'w') as f:
            f.write(content)
        print(f"已备份: {bak}")
        return bak
    return None

# text_to_html函数
TEXT_TO_HTML_FUNC = '''
def text_to_html(text):
    """将纯文本转为格式化HTML"""
    if not text:
        return ''
    # 先处理GitHub项目信息
    text = re.sub(r'⭐\\s*Stars:\\s*([\\d,]+)', r'<div class="gh-stat"><span class="gh-stat-label">⭐ Stars</span><span class="gh-stat-value">\\1</span></div>', text)
    text = re.sub(r'Forks:\\s*([\\d,]+)', r'<div class="gh-stat"><span class="gh-stat-label">Forks</span><span class="gh-stat-value">\\1</span></div>', text)
    text = re.sub(r'许可证:\\s*(\\S+)', r'<div class="gh-license">许可证: \\1</div>', text)
    text = re.sub(r'项目地址:\\s*(https?://\\S+)', r'<div class="gh-link">🔗 <a href="\\1" target="_blank" rel="noopener">\\1</a></div>', text)
    # URL转链接
    def make_link(match):
        url = match.group(1)
        return '<a href="' + url + '" target="_blank" rel="noopener">' + url + '</a> '
    text = re.sub(r'(https?://\\S+?)(?:\\s|$|<)', make_link, text)
    # 段落分隔
    paragraphs = text.split('\\n\\n')
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        p = p.replace('\\n', '<br>')
        if p.startswith('<div'):
            html_parts.append(p)
        else:
            html_parts.append('<p>' + p + '</p>')
    return '\\n'.join(html_parts)

'''

# translate_text函数
TRANSLATE_FUNC = '''
def translate_text(text, source_lang='en', target_lang='zh-CN'):
    """使用MyMemory API翻译文本"""
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
            url = 'https://api.mymemory.translated.net/get?q=' + urllib.parse.quote(seg[:500]) + '&langpair=' + source_lang + '|' + target_lang
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                translated.append(data.get('responseData', {}).get('translatedText', seg))
            time.sleep(0.5)
        except Exception as e:
            translated.append(seg)
    return '\\n'.join(translated)

'''

# 读取app.py
print("\n1. 读取app.py...")
with open('/var/www/dongshushu-paper/app.py', 'r') as f:
    app_content = f.read()
print(f"  app.py长度: {len(app_content)}")

# 读取模板
print("2. 读取模板...")
with open('/var/www/dongshushu-paper/templates/article_detail.html', 'r') as f:
    template_content = f.read()
print(f"  模板长度: {len(template_content)}")

# 备份
print("\n3. 备份文件...")
backup_file('/var/www/dongshushu-paper/app.py')
backup_file('/var/www/dongshushu-paper/templates/article_detail.html')

# 修改app.py
print("\n4. 修改app.py...")

# 添加函数
if 'def text_to_html' not in app_content:
    # 在app = Flask之后添加
    app_line = app_content.find('app = Flask')
    if app_line > 0:
        insert_pos = app_content.find('\n', app_line) + 1
        app_content = app_content[:insert_pos] + TEXT_TO_HTML_FUNC + TRANSLATE_FUNC + app_content[insert_pos:]
        print("  ✓ 已添加text_to_html和translate_text函数")

# 修改article_detail路由中的render_template
if "render_template('article_detail.html', article=article" in app_content:
    old = "render_template('article_detail.html', article=article"
    new = "render_template('article_detail.html', article=article, content_html=text_to_html(article.content if article.content else ''), content_cn_html=text_to_html(article.content_cn) if article.content_cn else '')"
    app_content = app_content.replace(old, new)
    print("  ✓ 已修改render_template")
elif 'render_template("article_detail.html", article=article' in app_content:
    old = 'render_template("article_detail.html", article=article'
    new = 'render_template("article_detail.html", article=article, content_html=text_to_html(article.content if article.content else ""), content_cn_html=text_to_html(article.content_cn) if article.content_cn else "")'
    app_content = app_content.replace(old, new)
    print("  ✓ 已修改render_template(双引号)")

# 保存app.py
print("\n5. 保存app.py...")
with open('/var/www/dongshushu-paper/app.py', 'w') as f:
    f.write(app_content)
print("  ✓ app.py已保存")

# 修改模板
print("\n6. 修改模板...")

# 添加CSS样式
CSS_STYLE = '''
<style>
.gh-stat { display: inline-block; margin-right: 15px; font-family: var(--wired-font-mono); font-size: 0.85em; }
.gh-stat-label { color: var(--wired-gray); }
.gh-stat-value { font-weight: bold; margin-left: 5px; }
.gh-tags { font-family: var(--wired-font-mono); font-size: 0.8em; color: var(--wired-gray); margin: 8px 0; }
.gh-license { font-family: var(--wired-font-mono); font-size: 0.8em; color: var(--wired-gray); margin: 5px 0; }
.gh-link { font-family: var(--wired-font-mono); font-size: 0.85em; word-break: break-all; margin: 8px 0; }
.gh-link a { color: #057dbc; }
.translation-section { margin-top: 30px; padding-top: 20px; border-top: 2px dashed #ccc; }
.translation-divider { text-align: center; margin-bottom: 15px; position: relative; }
.translation-divider::before { content: ''; position: absolute; top: 50%; left: 0; right: 0; border-top: 2px dashed #ccc; }
.translation-divider span { font-family: var(--wired-font-mono); font-size: 0.7em; text-transform: uppercase; letter-spacing: 2px; color: var(--wired-gray); background: #fff; padding: 0 10px; position: relative; }
</style>
'''

if '<style>' not in template_content or 'gh-stat' not in template_content:
    if '</head>' in template_content:
        template_content = template_content.replace('</head>', CSS_STYLE + '\n</head>')
    else:
        template_content = CSS_STYLE + template_content
    print("  ✓ 已添加CSS样式")

# 替换内容显示
if '{{ article.content|safe }}' in template_content:
    old_content = "{{ article.content|safe }}"
    new_content = """{% if content_html %}
<div class="article-content formatted-content">
    {{ content_html|safe }}
</div>
{% endif %}"""
    template_content = template_content.replace(old_content, new_content)
    print("  ✓ 已替换article.content为content_html")

# 添加中文翻译区域
if 'translation-section' not in template_content:
    if '</article>' in template_content:
        translation_section = '''
{% if content_cn_html %}
<div class="translation-section">
    <div class="translation-divider"><span>中文翻译</span></div>
    <div class="article-content formatted-content">
        {{ content_cn_html|safe }}
    </div>
</div>
{% endif %}
'''
        template_content = template_content.replace('</article>', translation_section + '</article>')
        print("  ✓ 已添加中文翻译区域")

# 保存模板
print("\n7. 保存模板...")
with open('/var/www/dongshushu-paper/templates/article_detail.html', 'w') as f:
    f.write(template_content)
print("  ✓ 模板已保存")

# 批量翻译
print("\n8. 批量翻译未翻译的文章...")
try:
    conn = MySQLdb.connect(host='localhost', user='paper_user', passwd='paper_db2026', db='dongshushu_paper', charset='utf8mb4')
    cur = conn.cursor()
    
    cur.execute("SELECT id, content, title FROM article WHERE (content_cn IS NULL OR content_cn = '') AND content IS NOT NULL AND content != ''")
    articles = cur.fetchall()
    
    print(f"  找到 {len(articles)} 篇需要翻译的文章")
    
    success_count = 0
    for i, (aid, content, title) in enumerate(articles):
        if not content:
            continue
        # 检测是否需要翻译
        en_chars = sum(1 for c in content if ord(c) < 128 and c.isalpha())
        total_alpha = sum(1 for c in content if c.isalpha())
        if total_alpha > 0 and en_chars / total_alpha >= 0.5:
            print(f"  [{i+1}/{len(articles)}] 翻译文章 {aid}: {str(title)[:30]}...")
            cn = translate_text(content)
            if cn and cn != content:
                cur.execute("UPDATE article SET content_cn=%s WHERE id=%s", (cn, aid))
                conn.commit()
                print(f"    ✓ 翻译成功 ({len(cn)} 字符)")
                success_count += 1
            time.sleep(0.5)
    
    cur.close()
    conn.close()
    print(f"  翻译完成: {success_count} 篇")
    
except Exception as e:
    print(f"  翻译过程出错: {e}")

# 重启Gunicorn
print("\n9. 重启Gunicorn...")
os.system("pkill -9 gunicorn")
time.sleep(2)
result = os.system("cd /var/www/dongshushu-paper && gunicorn -c gunicorn_config.py app:app -D")
if result == 0:
    print("  ✓ Gunicorn已重启")
else:
    print("  ! Gunicorn重启可能有问题")

time.sleep(3)

# 验证
print("\n10. 验证修复...")
result = os.popen("curl -s http://127.0.0.1:8000/article/1 2>&1 | head -c 1000").read()
if '<p>' in result or 'formatted-content' in result:
    print("  ✓ 验证成功: 文章内容已格式化为HTML")
elif 'Internal Server Error' in result:
    print("  ! 服务器有错误，请检查日志")
else:
    print(f"  验证输出前500字符:\n{result[:500]}")

print("\n" + "="*60)
print("修复完成!")
print("="*60)
