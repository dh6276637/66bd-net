#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整修复脚本 - 直接重建app.py
"""
import MySQLdb
import urllib.request
import urllib.parse
import json
import time
import re
import os
import sys

print("="*60)
print("开始完整修复...")
print("="*60)

# 读取原始文件
print("\n1. 读取原始文件...")
with open('/var/www/dongshushu-paper/app.py', 'r') as f:
    content = f.read()
print(f"  原始长度: {len(content)}")

# 检查是否已经有text_to_html函数
has_text_to_html = 'def text_to_html' in content
has_translate_func = 'def translate_text' in content
has_render_mod = 'content_html=' in content

print(f"  has_text_to_html: {has_text_to_html}")
print(f"  has_translate_func: {has_translate_func}")
print(f"  has_render_mod: {has_render_mod}")

# 添加函数定义
TEXT_TO_HTML = '''
def text_to_html(text):
    """将纯文本转为格式化HTML"""
    if not text:
        return ''
    text = re.sub(r'⭐\\s*Stars:\\s*([\\d,]+)', r'<div class="gh-stat"><span class="gh-stat-label">⭐ Stars</span><span class="gh-stat-value">\\1</span></div>', text)
    text = re.sub(r'Forks:\\s*([\\d,]+)', r'<div class="gh-stat"><span class="gh-stat-label">Forks</span><span class="gh-stat-value">\\1</span></div>', text)
    text = re.sub(r'许可证:\\s*(\\S+)', r'<div class="gh-license">许可证: \\1</div>', text)
    text = re.sub(r'项目地址:\\s*(https?://\\S+)', r'<div class="gh-link">🔗 <a href="\\1" target="_blank" rel="noopener">\\1</a></div>', text)
    def make_link(match):
        url = match.group(1)
        return '<a href="' + url + '" target="_blank" rel="noopener">' + url + '</a> '
    text = re.sub(r'(https?://\\S+?)(?:\\s|$|<)', make_link, text)
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

TRANSLATE_TEXT = '''
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

# 备份
print("\n2. 备份...")
bak = '/var/www/dongshushu-paper/app.py.bak.' + time.strftime('%Y%m%d%H%M%S')
with open(bak, 'w') as f:
    f.write(content)
print(f"  备份完成: {bak}")

# 修改内容
new_content = content

# 1. 添加函数
if not has_text_to_html:
    # 找到 app = Flask 之后的位置
    flask_pos = new_content.find('app = Flask')
    if flask_pos > 0:
        insert_pos = new_content.find('\n', flask_pos) + 1
        new_content = new_content[:insert_pos] + TEXT_TO_HTML + TRANSLATE_TEXT + new_content[insert_pos:]
        print("  ✓ 已添加函数")
else:
    # 确保translate_text也存在
    if not has_translate_func:
        # 找到text_to_html结束位置
        func_end = new_content.find('\ndef text_to_html')
        if func_end < 0:
            func_end = new_content.find('\n\ndef text_to_html')
        insert_pos = new_content.find('\n', func_end + 10)
        if insert_pos > 0:
            new_content = new_content[:insert_pos] + TRANSLATE_TEXT + new_content[insert_pos:]
            print("  ✓ 已添加translate_text")

# 2. 修改render_template
# 查找article_detail路由中的render_template
old_pattern = "render_template('article_detail.html', article=article"
if old_pattern in new_content:
    new_pattern = "render_template('article_detail.html', article=article, content_html=text_to_html(article.content if article.content else ''), content_cn_html=text_to_html(article.content_cn) if article.content_cn else '')"
    new_content = new_content.replace(old_pattern, new_pattern)
    print("  ✓ 已修改render_template(单引号)")
elif 'render_template("article_detail.html", article=article' in new_content:
    old_pattern = 'render_template("article_detail.html", article=article'
    new_pattern = 'render_template("article_detail.html", article=article, content_html=text_to_html(article.content if article.content else ""), content_cn_html=text_to_html(article.content_cn) if article.content_cn else "")'
    new_content = new_content.replace(old_pattern, new_pattern)
    print("  ✓ 已修改render_template(双引号)")

# 保存
print("\n3. 保存修改...")
with open('/var/www/dongshushu-paper/app.py', 'w') as f:
    f.write(new_content)
print(f"  新长度: {len(new_content)}")

# 验证语法
print("\n4. 验证语法...")
try:
    compile(new_content, 'app.py', 'exec')
    print("  ✓ 语法正确")
except SyntaxError as e:
    print(f"  ✗ 语法错误: {e}")
    # 恢复备份
    with open(bak, 'r') as f:
        content = f.read()
    with open('/var/www/dongshushu-paper/app.py', 'w') as f:
        f.write(content)
    print("  已恢复备份")
    sys.exit(1)

# 测试导入
print("\n5. 测试导入...")
try:
    # 重新加载
    import importlib
    if 'app' in sys.modules:
        del sys.modules['app']
    import app
    print("  ✓ 导入成功")
except Exception as e:
    print(f"  ✗ 导入失败: {e}")
    sys.exit(1)

# 修改模板
print("\n6. 修改模板...")
with open('/var/www/dongshushu-paper/templates/article_detail.html', 'r') as f:
    tmpl = f.read()

# 备份
tmpl_bak = '/var/www/dongshushu-paper/templates/article_detail.html.bak.' + time.strftime('%Y%m%d%H%M%S')
with open(tmpl_bak, 'w') as f:
    f.write(tmpl)
print(f"  模板备份: {tmpl_bak}")

CSS = '''
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

# 添加CSS
if 'gh-stat' not in tmpl:
    if '</head>' in tmpl:
        tmpl = tmpl.replace('</head>', CSS + '\n</head>')
    else:
        tmpl = CSS + tmpl
    print("  ✓ 已添加CSS")

# 替换内容
if '{{ article.content|safe }}' in tmpl and 'content_html' not in tmpl:
    old = "{{ article.content|safe }}"
    new = """{% if content_html %}
<div class="article-content formatted-content">
    {{ content_html|safe }}
</div>
{% endif %}"""
    tmpl = tmpl.replace(old, new)
    print("  ✓ 已替换内容显示")

# 添加翻译区域
if 'translation-section' not in tmpl and '</article>' in tmpl:
    trans = '''
{% if content_cn_html %}
<div class="translation-section">
    <div class="translation-divider"><span>中文翻译</span></div>
    <div class="article-content formatted-content">
        {{ content_cn_html|safe }}
    </div>
</div>
{% endif %}
'''
    tmpl = tmpl.replace('</article>', trans + '</article>')
    print("  ✓ 已添加翻译区域")

with open('/var/www/dongshushu-paper/templates/article_detail.html', 'w') as f:
    f.write(tmpl)
print("  ✓ 模板已保存")

# 重启Gunicorn
print("\n7. 重启Gunicorn...")
os.system("pkill -9 gunicorn")
time.sleep(2)
os.system("cd /var/www/dongshushu-paper && gunicorn -c gunicorn_config.py app:app -D")
print("  ✓ 已重启")

time.sleep(3)

# 验证
print("\n8. 验证...")
result = os.popen("curl -s http://127.0.0.1:8000/ 2>&1").read()
if result:
    print(f"  ✓ 首页返回 {len(result)} 字节")
else:
    print("  ! 首页返回为空")

result2 = os.popen("curl -s http://127.0.0.1:8000/article/1 2>&1").read()
if '<p>' in result2 or 'formatted-content' in result2:
    print("  ✓ 文章已格式化")
elif 'Internal Server Error' in result2:
    print("  ! 服务器错误")
else:
    print(f"  文章页返回 {len(result2)} 字节")

print("\n" + "="*60)
print("修复完成!")
print("="*60)
