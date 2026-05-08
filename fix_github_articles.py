#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量为GitHub文章补充README内容 (增强版)
支持多种标题格式
"""

import requests
import time
import pymysql
import re
import base64

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'paper_user',
    'password': 'paper_db2026',
    'database': 'dongshushu_paper',
    'charset': 'utf8mb4'
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def extract_github_repo_name(title):
    """从标题提取GitHub仓库名 - 支持多种格式"""
    patterns = [
        r'GitHub热门项目:\s*(.+)',   # GitHub热门项目: xxx
        r'GitHub热门:\s*(.+)',         # GitHub热门: xxx
        r'^(.+)$',                      # 直接是仓库名
    ]
    for pattern in patterns:
        match = re.search(pattern, title.strip())
        if match:
            repo_name = match.group(1).strip()
            # 清理可能的特殊字符
            repo_name = repo_name.strip()
            if repo_name and not repo_name.startswith('GitHub'):
                return repo_name
    return None

def get_github_repo_by_name(repo_name):
    """通过GitHub API搜索仓库获取信息"""
    try:
        # 尝试精确匹配
        url = f"https://api.github.com/repos/{repo_name}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        
        # 如果精确匹配失败，尝试搜索
        url = f"https://api.github.com/search/repositories?q={repo_name}+in:name&sort=stars&order=desc&per_page=3"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('items'):
                # 找最匹配的
                for item in data['items']:
                    if item['name'].lower() == repo_name.lower():
                        return item
                return data['items'][0]  # 返回stars最高的
    except Exception as e:
        print(f"API搜索失败: {e}")
    return None

def fetch_readme(owner, repo_name):
    """抓取README内容"""
    # 尝试 main 分支
    for branch in ['main', 'master']:
        try:
            url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/{branch}/README.md"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                return resp.text[:3000]
        except:
            pass
    
    # 尝试 GitHub API
    try:
        url = f"https://api.github.com/repos/{owner}/{repo_name}/readme"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('content'):
                content = base64.b64decode(data['content']).decode('utf-8')
                return content[:3000]
    except Exception as e:
        print(f"API README获取失败: {e}")
    
    return None

def update_article(article_id, content, content_cn, url=None):
    """更新文章内容"""
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            if url:
                cur.execute(
                    "UPDATE article SET content=%s, content_cn=%s, url=%s WHERE id=%s",
                    (content[:3000], content_cn[:3000], url, article_id)
                )
            else:
                cur.execute(
                    "UPDATE article SET content=%s, content_cn=%s WHERE id=%s",
                    (content[:3000], content_cn[:3000], article_id)
                )
        conn.commit()
        return True
    finally:
        conn.close()

def main():
    print("=== 开始批量补充GitHub README (增强版) ===")
    
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            # 获取所有GitHub文章
            cur.execute("SELECT id, title, content, url FROM article WHERE source='GitHub Trending'")
            articles = cur.fetchall()
            print(f"共找到 {len(articles)} 篇GitHub文章")
            
            success_count = 0
            fail_count = 0
            skip_count = 0
            
            for article in articles:
                article_id, title, content, existing_url = article
                print(f"\n处理: {title[:50]}...")
                
                # 从标题提取仓库名
                repo_name = extract_github_repo_name(title)
                if not repo_name:
                    print(f"  -> 无法提取仓库名")
                    fail_count += 1
                    continue
                
                print(f"  -> 提取到仓库名: {repo_name}")
                
                # 获取仓库信息
                repo_info = get_github_repo_by_name(repo_name)
                if not repo_info:
                    print(f"  -> 未找到仓库: {repo_name}")
                    fail_count += 1
                    continue
                
                owner = repo_info['owner']['login']
                repo_full_name = repo_info['name']
                html_url = repo_info['html_url']
                stars = repo_info['stargazers_count']
                description = repo_info.get('description') or '暂无描述'
                
                print(f"  -> 找到仓库: {owner}/{repo_full_name} ({stars} stars)")
                
                # 抓取README
                readme = fetch_readme(owner, repo_full_name)
                
                # 构建新内容
                new_content = f"""📦 GitHub项目：{repo_full_name}
🔗 仓库地址：{html_url}
⭐ Stars：{stars} | 👤 作者：{owner}

📝 项目描述：{description}

{'='*50}
📖 README 内容：
{'='*50}
{readme if readme else '(暂无README)'}"""

                # 更新数据库（包含URL）
                if update_article(article_id, new_content, new_content, html_url):
                    success_count += 1
                    print(f"  -> 更新成功!")
                else:
                    fail_count += 1
                    print(f"  -> 更新失败")
                
                # 速率限制
                time.sleep(1.5)
                
    finally:
        conn.close()
    
    print(f"\n=== 完成: 成功 {success_count}, 失败 {fail_count} ===")

if __name__ == "__main__":
    main()

