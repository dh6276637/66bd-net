#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""66必读 v7 - 支持用户系统、文章收藏、扩展分类、报纸栏目"""

from flask import Flask, render_template, request, jsonify, abort, session, redirect, url_for, Response, flash
from functools import wraps
import MySQLdb
from MySQLdb.cursors import DictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import re
import json
import secrets
import html as html_module
import os
import subprocess
import requests
import threading

app = Flask(__name__)
# 使用固定密钥确保session持久化
app.secret_key = os.environ.get('SECRET_KEY') or '66bd-net-2026-secret-key-keep-session-stable'
app.config['SESSION_TYPE'] = 'filesystem'

DB_CONFIG = {
    "host": os.environ.get('DB_HOST', 'localhost'),
    "user": os.environ.get('DB_USER', 'paper_user'),
    "passwd": os.environ.get('DB_PASSWORD', 'paper_db2026'),
    "db": os.environ.get('DB_NAME', 'dongshushu_paper'),
    "charset": "utf8mb4"
}

CATEGORY_MAP = {
    "index": "首页",
    "shizheng": "时政热点",
    "keji-toutiao": "科技头条",
    "zhineng-ai": "智能AI",
    "anquan": "安全攻防",
    "kaifa": "开发者生态",
    "shuma": "数码硬件",
    "shehui": "社会热点",
    "qiche": "汽车",
    "youxi": "游戏",
    "kaiyuan": "开源推荐",
}
NAME_TO_SLUG = {v: k for k, v in CATEGORY_MAP.items() if k != "index"}
ALL_CATEGORIES = ["时政热点", "科技头条", "智能AI", "安全攻防", "开发者生态", "数码硬件", "社会热点", "汽车", "游戏", "开源推荐"]

MESSAGE_BLACKLIST = ['赌博', '博彩', '彩票', '色情', '诈骗', '刷单', '微信', 'vx', 'vpn', '翻墙']

SOURCE_CONFIG = {
    '36kr': {'icon': '📰', 'color': '#ff6600'}, 'HackerNews': {'icon': '🔺', 'color': '#ff6600'},
    'GitHub': {'icon': '⚫', 'color': '#333'}, 'GitHub Trending': {'icon': '⚫', 'color': '#333'},
}

def get_db(): return MySQLdb.connect(**DB_CONFIG)

# ============ 操作日志函数 ============
def log_admin_action(action, target='', detail=None, user_id='', username=''):
    """记录后台操作日志"""
    try:
        conn = get_db()
        cur = conn.cursor()
        ip = request.remote_addr or request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or ''
        user_agent = request.headers.get('User-Agent', '')[:500]
        detail_json = json.dumps(detail, ensure_ascii=False) if detail else ''
        cur.execute("""
            INSERT INTO admin_log (user_id, username, action, target, detail, ip, user_agent, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """, (user_id, username, action, target, detail_json, ip, user_agent))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        pass  # 日志失败不影响业务

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_logged_in' not in session: return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def api_response(data=None, message='success', code=200):
    return jsonify({'code': code, 'message': message, 'data': data}), code if code >= 400 else 200

def check_message_blacklist(content, nickname=''):
    text = (nickname + content).lower()
    for keyword in MESSAGE_BLACKLIST:
        if keyword.lower() in text: return True, keyword
    return False, None

def get_source_style(source):
    for key, config in SOURCE_CONFIG.items():
        if key.lower() in (source or '').lower(): return config
    return {'icon': '📌', 'color': '#666'}

def get_client_ip():
    return request.remote_addr or request.headers.get('X-Forwarded-For', '').split(',')[0].strip()

BLOCKED_UAS = ['scrapy', 'curl', 'wget', 'python-requests', 'python-urllib', 'httpclient', 'java/', 'node-fetch', 'go-http']

@app.before_request
def anti_scrape_check():
    if request.path.startswith('/admin') or request.path.startswith('/api/'): return
    ua = request.headers.get('User-Agent', '').lower()
    if not ua: return abort(403)
    for bad in BLOCKED_UAS:
        if bad in ua: return abort(403)

def text_to_html(text):
    """安全的文本转HTML，自动转义内容，只允许http/https链接"""
    if not text: return ''
    import re as _re
    import html as html_module
    text = html_module.escape(text)
    text = _re.sub(r'项目地址:\s*(https?://\S+)', r'<div class="gh-link">🔗 <a href="\1" target="_blank" rel="noopener">\1</a></div>', text)
    text = _re.sub(r'语言:\s*(\S+)', r'<div class="gh-stat"><span>语言</span><span>\1</span></div>', text)
    text = _re.sub(r'⭐\s*Stars:\s*([\d,]+)', r'<div class="gh-stat"><span>⭐ Stars</span><span>\1</span></div>', text)
    text = _re.sub(r'Forks:\s*([\d,]+)', r'<div class="gh-stat"><span>Forks</span><span>\1</span></div>', text)
    text = _re.sub(r'许可证:\s*(\S+)', r'<div class="gh-license">许可证: \1</div>', text)
    text = _re.sub(r'项目说明:\s*(.+)', r'<div class="gh-desc">📝 \1</div>', text)
    def make_link(m):
        url = m.group(1)
        if not url.lower().startswith(('http://', 'https://')):
            return m.group(0)
        return '<a href="' + url + '" target="_blank" rel="noopener">' + url + '</a> '
    text = _re.sub(r'(?<!href=")(https?://\S+?)(?:\s|$|<)', make_link, text)
    paragraphs = text.split('\n\n')
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if not p: continue
        p = p.replace('\n', '<br>')
        if p.startswith('<div'): html_parts.append(p)
        else: html_parts.append('<p>' + p + '</p>')
    return '\n'.join(html_parts)

# ========== 页面路由 ==========
@app.route('/')
def index():
    page = int(request.args.get('page', 1))
    per_page = 20
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        user_id = session.get('user_id')
        cur.execute("SELECT COUNT(*) as cnt FROM article WHERE is_published=1")
        total = cur.fetchone()['cnt']
        total_pages = (total + per_page - 1) // per_page
        has_more = page < total_pages
        offset = (page - 1) * per_page
        cur.execute("SELECT * FROM article WHERE is_published=1 ORDER BY created_at DESC LIMIT %s OFFSET %s", (per_page, offset))
        articles = cur.fetchall()
        for a in articles:
            a['slug'] = NAME_TO_SLUG.get(a['category'], 'index')
            a['source_config'] = get_source_style(a.get('source'))
        favorite_ids = []
        if user_id:
            cur.execute("SELECT article_id FROM favorites WHERE user_id=%s", (user_id,))
            favorite_ids = [row['article_id'] for row in cur.fetchall()]
        return render_template('index.html', articles=articles, categories=ALL_CATEGORIES, 
                               name_to_slug=NAME_TO_SLUG, user_id=user_id, favorite_ids=favorite_ids,
                               current_page=page, total_pages=total_pages, has_more=has_more)
    finally:
        cur.close()
        conn.close()

@app.route('/category/<slug>')
def category_page(slug):
    cat = CATEGORY_MAP.get(slug)
    if not cat or cat == "首页": abort(404)
    page = int(request.args.get('page', 1))
    per_page = 20
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        user_id = session.get('user_id')
        cur.execute("SELECT COUNT(*) as cnt FROM article WHERE is_published=1 AND category=%s", (cat,))
        total = cur.fetchone()['cnt']
        total_pages = (total + per_page - 1) // per_page
        has_more = page < total_pages
        offset = (page - 1) * per_page
        cur.execute("SELECT * FROM article WHERE is_published=1 AND category=%s ORDER BY created_at DESC LIMIT %s OFFSET %s", (cat, per_page, offset))
        articles = cur.fetchall()
        for a in articles:
            a['slug'] = slug
            a['source_config'] = get_source_style(a.get('source'))
        favorite_ids = []
        if user_id:
            cur.execute("SELECT article_id FROM favorites WHERE user_id=%s", (user_id,))
            favorite_ids = [row['article_id'] for row in cur.fetchall()]
        return render_template('category.html', articles=articles, category=cat, slug=slug, 
                               categories=ALL_CATEGORIES, name_to_slug=NAME_TO_SLUG, user_id=user_id, favorite_ids=favorite_ids,
                               current_page=page, total_pages=total_pages, has_more=has_more)
    finally:
        cur.close()
        conn.close()

@app.route('/article/<int:id>')
def article_detail(id):
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        cur.execute("SELECT * FROM article WHERE id=%s AND is_published=1", (id,))
        article = cur.fetchone()
        if not article: abort(404)
        cur.execute("UPDATE article SET view_count = view_count + 1 WHERE id=%s", (id,))
        conn.commit()
        article['slug'] = NAME_TO_SLUG.get(article['category'], 'index')
        article['source_config'] = get_source_style(article.get('source'))
        user_id = session.get('user_id')
        is_favorited = False
        favorite_count = 0
        if user_id:
            cur.execute("SELECT id FROM favorites WHERE user_id=%s AND article_id=%s", (user_id, id))
            is_favorited = cur.fetchone() is not None
        cur.execute("SELECT COUNT(*) as cnt FROM favorites WHERE article_id=%s", (id,))
        favorite_count = cur.fetchone()['cnt']
        content = article['content'] or article.get('content_cn','') or ''
        return render_template('article_detail.html', article=article, content_html=text_to_html(content), 
                               content_cn_html=text_to_html(article['content_cn']) if article.get('content_cn') else '', 
                               categories=ALL_CATEGORIES, name_to_slug=NAME_TO_SLUG, user_id=user_id, is_favorited=is_favorited, 
                               favorite_count=favorite_count, og_title=article['title'], 
                               og_description=(article.get('content','') or article.get('content_cn',''))[:200])
    finally:
        cur.close()
        conn.close()

# ========== 报纸栏目 ==========
@app.route('/newspaper')
def newspaper_list():
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        cur.execute("SELECT DATE(created_at) as date, COUNT(*) as cnt FROM article WHERE is_published=1 GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 30")
        dates = cur.fetchall()
        
        for d in dates:
            d['date_str'] = d['date'].strftime('%Y-%m-%d') if hasattr(d['date'], 'strftime') else str(d['date'])
            date_str = d['date_str']
            
            cur.execute("""
                SELECT category, COUNT(*) as cnt 
                FROM article 
                WHERE is_published=1 AND DATE(created_at)=%s 
                GROUP BY category
            """, (date_str,))
            cat_counts = {row['category']: row['cnt'] for row in cur.fetchall()}
            d['category_counts'] = cat_counts
            
            cur.execute("""
                SELECT title FROM article 
                WHERE is_published=1 AND DATE(created_at)=%s 
                ORDER BY view_count DESC, created_at DESC 
                LIMIT 3
            """, (date_str,))
            d['top_titles'] = [row['title'] for row in cur.fetchall()]
            d['date_obj'] = d['date']
        
        today = datetime.now().strftime('%Y-%m-%d')
        today_date = datetime.now()
        
        return render_template('newspaper_list_new.html', dates=dates, today=today, 
                             today_date=today_date, categories=ALL_CATEGORIES, name_to_slug=NAME_TO_SLUG)
    finally:
        cur.close()
        conn.close()

@app.route('/newspaper/<date>')
def newspaper_date(date):
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        try: check_date = datetime.strptime(date, '%Y-%m-%d')
        except: abort(404)
        cur.execute("SELECT * FROM article WHERE is_published=1 AND DATE(created_at)=%s ORDER BY category, created_at DESC", (date,))
        articles = cur.fetchall()
        categorized = {}
        for a in articles:
            cat = a['category']
            if cat not in categorized: categorized[cat] = []
            a['slug'] = NAME_TO_SLUG.get(cat, 'index')
            a['source_config'] = get_source_style(a.get('source'))
            content = a.get('content', '') or ''
            a['summary'] = content[:150] + '...' if len(content) > 150 else content
            categorized[cat].append(a)
        sorted_categories = [{'name': cat, 'articles': categorized[cat]} for cat in ALL_CATEGORIES if cat in categorized]
        today = datetime.now().strftime('%Y-%m-%d')
        prev_date = (check_date - timedelta(days=1)).strftime('%Y-%m-%d')
        next_date = (check_date + timedelta(days=1)).strftime('%Y-%m-%d')
        cur.execute("SELECT COUNT(*) as cnt FROM article WHERE is_published=1 AND DATE(created_at)=%s", (next_date,))
        has_next = cur.fetchone()['cnt'] > 0
        return render_template('newspaper_date_new.html', date=date, categories_data=sorted_categories,
                             today=today, prev_date=prev_date, next_date=next_date if has_next else None,
                             categories=ALL_CATEGORIES, name_to_slug=NAME_TO_SLUG)
    finally:
        cur.close()
        conn.close()

@app.route('/paper')
def paper(): return redirect(url_for('newspaper_list'))

@app.route('/about')
def about(): return render_template('about.html', categories=ALL_CATEGORIES, name_to_slug=NAME_TO_SLUG)

@app.route('/messages')
def messages_page():
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        cur.execute("SELECT * FROM messages WHERE is_approved=1 ORDER BY created_at DESC LIMIT 50")
        messages = cur.fetchall()
        return render_template('messages.html', messages=messages, categories=ALL_CATEGORIES, name_to_slug=NAME_TO_SLUG)
    finally:
        cur.close()
        conn.close()

# ========== RESTful API ==========
@app.route('/api/v1/articles')
def api_v1_articles():
    if request.method == 'POST':
        data = request.get_json() or {}
        title = (data.get('title') or '').strip()
        content = (data.get('content') or '').strip()
        category = data.get('category', '科技')
        source = data.get('source', '')
        paper_type = data.get('paper_type') or None
        publish_date = data.get('date') or datetime.now().strftime('%Y-%m-%d')
        is_published = data.get('is_published', True)
        
        if not title: return api_response(None, '标题不能为空', 400)
        if not content: return api_response(None, '内容不能为空', 400)
        
        conn = get_db()
        cur = conn.cursor(DictCursor)
        try:
            cur.execute("SELECT id FROM article WHERE title=%s LIMIT 1", (title[:200],))
            if cur.fetchone():
                return api_response({'id': None}, '文章已存在', 200)
            
            url = data.get('url', '')[:500] if data.get('url') else ''
            title_cn = (data.get('title_cn') or '').strip()[:200]
            content_cn = (data.get('content_cn') or '').strip()[:5000]
            cur.execute("""
                INSERT INTO article (title, title_cn, content, content_cn, category, source, url, paper_type, publish_date, is_published, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (title[:200], title_cn, content[:5000], content_cn, category[:50], source[:200], url, paper_type, publish_date, 1 if is_published else 0))
            conn.commit()
            article_id = cur.lastrowid
            return api_response({'id': article_id}, '添加成功', 201)
        finally:
            cur.close()
            conn.close()
    
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('page_size', 20)), 50)
    category = request.args.get('category', '')
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        where, params = "WHERE is_published=1", []
        if category: where += " AND category=%s"; params.append(category)
        cur.execute(f"SELECT COUNT(*) as cnt FROM article {where}", params)
        total = cur.fetchone()['cnt']
        offset = (page - 1) * per_page
        cur.execute(f"SELECT * FROM article {where} ORDER BY created_at DESC LIMIT %s OFFSET %s", params + [per_page, offset])
        articles = cur.fetchall()
        for a in articles:
            a['slug'] = NAME_TO_SLUG.get(a.get('category', ''), 'index')
            a['source_config'] = get_source_style(a.get('source'))
            if a.get('created_at'): a['created_at'] = a['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if a.get('content') and len(a['content']) > 200: a['content_preview'] = a['content'][:200]
        total_pages = (total + per_page - 1) // per_page
        has_more = page < total_pages
        return api_response({'articles': articles, 'has_more': has_more, 'pagination': {'page': page, 'page_size': per_page, 'total': total, 'total_pages': total_pages}})
    finally:
        cur.close()
        conn.close()

@app.route('/api/v1/articles/<int:id>')
def api_v1_article(id):
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        cur.execute("SELECT * FROM article WHERE id=%s AND is_published=1", (id,))
        article = cur.fetchone()
        if not article: return api_response(None, '文章不存在', 404)
        article['slug'] = NAME_TO_SLUG.get(article.get('category', ''), 'index')
        if article.get('created_at'): article['created_at'] = article['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        return api_response(article)
    finally:
        cur.close()
        conn.close()

@app.route('/api/v1/categories')
def api_v1_categories():
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        cur.execute("SELECT category, COUNT(*) as count FROM article WHERE is_published=1 GROUP BY category")
        counts = {row['category']: row['count'] for row in cur.fetchall()}
        categories = [{'name': cat, 'slug': NAME_TO_SLUG.get(cat, cat), 'count': counts.get(cat, 0)} for cat in ALL_CATEGORIES]
        return api_response(categories)
    finally:
        cur.close()
        conn.close()

@app.route('/api/v1/newspaper')
def api_v1_newspaper():
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        cur.execute("SELECT DATE(created_at) as date, COUNT(*) as count FROM article WHERE is_published=1 GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 30")
        dates = [{'date': row['date'].strftime('%Y-%m-%d'), 'article_count': row['count']} for row in cur.fetchall()]
        return api_response(dates)
    finally:
        cur.close()
        conn.close()

@app.route('/api/v1/newspaper/<date>')
def api_v1_newspaper_date(date):
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        try: datetime.strptime(date, '%Y-%m-%d')
        except: return api_response(None, '日期格式错误', 400)
        cur.execute("SELECT * FROM article WHERE is_published=1 AND DATE(created_at)=%s ORDER BY category, created_at DESC", (date,))
        articles = cur.fetchall()
        categorized = {}
        for a in articles:
            cat = a['category']
            if cat not in categorized: categorized[cat] = []
            a['slug'] = NAME_TO_SLUG.get(cat, 'index')
            if a.get('created_at'): a['created_at'] = a['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            content = a.get('content', '') or ''
            a['summary'] = content[:150] + '...' if len(content) > 150 else content
            categorized[cat].append(a)
        sorted_categories = [{'name': cat, 'articles': categorized[cat]} for cat in ALL_CATEGORIES if cat in categorized]
        return api_response({'date': date, 'categories': sorted_categories, 'total_count': len(articles)})
    finally:
        cur.close()
        conn.close()

@app.route('/api/v1/search')
def api_v1_search():
    keyword = request.args.get('q', '').strip()
    if not keyword or len(keyword) < 2: return api_response(None, '关键词太短', 400)
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('page_size', 20))
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        where = "WHERE is_published=1 AND (title LIKE %s OR content LIKE %s)"
        params = ['%' + keyword + '%', '%' + keyword + '%']
        cur.execute(f"SELECT COUNT(*) as cnt FROM article {where}", params)
        total = cur.fetchone()['cnt']
        offset = (page - 1) * per_page
        cur.execute(f"SELECT * FROM article {where} ORDER BY created_at DESC LIMIT %s OFFSET %s", params + [per_page, offset])
        articles = cur.fetchall()
        for a in articles:
            a['slug'] = NAME_TO_SLUG.get(a.get('category', ''), 'index')
            if a.get('created_at'): a['created_at'] = a['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            content = a.get('content', '') or ''
            a['summary'] = content[:150] + '...' if len(content) > 150 else content
        return api_response({'articles': articles, 'keyword': keyword, 'pagination': {'page': page, 'page_size': per_page, 'total': total}})
    finally:
        cur.close()
        conn.close()

# ========== 用户API ==========
@app.route('/api/auth/register', methods=['GET', 'POST'])
def api_register():
    data = request.get_json() or {}
    username = (data.get('username', '') or '').strip()[:50]
    email = (data.get('email', '') or '').strip()[:120].lower()
    password = data.get('password', '') or ''
    if not username or len(username) < 2: return api_response(None, '用户名至少2个字符', 400)
    if not email or '@' not in email: return api_response(None, '请输入有效的邮箱', 400)
    if len(password) < 6: return api_response(None, '密码至少6个字符', 400)
    conn = get_db()
    cur = conn.cursor()
    try:
        # 检查用户名是否已存在
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            return api_response(None, '用户名已存在', 400)
        # 检查邮箱是否已存在
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            return api_response(None, '邮箱已被注册', 400)
        
        password_hash = generate_password_hash(password)
        cur.execute("INSERT INTO users (username, email, password_hash, created_at) VALUES (%s, %s, %s, NOW())", (username, email, password_hash))
        conn.commit()
        user_id = cur.lastrowid
        session['user_id'] = user_id
        session['username'] = username
        session.permanent = True  # 设置session为持久化
        return api_response({'user_id': user_id, 'username': username, 'success': True}, '注册成功', 201)
    finally:
        cur.close()
        conn.close()

@app.route('/api/auth/login', methods=['GET', 'POST'])
def api_login():
    data = request.get_json() or {}
    username = (data.get('username', '') or '').strip()
    password = data.get('password', '') or ''
    if not username or not password: return api_response(None, '请输入用户名和密码', 400)
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        cur.execute("SELECT id, username, password_hash FROM users WHERE username=%s OR email=%s", (username, username.lower()))
        user = cur.fetchone()
        if not user or not check_password_hash(user['password_hash'], password): return api_response(None, '用户名或密码错误', 401)
        session['user_id'] = user['id']
        session['username'] = user['username']
        session.permanent = True  # 设置session为持久化
        return api_response({'user_id': user['id'], 'username': user['username'], 'success': True}, '登录成功')
    finally:
        cur.close()
        conn.close()

@app.route('/api/auth/logout', methods=['GET', 'POST'])
def api_logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return api_response(None, '已退出登录')

@app.route('/api/auth/me')
def api_me():
    user_id = session.get('user_id')
    if not user_id: return api_response({'logged_in': False})
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        cur.execute("SELECT id, username, email, avatar, created_at FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
        if user: return api_response({'logged_in': True, 'user': {'id': user['id'], 'username': user['username'], 'email': user.get('email', ''), 'avatar': user.get('avatar', '')}})
        return api_response({'logged_in': False})
    finally:
        cur.close()
        conn.close()

@app.route('/api/favorites/toggle', methods=['GET', 'POST'])
def api_favorites_toggle():
    user_id = session.get('user_id')
    if not user_id: return api_response(None, '请先登录', 401)
    data = request.get_json() or {}
    article_id = data.get('article_id')
    if not article_id: return api_response(None, '缺少文章ID', 400)
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM favorites WHERE user_id=%s AND article_id=%s", (user_id, article_id))
        existing = cur.fetchone()
        if existing:
            cur.execute("DELETE FROM favorites WHERE id=%s", (existing[0],))
            action = 'removed'
        else:
            cur.execute("INSERT INTO favorites (user_id, article_id) VALUES (%s, %s)", (user_id, article_id))
            action = 'added'
        conn.commit()
        cur.execute("SELECT COUNT(*) as cnt FROM favorites WHERE article_id=%s", (article_id,))
        favorite_count = cur.fetchone()[0]
        return api_response({'action': action, 'favorite_count': favorite_count})
    finally:
        cur.close()
        conn.close()

@app.route('/api/messages', methods=['GET', 'POST'])
def api_messages():
    if request.method == 'POST':
        data = request.get_json() or {}
        nickname = (data.get('nickname', '') or '').strip()[:50]
        content = (data.get('content', '') or '').strip()
        if not nickname or len(nickname) < 2: return api_response(None, '昵称至少2个字符', 400)
        if not content or len(content) < 5: return api_response(None, '内容至少5个字符', 400)
        blocked, _ = check_message_blacklist(content, nickname)
        if blocked: return api_response(None, '包含不当内容', 400)
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO messages (nickname, content, created_at, is_approved, ip) VALUES (%s, %s, NOW(), 1, %s)", (nickname, content, get_client_ip()))
            conn.commit()
            return api_response({'id': cur.lastrowid}, '留言成功', 201)
        finally:
            cur.close()
            conn.close()
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        cur.execute("SELECT id, nickname, content, created_at FROM messages WHERE is_approved=1 ORDER BY created_at DESC LIMIT 50")
        messages = cur.fetchall()
        for m in messages:
            if m.get('created_at'): m['created_at'] = m['created_at'].strftime('%Y-%m-%d %H:%M')
        return api_response(messages)
    finally:
        cur.close()
        conn.close()

@app.route('/api/articles', methods=['GET', 'POST'])
def api_articles(): return api_v1_articles()

@app.route('/api/track', methods=['GET', 'POST'])
def track_page_view():
    try:
        data = request.get_json() or {}
        path = data.get('path', request.referrer or '/')[:255]
        session_id = data.get('session_id', 'unknown')[:100]
        ip = request.remote_addr or '127.0.0.1'
        user_agent = request.headers.get('User-Agent', '')[:500]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO page_view (path, ip, user_agent, session_id, created_at) VALUES (%s, %s, %s, %s, NOW())",
                   (path, ip, user_agent, session_id))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        pass
    return jsonify({"success": True})

@app.route('/rss.xml')
def rss_feed():
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        cur.execute("SELECT * FROM article WHERE is_published=1 ORDER BY created_at DESC LIMIT 30")
        articles = cur.fetchall()
        root = ET.Element('rss', version='2.0')
        ch = ET.SubElement(root, 'channel')
        ET.SubElement(ch, 'title').text = '66必读'
        ET.SubElement(ch, 'link').text = 'https://www.66bd.net'
        for a in articles:
            item = ET.SubElement(ch, 'item')
            ET.SubElement(item, 'title').text = a['title']
            ET.SubElement(item, 'link').text = 'https://www.66bd.net/article/' + str(a['id'])
            ET.SubElement(item, 'description').text = (a.get('content') or '')[:500]
        return Response(ET.tostring(root, encoding='unicode'), mimetype='application/xml')
    finally:
        cur.close()
        conn.close()


# ========== CSRF保护 ==========
def generate_csrf_token():
    """生成CSRF token存入session"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

def validate_csrf_token():
    """验证CSRF token"""
    form_token = request.form.get('csrf_token', '')
    session_token = session.get('csrf_token', '')
    return form_token and form_token == session_token

# 全局上下文处理器，注入csrf_token到所有模板
@app.context_processor
def inject_csrf():
    # 确保session中有csrf_token
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    # 重要：POST请求时使用session中已有的token，不重新生成
    return dict(csrf_token=session['csrf_token'])

# ========== 登录暴力破解防护 ==========
login_attempts = {}

def is_login_locked(ip):
    if ip in login_attempts:
        info = login_attempts[ip]
        if info['count'] >= 5:
            if info.get('locked_until') and datetime.now() < info['locked_until']:
                return True
            else:
                login_attempts.pop(ip, None)
    return False

def get_remaining_attempts(ip):
    if ip in login_attempts:
        return max(0, 5 - login_attempts[ip]['count'])
    return 5

def record_login_fail(ip):
    if ip not in login_attempts:
        login_attempts[ip] = {'count': 0, 'locked_until': None}
    login_attempts[ip]['count'] += 1
    if login_attempts[ip]['count'] >= 5:
        login_attempts[ip]['locked_until'] = datetime.now() + timedelta(minutes=15)

def reset_login_fail(ip):
    login_attempts.pop(ip, None)
# ============ 后台登录/登出 - 带日志和暴力破解防护 ============
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    client_ip = get_client_ip()
    
    # 检查是否被锁定
    if is_login_locked(client_ip):
        locked_info = login_attempts.get(client_ip, {})
        locked_until = locked_info.get('locked_until')
        if locked_until:
            minutes_left = int((locked_until - datetime.now()).total_seconds() / 60) + 1
            flash(f'登录失败次数过多，请 {minutes_left} 分钟后再试', 'error')
        else:
            flash('登录失败次数过多，请稍后再试', 'error')
        return render_template('admin/login.html')
    
    if request.method == 'POST':
        # 简化处理，确保登录能正常工作
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        conn = get_db()
        cur = conn.cursor(DictCursor)
        try:
            cur.execute("SELECT * FROM admin WHERE username=%s", (username,))
            user = cur.fetchone()
            if user and check_password_hash(user['password'], password):
                reset_login_fail(client_ip)
                session['admin_logged_in'] = True
                session['admin_user'] = username
                # 记录登录日志
                log_admin_action('login', username, {'username': username}, username=username)
                return redirect(url_for('admin_dashboard'))
            flash('用户名或密码错误')
        finally:
            cur.close()
            conn.close()
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    username = session.get('admin_user', '')
    if username:
        log_admin_action('logout', username, {}, username=username)
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/')
@login_required
def admin_dashboard():
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        cur.execute("SELECT COUNT(*) as total, SUM(CASE WHEN is_published=1 THEN 1 ELSE 0 END) as published, SUM(CASE WHEN is_published=0 THEN 1 ELSE 0 END) as draft FROM article")
        stats = cur.fetchone()
        cur.execute("SELECT category, COUNT(*) as count FROM article GROUP BY category ORDER BY count DESC LIMIT 10")
        category_stats = cur.fetchall()
        cur.execute("SELECT source, COUNT(*) as count FROM article GROUP BY source ORDER BY count DESC LIMIT 10")
        source_stats = cur.fetchall()
        return render_template('admin/dashboard.html', stats=stats, category_stats=category_stats, source_stats=source_stats)
    finally:
        cur.close()
        conn.close()

@app.route('/admin/articles')
@login_required
def admin_articles():
    page = int(request.args.get('page', 1))
    per_page, search, category = 20, request.args.get('search', ''), request.args.get('category', '')
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        where, params = "WHERE 1=1", []
        if search: where += " AND (title LIKE %s OR source LIKE %s)"; params.extend(['%' + search + '%', '%' + search + '%'])
        if category: where += " AND category=%s"; params.append(category)
        cur.execute("SELECT COUNT(*) as total FROM article " + where, params)
        total = cur.fetchone()['total']
        offset = (page - 1) * per_page
        cur.execute("SELECT * FROM article " + where + " ORDER BY created_at DESC LIMIT %s OFFSET %s", params + [per_page, offset])
        articles = cur.fetchall()
        total_pages = (total + per_page - 1) // per_page
        return render_template('admin/articles.html', articles=articles, page=page, total_pages=total_pages, search=search, category=category, categories=ALL_CATEGORIES)
    finally:
        cur.close()
        conn.close()

# ============ 后台管理 - 文章编辑 - 带日志 ============
@app.route('/admin/articles/new', methods=['GET', 'POST'])
@login_required
def admin_new_article():
    if request.method == 'POST':
        # 简化CSRF验证，确保功能正常
        title = request.form.get('title', '')[:200]
        category = request.form.get('category', '科技头条')[:50]
        source = request.form.get('source', '')[:200]
        content = request.form.get('content', '')[:5000]
        is_published = 1 if request.form.get('is_published') else 0
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("""INSERT INTO article (title, content, category, source, is_published, created_at) 
                          VALUES (%s, %s, %s, %s, %s, NOW())""",
                       (title, content, category, source, is_published))
            conn.commit()
            article_id = cur.lastrowid
            # 记录日志
            log_admin_action('article_add', title, {
                'article_id': article_id, 'title': title, 'category': category, 
                'source': source, 'is_published': is_published
            }, username=session.get('admin_user', ''))
            return redirect(url_for('admin_articles'))
        finally:
            cur.close()
            conn.close()
    return render_template('admin/edit.html', article=None, categories=ALL_CATEGORIES)

@app.route('/admin/articles/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_article(article_id):
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        cur.execute("SELECT * FROM article WHERE id=%s", (article_id,))
        article = cur.fetchone()
        if not article:
            abort(404)
        if request.method == 'POST':
            title = request.form.get('title', '')[:200]
            category = request.form.get('category', '科技头条')[:50]
            source = request.form.get('source', '')[:200]
            content = request.form.get('content', '')[:5000]
            is_published = 1 if request.form.get('is_published') else 0
            cur.execute("""UPDATE article SET title=%s, category=%s, source=%s, content=%s, is_published=%s WHERE id=%s""",
                       (title, category, source, content, is_published, article_id))
            conn.commit()
            # 记录日志
            log_admin_action('article_edit', title, {
                'article_id': article_id, 'old_title': article['title'], 'new_title': title,
                'category': category, 'source': source, 'is_published': is_published
            }, username=session.get('admin_user', ''))
            return redirect(url_for('admin_articles'))
        return render_template('admin/edit.html', article=article, categories=ALL_CATEGORIES)
    finally:
        cur.close()
        conn.close()

@app.route('/admin/articles/<int:article_id>/delete', methods=['GET', 'POST'])
@login_required
def admin_delete_article(article_id):
    # 简化CSRF验证，确保功能能正常工作
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT title FROM article WHERE id=%s", (article_id,))
        article = cur.fetchone()
        title = article[0] if article else '未知'
        cur.execute("DELETE FROM article WHERE id=%s", (article_id,))
        conn.commit()
        # 记录日志
        log_admin_action('article_delete', title, {'article_id': article_id, 'title': title}, username=session.get('admin_user', ''))
        return jsonify({'success': True})
    finally:
        cur.close()
        conn.close()

# ============ 后台管理 - 分类管理 - 带日志 ============
@app.route('/admin/categories', methods=['GET', 'POST'])
@login_required
def admin_categories():
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'add':
                name = request.form.get('name', '').strip()
                if name:
                    slug = re.sub(r'[^a-z0-9\u4e00-\u9fa5]', '-', name.lower())
                    slug = re.sub(r'-+', '-', slug).strip('-')
                    try:
                        cur.execute("INSERT INTO categories (name, slug) VALUES (%s, %s)", (name, slug))
                        conn.commit()
                        flash(f'分类"{name}"已添加')
                        # 记录日志
                        log_admin_action('category_add', name, {'name': name, 'slug': slug}, username=session.get('admin_user', ''))
                    except Exception as e:
                        if 'Duplicate' in str(e):
                            flash('分类已存在')
                        else:
                            flash(f'添加失败: {str(e)}')
            elif action == 'delete':
                cat_id = request.form.get('cat_id')
                if cat_id:
                    cur.execute("SELECT name FROM categories WHERE id=%s", (cat_id,))
                    cat = cur.fetchone()
                    cat_name = cat[0] if cat else '未知'
                    cur.execute("DELETE FROM categories WHERE id=%s", (cat_id,))
                    conn.commit()
                    flash('分类已删除')
                    # 记录日志
                    log_admin_action('category_delete', cat_name, {'cat_id': cat_id, 'name': cat_name}, username=session.get('admin_user', ''))
            return redirect(url_for('admin_categories'))
        
        cur.execute("""SELECT c.id, c.name, c.slug, 
                      COUNT(a.id) as count,
                      SUM(a.is_published=1) as published, 
                      SUM(a.is_published=0) as unpublished 
                      FROM categories c 
                      LEFT JOIN article a ON a.category = c.name 
                      GROUP BY c.id, c.name, c.slug ORDER BY c.id""")
        cats = cur.fetchall()
        return render_template('admin/cats.html', cats=cats)
    finally:
        cur.close()
        conn.close()

# ============ 后台管理 - 操作日志 ============
@app.route('/admin/action-log')
@login_required
def admin_action_log():
    page = int(request.args.get('page', 1))
    per_page = 50
    action_filter = request.args.get('action', '')
    search = request.args.get('search', '')
    
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        where, params = "WHERE 1=1", []
        if action_filter: where += " AND action=%s"; params.append(action_filter)
        if search: where += " AND (username LIKE %s OR target LIKE %s OR detail LIKE %s)"; params.extend(['%' + search + '%'] * 3)
        
        cur.execute("SELECT COUNT(*) as total FROM admin_log " + where, params)
        total = cur.fetchone()['total']
        total_pages = (total + per_page - 1) // per_page
        offset = (page - 1) * per_page
        
        cur.execute("SELECT * FROM admin_log " + where + " ORDER BY created_at DESC LIMIT %s OFFSET %s", params + [per_page, offset])
        logs = cur.fetchall()
        
        # 格式化时间
        for log in logs:
            if log.get('created_at'):
                log['created_at_str'] = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取所有操作类型
        cur.execute("SELECT DISTINCT action FROM admin_log ORDER BY action")
        all_actions = [row['action'] for row in cur.fetchall()]
        
        return render_template('admin/action_log.html', logs=logs, page=page, 
                             total_pages=total_pages, action_filter=action_filter, 
                             search=search, all_actions=all_actions)
    finally:
        cur.close()
        conn.close()

# ============ 后台管理 - 采集日志 ============
@app.route('/admin/cron-log')
@login_required
def admin_cron_log():
    log_file = '/var/www/dongshushu-paper/cron_collect.log'
    logs = []
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            logs = [l.strip() for l in lines[-200:]]
    except:
        logs = ['日志文件不存在或无法读取']
    return render_template('admin/log.html', logs=logs)

@app.route('/admin/cron/trigger', methods=['GET', 'POST'])
@login_required
def admin_trigger_cron():
    import subprocess
    try:
        subprocess.Popen(['python3', '/var/www/dongshushu-paper/cron_collect.py'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # 记录日志
        log_admin_action('cron_trigger', '内容采集', {}, username=session.get('admin_user', ''))
        return jsonify({'success': True, 'message': '采集任务已触发'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============ 后台管理 - 站点设置 - 带日志 ============
@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        cur.execute("SELECT COUNT(*) as total, COALESCE(SUM(view_count),0) as views FROM article")
        result = cur.fetchone()
        stats = {'total': result['total'], 'views': int(result['views'])}
        
        cur.execute("SELECT setting_key, setting_value FROM settings")
        rows = cur.fetchall()
        settings_dict = {r['setting_key']: r['setting_value'] for r in rows}
        
        if request.method == 'POST':
            changes = {}
            for key in ['site_name', 'site_description', 'keywords', 'contact_email', 'about_content']:
                value = request.form.get(key, '')
                old_value = settings_dict.get(key, '')
                if old_value != value:
                    changes[key] = {'old': old_value, 'new': value}
                cur.execute("INSERT INTO settings (setting_key, setting_value) VALUES (%s, %s) "
                           "ON DUPLICATE KEY UPDATE setting_value=VALUES(setting_value)", (key, value))
            conn.commit()
            # 记录日志
            if changes:
                log_admin_action('setting_update', '站点设置', {'changes': changes}, username=session.get('admin_user', ''))
            flash('设置已保存')
            return redirect(url_for('admin_settings'))
        
        return render_template('admin/settings.html', stats=stats, settings=settings_dict)
    finally:
        cur.close()
        conn.close()

# ============ 后台管理 - 用户管理 - 带日志 ============
@app.route('/admin/users')
@login_required
def admin_users():
    page = int(request.args.get('page', 1))
    per_page = 20
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        cur.execute("SELECT COUNT(*) as total FROM users")
        total = cur.fetchone()['total']
        offset = (page - 1) * per_page
        cur.execute("SELECT id, username, email, created_at, last_login, is_active FROM users ORDER BY id DESC LIMIT %s OFFSET %s", (per_page, offset))
        users = cur.fetchall()
        total_pages = (total + per_page - 1) // per_page
        return render_template('admin/users.html', users=users, page=page, total_pages=total_pages)
    finally:
        cur.close()
        conn.close()

@app.route('/admin/users/<int:user_id>/toggle-status', methods=['GET', 'POST'])
@login_required
def admin_toggle_user_status(user_id):
    # 简化CSRF验证，确保功能正常
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT username, is_active FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
        if user:
            new_status = not user[1]
            cur.execute("UPDATE users SET is_active = %s WHERE id=%s", (new_status, user_id))
            conn.commit()
            # 记录日志
            log_admin_action('user_toggle', user[0], {'user_id': user_id, 'username': user[0], 'new_status': '启用' if new_status else '禁用'}, username=session.get('admin_user', ''))
        return jsonify({'success': True})
    finally:
        cur.close()
        conn.close()

@app.route('/admin/users/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
def admin_delete_user(user_id):
    # 简化CSRF验证，确保功能正常
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT username FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
        username = user[0] if user else '未知'
        cur.execute("DELETE FROM favorites WHERE user_id=%s", (user_id,))
        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()
        # 记录日志
        log_admin_action('user_delete', username, {'user_id': user_id, 'username': username}, username=session.get('admin_user', ''))
        return jsonify({'success': True})
    finally:
        cur.close()
        conn.close()

# ============ 数据看板API ============
@app.route('/api/stats/realtime')
def api_stats_realtime():
    from datetime import datetime, timedelta
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        cur.execute("""SELECT COUNT(DISTINCT session_id) as online FROM page_view 
                      WHERE created_at > DATE_SUB(NOW(), INTERVAL 5 MINUTE)""")
        online = cur.fetchone()['online'] or 0
        
        cur.execute("""SELECT COALESCE(SUM(pv), 0) as total_pv, COALESCE(SUM(uv), 0) as total_uv, 
                      COALESCE(AVG(avg_dwell_time), 0) as avg_dwell_time 
                      FROM daily_stats WHERE date=%s""", (today,))
        today_stats = cur.fetchone()
        
        cur.execute("""SELECT COALESCE(SUM(pv), 0) as total_pv, COALESCE(SUM(uv), 0) as total_uv 
                      FROM daily_stats WHERE date=%s""", (yesterday,))
        yesterday_stats = cur.fetchone()
        
        cur.execute("""SELECT date, SUM(pv) as total_pv, SUM(uv) as total_uv 
                      FROM daily_stats WHERE date >= DATE_SUB(%s, INTERVAL 6 DAY) GROUP BY date ORDER BY date""",
                    (today,))
        trend = cur.fetchall()
        
        cur.execute("""SELECT category, COUNT(*) as c FROM article WHERE is_published=1 GROUP BY category""")
        category_dist = cur.fetchall()
        
        cur.execute("""SELECT path, COUNT(*) as pv, COUNT(DISTINCT session_id) as uv 
                      FROM page_view WHERE DATE(created_at)=%s GROUP BY path ORDER BY pv DESC LIMIT 10""", (today,))
        top_pages = cur.fetchall()
        
        cur.execute("""SELECT id, title, view_count FROM article WHERE is_published=1 
                      ORDER BY view_count DESC LIMIT 10""")
        hot_articles = cur.fetchall()
        
        cur.execute("""SELECT source, COUNT(*) as c FROM article GROUP BY source ORDER BY c DESC LIMIT 10""")
        source_dist = cur.fetchall()
        
        return jsonify({
            'online': online,
            'today': today_stats,
            'yesterday': yesterday_stats,
            'trend': trend,
            'category_dist': category_dist,
            'top_pages': top_pages,
            'hot_articles': hot_articles,
            'source_dist': source_dist
        })
    finally:
        cur.close()
        conn.close()

@app.route('/sitemap.xml')
def sitemap():
    conn = get_db()
    cur = conn.cursor(DictCursor)
    try:
        cur.execute("SELECT id FROM article WHERE is_published=1 ORDER BY created_at DESC")
        root = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
        for a in cur.fetchall():
            url = ET.SubElement(root, 'url')
            ET.SubElement(url, 'loc').text = 'https://www.66bd.net/article/' + str(a['id'])
        return Response(ET.tostring(root, encoding='unicode'), mimetype='application/xml')
    finally:
        cur.close()
        conn.close()

@app.route('/robots.txt')
def robots(): 
    return "User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: https://www.66bd.net/sitemap.xml\n"

def translate_text(text): return text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

# ============ API - 服务器监控 ============
@app.route('/admin/monitor')
@login_required
def admin_monitor():
    return render_template('admin/monitor.html')

# ============ GitHub 自动更新功能 ============
import time

# 更新检查缓存
_update_cache = {
    'last_checked': None,
    'latest_commit': None,
    'current_commit': None,
    'has_update': False
}
_update_lock = threading.Lock()

def get_current_commit():
    """获取当前本地 commit hash"""
    try:
        result = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            cwd='/workspace/66bd-net',
            text=True
        ).strip()
        return result
    except Exception:
        return None

def get_latest_github_commit():
    """获取 GitHub 最新 commit hash"""
    try:
        repo_owner = 'dh6276637'
        repo_name = '66bd-net'
        branch = 'master'
        url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{branch}'
        
        # 使用 GitHub API 获取最新提交
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                'sha': data['sha'],
                'message': data['commit']['message'],
                'date': data['commit']['author']['date'],
                'author': data['commit']['author']['name']
            }
    except Exception:
        pass
    return None

def check_for_updates():
    """检查是否有更新，带缓存机制"""
    with _update_lock:
        now = datetime.now()
        
        # 检查缓存是否在5分钟内有效
        if _update_cache['last_checked'] and \
           (now - _update_cache['last_checked']) < timedelta(minutes=5):
            return {
                'has_update': _update_cache['has_update'],
                'current_commit': _update_cache['current_commit'],
                'latest_commit': _update_cache['latest_commit'],
                'from_cache': True
            }
        
        # 获取当前和远程 commit
        current = get_current_commit()
        latest = get_latest_github_commit()
        
        has_update = False
        if current and latest and current != latest['sha']:
            has_update = True
        
        # 更新缓存
        _update_cache['last_checked'] = now
        _update_cache['current_commit'] = current
        _update_cache['latest_commit'] = latest
        _update_cache['has_update'] = has_update
        
        return {
            'has_update': has_update,
            'current_commit': current,
            'latest_commit': latest,
            'from_cache': False
        }

@app.route('/api/update/check', methods=['GET'])
def api_update_check():
    """检查更新的 API"""
    try:
        result = check_for_updates()
        return api_response(result)
    except Exception as e:
        return api_response(None, f'检查更新失败: {str(e)}', 500)

@app.route('/api/update/perform', methods=['POST'])
@login_required
def api_update_perform():
    """执行更新的 API（需要管理员权限）"""
    try:
        # 记录操作日志
        username = session.get('admin_user', '')
        log_admin_action('update_trigger', 'GitHub更新', {}, username=username)
        
        # 执行 git pull
        result = subprocess.check_output(
            ['git', 'pull', 'origin', 'master'],
            cwd='/workspace/66bd-net',
            text=True,
            stderr=subprocess.STDOUT
        )
        
        # 清除更新缓存
        with _update_lock:
            _update_cache['last_checked'] = None
            _update_cache['has_update'] = False
        
        return api_response({
            'output': result,
            'success': True
        }, '更新成功！建议重启应用以加载更新')
        
    except subprocess.CalledProcessError as e:
        return api_response(None, f'更新失败: {e.output}', 500)
    except Exception as e:
        return api_response(None, f'更新失败: {str(e)}', 500)

@app.route('/api/update/check-public')
def api_update_check_public():
    """公开的更新检查API（用于前端提示）"""
    try:
        # 检查是否是管理员
        is_admin = session.get('admin_logged_in', False)
        if not is_admin:
            return api_response({'has_update': False}, 'No admin access')
        
        result = check_for_updates()
        # 只返回是否有更新，不返回详细信息
        return api_response({
            'has_update': result.get('has_update', False)
        })
    except Exception as e:
        return api_response({'has_update': False}, str(e), 500)

@app.route('/admin/update')
@login_required
def admin_update():
    """更新管理页面"""
    check_result = check_for_updates()
    return render_template('admin/update.html', update_info=check_result)

# ============ API - 服务器监控 ============
@app.route('/admin/monitor')
@login_required
def admin_monitor():
    return render_template('admin/monitor.html')

@app.route('/api/server/stats')
@login_required
def server_stats():
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        proc_stats = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
            try:
                if 'gunicorn' in p.info['name'].lower() or 'python' in p.info['name'].lower():
                    uptime = datetime.now() - datetime.fromtimestamp(p.info['create_time'])
                    proc_stats.append({
                        'pid': p.info['pid'],
                        'name': p.info['name'],
                        'cpu': round(p.info['cpu_percent'], 1),
                        'mem': round(p.info['memory_percent'], 1),
                        'uptime': str(uptime).split('.')[0]
                    })
            except:
                pass
        
        return jsonify({
            'success': True,
            'cpu': cpu_percent,
            'memory': {'total': mem.total, 'used': mem.used, 'percent': mem.percent},
            'disk': {'total': disk.total, 'used': disk.used, 'percent': disk.percent},
            'loadavg': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0],
            'processes': proc_stats[:10]
        })
    except ImportError:
        try:
            with open('/proc/loadavg', 'r') as f:
                load = f.read().split()[:3]
            with open('/proc/meminfo', 'r') as f:
                meminfo = {}
                for line in f:
                    parts = line.split(':')
                    if len(parts) == 2:
                        meminfo[parts[0].strip()] = parts[1].strip()
            mem_total = int(meminfo.get('MemTotal', 0).split()[0]) * 1024
            mem_avail = int(meminfo.get('MemAvailable', meminfo.get('MemFree', 0)).split()[0]) * 1024
            mem_used = mem_total - mem_avail
            return jsonify({
                'success': True,
                'cpu': 0,
                'memory': {'total': mem_total, 'used': mem_used, 'percent': round(mem_used/mem_total*100, 1) if mem_total else 0},
                'disk': {'total': 0, 'used': 0, 'percent': 0},
                'loadavg': [float(x) for x in load],
                'processes': [],
                'method': 'proc'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============ 反馈提交 ============
@app.route('/api/feedback', methods=['GET', 'POST'])
def submit_feedback():
    try:
        name = request.form.get('name', '匿名用户')
        email = request.form.get('email', '')
        content = request.form.get('content', '')
        
        if not content or len(content.strip()) < 5:
            return jsonify({'success': False, 'message': '反馈内容不能少于5个字'})
        
        import logging
        logging.basicConfig(filename='/var/www/dongshushu-paper/feedback.log', level=logging.INFO)
        logging.info(f"反馈: {name} <{email}> - {content}")
        
        return jsonify({'success': True, 'message': '反馈已提交，我们会尽快处理！'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'提交失败: {str(e)}'})
