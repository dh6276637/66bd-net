#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复文章分类错误"""

import MySQLdb
import re

DB_CONFIG = {
    "host": "localhost",
    "user": "paper_user",
    "passwd": "paper_db2026",
    "db": "dongshushu_paper",
    "charset": "utf8mb4"
}

# 扩展后的分类关键词 - 新增医疗健康分类
CATEGORY_KEYWORDS_EXTENDED = {
    # 医疗健康 - 新增分类
    "医疗健康": [
        "医疗", "健康", "医院", "医生", "药品", "药物", "疫苗", "疾病",
        "癌症", "肿瘤", "手术", "治疗", "诊断", "体检", "问诊", "挂号",
        "红霉素", "软膏", "药膏", "抗生素", "药店", "药店", "中医", "西医",
        "症状", "发烧", "感冒", "咳嗽", "皮肤", "过敏", "疫苗", "核酸",
        "血压", "血糖", "血脂", "减肥", "营养", "食疗", "保健", "养生"
    ],
    # 智能AI
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
    # 汽车 - 扩展关键词
    "汽车": [
        "汽车", "电动车", "新能源", "智驾", "自动驾驶", "车企",
        "比亚迪", "特斯拉", "蔚来", "理想", "小鹏", "吉利", "长安",
        "座椅", "续航", "充电", "电池", "辅助驾驶", "车祸", "Cybertruck", "召回",
        "小米汽车", "SU7", "YU7", "GT", "SUV", "轿车", "跑车", "MPV",
        "实车", "到店", "发布", "试驾", "预售", "上市", "发布会",
        "汽油", "燃油", "油价", "柴油", "机油", "加油站", "加油",
        "发动机", "变速箱", "底盘", "轮毂", "轮胎", "刹车", "车灯",
        "保时捷", "奔驰", "宝马", "奥迪", "路虎", "捷豹", "超跑", "豪华车"
    ],
    # 数码硬件 - 更精确的关键词
    "数码硬件": [
        "CPU", "GPU", "显卡", "英特尔", "AMD", "NVIDIA", "评测", "手机", "电脑",
        "笔记本", "显示器", "屏幕", "OLED", "LCD", "内存", "硬盘", "SSD",
        "Mac", "iPhone", "iPad", "MacBook", "大疆", "影石", "相机", "耳机",
        "鼠标", "键盘", "外设", "路由器", "音响", "音箱", "麦克风",
        "摄像头", "平板", "智能手表", "手环", "充电器", "数据线", "充电宝",
        "英菲克", "罗技", "雷蛇", "樱桃", "机械键盘", "无线充电", "震动反馈"
    ],
    # 开发者生态
    "开发者生态": [
        "Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C++", "PHP",
        "编程", "开发", "API", "框架", "GitHub", "代码", "程序员",
        "Docker", "K8s", "Kubernetes", "DevOps", "CI/CD", "前端", "后端",
        "React", "Vue", "Angular", "Django", "Flask", "Spring", "数据库", "Redis"
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
    # 社会热点 - 扩展关键词
    "社会热点": [
        "社会", "民生", "就业", "房价", "工资", "社保", "医保",
        "教育", "学校", "高考", "环境", "污染", "火灾", "灾害",
        "消费", "电商", "网红", "餐饮", "美食", "旅行", "旅游", "景区",
        "电动车", "电动自行车", "限速", "外卖", "骑手", "交通", "新规",
        "新闻", "热点", "热议", "讨论", "事件", "调查", "曝光", "整治"
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

# 优先级顺序：医疗健康 > 游戏 > 汽车 > 数码硬件 > 社会热点 > 安全 > AI > 开源 > 时政 > 开发者 > 科技头条
PRIORITY_ORDER = [
    "医疗健康", "游戏", "汽车", "数码硬件", "社会热点", 
    "安全攻防", "智能AI", "开源推荐", "时政热点", "开发者生态", "科技头条"
]

def get_db():
    return MySQLdb.connect(**DB_CONFIG)

def classify_article(title, content, current_category):
    """根据标题和内容重新分类文章"""
    text = (title + " " + content).lower()
    
    for cat in PRIORITY_ORDER:
        if cat == current_category:
            continue
        keywords = CATEGORY_KEYWORDS_EXTENDED.get(cat, [])
        for kw in keywords:
            if kw.lower() in text:
                return cat
    
    return current_category

def fix_all_categories():
    """修复所有文章的分类"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT id, title, content, category FROM article WHERE is_published=1")
        articles = cur.fetchall()
        
        print(f"共找到 {len(articles)} 篇已发布文章")
        
        changes = []
        for article in articles:
            article_id, title, content, current_category = article
            content = content or ''
            
            new_category = classify_article(title, content, current_category)
            
            if new_category != current_category:
                changes.append({
                    'id': article_id,
                    'title': title[:50] + '...' if len(title) > 50 else title,
                    'old': current_category,
                    'new': new_category
                })
        
        print(f"\n需要修改 {len(changes)} 篇文章的分类：")
        for change in changes[:20]:
            print(f"  [{change['id']}] {change['title']}")
            print(f"      旧分类: {change['old']} -> 新分类: {change['new']}")
        
        if len(changes) > 20:
            print(f"  ... 还有 {len(changes) - 20} 条未显示")
        
        if changes:
            confirm = input("\n确认要修改这些分类吗? (y/n): ")
            if confirm.lower() == 'y':
                for change in changes:
                    cur.execute(
                        "UPDATE article SET category=%s WHERE id=%s",
                        (change['new'], change['id'])
                    )
                conn.commit()
                print(f"\n已成功修改 {len(changes)} 篇文章的分类")
            else:
                print("取消修改")
        else:
            print("\n没有需要修改的文章")
        
    finally:
        cur.close()
        conn.close()

def show_wrong_categories():
    """显示明显分类错误的文章"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # 查询明显错误的分类
        wrong_categories = []
        
        # 数码硬件分类中的非数码文章
        cur.execute("SELECT id, title, category FROM article WHERE category='数码硬件' AND is_published=1")
        for article in cur.fetchall():
            article_id, title, category = article
            text = title.lower()
            if any(kw in text for kw in ['医疗', '健康', '药品', '汽车', '汽油', '燃油', '自行车']):
                wrong_categories.append({'id': article_id, 'title': title, 'current': category, 'suggested': '需要重新分类'})
        
        # 汽车分类中的非汽车文章
        cur.execute("SELECT id, title, category FROM article WHERE category='汽车' AND is_published=1")
        for article in cur.fetchall():
            article_id, title, category = article
            text = title.lower()
            if any(kw in text for kw in ['鼠标', '键盘', '耳机', '电脑', '手机']):
                wrong_categories.append({'id': article_id, 'title': title, 'current': category, 'suggested': '数码硬件'})
        
        print("明显分类错误的文章:")
        for item in wrong_categories:
            print(f"  [{item['id']}] {item['title']}")
            print(f"      当前分类: {item['current']} -> 建议分类: {item['suggested']}")
    
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("=== 文章分类修复工具 ===")
    print("1. 显示明显分类错误")
    print("2. 自动修复所有分类")
    
    choice = input("请选择操作 (1/2): ")
    
    if choice == '1':
        show_wrong_categories()
    elif choice == '2':
        fix_all_categories()
    else:
        print("无效选择")