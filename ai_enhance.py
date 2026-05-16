#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能增强系统 - 为网站赋予强大的AI能力
包含：智能摘要、标签推荐、相似文章、内容分析、智能搜索、趋势预测
"""

import re
import jieba
import jieba.analyse
from collections import Counter
from datetime import datetime, timedelta
import hashlib
import json

class AITextProcessor:
    """AI文本处理引擎"""
    
    def __init__(self):
        self.stopwords = self._load_stopwords()
        jieba.initialize()
    
    def _load_stopwords(self):
        """加载停用词"""
        base = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '他', '她', '它', '们', '这个', '那个', '什么', '怎么',
            '可以', '可能', '应该', '但是', '如果', '因为', '所以', '虽然', '然后',
            '一些', '各种', '每个', '其他', '另外', '今天', '昨天', '明天', '时候'
        }
        return base
    
    def extract_keywords(self, text, topK=10):
        """提取关键词"""
        if not text:
            return []
        
        keywords = jieba.analyse.extract_tags(text, topK=topK, withWeight=True)
        return keywords
    
    def extract_keywords_textrank(self, text, topK=10):
        """使用TextRank算法提取关键词"""
        if not text:
            return []
        
        keywords = jieba.analyse.textrank(text, topK=topK, withWeight=True)
        return keywords
    
    def generate_summary(self, content, max_length=200):
        """生成文章摘要"""
        if not content:
            return ""
        
        content = re.sub(r'<[^>]+>', '', content)
        content = re.sub(r'\s+', ' ', content).strip()
        
        if len(content) <= max_length:
            return content
        
        sentences = re.split(r'[。！？\n]', content)
        summary = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            if len(summary) + len(sentence) + 1 <= max_length:
                summary += sentence + "。"
            else:
                break
        
        if not summary:
            summary = content[:max_length] + "..."
        
        return summary
    
    def extract_tags(self, title, content, topK=5):
        """智能提取标签"""
        full_text = f"{title} {content or ''}"
        full_text = re.sub(r'<[^>]+>', '', full_text)
        
        keywords_tfidf = self.extract_keywords(full_text, topK)
        keywords_textrank = self.extract_keywords_textrank(full_text, topK)
        
        keyword_scores = {}
        for kw, weight in keywords_tfidf:
            keyword_scores[kw] = keyword_scores.get(kw, 0) + weight * 1.5
        
        for kw, weight in keywords_textrank:
            keyword_scores[kw] = keyword_scores.get(kw, 0) + weight
        
        sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
        return [kw for kw, score in sorted_keywords[:topK]]
    
    def analyze_sentiment(self, text):
        """简单情感分析（基于关键词）"""
        positive_words = {'好', '棒', '优秀', '出色', '完美', '喜欢', '赞', '强', '牛', '顶', '支持', '期待', '兴奋', '精彩', '卓越'}
        negative_words = {'差', '烂', '糟', '失望', '垃圾', '无语', '坑', '黑', '骂', '喷', '垃圾', '废物', '可恶'}
        
        words = set(jieba.cut(text))
        
        pos_count = len(words & positive_words)
        neg_count = len(words & negative_words)
        
        if pos_count > neg_count:
            return {'sentiment': 'positive', 'score': pos_count / (pos_count + neg_count + 1)}
        elif neg_count > pos_count:
            return {'sentiment': 'negative', 'score': neg_count / (pos_count + neg_count + 1)}
        else:
            return {'sentiment': 'neutral', 'score': 0.5}
    
    def calculate_readability(self, content):
        """计算内容可读性得分"""
        content = re.sub(r'<[^>]+>', '', content)
        content = re.sub(r'[^\w\s]', '', content)
        
        words = len(content.split())
        sentences = len(re.split(r'[。！？\n]', content))
        
        if sentences == 0:
            sentences = 1
        
        avg_sentence_length = words / sentences
        
        if avg_sentence_length < 15:
            readability = 'easy'
            score = 90
        elif avg_sentence_length < 25:
            readability = 'medium'
            score = 75
        else:
            readability = 'hard'
            score = 60
        
        return {
            'readability': readability,
            'score': score,
            'words': words,
            'sentences': sentences,
            'avg_sentence_length': round(avg_sentence_length, 1)
        }


class AIArticleAnalyzer:
    """AI文章分析器"""
    
    def __init__(self, db):
        self.db = db
        self.text_processor = AITextProcessor()
    
    def analyze_article(self, article_id):
        """全面分析单篇文章"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT * FROM article WHERE id = %s", (article_id,))
            article = cur.fetchone()
            
            if not article:
                return None
            
            title = article[2]
            content = article[3]
            
            keywords = self.text_processor.extract_tags(title, content, topK=8)
            summary = self.text_processor.generate_summary(content, max_length=200)
            sentiment = self.text_processor.analyze_sentiment(f"{title} {content}")
            readability = self.text_processor.calculate_readability(content)
            
            analysis_result = {
                'article_id': article_id,
                'keywords': keywords,
                'summary': summary,
                'sentiment': sentiment,
                'readability': readability,
                'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return analysis_result
        
        finally:
            cur.close()
    
    def batch_analyze(self, limit=100):
        """批量分析文章"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT id, title, content 
                FROM article 
                WHERE is_published = 1 
                LIMIT %s
            """, (limit,))
            
            articles = cur.fetchall()
            results = []
            
            for article in articles:
                article_id, title, content = article[0], article[2], article[3]
                try:
                    result = self.analyze_article(article_id)
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"分析文章 {article_id} 失败: {e}")
            
            return results
        
        finally:
            cur.close()


class AISimilarityEngine:
    """AI相似度计算引擎"""
    
    def __init__(self, db):
        self.db = db
        self.text_processor = AITextProcessor()
    
    def calculate_text_similarity(self, text1, text2):
        """计算两段文本的相似度"""
        words1 = set(jieba.cut(text1))
        words2 = set(jieba.cut(text2))
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        
        words1_counter = Counter(jieba.cut(text1))
        words2_counter = Counter(jieba.cut(text2))
        
        all_words = set(words1_counter.keys()) | set(words2_counter.keys())
        dot_product = sum(words1_counter[w] * words2_counter[w] for w in all_words)
        norm1 = sum(v ** 2 for v in words1_counter.values()) ** 0.5
        norm2 = sum(v ** 2 for v in words2_counter.values()) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            cosine = 0
        else:
            cosine = dot_product / (norm1 * norm2)
        
        return (jaccard * 0.3 + cosine * 0.7)
    
    def find_similar_articles(self, article_id, top_n=5):
        """查找相似文章"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT title, content FROM article WHERE id = %s", (article_id,))
            source = cur.fetchone()
            
            if not source:
                return []
            
            source_title = source[0]
            source_content = source[1] or ""
            source_text = f"{source_title} {source_content}"
            
            cur.execute("""
                SELECT id, title, content 
                FROM article 
                WHERE id != %s AND is_published = 1
            """, (article_id,))
            
            articles = cur.fetchall()
            similarities = []
            
            for article in articles:
                article_id, title, content = article[0], article[1], article[2] or ""
                article_text = f"{title} {content}"
                
                similarity = self.calculate_text_similarity(source_text, article_text)
                
                if similarity > 0.1:
                    similarities.append({
                        'article_id': article_id,
                        'title': title,
                        'similarity': round(similarity * 100, 1)
                    })
            
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:top_n]
        
        finally:
            cur.close()


class AIRecommendationEngine:
    """AI智能推荐引擎"""
    
    def __init__(self, db):
        self.db = db
        self.similarity_engine = AISimilarityEngine(db)
        self.text_processor = AITextProcessor()
    
    def get_personalized_recommendations(self, user_id=None, article_id=None, top_n=10):
        """获取个性化推荐"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            recommendations = []
            
            if article_id:
                cur.execute("SELECT category FROM article WHERE id = %s", (article_id,))
                result = cur.fetchone()
                if result:
                    category = result[0]
                    
                    cur.execute("""
                        SELECT id, title, content, category, view_count 
                        FROM article 
                        WHERE category = %s AND id != %s AND is_published = 1
                        ORDER BY view_count DESC, created_at DESC
                        LIMIT %s
                    """, (category, article_id, top_n // 2))
                    
                    category_articles = cur.fetchall()
                    recommendations.extend(category_articles)
            
            cur.execute("""
                SELECT id, title, content, category, view_count, created_at
                FROM article 
                WHERE is_published = 1
                ORDER BY view_count DESC, created_at DESC
                LIMIT %s
            """, (top_n,))
            
            recent_popular = cur.fetchall()
            
            seen_ids = {r[0] for r in recommendations}
            for article in recent_popular:
                if article[0] not in seen_ids:
                    recommendations.append(article)
                    seen_ids.add(article[0])
            
            return recommendations[:top_n]
        
        finally:
            cur.close()
    
    def get_related_articles(self, article_id, top_n=5):
        """获取相关文章"""
        return self.similarity_engine.find_similar_articles(article_id, top_n)
    
    def get_trending_articles(self, days=7, top_n=10):
        """获取热门文章（基于近期浏览量）"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            cur.execute("""
                SELECT id, title, content, category, view_count
                FROM article 
                WHERE is_published = 1 AND created_at >= %s
                ORDER BY view_count DESC
                LIMIT %s
            """, (since_date, top_n))
            
            return cur.fetchall()
        
        finally:
            cur.close()


class AISearchEngine:
    """AI智能搜索引擎"""
    
    def __init__(self, db):
        self.db = db
        self.text_processor = AITextProcessor()
    
    def smart_search(self, query, filters=None, page=1, per_page=20):
        """智能搜索"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            query_words = list(jieba.cut(query))
            query_words = [w for w in query_words if len(w) > 1 and w not in self.text_processor.stopwords]
            
            if not query_words:
                query_words = list(jieba.cut(query))
            
            conditions = []
            params = []
            
            for word in query_words:
                conditions.append("(title LIKE %s OR content LIKE %s)")
                params.extend([f"%{word}%", f"%{word}%"])
            
            where_clause = " OR ".join(conditions) if conditions else "1=1"
            
            category_filter = ""
            if filters and filters.get('category'):
                category_filter = " AND category = %s"
                params.append(filters['category'])
            
            status_filter = ""
            if filters and filters.get('status') == 'published':
                status_filter = " AND is_published = 1"
            elif filters and filters.get('status') == 'draft':
                status_filter = " AND is_published = 0"
            
            offset = (page - 1) * per_page
            
            count_query = f"""
                SELECT COUNT(*) 
                FROM article 
                WHERE {where_clause} {category_filter} {status_filter}
            """
            cur.execute(count_query, params)
            total_count = cur.fetchone()[0]
            
            search_query = f"""
                SELECT id, title, content, category, view_count, created_at, source
                FROM article 
                WHERE {where_clause} {category_filter} {status_filter}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            params.extend([per_page, offset])
            cur.execute(search_query, params)
            
            articles = cur.fetchall()
            
            results = []
            for article in articles:
                title = article[1]
                content = article[2] or ""
                
                relevance = self._calculate_relevance(query_words, title, content)
                
                results.append({
                    'id': article[0],
                    'title': title,
                    'content': content[:200] + "..." if len(content) > 200 else content,
                    'category': article[3],
                    'view_count': article[4],
                    'created_at': article[5],
                    'source': article[6],
                    'relevance': round(relevance * 100, 1)
                })
            
            results.sort(key=lambda x: x['relevance'], reverse=True)
            
            return {
                'articles': results,
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'query': query,
                'query_words': query_words
            }
        
        finally:
            cur.close()
    
    def _calculate_relevance(self, query_words, title, content):
        """计算搜索相关性"""
        title_lower = title.lower()
        content_lower = content.lower() if content else ""
        
        title_score = 0
        content_score = 0
        
        for word in query_words:
            word_lower = word.lower()
            
            if word_lower in title_lower:
                title_score += 2
                if title_lower.startswith(word_lower):
                    title_score += 3
            
            if word_lower in content_lower:
                content_score += 1
        
        max_possible = len(query_words) * 5
        
        return min((title_score + content_score * 0.3) / max_possible, 1.0) if max_possible > 0 else 0


class AITrendAnalyzer:
    """AI趋势分析器"""
    
    def __init__(self, db):
        self.db = db
    
    def get_category_trends(self, days=30):
        """获取分类趋势"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            cur.execute("""
                SELECT category, COUNT(*) as count, 
                       SUM(view_count) as total_views,
                       AVG(view_count) as avg_views
                FROM article 
                WHERE is_published = 1 AND created_at >= %s
                GROUP BY category
                ORDER BY count DESC
            """, (since_date,))
            
            results = cur.fetchall()
            
            trends = []
            for row in results:
                trends.append({
                    'category': row[0],
                    'article_count': row[1],
                    'total_views': row[2] or 0,
                    'avg_views': round(row[3] or 0, 1)
                })
            
            return trends
        
        finally:
            cur.close()
    
    def get_hot_topics(self, days=7, top_n=10):
        """获取热门话题"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            cur.execute("""
                SELECT title, view_count, category, created_at
                FROM article 
                WHERE is_published = 1 AND created_at >= %s
                ORDER BY view_count DESC
                LIMIT %s
            """, (since_date, top_n))
            
            return cur.fetchall()
        
        finally:
            cur.close()
    
    def get_content_insights(self):
        """获取内容洞察"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            insights = {}
            
            cur.execute("SELECT COUNT(*) FROM article WHERE is_published = 1")
            insights['total_articles'] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM article WHERE DATE(created_at) = CURDATE()")
            insights['today_articles'] = cur.fetchone()[0]
            
            cur.execute("SELECT AVG(view_count) FROM article WHERE is_published = 1")
            insights['avg_views'] = round(cur.fetchone()[0] or 0, 1)
            
            cur.execute("""
                SELECT category, COUNT(*) as count 
                FROM article 
                WHERE is_published = 1 
                GROUP BY category 
                ORDER BY count DESC 
                LIMIT 1
            """)
            top_cat = cur.fetchone()
            insights['top_category'] = top_cat[0] if top_cat else None
            insights['top_category_count'] = top_cat[1] if top_cat else 0
            
            return insights
        
        finally:
            cur.close()


class AIAutoTagSystem:
    """AI自动标签系统"""
    
    def __init__(self, db):
        self.db = db
        self.text_processor = AITextProcessor()
        self._init_tag_table()
    
    def _init_tag_table(self):
        """初始化标签表"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS article_tags (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    article_id INT NOT NULL,
                    tag VARCHAR(100) NOT NULL,
                    weight FLOAT DEFAULT 1.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_article_tag (article_id, tag),
                    INDEX idx_tag (tag)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()
        finally:
            cur.close()
    
    def generate_tags_for_article(self, article_id):
        """为文章生成标签"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT title, content FROM article WHERE id = %s", (article_id,))
            article = cur.fetchone()
            
            if not article:
                return []
            
            title, content = article[0], article[1] or ""
            
            tags = self.text_processor.extract_tags(title, content, topK=10)
            
            cur.execute("DELETE FROM article_tags WHERE article_id = %s", (article_id,))
            
            for tag in tags:
                cur.execute("""
                    INSERT INTO article_tags (article_id, tag, weight)
                    VALUES (%s, %s, %s)
                """, (article_id, tag, 1.0))
            
            conn.commit()
            
            return tags
        
        finally:
            cur.close()
    
    def get_article_tags(self, article_id):
        """获取文章标签"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT tag FROM article_tags WHERE article_id = %s ORDER BY weight DESC", (article_id,))
            return [row[0] for row in cur.fetchall()]
        finally:
            cur.close()
    
    def get_popular_tags(self, limit=20):
        """获取热门标签"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT tag, COUNT(*) as count 
                FROM article_tags 
                GROUP BY tag 
                ORDER BY count DESC 
                LIMIT %s
            """, (limit,))
            
            return [{'tag': row[0], 'count': row[1]} for row in cur.fetchall()]
        finally:
            cur.close()


class AIEnhancedClassifier:
    """AI增强分类器（集成到现有系统）"""
    
    def __init__(self):
        self.text_processor = AITextProcessor()
        self.categories = {
            '时政热点': ['政治', '政府', '政策', '外交', '国际', '峰会', '联合国', '经济', 'GDP', '财政', '央行', '汇率', '贸易战', '美国', '中国', '俄罗斯', '欧洲', '日本', '韩国', '欧盟', '北约', '中东', '乌克兰', '以色列', '制裁', '选举', '总统', '总理', '议会', '法律', 'G20'],
            '科技头条': ['科技', '互联网', '苹果', '谷歌', '微软', '腾讯', '阿里', '字节', '发布', '发布会', '融资', '上市', 'IPO', '投资', '收购', '财报', '营收', '利润', '裁员', '招聘', '芯片', '半导体', '台积电', '代工', '5G', '云计算', '服务器', '量子计算', '无人机', '机器人', 'SpaceX', '火箭', '卫星'],
            '智能AI': ['AI', '人工智能', '大模型', 'LLM', 'GPT', 'ChatGPT', 'Claude', 'DeepSeek', 'Kimi', '豆包', '文心一言', '通义千问', '智谱', '百川', '机器学习', '深度学习', '神经网络', 'Transformer', 'Copilot', 'Cursor', 'Agent', 'Stable Diffusion', 'Midjourney', 'Sora', 'OpenAI', 'Anthropic', 'Embedding', 'RAG', 'Prompt', 'Token', 'Hugging Face', 'Ollama'],
            '安全攻防': ['漏洞', 'CVE', '黑客', '安全', '攻击', '渗透', '入侵', '泄露', '恶意软件', '病毒', '木马', '钓鱼', '勒索', 'APT', '0day', '补丁', 'CTF', '逆向', '取证', 'SQL注入', 'XSS', 'CSRF', 'DDOS'],
            '开发者生态': ['Python', 'JavaScript', 'TypeScript', 'Java', 'Go', 'Rust', 'C++', 'PHP', '编程', '开发', 'API', '框架', 'GitHub', '代码', '程序员', 'Docker', 'K8s', 'Kubernetes', 'DevOps', 'CI/CD', '前端', '后端', 'React', 'Vue', 'Angular', 'Django', 'Flask', 'Spring', '数据库', 'Redis'],
            '数码硬件': ['CPU', 'GPU', '显卡', '英特尔', 'AMD', 'NVIDIA', '评测', '手机', '电脑', '笔记本', '显示器', '屏幕', 'OLED', 'LCD', '内存', '硬盘', 'SSD', 'Mac', 'iPhone', 'iPad', 'MacBook', '大疆', '影石', '相机', '耳机', '鼠标', '键盘', '外设', '路由器', '音响', '音箱', '麦克风', '摄像头', '平板', '智能手表', '手环', '充电器', '数据线', '充电宝', '英菲克', '罗技', '雷蛇', '樱桃', '机械键盘', '无线充电'],
            '社会热点': ['社会', '民生', '就业', '房价', '工资', '社保', '医保', '教育', '学校', '高考', '环境', '污染', '火灾', '灾害', '消费', '电商', '网红', '餐饮', '美食', '旅行', '旅游', '景区', '电动车', '电动自行车', '限速', '外卖', '骑手', '交通', '新规', '新闻', '热点', '热议', '讨论', '事件', '调查', '曝光', '整治'],
            '汽车': ['汽车', '电动车', '新能源', '智驾', '自动驾驶', '车企', '比亚迪', '特斯拉', '蔚来', '理想', '小鹏', '吉利', '长安', '座椅', '续航', '充电', '电池', '辅助驾驶', '车祸', 'Cybertruck', '召回', '小米汽车', 'SU7', 'YU7', 'GT', 'SUV', '轿车', '跑车', 'MPV', '实车', '到店', '汽油', '燃油', '油价', '柴油', '机油', '加油站', '加油', '发动机', '变速箱', '底盘', '轮毂', '轮胎', '刹车', '保时捷', '奔驰', '宝马', '奥迪', '超跑', '豪华车'],
            '游戏': ['游戏', 'Steam', 'PS5', 'Switch', 'Xbox', '巫师', 'GTA', '塞尔达', '任天堂', '暴雪', 'Epic', '博德之门', '战神', '原神', '宝可梦', '马里奥', '最终幻想', '黑神话', '使命召唤', '守望先锋', '魔兽世界', '吃鸡', '英雄联盟', 'LOL', 'Dota', 'SteamDeck', '育碧', 'DLSS', '玩家'],
            '开源推荐': ['GitHub', '开源项目', '开源工具', '开源框架', 'Repository', 'Repo', 'Trending', 'Stars', 'Firecrawl', 'OpenCode', 'ScreenBox', 'Claude-Code', 'Agency', 'Hermes', 'Skills'],
            '医疗健康': ['医疗', '健康', '医院', '医生', '药品', '药物', '疫苗', '疾病', '癌症', '肿瘤', '手术', '治疗', '诊断', '体检', '问诊', '挂号', '红霉素', '软膏', '药膏', '抗生素', '药店', '中医', '西医', '症状', '发烧', '感冒', '咳嗽', '皮肤', '过敏', '核酸', '血压', '血糖', '血脂', '减肥', '营养', '食疗', '保健', '养生']
        }
    
    def classify(self, title, content):
        """AI智能分类"""
        full_text = (title + " " + (content or "")).lower()
        
        scores = {}
        
        for category, keywords in self.categories.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in full_text:
                    score += 1
                    matched_keywords.append(keyword)
                    
                    if keyword.lower() in title.lower():
                        score += 2
            
            if matched_keywords:
                scores[category] = {
                    'score': score,
                    'matched_keywords': matched_keywords,
                    'confidence': min(score / (len(keywords) * 0.3), 1.0)
                }
        
        if not scores:
            return {
                'category': '科技头条',
                'confidence': 0.3,
                'matched_keywords': []
            }
        
        best_category = max(scores.items(), key=lambda x: x[1]['score'])
        
        return {
            'category': best_category[0],
            'confidence': round(best_category[1]['confidence'] * 100, 1),
            'matched_keywords': best_category[1]['matched_keywords'][:5],
            'all_scores': {k: v['score'] for k, v in scores.items()}
        }


def init_ai_system(db):
    """初始化AI系统"""
    print("\n" + "="*60)
    print("🤖 AI智能增强系统初始化")
    print("="*60)
    
    print("\n📊 系统组件:")
    print("   ✓ AITextProcessor - 文本处理引擎")
    print("   ✓ AIArticleAnalyzer - 文章分析器")
    print("   ✓ AISimilarityEngine - 相似度计算")
    print("   ✓ AIRecommendationEngine - 推荐引擎")
    print("   ✓ AISearchEngine - 智能搜索")
    print("   ✓ AITrendAnalyzer - 趋势分析")
    print("   ✓ AIAutoTagSystem - 自动标签")
    print("   ✓ AIEnhancedClassifier - 增强分类器")
    
    print("\n📈 统计信息:")
    classifier = AIEnhancedClassifier()
    print(f"   - 支持分类数: {len(classifier.categories)}")
    print(f"   - 关键词库总量: {sum(len(v) for v in classifier.categories.values())}")
    
    print("\n" + "="*60)
    print("✅ AI系统初始化完成")
    print("="*60 + "\n")
    
    return {
        'classifier': AIEnhancedClassifier(),
        'text_processor': AITextProcessor(),
        'analyzer': AIArticleAnalyzer(db),
        'similarity': AISimilarityEngine(db),
        'recommender': AIRecommendationEngine(db),
        'search': AISearchEngine(db),
        'trends': AITrendAnalyzer(db),
        'auto_tagger': AIAutoTagSystem(db)
    }


if __name__ == "__main__":
    print("🚀 AI智能增强系统测试")
    
    processor = AITextProcessor()
    
    test_text = "OpenAI发布了最新的大语言模型GPT-5，性能大幅提升超越GPT-4"
    
    print(f"\n📝 测试文本: {test_text}")
    print(f"\n🔑 关键词提取: {processor.extract_keywords(test_text, topK=5)}")
    print(f"\n📋 标签生成: {processor.extract_tags(test_text, '', topK=5)}")
    print(f"\n📖 摘要生成: {processor.generate_summary(test_text, max_length=50)}")
    print(f"\n💭 情感分析: {processor.analyze_sentiment(test_text)}")
    print(f"\n📊 可读性分析: {processor.calculate_readability(test_text)}")
    
    classifier = AIEnhancedClassifier()
    result = classifier.classify("苹果发布iPhone 16，搭载最新AI芯片", "苹果公司今日发布了全新iPhone 16系列...")
    print(f"\n🏷️ 智能分类: {result}")
