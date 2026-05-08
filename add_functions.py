#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在服务器上添加函数"""
import re
import os

# 读取app.py
with open('/var/www/dongshushu-paper/app.py', 'r') as f:
    content = f.read()

# 检查是否已有函数
if 'def text_to_html' in content:
    print("函数已存在")
else:
    print("添加函数...")
    
    # text_to_html函数
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
            import time
            url = 'https://api.mymemory.translated.net/get?q=' + urllib.parse.quote(seg[:500]) + '&langpair=' + source_lang + '|' + target_lang
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                translated.append(data.get('responseData', {}).get('translatedText', seg))
            time.sleep(0.5)
        except:
            translated.append(seg)
    return '\\n'.join(translated)

'''

    # 在文件开头找到import区域之后添加
    # 找到 app = Flask 之后
    flask_pos = content.find('app = Flask')
    if flask_pos > 0:
        insert_pos = content.find('\\n', flask_pos) + 1
        content = content[:insert_pos] + TEXT_TO_HTML + TRANSLATE_TEXT + content[insert_pos:]
        print(f"已添加函数到位置 {insert_pos}")
        
        # 保存
        with open('/var/www/dongshushu-paper/app.py', 'w') as f:
            f.write(content)
        print(f"新长度: {len(content)}")
    else:
        print("找不到 app = Flask")

# 验证语法
try:
    with open('/var/www/dongshushu-paper/app.py', 'r') as f:
        test_content = f.read()
    compile(test_content, 'app.py', 'exec')
    print("语法正确!")
except SyntaxError as e:
    print(f"语法错误: {e}")
