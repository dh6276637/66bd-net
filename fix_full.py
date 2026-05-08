#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整修复app.py - 使用完整内容替换"""
import re
import os
import time

print("="*60)
print("完整修复app.py...")
print("="*60)

# 读取备份文件
print("\n1. 读取备份...")
with open('/var/www/dongshushu-paper/app.py.bak.20260505053816', 'r') as f:
    content = f.read()
print(f"  原始长度: {len(content)}")

# 备份
bak = '/var/www/dongshushu-paper/app.py.bak.' + time.strftime('%Y%m%d%H%M%S')
with open(bak, 'w') as f:
    f.write(content)
print(f"  备份: {bak}")

# text_to_html函数 - 使用单引号避免转义问题
TEXT_TO_HTML = '''

def text_to_html(text):
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

# translate_text函数
TRANSLATE_TEXT = '''
def translate_text(text, source_lang='en', target_lang='zh-CN'):
    if not text or len(text.strip()) < 10:
        return ''
    en_chars = sum(1 for c in text if ord(c) < 128 and c.isalpha())
    total_alpha = sum(1 for c in text if c.isalpha())
    if total_alpha > 0 and en_chars / total_alpha < 0.5:
        return ''
    import urllib.request
    import urllib.parse
    import json
    import time as time_module
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
            time_module.sleep(0.5)
        except:
            translated.append(seg)
    return '\\n'.join(translated)

'''

new_content = content

# 添加函数 - 在 strip_html 函数之后
strip_html_pos = new_content.find('def strip_html')
if strip_html_pos >= 0:
    # 找到这个函数结束的位置
    next_def = new_content.find('def ', strip_html_pos + 20)
    if next_def > 0:
        insert_pos = new_content.find('\n', next_def) + 1
        new_content = new_content[:insert_pos] + TEXT_TO_HTML + TRANSLATE_TEXT + new_content[insert_pos:]
        print("  ✓ 已添加函数")

# 修改render_template - 找到article_detail的那一行
# 原始: return render_template('article_detail.html', article=article, categories=ALL_CATEGORIES...
# 新:   return render_template('article_detail.html', article=article, content_html=text_to_html(...), content_cn_html=text_to_html(...), categories=ALL_CATEGORIES...

old_rt = "return render_template('article_detail.html', article=article, categories=ALL_CATEGORIES, name_to_slug=NAME_TO_SLUG,"
new_rt = "return render_template('article_detail.html', article=article, content_html=text_to_html(article.content if article.content else ''), content_cn_html=text_to_html(article.content_cn) if article.content_cn else '', categories=ALL_CATEGORIES, name_to_slug=NAME_TO_SLUG,"

if old_rt in new_content:
    new_content = new_content.replace(old_rt, new_rt)
    print("  ✓ 已修改render_template")
else:
    # 尝试其他格式
    old_rt2 = "return render_template('article_detail.html', article=article,"
    if old_rt2 in new_content:
        new_rt2 = "return render_template('article_detail.html', article=article, content_html=text_to_html(article.content if article.content else ''), content_cn_html=text_to_html(article.content_cn) if article.content_cn else '',"
        new_content = new_content.replace(old_rt2, new_rt2)
        print("  ✓ 已修改render_template(备用格式)")

# 保存
print("\n2. 保存...")
with open('/var/www/dongshushu-paper/app.py', 'w') as f:
    f.write(new_content)
print(f"  新长度: {len(new_content)}")

# 验证语法
print("\n3. 验证语法...")
try:
    compile(new_content, 'app.py', 'exec')
    print("  ✓ 语法正确")
except SyntaxError as e:
    print(f"  ✗ 语法错误: {e}")
    with open(bak, 'r') as f:
        content = f.read()
    with open('/var/www/dongshushu-paper/app.py', 'w') as f:
        f.write(content)
    print("  已恢复备份")
    exit(1)

# 重启Gunicorn
print("\n4. 重启Gunicorn...")
os.system("pkill -9 gunicorn 2>/dev/null")
time.sleep(2)
os.system("cd /var/www/dongshushu-paper && gunicorn -c gunicorn_config.py app:app -D 2>/dev/null")
time.sleep(3)
print("  ✓ 完成")

# 验证
print("\n5. 验证...")
result = os.popen("curl -s http://127.0.0.1:5000/ 2>&1 | head -c 200")
if result:
    print(f"  网站响应: {result[:100]}")
else:
    print("  ! 无响应")

print("\n" + "="*60)
print("完成!")
print("="*60)
