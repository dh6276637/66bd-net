# 66必读 (66bd-net) Code Wiki

## 文档信息

| 项目名称 | 66必读 |
|---------|--------|
| 仓库地址 | https://github.com/dh6276637/66bd-net |
| 文档版本 | v1.0 |
| 更新日期 | 2026-05-15 |

---

## 一、项目概述

### 1.1 项目简介

**66必读**是一个简洁、高效、无干扰的科技资讯阅读平台，主要功能包括：

- 聚合多个科技资讯源（36氪、钛媒体、少数派、IT之家等）
- 中英双语文章展示
- 简洁无广告的阅读体验
- 自动定时更新内容
- 用户系统（注册、登录、收藏）
- 留言板功能
- 报纸栏目（按日期归档）
- RSS订阅支持

### 1.2 核心特性

- **内容聚合**: 通过RSS采集来自多个源的文章
- **自动分类**: 基于关键词的内容自动分类系统
- **双语翻译**: 英文文章自动翻译为中文
- **用户互动**: 收藏文章、留言反馈
- **数据看板**: 实时统计PV/UV/在线人数

---

## 二、技术架构

### 2.1 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | Python Flask | Web应用框架 |
| WSGI服务器 | Gunicorn + gevent | 生产环境部署 |
| 数据库 | MySQL | 主数据存储 |
| 前端 | HTML/CSS/JavaScript | 响应式设计 |
| 内容采集 | feedparser + BeautifulSoup | RSS解析、网页抓取 |
| 翻译服务 | Google Translate API | 中英互译 |
| 负载均衡 | Nginx | 反向代理 |

### 2.2 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         客户端层                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐   │
│  │  PC浏览器 │  │  移动端   │  │ RSS阅读器 │  │  第三方订阅服务  │   │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────────┬────────┘   │
└───────┼─────────────┼───────────┼────────────────┼─────────────┘
        │             │           │                │
        └─────────────┴───────────┴────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Nginx层 (反向代理)                        │
│                    端口: 80/443 (HTTP/HTTPS)                      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Gunicorn + gevent层                          │
│                      端口: 127.0.0.1:5000                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      Flask应用                            │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │   │
│  │  │ 前台页面 │ │ 后台管理 │ │ REST API │ │ 用户系统 │        │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    MySQL      │    │  cron_collect   │    │     静态资源     │
│    数据库      │    │   内容采集脚本   │    │  /static/       │
└───────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │        RSS源 (35+个)           │
              │  36kr/钛媒体/少数派/HackerNews │
              │  GitHub/安全客/FreeBuf/...     │
              └───────────────────────────────┘
```

---

## 三、目录结构

```
66bd-net/
├── app.py                      # Flask主应用 (核心文件)
├── cron_collect.py              # 内容采集脚本
├── add_functions.py             # 服务器端函数追加脚本
├── gunicorn_config.py           # Gunicorn配置
├── batch_translate*.py          # 批量翻译脚本
├── clean_*.py                   # 数据清理脚本
├── fix_*.py                     # 数据修复脚本
├── translate_*.py               # 翻译脚本
├── update_urls.py               # URL更新脚本
├── patch_seo.py                 # SEO优化脚本
│
├── backup/                      # 备份文件
│   ├── crontab.txt             # 定时任务配置
│   ├── nginx.conf              # Nginx配置备份
│   └── services.txt            # 服务配置
│
├── static/                      # 静态资源
│   ├── css/
│   │   ├── wired-style.css     # 主样式文件
│   │   └── admin.css           # 后台管理样式
│   ├── og-default.*            # Open Graph默认图片
│   ├── robots.txt              # 爬虫协议
│   └── sitemap.xml             # 网站地图
│
├── templates/                   # Jinja2模板
│   ├── base.html               # 基础模板
│   ├── index.html              # 首页
│   ├── category.html           # 分类页
│   ├── article_detail.html     # 文章详情页
│   ├── newspaper_*.html        # 报纸相关页面
│   ├── messages.html           # 留言板
│   ├── about.html              # 关于页面
│   ├── user_*.html             # 用户相关页面
│   │
│   └── admin/                  # 后台管理模板
│       ├── dashboard.html      # 数据看板
│       ├── articles.html       # 文章管理
│       ├── cats.html           # 分类管理
│       ├── users.html          # 用户管理
│       ├── action_log.html     # 操作日志
│       ├── log.html            # 采集日志
│       ├── monitor.html        # 服务器监控
│       ├── settings.html       # 站点设置
│       ├── edit.html           # 文章编辑
│       └── login.html          # 登录页
│
├── DEPLOYMENT_REPORT.md        # 部署报告
└── README.md                   # 项目说明
```

---

## 四、核心模块详解

### 4.1 app.py - Flask主应用

#### 4.1.1 配置常量

| 常量名 | 类型 | 说明 |
|--------|------|------|
| `DB_CONFIG` | dict | MySQL数据库连接配置 |
| `CATEGORY_MAP` | dict | URL别名到分类名称的映射 |
| `ALL_CATEGORIES` | list | 所有分类列表 |
| `MESSAGE_BLACKLIST` | list | 留言黑名单关键词 |
| `SOURCE_CONFIG` | dict | 来源样式配置(图标/颜色) |

#### 4.1.2 核心函数

##### `get_db()`

```python
def get_db() -> MySQLdb.connection
```

**功能**: 获取数据库连接

**返回值**: MySQLdb连接对象

**使用示例**:
```python
conn = get_db()
cur = conn.cursor(DictCursor)
cur.execute("SELECT * FROM article LIMIT 10")
```

---

##### `log_admin_action(action, target='', detail=None, user_id='', username='')`

**功能**: 记录后台操作日志

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `action` | str | 操作类型(article_add/edit/delete等) |
| `target` | str | 操作对象 |
| `detail` | dict | 详细信息 |
| `user_id` | str | 用户ID |
| `username` | str | 用户名 |

---

##### `login_required(f)`

**功能**: 装饰器，验证后台登录状态

**使用示例**:
```python
@app.route('/admin/articles')
@login_required
def admin_articles():
    ...
```

---

##### `api_response(data=None, message='success', code=200)`

**功能**: 统一API响应格式

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `data` | any | 响应数据 |
| `message` | str | 提示消息 |
| `code` | int | HTTP状态码 |

**返回值**: Flask Response对象(JSON)

---

##### `check_message_blacklist(content, nickname='')`

**功能**: 检查留言是否包含黑名单关键词

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `content` | str | 留言内容 |
| `nickname` | str | 昵称 |

**返回值**: (bool, str|None) - (是否违规, 违规关键词)

---

##### `text_to_html(text)`

**功能**: 将纯文本转换为安全的HTML格式

**处理逻辑**:
1. HTML转义特殊字符
2. 识别GitHub项目信息(Stars/Forks/许可证)
3. 自动将URL转换为可点击链接
4. 段落换行处理

---

##### `get_source_style(source)`

**功能**: 根据来源名称获取样式配置

**返回值**: dict - {icon, color}

---

##### `generate_csrf_token()` / `validate_csrf_token()`

**功能**: CSRF令牌生成与验证

---

##### `is_login_locked(ip)` / `record_login_fail(ip)` / `reset_login_fail(ip)`

**功能**: 登录暴力破解防护
- 同一IP失败5次后锁定15分钟

---

### 4.2 前台页面路由

| 路由 | 函数 | 说明 |
|------|------|------|
| `/` | `index()` | 首页，展示文章列表 |
| `/category/<slug>` | `category_page(slug)` | 分类页面 |
| `/article/<int:id>` | `article_detail(id)` | 文章详情 |
| `/newspaper` | `newspaper_list()` | 报纸列表(按日期) |
| `/newspaper/<date>` | `newspaper_date(date)` | 单日报纸 |
| `/paper` | `paper()` | 重定向到报纸列表 |
| `/about` | `about()` | 关于页面 |
| `/messages` | `messages_page()` | 留言板 |

### 4.3 REST API路由

#### 用户认证API

| 路由 | 方法 | 函数 | 说明 |
|------|------|------|------|
| `/api/auth/register` | GET/POST | `api_register()` | 用户注册 |
| `/api/auth/login` | GET/POST | `api_login()` | 用户登录 |
| `/api/auth/logout` | GET/POST | `api_logout()` | 用户登出 |
| `/api/auth/me` | GET | `api_me()` | 获取当前用户信息 |

#### 文章API

| 路由 | 方法 | 函数 | 说明 |
|------|------|------|------|
| `/api/v1/articles` | GET | `api_v1_articles()` | 获取文章列表 |
| `/api/v1/articles` | POST | `api_v1_articles()` | 添加文章(采集脚本用) |
| `/api/v1/articles/<int:id>` | GET | `api_v1_article()` | 获取单篇文章 |
| `/api/v1/categories` | GET | `api_v1_categories()` | 获取分类统计 |
| `/api/v1/newspaper` | GET | `api_v1_newspaper()` | 获取报纸日期列表 |
| `/api/v1/newspaper/<date>` | GET | `api_v1_newspaper_date()` | 获取单日报纸 |
| `/api/v1/search` | GET | `api_v1_search()` | 搜索文章 |

#### 用户功能API

| 路由 | 方法 | 函数 | 说明 |
|------|------|------|------|
| `/api/favorites/toggle` | GET/POST | `api_favorites_toggle()` | 切换收藏状态 |
| `/api/messages` | GET/POST | `api_messages()` | 留言板 |
| `/api/feedback` | GET/POST | `submit_feedback()` | 提交反馈 |
| `/api/track` | GET/POST | `track_page_view()` | 页面访问追踪 |

#### 数据统计API

| 路由 | 方法 | 函数 | 说明 |
|------|------|------|------|
| `/api/stats/realtime` | GET | `api_stats_realtime()` | 实时统计数据 |

#### 服务器监控API

| 路由 | 方法 | 函数 | 说明 |
|------|------|------|------|
| `/api/server/stats` | GET | `server_stats()` | 服务器状态(需登录) |

### 4.4 后台管理路由

| 路由 | 函数 | 权限 | 说明 |
|------|------|------|------|
| `/admin/login` | `admin_login()` | 公开 | 管理员登录 |
| `/admin/logout` | `admin_logout()` | 登录 | 管理员登出 |
| `/admin/` | `admin_dashboard()` | 登录 | 数据看板 |
| `/admin/articles` | `admin_articles()` | 登录 | 文章列表 |
| `/admin/articles/new` | `admin_new_article()` | 登录 | 新建文章 |
| `/admin/articles/<id>/edit` | `admin_edit_article()` | 登录 | 编辑文章 |
| `/admin/articles/<id>/delete` | `admin_delete_article()` | 登录 | 删除文章 |
| `/admin/categories` | `admin_categories()` | 登录 | 分类管理 |
| `/admin/users` | `admin_users()` | 登录 | 用户管理 |
| `/admin/users/<id>/toggle-status` | `admin_toggle_user_status()` | 登录 | 切换用户状态 |
| `/admin/users/<id>/delete` | `admin_delete_user()` | 登录 | 删除用户 |
| `/admin/action-log` | `admin_action_log()` | 登录 | 操作日志 |
| `/admin/cron-log` | `admin_cron_log()` | 登录 | 采集日志 |
| `/admin/cron/trigger` | `admin_trigger_cron()` | 登录 | 手动触发采集 |
| `/admin/settings` | `admin_settings()` | 登录 | 站点设置 |
| `/admin/monitor` | `admin_monitor()` | 登录 | 服务器监控页面 |

### 4.5 其他路由

| 路由 | 函数 | 说明 |
|------|------|------|
| `/rss.xml` | `rss_feed()` | RSS订阅源 |
| `/sitemap.xml` | `sitemap()` | 网站地图 |
| `/robots.txt` | `robots()` | 爬虫协议 |

---

## 五、cron_collect.py - 内容采集脚本

### 5.1 核心函数

#### `extract_article_content(url, timeout=15)`

**功能**: 从URL抓取文章正文内容

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | str | - | 文章URL |
| `timeout` | int | 15 | 超时秒数 |

**返回值**: (text, html) - 纯文本和HTML格式

**提取策略**:
1. 优先查找`<article>`标签
2. 其次查找`<main>`标签
3. 查找内容最丰富的`<div>`或`<section>`
4. 最后使用`<body>`内容

---

#### `get_hn_comments_summary(hn_item_id, timeout=10)`

**功能**: 获取Hacker News帖子的评论摘要

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `hn_item_id` | str | - | HN帖子ID |
| `timeout` | int | 10 | 超时秒数 |

**返回值**: str - 前5条评论的合并文本

---

#### `translate_to_chinese(text, max_retries=3)`

**功能**: 使用Google Translate API翻译文本

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `text` | str | - | 待翻译文本(最多5000字符) |
| `max_retries` | int | 3 | 最大重试次数 |

**返回值**: str - 翻译后的中文文本

---

#### `translate_long_text(text, chunk_size=1800)`

**功能**: 翻译长文本(自动分段)

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `text` | str | - | 长文本 |
| `chunk_size` | int | 1800 | 每段最大字符数 |

**分段策略**:
- 按段落`\n\n`分割
- 每段翻译间隔1.2秒(避免API限流)

---

#### `fetch_rss_source(source_name, config)`

**功能**: 从单个RSS源抓取文章

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `source_name` | str | 来源名称 |
| `config` | dict | 配置{url, category, min_content_length} |

**处理流程**:
1. 请求RSS feed
2. 解析条目(最多8条)
3. 提取正文内容
4. 过滤禁用内容
5. 关键词二次分类
6. 中英双语翻译
7. 去重(MD5哈希)
8. 返回文章列表

---

#### `fetch_github_trending()`

**功能**: 抓取GitHub Trending项目

**数据来源**: GitHub REST API v3

**返回字段**:
- 项目名称、描述
- Stars数量
- 作者
- README内容

---

#### `is_forbidden_content(title, content="")`

**功能**: 检查内容是否包含禁用关键词

**禁用类别**:
- 黄金/金价相关
- 娱乐八卦
- 股市财经
- 博彩彩票

---

#### `refine_category(title, content, default_category)`

**功能**: 根据关键词二次分类

**优先级顺序**:
```
游戏 > 汽车 > 社会热点 > 安全攻防 > 智能AI > 开源推荐 
> 时政热点 > 开发者生态 > 数码硬件 > 科技头条
```

**关键词映射表(CATEGORY_KEYWORDS)**:
```python
CATEGORY_KEYWORDS = {
    "智能AI": ["AI", "人工智能", "大模型", "LLM", "GPT", ...],
    "安全攻防": ["漏洞", "CVE", "黑客", "安全", ...],
    "游戏": ["游戏", "Steam", "PS5", "Switch", ...],
    "汽车": ["汽车", "电动车", "新能源", "智驾", ...],
    # ... 更多分类
}
```

---

#### `collect_all(paper_type="morning")`

**功能**: 执行全量采集

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `paper_type` | str | "morning" | 采集类型(morning/evening) |

**流程**:
1. 遍历所有RSS源
2. 抓取GitHub Trending
3. 去重合并
4. 统计分类分布
5. 推送到API

---

### 5.2 RSS数据源配置

项目配置了35+个RSS源，覆盖以下分类：

| 分类 | 来源数量 | 示例来源 |
|------|---------|---------|
| 智能AI | 7 | 量子位、新智元、OpenAI博客、MIT AI |
| 安全攻防 | 7 | FreeBuf、先知社区、嘶吼、The Hacker News |
| 时政热点 | 5 | 央视新闻、中国日报、BBC中文 |
| 科技头条 | 9 | 36kr、钛媒体、少数派、IT之家 |
| 开发者生态 | 6 | 阮一峰博客、Hacker News、CSDN |
| 数码硬件 | 4 | 中关村在线、Phoronix |
| 社会热点 | 3 | 中新经纬、观察者网、新京报 |
| 汽车 | 3 | 车云网、汽车之家、新浪汽车 |
| 游戏 | 4 | 机核网、Steam新闻、TapTap |

---

## 六、数据库结构

### 6.1 核心数据表

#### `article` - 文章表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | INT AUTO_INCREMENT | 主键 |
| `title` | VARCHAR(200) | 英文标题 |
| `title_cn` | VARCHAR(200) | 中文标题 |
| `content` | TEXT | 英文正文 |
| `content_cn` | TEXT | 中文正文 |
| `content_html` | TEXT | HTML格式正文 |
| `category` | VARCHAR(50) | 分类 |
| `source` | VARCHAR(200) | 来源 |
| `url` | VARCHAR(500) | 原文链接 |
| `paper_type` | VARCHAR(20) | 报纸类型(morning/evening) |
| `publish_date` | DATE | 发布日期 |
| `is_published` | TINYINT | 是否发布(0/1) |
| `view_count` | INT | 阅读数 |
| `created_at` | DATETIME | 创建时间 |

#### `users` - 用户表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | INT AUTO_INCREMENT | 主键 |
| `username` | VARCHAR(50) | 用户名 |
| `email` | VARCHAR(120) | 邮箱 |
| `password_hash` | VARCHAR(255) | 密码哈希 |
| `avatar` | VARCHAR(255) | 头像URL |
| `created_at` | DATETIME | 注册时间 |
| `last_login` | DATETIME | 最后登录 |
| `is_active` | TINYINT | 是否启用 |

#### `admin` - 管理员表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | INT AUTO_INCREMENT | 主键 |
| `username` | VARCHAR(50) | 用户名 |
| `password` | VARCHAR(255) | 密码(werkzeug哈希) |

#### `favorites` - 收藏表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | INT AUTO_INCREMENT | 主键 |
| `user_id` | INT | 用户ID |
| `article_id` | INT | 文章ID |
| `created_at` | DATETIME | 收藏时间 |

#### `messages` - 留言表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | INT AUTO_INCREMENT | 主键 |
| `nickname` | VARCHAR(50) | 昵称 |
| `content` | TEXT | 留言内容 |
| `ip` | VARCHAR(50) | IP地址 |
| `is_approved` | TINYINT | 是否审核 |
| `created_at` | DATETIME | 发布时间 |

#### `admin_log` - 操作日志表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | INT AUTO_INCREMENT | 主键 |
| `user_id` | VARCHAR(50) | 操作用户ID |
| `username` | VARCHAR(50) | 操作用户名 |
| `action` | VARCHAR(50) | 操作类型 |
| `target` | VARCHAR(200) | 操作对象 |
| `detail` | TEXT | 详细信息(JSON) |
| `ip` | VARCHAR(50) | IP地址 |
| `user_agent` | VARCHAR(500) | User-Agent |
| `created_at` | DATETIME | 操作时间 |

#### `categories` - 分类表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | INT AUTO_INCREMENT | 主键 |
| `name` | VARCHAR(50) | 分类名称 |
| `slug` | VARCHAR(50) | URL别名 |

#### `settings` - 站点设置表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | INT AUTO_INCREMENT | 主键 |
| `setting_key` | VARCHAR(50) | 设置键 |
| `setting_value` | TEXT | 设置值 |

#### `page_view` - 页面访问表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | INT AUTO_INCREMENT | 主键 |
| `path` | VARCHAR(255) | 页面路径 |
| `ip` | VARCHAR(50) | IP地址 |
| `user_agent` | VARCHAR(500) | User-Agent |
| `session_id` | VARCHAR(100) | 会话ID |
| `created_at` | DATETIME | 访问时间 |

#### `daily_stats` - 每日统计表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `date` | DATE | 日期 |
| `pv` | INT | 页面浏览量 |
| `uv` | INT | 独立访客 |
| `avg_dwell_time` | FLOAT | 平均停留时间(秒) |

---

## 七、依赖关系

### 7.1 Python依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| Flask | 2.0.3 | Web框架 |
| MySQLdb | - | MySQL驱动 |
| feedparser | 6.0.12 | RSS解析 |
| requests | 2.27.1 | HTTP请求 |
| beautifulsoup4 | 4.12.3 | HTML解析 |
| lxml | 5.4.0 | XML/HTML处理 |
| gunicorn | 21.2.0 | WSGI服务器 |
| werkzeug | - | 安全工具(password hash) |
| psutil | - | 系统监控(可选) |

### 7.2 外部服务依赖

| 服务 | 用途 | 调用方式 |
|------|------|---------|
| Google Translate API | 中英翻译 | 公共API |
| Hacker News API | HN评论获取 | Firebase API |
| GitHub API v3 | GitHub Trending | REST API |
| 35+ RSS源 | 内容采集 | HTTP请求 |

### 7.3 系统依赖

| 组件 | 版本 | 用途 |
|------|------|------|
| Python | 3.6.8+ | 运行时 |
| MySQL | 5.7+ | 数据库 |
| Nginx | - | 反向代理 |
| Linux | - | 操作系统 |

---

## 八、项目运行

### 8.1 开发环境

```bash
# 克隆项目
git clone https://github.com/dh6276637/66bd-net.git
cd 66bd-net

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export DB_HOST=localhost
export DB_USER=paper_user
export DB_PASSWORD=paper_db2026
export DB_NAME=dongshushu_paper
export SECRET_KEY=your-secret-key

# 运行Flask开发服务器
python app.py
```

### 8.2 生产环境

#### Gunicorn启动

```bash
gunicorn -c gunicorn_config.py app:app
```

**gunicorn_config.py配置**:
```python
bind = "127.0.0.1:5000"     # 监听地址
workers = 4                  # 工作进程数
worker_class = "gevent"      # 异步工作模式
timeout = 120                 # 请求超时
max_requests = 1000          # 最大请求数后重启
```

#### Nginx配置示例

```nginx
server {
    listen 80;
    server_name www.66bd.net;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /var/www/dongshushu-paper/static/;
        expires 30d;
    }
}
```

### 8.3 定时任务配置

```bash
# 编辑crontab
crontab -e

# 添加以下任务
# 早报采集 - 每天06:30
30 6 * * * cd /var/www/dongshushu-paper && python3 cron_collect.py morning

# 晚报采集 - 每天19:30
30 19 * * * cd /var/www/dongshushu-paper && python3 cron_collect.py evening

# 证书续期
0 3 * * * /usr/bin/certbot renew --quiet --post-hook "/usr/bin/systemctl reload nginx"
```

### 8.4 手动触发采集

```bash
# 采集早报
python3 cron_collect.py morning

# 采集晚报
python3 cron_collect.py evening

# 后台触发(通过API)
curl -X POST http://127.0.0.1:5000/admin/cron/trigger
```

### 8.5 常用管理命令

```bash
# 查看采集日志
tail -f /var/www/dongshushu-paper/cron_collect.log

# 重启Gunicorn
systemctl restart gunicorn

# 重启Nginx
systemctl restart nginx

# 查看Python进程
ps aux | grep python

# 数据库备份
mysqldump -u paper_user -p dongshushu_paper > backup.sql
```

---

## 九、安全特性

### 9.1 CSRF保护

- 所有POST请求验证CSRF令牌
- 令牌存储在session中
- 登录页面GET请求时刷新令牌

### 9.2 登录防护

- 登录失败5次后锁定15分钟
- 使用werkzeug安全密码哈希
- 操作日志完整记录

### 9.3 反爬虫

- 检测并屏蔽常见爬虫User-Agent
- 页面访问追踪统计

### 9.4 内容过滤

- 留言板黑名单关键词过滤
- 采集内容禁用词过滤

### 9.5 XSS防护

- HTML特殊字符自动转义
- URL白名单检查(http/https)

---

## 十、扩展脚本

| 脚本名 | 功能 |
|--------|------|
| `batch_translate*.py` | 批量翻译文章 |
| `clean_dup.py` | 清理重复文章 |
| `clean_urls.py` | 清理无效URL |
| `fix_complete.py` | 修复文章完整性 |
| `fix_titles.py` | 修复文章标题 |
| `patch_seo.py` | SEO优化 |
| `add_functions.py` | 服务器端函数追加 |
| `update_urls.py` | 批量更新URL |

---

## 十一、常见问题

### Q1: 采集脚本执行失败怎么办？

1. 检查网络连接
2. 确认RSS源可访问
3. 查看日志: `tail -f /var/www/dongshushu-paper/cron_collect.log`
4. 确认Flask API服务运行中

### Q2: 如何添加新的RSS源？

编辑`cron_collect.py`，在`RSS_SOURCES`字典中添加：
```python
"新来源": {
    "url": "https://example.com/feed",
    "category": "科技头条",
    "min_content_length": 50
}
```

### Q3: 如何修改分类关键词？

编辑`cron_collect.py`中的`CATEGORY_KEYWORDS`字典，按优先级添加关键词。

### Q4: 数据库连接失败？

1. 检查MySQL服务状态
2. 验证`DB_CONFIG`配置
3. 确认用户权限

---

## 附录

### A. URL路由速查表

| 页面 | URL |
|------|-----|
| 首页 | / |
| 分类页 | /category/keji-toutiao |
| 文章详情 | /article/123 |
| 报纸列表 | /newspaper |
| 单日报纸 | /newspaper/2026-05-15 |
| 留言板 | /messages |
| 关于 | /about |
| RSS订阅 | /rss.xml |
| 后台登录 | /admin/login |
| 后台管理 | /admin/ |

### B. API响应格式

**成功响应**:
```json
{
    "code": 200,
    "message": "success",
    "data": { ... }
}
```

**错误响应**:
```json
{
    "code": 400,
    "message": "错误描述",
    "data": null
}
```

### C. 环境变量参考

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DB_HOST` | localhost | 数据库主机 |
| `DB_USER` | paper_user | 数据库用户 |
| `DB_PASSWORD` | paper_db2026 | 数据库密码 |
| `DB_NAME` | dongshushu_paper | 数据库名 |
| `SECRET_KEY` | (随机生成) | Flask密钥 |
