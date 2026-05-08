#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SEO全面优化补丁脚本 - 66必读网站"""

import os
import re
from datetime import datetime

BASE_DIR = "/var/www/dongshushu-paper"
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print("读取文件失败 {}: {}".format(path, e))
        return None

def write_file(path, content):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("  写入成功: {}".format(path))
        return True
    except Exception as e:
        print("  写入失败 {}: {}".format(path, e))
        return False

def backup_file(path):
    if os.path.exists(path):
        backup_path = path + ".bak.{}".format(datetime.now().strftime('%Y%m%d%H%M%S'))
        with open(path, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        print("  备份: {}".format(backup_path))

def generate_og_image():
    os.makedirs(STATIC_DIR, exist_ok=True)
    
    svg_content = '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630"><defs><linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#1a1a2e"/><stop offset="100%" style="stop-color:#16213e"/></linearGradient><filter id="g"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><rect width="1200" height="630" fill="url(#bg)"/><line x1="0" y1="580" x2="1200" y2="580" stroke="#e94560" stroke-width="2" opacity="0.5"/><text x="600" y="280" font-family="Arial" font-size="180" font-weight="bold" fill="#fff" text-anchor="middle" filter="url(#g)">66必读</text><text x="600" y="380" font-family="Arial" font-size="36" fill="#a0a0a0" text-anchor="middle">每日精选 · 深度阅读</text><circle cx="300" cy="450" r="4" fill="#e94560" opacity="0.6"/><circle cx="600" cy="450" r="4" fill="#e94560" opacity="0.6"/><circle cx="900" cy="450" r="4" fill="#e94560" opacity="0.6"/><text x="600" y="550" font-family="Arial" font-size="24" fill="#666" text-anchor="middle">66bd.net - 发现值得阅读的内容</text></svg>'
    
    svg_path = os.path.join(STATIC_DIR, "og-default.svg")
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print("  生成OG图片SVG: {}".format(svg_path))
    
    html_og = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>66必读 OG Image</title><style>*{margin:0;padding:0;box-sizing:border-box}body{width:1200px;height:630px;background:linear-gradient(135deg,#1a1a2e,#16213e);display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:PingFang SC,Microsoft YaHei,sans-serif}.logo{font-size:120px;font-weight:bold;color:#fff;text-shadow:0 0 30px rgba(233,69,96,0.5)}.tagline{font-size:28px;color:#888;margin-top:20px;letter-spacing:4px}.url{font-size:18px;color:#555;margin-top:80px}</style></head><body><div class="logo">66必读</div><div class="tagline">每日精选 · 深度阅读</div><div class="url">66bd.net - 发现值得阅读的内容</div></body></html>'
    
    html_path = os.path.join(STATIC_DIR, "og-default.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_og)
    print("  生成OG图片HTML备用: {}".format(html_path))
    return True

def patch_base_html():
    base_path = os.path.join(TEMPLATES_DIR, "base.html")
    if not os.path.exists(base_path):
        print("  base.html不存在，跳过")
        return False
    
    content = read_file(base_path)
    if content is None:
        return False
    
    backup_file(base_path)
    
    if '{% block seo' in content:
        print("  base.html已有SEO block，跳过")
        return True
    
    seo_head_insert = '''
    <!-- SEO Meta Tags -->
    <meta name="robots" content="index, follow">
    <meta name="applicable-device" content="pc,mobile">
    <meta name="theme-color" content="#1a1a2e">
    
    <!-- Preconnect for Performance -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="dns-prefetch" href="https://www.66bd.net">
    
    <!-- Open Graph & Twitter Card -->
    <meta property="og:site_name" content="66必读">
    <meta property="og:locale" content="zh_CN">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:site" content="@66bixu">
    
    <!-- Canonical URL -->
    <link rel="canonical" href="{{ request.url_root }}{{ request.path.lstrip("/") }}">
    
    <!-- SEO Block -->
    {% block seo_head %}{% endblock %}
'''
    
    content = content.replace('</head>', seo_head_insert + '</head>')
    return write_file(base_path, content)

def patch_app_py():
    app_path = os.path.join(BASE_DIR, "app.py")
    if not os.path.exists(app_path):
        print("  app.py不存在，跳过")
        return False
    
    content = read_file(app_path)
    if content is None:
        return False
    
    backup_file(app_path)
    
    seo_funcs = """

# ============ SEO优化工具函数 ============
def strip_html(text):
    if text is None:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    return text.strip()

def truncate_text(text, length=150):
    if text is None:
        return ""
    text = strip_html(text)
    if len(text) <= length:
        return text
    return text[:length] + '...'

def get_article_seo(article, request):
    title = article.get('title', '未命名文章') if article else '未命名文章'
    content = article.get('content', '') if article else ''
    description = truncate_text(content, 150)
    category = article.get('category', '') if article else ''
    created_at = article.get('created_at', '') if article else ''
    base_url = request.url_root.rstrip('/')
    article_url = base_url + '/article/' + str(article.get('slug', article.get('id', '')))
    return {
        'title': title + ' - 66必读',
        'description': description,
        'keywords': category + ',' + title[:20],
        'og_title': title,
        'og_description': description,
        'og_url': article_url,
        'og_type': 'article',
        'og_image': base_url + '/static/og-default.png',
        'article_published_time': created_at,
        'article_section': category,
        'twitter_title': title,
        'twitter_description': description,
        'canonical_url': article_url,
    }

def get_category_seo(category_name, category_desc, request):
    name = category_name or '全部'
    desc = category_desc or '浏览' + name + '分类下的所有文章'
    base_url = request.url_root.rstrip('/')
    if category_name:
        category_url = base_url + '/category/' + category_name
    else:
        category_url = base_url + '/category'
    return {
        'title': name + ' - 66必读',
        'description': desc,
        'keywords': name + ',66必读,' + name + '文章',
        'og_title': name + ' - 66必读',
        'og_description': desc,
        'og_url': category_url,
        'og_type': 'website',
        'og_image': base_url + '/static/og-default.png',
        'twitter_title': name + ' - 66必读',
        'twitter_description': desc,
        'canonical_url': category_url,
    }

def get_homepage_seo(request):
    site_url = request.url_root.rstrip('/')
    return {
        'title': '66必读 - 每日精选科技资讯·深度阅读',
        'description': '66必读，每日精选优质科技资讯、深度好文。涵盖科技趋势、创业故事、产品评测等多元内容，帮你节省筛选时间，发现真正有价值的信息。',
        'keywords': '66必读,科技资讯,深度阅读,科技趋势,创业故事,产品评测,好文推荐',
        'og_title': '66必读 - 每日精选·深度阅读',
        'og_description': '每日精选优质科技资讯、深度好文，帮你发现真正有价值的信息。',
        'og_url': site_url,
        'og_type': 'website',
        'og_image': site_url + '/static/og-default.png',
        'twitter_title': '66必读 - 每日精选·深度阅读',
        'twitter_description': '每日精选优质科技资讯、深度好文',
        'canonical_url': site_url,
    }

def generate_json_ld(seo_data, page_type, extra_data=None):
    if page_type == 'homepage':
        return '<script type=\"application/ld+json\">{\"@context\":\"https://schema.org\",\"@type\":\"WebSite\",\"name\":\"66必读\",\"url\":\"https://www.66bd.net\",\"description\":\"每日精选科技资讯·深度阅读\",\"potentialAction\":{\"@type\":\"SearchAction\",\"target\":\"https://www.66bd.net/search?q={search_term_string}\",\"query-input\":\"required name=search_term_string\"},\"publisher\":{\"@type\":\"Organization\",\"name\":\"66必读\",\"logo\":{\"@type\":\"ImageObject\",\"url\":\"https://www.66bd.net/static/og-default.png\"}}}</script>'
    elif page_type == 'article' and extra_data:
        article = extra_data.get('article', {})
        headline = seo_data.get('og_title', '').replace('\"', '\\\\\"')
        desc = seo_data.get('og_description', '').replace('\"', '\\\\\"')
        og_image = seo_data.get('og_image', '')
        canonical = seo_data.get('canonical_url', '')
        created = article.get('created_at', '')
        updated = article.get('updated_at', article.get('created_at', ''))
        category = article.get('category', '文章')
        json_ld = '<script type=\"application/ld+json\">{\"@context\":\"https://schema.org\",\"@type\":\"Article\",\"headline\":\"' + headline + '\",\"description\":\"' + desc + '\",\"image\":\"' + og_image + '\",\"author\":{\"@type\":\"Person\",\"name\":\"66必读\"},\"publisher\":{\"@type\":\"Organization\",\"name\":\"66必读\",\"logo\":{\"@type\":\"ImageObject\",\"url\":\"https://www.66bd.net/static/og-default.png\"}},\"datePublished\":\"' + created + '\",\"dateModified\":\"' + updated + '\",\"mainEntityOfPage\":{\"@type\":\"WebPage\",\"@id\":\"' + canonical + '\"}}</script>'
        breadcrumb = '<script type=\"application/ld+json\">{\"@context\":\"https://schema.org\",\"@type\":\"BreadcrumbList\",\"itemListElement\":[{\"@type\":\"ListItem\",\"position\":1,\"name\":\"首页\",\"item\":\"https://www.66bd.net\"},{\"@type\":\"ListItem\",\"position\":2,\"name\":\"' + category + '\",\"item\":\"https://www.66bd.net/category/' + category + '\"},{\"@type\":\"ListItem\",\"position\":3,\"name\":\"' + headline + '\"}]}</script>'
        return json_ld + breadcrumb
    elif page_type == 'category':
        title = seo_data.get('title', '').replace('\"', '\\\\\"')
        desc = seo_data.get('description', '').replace('\"', '\\\\\"')
        url = seo_data.get('canonical_url', '')
        return '<script type=\"application/ld+json\">{\"@context\":\"https://schema.org\",\"@type\":\"CollectionPage\",\"name\":\"' + title + '\",\"description\":\"' + desc + '\",\"url\":\"' + url + '\"}</script>'
    return ""

# ============ SEO辅助函数结束 ============

"""
    
    if "# ============ SEO优化工具函数 ============" not in content:
        import_pos = content.find("from flask import")
        if import_pos == -1:
            import_pos = content.find("import")
        if import_pos != -1:
            next_newline = content.find("\n", import_pos)
            if next_newline != -1:
                insert_pos = content.find("\n", next_newline + 1)
                if insert_pos != -1:
                    content = content[:insert_pos + 1] + seo_funcs + content[insert_pos + 1:]
    
    return write_file(app_path, content)

def patch_template(template_path, seo_block):
    if not template_path or not os.path.exists(template_path):
        return False
    
    content = read_file(template_path)
    if content is None:
        return False
    
    backup_file(template_path)
    
    if "{% block seo_head %}" not in content:
        content = content.replace("</head>", seo_block + "\n</head>")
    
    return write_file(template_path, content)

def patch_article_template():
    seo_block = '''
{% block seo_head %}
<title>{{ seo.title if seo else article.title + ' - 66必读' }}</title>
<meta name="description" content="{{ seo.description if seo else '' }}">
<meta name="keywords" content="{{ seo.keywords if seo else '' }}">
<meta property="og:title" content="{{ seo.og_title if seo else article.title }}">
<meta property="og:description" content="{{ seo.og_description if seo else '' }}">
<meta property="og:url" content="{{ seo.og_url if seo else '' }}">
<meta property="og:type" content="{{ seo.og_type if seo else 'article' }}">
<meta property="og:image" content="{{ seo.og_image if seo else '' }}">
<meta property="article:published_time" content="{{ seo.article_published_time if seo else '' }}">
<meta property="article:section" content="{{ seo.article_section if seo else '' }}">
<meta name="twitter:title" content="{{ seo.twitter_title if seo else article.title }}">
<meta name="twitter:description" content="{{ seo.twitter_description if seo else '' }}">
<link rel="canonical" href="{{ seo.canonical_url if seo else '' }}">
{{ seo.json_ld|safe if seo and seo.json_ld else '' }}
{% endblock %}
'''
    for name in ["article_detail.html", "article.html", "post.html", "article.html.j2", "article_detail.html.j2"]:
        path = os.path.join(TEMPLATES_DIR, name)
        if patch_template(path, seo_block):
            print("  修改文章模板: {}".format(name))
            return True
    return False

def patch_category_template():
    seo_block = '''
{% block seo_head %}
<title>{{ seo.title if seo else (category_name + ' - 66必读') }}</title>
<meta name="description" content="{{ seo.description if seo else '' }}">
<meta name="keywords" content="{{ seo.keywords if seo else '' }}">
<meta property="og:title" content="{{ seo.og_title if seo else '' }}">
<meta property="og:description" content="{{ seo.og_description if seo else '' }}">
<meta property="og:url" content="{{ seo.og_url if seo else '' }}">
<meta property="og:type" content="website">
<meta property="og:image" content="{{ seo.og_image if seo else '' }}">
<meta name="twitter:title" content="{{ seo.twitter_title if seo else '' }}">
<meta name="twitter:description" content="{{ seo.twitter_description if seo else '' }}">
<link rel="canonical" href="{{ seo.canonical_url if seo else '' }}">
{{ seo.json_ld|safe if seo and seo.json_ld else '' }}
{% endblock %}
'''
    for name in ["category.html", "category.html.j2"]:
        path = os.path.join(TEMPLATES_DIR, name)
        if patch_template(path, seo_block):
            print("  修改分类模板: {}".format(name))
            return True
    return False

def patch_index_template():
    seo_block = '''
{% block seo_head %}
<title>{{ seo.title if seo else '66必读 - 每日精选科技资讯·深度阅读' }}</title>
<meta name="description" content="{{ seo.description if seo else '66必读，每日精选优质科技资讯、深度好文。涵盖科技趋势、创业故事、产品评测等多元内容，帮你节省筛选时间，发现真正有价值的信息。' }}">
<meta name="keywords" content="{{ seo.keywords if seo else '66必读,科技资讯,深度阅读,科技趋势,创业故事,产品评测,好文推荐' }}">
<meta property="og:title" content="{{ seo.og_title if seo else '66必读 - 每日精选·深度阅读' }}">
<meta property="og:description" content="{{ seo.og_description if seo else '每日精选优质科技资讯、深度好文，帮你发现真正有价值的信息。' }}">
<meta property="og:url" content="{{ seo.og_url if seo else '' }}">
<meta property="og:type" content="website">
<meta property="og:image" content="{{ seo.og_image if seo else '' }}">
<meta name="twitter:title" content="{{ seo.twitter_title if seo else '66必读 - 每日精选·深度阅读' }}">
<meta name="twitter:description" content="{{ seo.twitter_description if seo else '每日精选优质科技资讯、深度好文' }}">
<link rel="canonical" href="{{ seo.canonical_url if seo else '' }}">
{{ seo.json_ld|safe if seo and seo.json_ld else '' }}
{% endblock %}
'''
    for name in ["index.html", "home.html", "index.html.j2"]:
        path = os.path.join(TEMPLATES_DIR, name)
        if patch_template(path, seo_block):
            print("  修改首页模板: {}".format(name))
            return True
    return False

def update_robots_txt():
    robots_path = os.path.join(BASE_DIR, "robots.txt")
    if os.path.exists(robots_path):
        backup_file(robots_path)
    
    robots_content = """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/
Disallow: /static/admin/
Sitemap: https://www.66bd.net/sitemap.xml
Crawl-delay: 1
"""
    return write_file(robots_path, robots_content)

def main():
    print("=" * 50)
    print("66必读 SEO全面优化补丁")
    print("=" * 50)
    
    if not os.path.exists(BASE_DIR):
        print("错误: 目录不存在: {}".format(BASE_DIR))
        return False
    
    print("\n工作目录: {}".format(BASE_DIR))
    
    print("\n[1/5] 生成默认OG分享图...")
    generate_og_image()
    
    print("\n[2/5] 修改基础模板...")
    patch_base_html()
    
    print("\n[3/5] 修改app.py添加SEO函数...")
    patch_app_py()
    
    print("\n[4/5] 修改各页面模板...")
    patch_article_template()
    patch_category_template()
    patch_index_template()
    
    print("\n[5/5] 更新robots.txt...")
    update_robots_txt()
    
    print("\n" + "=" * 50)
    print("SEO优化补丁执行完成!")
    print("重启命令: pkill -9 gunicorn; sleep 2; cd /var/www/dongshushu-paper && gunicorn -c gunicorn_config.py app:app -D")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    main()
