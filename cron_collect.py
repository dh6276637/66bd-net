#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import feedparser
import json
import time
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from collections import defaultdict
import hashlib
import urllib.request
import urllib.parse
import re

# ============ 文章正文提取函数 ============

def extract_article_content(url, timeout=15):
    """从URL抓取文章正文内容，返回(text, html)"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        encoding = response.encoding
        if 'charset' in response.headers.get('Content-Type', ''):
            encoding = response.headers['Content-Type'].split('charset=')[-1]
        elif not encoding or encoding == 'ISO-8859-1':
            charset_match = re.search(r'charset=["\']*([^"\' >]+)', response.text[:2000])
            if charset_match:
                encoding = charset_match.group(1)
        
        html = response.content.decode(encoding or 'utf-8', errors='replace')
        soup = BeautifulSoup(html, 'lxml')
        
        for tag in soup(['script', 'style', 'noscript', 'iframe', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
        
        article = soup.find('article')
        if article:
            text = article.get_text(separator=' ', strip=True)
            text = ' '.join(text.split())
            return text[:5000], str(article)
        
        main = soup.find('main')
        if main:
            text = main.get_text(separator=' ', strip=True)
            text = ' '.join(text.split())
            return text[:5000], str(main)
        
        max_text = ''
        max_element = None
        for tag in soup.find_all(['div', 'section']):
            text = tag.get_text(strip=True)
            if len(text) > len(max_text):
                p_count = len(tag.find_all('p'))
                if p_count >= 2:
                    max_text = text
                    max_element = tag
        
        if max_element and len(max_text) > 200:
            text = max_element.get_text(separator=' ', strip=True)
            text = ' '.join(text.split())
            return text[:5000], str(max_element)
        
        body = soup.find('body')
        if body:
            text = body.get_text(separator=' ', strip=True)
            text = ' '.join(text.split())
            return text[:5000], str(body)
        
        return '', ''
        
    except Exception as e:
        logging.warning("抓取文章失败 %s: %s", url, str(e)[:100])
        return '', ''


def get_hn_comments_summary(hn_item_id, timeout=10):
    """获取HN帖子的评论摘要"""
    try:
        hn_api_url = "https://hacker-news.firebaseio.com/v0/item/%s.json" % hn_item_id
        response = requests.get(hn_api_url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            if data and 'kids' in data:
                comments = []
                for kid_id in data['kids'][:5]:
                    try:
                        comment_resp = requests.get("https://hacker-news.firebaseio.com/v0/item/%s.json" % kid_id, timeout=5)
                        if comment_resp.status_code == 200:
                            comment_data = comment_resp.json()
                            if comment_data and comment_data.get('text'):
                                text = BeautifulSoup(comment_data['text'], 'lxml').get_text()
                                comments.append(text[:500])
                    except:
                        continue
                return '\n'.join(comments)
    except Exception as e:
        logging.warning("获取HN评论失败 %s: %s", hn_item_id, str(e)[:50])
    return ''

# ============ 图片处理函数 ============

def get_base_url(url):
    """从URL提取基础域名"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def fix_relative_url(img_src, base_url):
    """修复相对路径图片URL"""
    if not img_src:
        return img_src
    
    if img_src.startswith(('http://', 'https://', '//')):
        if img_src.startswith('//'):
            return 'https:' + img_src
        return img_src
    
    if img_src.startswith('/'):
        base = get_base_url(base_url)
        return base + img_src
    else:
        from urllib.parse import urljoin
        return urljoin(base_url, img_src)

def process_html_with_images(html_content, source_url=''):
    """处理HTML内容，保留img标签，转换相对路径为绝对路径"""
    if not html_content:
        return ''
    
    soup = BeautifulSoup(html_content, 'lxml')
    
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src') or ''
        if src and not src.startswith('data:'):
            fixed_src = fix_relative_url(src, source_url)
            img['src'] = fixed_src
            img['referrerpolicy'] = 'no-referrer'
        
        data_src = img.get('data-src')
        if data_src and not data_src.startswith('data:'):
            fixed_src = fix_relative_url(data_src, source_url)
            img['data-src'] = fixed_src
            img['referrerpolicy'] = 'no-referrer'
        
        if not img.get('src'):
            img.decompose()
    
    return str(soup)

def clean_html(html_content):
    """清理HTML标签，提取纯文本"""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, 'lxml')
    text = soup.get_text(separator=' ', strip=True)
    text = ' '.join(text.split())
    return text

def extract_content_with_images(html_content, source_url=''):
    """提取内容，保留图片但清理危险标签"""
    if not html_content:
        return '', ''
    
    soup = BeautifulSoup(html_content, 'lxml')
    
    dangerous_tags = ['script', 'style', 'iframe', 'object', 'embed', 'form']
    for tag in soup(dangerous_tags):
        tag.decompose()
    
    dangerous_attrs = ['onclick', 'onerror', 'onload']
    for tag in soup.find_all(True):
        for attr in dangerous_attrs:
            if attr in tag.attrs:
                del tag[attr]
        href = tag.get('href', '')
        if href.startswith('javascript:'):
            del tag['href']
    
    html_with_images = process_html_with_images(str(soup), source_url)
    
    text_soup = BeautifulSoup(html_with_images, 'lxml')
    text = text_soup.get_text(separator=' ', strip=True)
    text = ' '.join(text.split())
    
    return html_with_images, text

# ============ 翻译功能 ============

def is_english_text(text):
    if not text:
        return False
    letters = sum(1 for c in text if c.isalpha())
    if letters == 0:
        return False
    english_letters = sum(1 for c in text if ord(c) < 128 and c.isalpha())
    return english_letters / letters > 0.5

def translate_to_chinese(text, max_retries=3):
    if not text or len(text.strip()) == 0:
        return text
    
    if not is_english_text(text):
        return text
    
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q=" + urllib.parse.quote(text[:5000])
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
        logging.warning("翻译失败: %s", str(e)[:100])
    
    return text

def translate_long_text(text, chunk_size=1800):
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

# ============ 采集脚本 ============

API_URL = "http://127.0.0.1:5000/api/articles"
LOG_FILE = "/var/www/dongshushu-paper/cron_collect.log"

# RSS源配置 - 按栏目分类
RSS_SOURCES = {
    # ============ 智能AI ============
    "量子位": {"url": "https://www.qbitai.com/feed", "category": "智能AI", "min_content_length": 50},
    "新智元": {"url": "https://plink.anyfeeder.com/weixin/AI_era", "category": "智能AI", "min_content_length": 50},
    "OpenAI博客": {"url": "https://openai.com/news/rss.xml", "category": "智能AI", "min_content_length": 50},
    "微软研究院AI": {"url": "https://plink.anyfeeder.com/weixin/MSRAsia", "category": "智能AI", "min_content_length": 50},
    "MIT AI": {"url": "https://www.technologyreview.com/feed/", "category": "智能AI", "min_content_length": 50},
    "arXiv AI": {"url": "https://rss.arxiv.org/rss/cs.AI", "category": "智能AI", "min_content_length": 50},
    "arXiv机器学习": {"url": "https://rss.arxiv.org/rss/cs.LG", "category": "智能AI", "min_content_length": 50},
    
    # ============ 安全攻防 ============
    "FreeBuf": {"url": "https://www.freebuf.com/feed", "category": "安全攻防", "min_content_length": 50},
    "先知社区": {"url": "https://xz.aliyun.com/feed", "category": "安全攻防", "min_content_length": 50},
    "嘶吼": {"url": "https://www.4hou.com/rss", "category": "安全攻防", "min_content_length": 50},
    "跳跳糖": {"url": "https://tttang.com/rss.xml", "category": "安全攻防", "min_content_length": 50},
    "Seebug Paper": {"url": "https://paper.seebug.org/rss/", "category": "安全攻防", "min_content_length": 50},
    "安全客": {"url": "https://api.anquanke.com/data/v1/rss", "category": "安全攻防", "min_content_length": 50},
    "The Hacker News": {"url": "https://feeds.feedburner.com/TheHackersNews", "category": "安全攻防", "min_content_length": 50},
    
    # ============ 时政热点 ============
    "央视新闻": {"url": "https://plink.anyfeeder.com/weixin/cctvnewscenter", "category": "时政热点", "min_content_length": 50},
    "中国日报": {"url": "https://plink.anyfeeder.com/chinadaily/china", "category": "时政热点", "min_content_length": 50},
    "BBC中文": {"url": "https://plink.anyfeeder.com/bbc/cn", "category": "时政热点", "min_content_length": 50},
    "参考消息": {"url": "https://plink.anyfeeder.com/weixin/ckxxwx", "category": "时政热点", "min_content_length": 50},
    "解放军报": {"url": "https://plink.anyfeeder.com/jiefangjunbao", "category": "时政热点", "min_content_length": 50},
    
    # ============ 科技头条 ============
    "36kr": {"url": "https://36kr.com/feed", "category": "科技头条", "min_content_length": 50},
    "钛媒体": {"url": "https://www.tmtpost.com/rss", "category": "科技头条", "min_content_length": 50},
    "少数派": {"url": "https://sspai.com/feed", "category": "科技头条", "min_content_length": 50},
    "IT之家": {"url": "https://www.ithome.com/rss/", "category": "科技头条", "min_content_length": 50},
    "爱范儿": {"url": "https://www.ifanr.com/feed", "category": "科技头条", "min_content_length": 50},
    "TechCrunch": {"url": "https://techcrunch.com/feed/", "category": "科技头条", "min_content_length": 50},
    "The Verge": {"url": "https://www.theverge.com/rss/index.xml", "category": "科技头条", "min_content_length": 50},
    "Wired": {"url": "https://www.wired.com/feed/rss", "category": "科技头条", "min_content_length": 50},
    "极客公园": {"url": "https://www.geekpark.net/rss", "category": "科技头条", "min_content_length": 50},
    
    # ============ 开发者生态 ============
    "阮一峰博客": {"url": "https://www.ruanyifeng.com/blog/atom.xml", "category": "开发者生态", "min_content_length": 50},
    "Hacker News": {"url": "https://hnrss.org/frontpage", "category": "开发者生态", "min_content_length": 50},
    "CSDN资讯": {"url": "https://plink.anyfeeder.com/weixin/CSDNnews", "category": "开发者生态", "min_content_length": 50},
    "InfoQ推荐": {"url": "https://plink.anyfeeder.com/infoq/recommend", "category": "开发者生态", "min_content_length": 50},
    "前端之巅": {"url": "https://plink.anyfeeder.com/weixin/frontshow", "category": "开发者生态", "min_content_length": 50},
    "SegmentFault": {"url": "https://segmentfault.com/rss/blog", "category": "开发者生态", "min_content_length": 50},
    
    # ============ 数码硬件 ============
    "中关村在线": {"url": "http://rss.zol.com.cn/", "category": "数码硬件", "min_content_length": 50},
    "Phoronix": {"url": "https://www.phoronix.com/rss.php", "category": "数码硬件", "min_content_length": 50},
    "超能网": {"url": "https://plink.anyfeeder.com/chuansongme", "category": "数码硬件", "min_content_length": 50},
    "快科技": {"url": "https://rss.mydrivers.com/Rss.aspx?Tid=1", "category": "数码硬件", "min_content_length": 50},
    
    # ============ 社会热点 ============
    "中新经纬": {"url": "https://www.chinanews.com.cn/rss/society.xml", "category": "社会热点", "min_content_length": 50},
    "观察者网": {"url": "https://www.guancha.cn/rss", "category": "社会热点", "min_content_length": 50},
    "新京报": {"url": "https://www.bjnews.com.cn/rss", "category": "社会热点", "min_content_length": 50},
    
    # ============ 汽车 ============
    "车云网": {"url": "https://www.cheyun.com/rss", "category": "汽车", "min_content_length": 50},
    "汽车之家": {"url": "https://www.autohome.com.cn/rss/news.xml", "category": "汽车", "min_content_length": 50},
    "新浪汽车": {"url": "https://auto.sina.com.cn/rss/jiaodian.xml", "category": "汽车", "min_content_length": 50},
    
    # ============ 游戏 ============
    "机核网": {"url": "https://www.gcores.com/rss", "category": "游戏", "min_content_length": 50},
    "Steam新闻": {"url": "https://store.steampowered.com/feeds/news.xml", "category": "游戏", "min_content_length": 50},
    "TapTap": {"url": "https://www.taptap.com/feed/rss", "category": "游戏", "min_content_length": 50},
    "IGN中国": {"url": "https://cn.ign.com/rss/news", "category": "游戏", "min_content_length": 50},
}

# 禁用关键词
FORBIDDEN_KEYWORDS = [
    "黄金", "金价", "金子", "金饰", "足金", "K金",
    "娱乐", "明星", "八卦", "绯闻", "综艺", "追星",
    "股市", "股票", "涨停", "跌停", "大盘", "K线",
    "彩票", "博彩", "赌博",
]

# 分类关键词（用于二次分类）
CATEGORY_KEYWORDS = {
    # 智能AI - 最高优先级
    "智能AI": [
        "AI", "人工智能", "大模型", "LLM", "GPT", "ChatGPT", "Claude", "DeepSeek",
        "Kimi", "豆包", "文心一言", "通义千问", "智谱", "百川",
        "机器学习", "深度学习", "神经网络", "Transformer", "Copilot", "Cursor",
        "Agent", "Stable Diffusion", "Midjourney", "Sora", "OpenAI", "Anthropic",
        "Embedding", "RAG", "Prompt", "Token", "Hugging Face", "Ollama"
    ],
    # 安全攻防
    "安全攻防": [
        "漏洞", "CVE", "黑客", "安全", "攻击", "渗透", "入侵", "泄露",
        "恶意软件", "病毒", "木马", "钓鱼", "勒索", "APT", "0day", "补丁",
        "CTF", "逆向", "取证", "SQL注入", "XSS", "CSRF", "DDOS"
    ],
    # 游戏
    "游戏": [
        "游戏", "Steam", "PS5", "Switch", "Xbox", "巫师", "GTA", "塞尔达",
        "任天堂", "暴雪", "Epic", "博德之门", "战神", "原神", "宝可梦",
        "马里奥", "最终幻想", "黑神话", "使命召唤", "守望先锋", "魔兽世界",
        "吃鸡", "英雄联盟", "LOL", "Dota", "SteamDeck", "育碧", "DLSS", "玩家"
    ],
    # 汽车
    "汽车": [
        "汽车", "电动车", "新能源", "智驾", "自动驾驶", "车企",
        "比亚迪", "特斯拉", "蔚来", "理想", "小鹏", "吉利", "长安",
        "座椅", "续航", "充电", "电池", "辅助驾驶", "车祸", "Cybertruck", "召回"
    ],
    # 开发者生态
    "开发者生态": [
        "Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C++", "PHP",
        "编程", "开发", "API", "框架", "GitHub", "代码", "程序员",
        "Docker", "K8s", "Kubernetes", "DevOps", "CI/CD", "前端", "后端",
        "React", "Vue", "Angular", "Django", "Flask", "Spring", "数据库", "Redis"
    ],
    # 数码硬件
    "数码硬件": [
        "CPU", "GPU", "显卡", "英特尔", "AMD", "NVIDIA", "评测", "手机", "电脑",
        "笔记本", "显示器", "屏幕", "OLED", "LCD", "内存", "硬盘", "SSD",
        "Mac", "iPhone", "iPad", "MacBook", "大疆", "影石", "相机", "耳机"
    ],
    # 开源推荐
    "开源推荐": [
        "GitHub", "开源项目", "开源工具", "开源框架", "Repository", "Repo",
        "Trending", "Stars", "Firecrawl", "OpenCode", "ScreenBox", "Claude-Code",
        "Agency", "Hermes", "Skills"
    ],
    # 时政热点
    "时政热点": [
        "政治", "政府", "政策", "外交", "国际", "峰会", "联合国",
        "经济", "GDP", "财政", "央行", "汇率", "贸易战",
        "美国", "中国", "俄罗斯", "欧洲", "日本", "韩国",
        "欧盟", "北约", "中东", "乌克兰", "以色列", "制裁",
        "选举", "总统", "总理", "议会", "法律", "G20"
    ],
    # 社会热点
    "社会热点": [
        "社会", "民生", "就业", "房价", "工资", "社保", "医保",
        "教育", "学校", "高考", "健康", "医院", "疾病", "疫苗",
        "环境", "污染", "火灾", "灾害", "消费", "电商", "网红",
        "餐饮", "美食", "旅行", "旅游", "景区", "动物", "鸟类"
    ],
    # 科技头条
    "科技头条": [
        "科技", "互联网", "苹果", "谷歌", "微软", "腾讯", "阿里", "字节",
        "发布", "发布会", "融资", "上市", "IPO", "投资", "收购",
        "财报", "营收", "利润", "裁员", "招聘", "芯片", "半导体",
        "台积电", "代工", "5G", "云计算", "服务器", "量子计算",
        "无人机", "机器人", "SpaceX", "火箭", "卫星"
    ],
}

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def is_forbidden_content(title, content=""):
    text = (title + " " + content).lower()
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword.lower() in text:
            return True
    return False

def refine_category(title, content, default_category):
    """根据关键词二次分类 - 优先级从高到低"""
    text = (title + " " + content).lower()
    
    # 优先级顺序：游戏 > 汽车 > 社会热点 > 安全 > AI > 开源 > 时政 > 开发者 > 硬件 > 科技头条
    priority_order = [
        "游戏", "汽车", "社会热点", "安全攻防", "智能AI", "开源推荐",
        "时政热点", "开发者生态", "数码硬件", "科技头条"
    ]
    
    for cat in priority_order:
        if cat == default_category:
            continue
        keywords = CATEGORY_KEYWORDS.get(cat, [])
        for kw in keywords:
            if kw.lower() in text:
                return cat
    
    return default_category

def fetch_rss_source(source_name, config):
    articles = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(config['url'], headers=headers, timeout=15)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        logger.info("从 %s 获取到 %d 条条目", source_name, len(feed.entries))
        
        for entry in feed.entries[:8]:
            try:
                title = entry.get('title', '').strip()
                if not title or len(title) < 5:
                    continue
                
                title = clean_html(title)
                
                original_url = entry.get('link', '') or ''
                
                # 优先从RSS获取摘要内容
                raw_content = ''
                if 'summary' in entry:
                    raw_content = entry.get('summary', '')
                elif 'description' in entry:
                    raw_content = entry.get('description', '')
                
                content_html, content_text = extract_content_with_images(raw_content, original_url)
                
                # 对于HN或内容太短的RSS，尝试抓取原始URL的正文
                need_fetch_article = 'hnrss.org' in config['url'] or len(content_text) < config['min_content_length']
                
                if need_fetch_article and original_url and not original_url.startswith('javascript:'):
                    if 'news.ycombinator.com' not in original_url:
                        time.sleep(1)
                        article_text, article_html = extract_article_content(original_url)
                        if len(article_text) > len(content_text):
                            content_text = article_text
                            content_html = article_html
                            logger.info("成功抓取原文: %s...", title[:30])
                        else:
                            if 'hnrss.org' in config['url']:
                                hn_guid = entry.get('guid', '')
                                if 'news.ycombinator.com/item?id=' in hn_guid:
                                    item_id = hn_guid.split('id=')[-1]
                                    comments_text = get_hn_comments_summary(item_id)
                                    if comments_text:
                                        content_text = '【HN用户评论摘要】\n\n' + comments_text + '\n\n原始链接: ' + original_url
                
                if len(content_text) < config['min_content_length']:
                    logger.info("内容太短跳过: %s... (长度:%d)", title[:30], len(content_text))
                    continue
                
                if is_forbidden_content(title, content_text):
                    continue
                
                category = config.get('category', '科技')
                if category in ['科技头条', '科技']:
                    category = refine_category(title, content_text, '科技头条')
                
                source = source_name
                if 'author' in entry and entry['author']:
                    source = entry['author']
                
                article_id = hashlib.md5(title.encode()).hexdigest()[:16]
                
                title_cn, content_cn = translate_article(title, content_text)
                
                time.sleep(1)
                
                articles.append({
                    'title': title[:200],
                    'title_cn': title_cn[:200] if title_cn else title[:200],
                    'content': content_text[:2000],
                    'content_html': content_html[:5000],
                    'content_cn': content_cn[:3000] if content_cn else content_text[:2000],
                    'category': category,
                    'source': source,
                    'url': original_url,
                    'paper_type': None,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'is_published': True,
                    '_id': article_id
                })
                
            except Exception as e:
                logger.warning("处理条目失败: %s", e)
                continue
        
    except Exception as e:
        logger.error("抓取 %s 失败: %s", source_name, e)
    
    return articles

def fetch_github_trending():
    articles = []
    
    try:
        url = "https://api.github.com/search/repositories?q=created:>2024-01-01&sort=stars&order=desc&per_page=8"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/vnd.github.v3+json'
        }
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            for repo in data.get('items', [])[:8]:
                title = "GitHub热门项目: %s" % repo['name']
                repo_url = repo.get('html_url', '')
                stars = repo.get('stargazers_count', 0)
                description = repo.get('description') or '暂无描述'
                owner = repo.get('owner', {}).get('login', 'unknown')
                
                content = """项目 %s 是近期热门的开源项目。

仓库地址：%s
Stars：%d
作者：%s
项目描述：%s""" % (repo['name'], repo_url, stars, owner, description)
                
                readme_content = ""
                try:
                    for branch in ['main', 'master']:
                        readme_url = "https://raw.githubusercontent.com/%s/%s/%s/README.md" % (owner, repo['name'], branch)
                        headers['User-Agent'] = 'Mozilla/5.0'
                        readme_resp = requests.get(readme_url, headers=headers, timeout=10)
                        if readme_resp.status_code == 200:
                            readme_content = readme_resp.text[:3000]
                            break
                except:
                    pass
                
                if readme_content:
                    content = """GitHub项目：%s
仓库地址：%s
Stars：%d | 作者：%s

项目描述：%s

%s
README 内容：
%s""" % (repo['name'], repo_url, stars, owner, description, "="*50, readme_content)
                
                if not is_forbidden_content(title, content):
                    title_cn = translate_to_chinese(title)
                    content_cn = translate_long_text(content)
                    
                    time.sleep(1.5)
                    
                    articles.append({
                        'title': title[:200],
                        'title_cn': title_cn[:200] if title_cn else title[:200],
                        'content': content[:3000],
                        'content_html': '',
                        'content_cn': content_cn[:3000] if content_cn else content[:3000],
                        'category': '开源推荐',
                        'source': 'GitHub Trending',
                        'url': repo_url,
                        'paper_type': None,
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'is_published': True,
                        '_id': hashlib.md5(title.encode()).hexdigest()[:16]
                    })
        
        if 'X-RateLimit-Remaining' in response.headers:
            remaining = response.headers.get('X-RateLimit-Remaining')
            logger.info("GitHub API剩余请求: %s", remaining)
            
    except Exception as e:
        logger.error("抓取GitHub Trending失败: %s", e)
    
    return articles

def translate_article(title, content):
    title_cn = translate_to_chinese(title) if is_english_text(title) else title
    content_cn = translate_long_text(content) if is_english_text(content) else content
    return title_cn, content_cn

def push_to_api(articles, paper_type="morning"):
    if not articles:
        logger.warning("没有文章需要推送")
        return 0
    
    success_count = 0
    
    for article in articles:
        article['paper_type'] = paper_type
        
        try:
            response = requests.post(
                API_URL,
                json=article,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                success_count += 1
                logger.info("推送成功: %s...", article['title'][:40])
            else:
                logger.warning("推送失败 [%d]: %s...", response.status_code, article['title'][:40])
                
        except requests.exceptions.ConnectionError:
            logger.error("无法连接到API服务")
        except Exception as e:
            logger.error("推送异常: %s", e)
        
        time.sleep(0.5)
    
    return success_count

def collect_all(paper_type="morning"):
    logger.info("=== 开始采集 [%s] ===", paper_type)
    
    all_articles = []
    seen_ids = set()
    
    logger.info("RSS源总数: %d", len(RSS_SOURCES))
    success_count = 0
    fail_count = 0
    
    for source_name, config in RSS_SOURCES.items():
        articles = fetch_rss_source(source_name, config)
        if articles:
            success_count += 1
        else:
            fail_count += 1
            
        for article in articles:
            if article['_id'] not in seen_ids:
                seen_ids.add(article['_id'])
                all_articles.append(article)
        time.sleep(0.5)
    
    logger.info("成功采集源: %d, 失败: %d", success_count, fail_count)
    
    logger.info("正在采集 GitHub Trending...")
    github_articles = fetch_github_trending()
    for article in github_articles:
        if article['_id'] not in seen_ids:
            seen_ids.add(article['_id'])
            all_articles.append(article)
    
    logger.info("共采集到 %d 篇去重文章", len(all_articles))
    
    category_stats = defaultdict(int)
    for article in all_articles:
        category_stats[article['category']] += 1
    
    logger.info("各栏目文章数:")
    for cat, count in sorted(category_stats.items(), key=lambda x: -x[1]):
        logger.info("  - %s: %d篇", cat, count)
    
    push_count = push_to_api(all_articles, paper_type)
    
    logger.info("=== 采集完成，成功推送 %d 篇 ===", push_count)
    return push_count

def main():
    import sys
    
    paper_type = "morning"
    if len(sys.argv) > 1:
        if sys.argv[1] == "evening":
            paper_type = "evening"
        elif sys.argv[1] == "morning":
            paper_type = "morning"
        else:
            hour = datetime.now().hour
            paper_type = "evening" if hour >= 12 else "morning"
    
    logger.info("新闻采集脚本启动 - 类型: %s", paper_type)
    
    try:
        success = collect_all(paper_type)
        sys.exit(0 if success > 0 else 1)
    except Exception as e:
        logger.error("采集过程异常: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
