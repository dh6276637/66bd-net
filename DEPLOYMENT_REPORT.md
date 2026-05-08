# 董蜀黍的报纸 - 新闻采集系统配置文档

## 部署信息

**服务器**: 103.155.123.107
**应用目录**: /var/www/dongshushu-paper/
**Python版本**: 3.6.8
**API地址**: http://127.0.0.1:5000/api/articles

---

## 已部署文件

### 1. 采集脚本
- **路径**: `/var/www/dongshushu-paper/cron_collect.py`
- **功能**: 从RSS源采集新闻，推送到本地Flask API
- **权限**: 755 (可执行)

### 2. Crontab定时任务
- **早报**: 每天 06:30 执行 `python3 cron_collect.py morning`
- **晚报**: 每天 19:30 执行 `python3 cron_collect.py evening`

---

## RSS数据源

| 名称 | URL | 分类 |
|------|-----|------|
| 36kr | https://36kr.com/feed | 科技 |
| Hacker News | https://hnrss.org/frontpage | 技术 |
| Hacker News Internal | https://news.ycombinator.com/rss | 开发者生态 |
| V2EX | https://www.v2ex.com/index.xml | 开发者生态 |
| The Hacker News | https://feeds.feedburner.com/TheHackersNews | CTF安全工具 |
| 安全客 | https://api.anquanke.com/data/v1/rss | CTF安全工具 |
| GitHub Trending API | https://api.github.com/search/repositories | 开源推荐 |

---

## 内容分类

自动分类规则（根据关键词匹配）：
- **时政热点**: 政治、政府、政策、外交、国际、社会
- **科技头条**: 科技、互联网、AI、人工智能、大模型
- **CTF安全工具**: 安全、漏洞、黑客、CTF、渗透、攻击
- **智能AI**: 人工智能、机器学习、深度学习、神经网络
- **开源推荐**: 开源、GitHub、仓库、项目、代码
- **开发者生态**: 编程、开发、代码、程序员
- **数码硬件**: 手机、电脑、笔记本、CPU、GPU
- **技术小贴士**: 教程、技巧、指南、解决方案

---

## 禁用关键词（自动过滤）

- 金价/黄金相关: 黄金、金价、金子、金饰、足金、K金
- 娱乐八卦: 娱乐、明星、八卦、绯闻、综艺、追星
- 财经股市: 股市、股票、涨停、跌停、大盘、K线
- 其他: 彩票、博彩、赌博

---

## 日志文件

- **采集日志**: `/var/www/dongshushu-paper/cron_collect.log`
- **早报日志**: `/var/www/dongshushu-paper/logs/collect_morning.log`
- **晚报日志**: `/var/www/dongshushu-paper/logs/collect_evening.log`

---

## 测试结果

### 早报采集测试 (2026-05-05 01:31)
- **采集源**: 36kr, Hacker News, V2EX, GitHub Trending, 安全新闻
- **去重后文章数**: 50篇
- **推送状态**: 全部成功
- **数据分类**: CTF安全工具、科技头条、开源推荐等

---

## API接口

**地址**: http://127.0.0.1:5000/api/articles
**方法**: POST
**格式**: JSON

```json
{
  "title": "标题",
  "content": "内容（≥50字）",
  "category": "科技",
  "source": "来源",
  "paper_type": "morning 或 evening",
  "date": "2026-05-05",
  "is_published": true
}
```

---

## 服务管理命令

```bash
# 查看采集日志
tail -f /var/www/dongshushu-paper/cron_collect.log

# 手动执行采集
cd /var/www/dongshushu-paper && python3 cron_collect.py morning
cd /var/www/dongshushu-paper && python3 cron_collect.py evening

# 查看定时任务
crontab -l

# 编辑定时任务
crontab -e

# 重启Flask服务 (如果需要)
systemctl restart gunicorn
```

---

## 依赖包

```
beautifulsoup4     4.12.3
feedparser        6.0.12
Flask             2.0.3
lxml              5.4.0
requests          2.27.1
gunicorn          21.2.0
```

---

## 注意事项

1. 确保Flask服务持续运行（gunicorn）
2. 采集脚本会自动去重，相同标题不会重复推送
3. 每篇文章内容保证≥50字
4. 网络中断时任务会失败，下次定时任务会自动重试

---

**部署时间**: 2026-05-05
**部署状态**: ✅ 完成
