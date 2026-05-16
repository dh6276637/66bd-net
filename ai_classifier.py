#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 分类学习系统 - 具有自主进化能力的文章分类器
基于 TF-IDF 特征提取 + 机器学习分类器
"""

import MySQLdb
from MySQLdb.cursors import DictCursor
import os
import pickle
import json
import re
from datetime import datetime
from collections import defaultdict

# 尝试导入机器学习库
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.svm import LinearSVC
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("警告: scikit-learn 未安装，将使用基于规则的分类")

# 尝试导入中文分词
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    print("警告: jieba 未安装，将使用简单分词")

DB_CONFIG = {
    "host": "localhost",
    "user": "paper_user",
    "passwd": "paper_db2026",
    "db": "dongshushu_paper",
    "charset": "utf8mb4"
}

# 项目根目录
PROJECT_ROOT = '/workspace/66bd-net'
if os.path.exists('/var/www/dongshushu-paper'):
    PROJECT_ROOT = '/var/www/dongshushu-paper'

MODEL_DIR = os.path.join(PROJECT_ROOT, 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

CLASSIFIER_MODEL_PATH = os.path.join(MODEL_DIR, 'article_classifier.pkl')
FEEDBACK_DB_PATH = os.path.join(MODEL_DIR, 'feedback_history.json')
STATS_PATH = os.path.join(MODEL_DIR, 'learning_stats.json')

CATEGORIES = [
    "时政热点", "科技头条", "智能AI", "安全攻防", "开发者生态",
    "数码硬件", "社会热点", "汽车", "游戏", "开源推荐", "医疗健康"
]

class ChineseTextProcessor:
    """中文文本处理器"""
    
    def __init__(self):
        self.stopwords = self._load_stopwords()
    
    def _load_stopwords(self):
        """加载停用词"""
        base_stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '他', '她', '它', '们', '这个', '那个', '什么', '怎么',
            '为什么', '如何', '为什么', '可以', '可能', '应该', '但是', '如果', '因为',
            '所以', '虽然', '然而', '并且', '或者', '还是', '以及', '对于', '关于',
            '通过', '使用', '进行', '开始', '继续', '结束', '之后', '之前', '之间',
            '一些', '各种', '每个', '某些', '其他', '另外', '此外', '总之', '总之',
            '现在', '今天', '昨天', '明天', '去年', '今年', '明年', '时候', '时间',
            '方式', '方法', '过程', '结果', '原因', '目的', '内容', '情况', '问题'
        }
        
        # 从文件加载停用词（如果存在）
        stopwords_file = os.path.join(PROJECT_ROOT, 'data', 'stopwords.txt')
        if os.path.exists(stopwords_file):
            with open(stopwords_file, 'r', encoding='utf-8') as f:
                base_stopwords.update(set(line.strip() for line in f if line.strip()))
        
        return base_stopwords
    
    def tokenize(self, text):
        """分词"""
        if JIEBA_AVAILABLE:
            words = jieba.cut(text)
        else:
            # 简单分词：按标点和空格分割
            words = re.findall(r'[\w]+', text)
        
        # 过滤停用词和短词
        filtered = []
        for word in words:
            word = word.strip().lower()
            if word and len(word) > 1 and word not in self.stopwords:
                filtered.append(word)
        
        return ' '.join(filtered)
    
    def preprocess(self, title, content):
        """预处理文本"""
        # 合并标题和内容
        full_text = f"{title} {content or ''}"
        
        # 清理 HTML 标签
        full_text = re.sub(r'<[^>]+>', '', full_text)
        
        # 清理特殊字符
        full_text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', full_text)
        
        # 分词
        return self.tokenize(full_text)


class AILearningClassifier:
    """AI 分类学习器"""
    
    def __init__(self):
        self.vectorizer = None
        self.classifier = None
        self.text_processor = ChineseTextProcessor()
        self.is_trained = False
        self.last_train_time = None
        self.stats = self._load_stats()
        
        # 加载已有模型
        self._load_model()
    
    def _load_stats(self):
        """加载学习统计"""
        if os.path.exists(STATS_PATH):
            try:
                with open(STATS_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            'total_predictions': 0,
            'correct_predictions': 0,
            'feedback_count': 0,
            'retrain_count': 0,
            'category_accuracy': {}
        }
    
    def _save_stats(self):
        """保存学习统计"""
        try:
            with open(STATS_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def _load_model(self):
        """加载已训练的模型"""
        if os.path.exists(CLASSIFIER_MODEL_PATH):
            try:
                with open(CLASSIFIER_MODEL_PATH, 'rb') as f:
                    model_data = pickle.load(f)
                    self.vectorizer = model_data.get('vectorizer')
                    self.classifier = model_data.get('classifier')
                    self.is_trained = model_data.get('is_trained', False)
                    self.last_train_time = model_data.get('last_train_time')
                print(f"✓ 已加载训练好的模型 (训练时间: {self.last_train_time})")
            except Exception as e:
                print(f"加载模型失败: {e}")
    
    def _save_model(self):
        """保存模型"""
        try:
            model_data = {
                'vectorizer': self.vectorizer,
                'classifier': self.classifier,
                'is_trained': self.is_trained,
                'last_train_time': self.last_train_time
            }
            with open(CLASSIFIER_MODEL_PATH, 'wb') as f:
                pickle.dump(model_data, f)
            print(f"✓ 模型已保存")
        except Exception as e:
            print(f"保存模型失败: {e}")
    
    def get_db(self):
        """获取数据库连接"""
        return MySQLdb.connect(**DB_CONFIG)
    
    def get_training_data(self, min_samples=10):
        """获取训练数据"""
        conn = self.get_db()
        cur = conn.cursor(DictCursor)
        
        try:
            # 获取已发布的文章作为训练数据
            cur.execute("""
                SELECT title, content, category 
                FROM article 
                WHERE is_published = 1 
                  AND category IS NOT NULL 
                  AND category != ''
                ORDER BY created_at DESC
                LIMIT 1000
            """)
            articles = cur.fetchall()
            
            # 获取反馈纠正的数据（优先使用）
            cur.execute("""
                SELECT title, content, correct_category as category
                FROM article_feedback
                WHERE status = 'approved'
                LIMIT 500
            """)
            feedback_articles = cur.fetchall()
            
            all_articles = articles + feedback_articles
            
            # 过滤有效的分类
            valid_articles = [
                a for a in all_articles 
                if a['category'] and a['category'] in CATEGORIES
            ]
            
            # 统计每个分类的样本数
            category_counts = defaultdict(int)
            for a in valid_articles:
                category_counts[a['category']] += 1
            
            # 检查是否满足最小样本要求
            if min_samples > 0:
                insufficient = [cat for cat, count in category_counts.items() if count < min_samples]
                if insufficient:
                    print(f"⚠ 以下分类样本不足 {min_samples} 个: {insufficient}")
                    print(f"   当前样本数: {dict(category_counts)}")
            
            return valid_articles
            
        finally:
            cur.close()
            conn.close()
    
    def train(self, force=False):
        """训练分类器"""
        if not ML_AVAILABLE:
            print("❌ 机器学习库不可用，无法训练")
            return False
        
        print("🔄 开始训练 AI 分类器...")
        
        # 获取训练数据
        articles = self.get_training_data(min_samples=5)
        
        if len(articles) < 50:
            print(f"⚠ 训练数据不足 ({len(articles)} 个)，需要至少 50 个样本")
            return False
        
        # 准备数据
        texts = []
        labels = []
        for article in articles:
            text = self.text_processor.preprocess(
                article['title'], 
                article.get('content', '')
            )
            texts.append(text)
            labels.append(article['category'])
        
        print(f"📊 训练数据: {len(texts)} 个样本")
        
        # 创建 TF-IDF 向量化器
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95
        )
        
        # 转换文本为向量
        X = self.vectorizer.fit_transform(texts)
        y = labels
        
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # 训练分类器（使用 LinearSVC，通常效果更好）
        self.classifier = LinearSVC(
            C=1.0,
            max_iter=10000,
            class_weight='balanced'
        )
        self.classifier.fit(X_train, y_train)
        
        # 评估
        train_score = self.classifier.score(X_train, y_train)
        test_score = self.classifier.score(X_test, y_test)
        
        print(f"✓ 训练完成!")
        print(f"   训练集准确率: {train_score:.2%}")
        print(f"   测试集准确率: {test_score:.2%}")
        
        # 详细分类报告
        y_pred = self.classifier.predict(X_test)
        print("\n📋 分类详情:")
        print(classification_report(y_test, y_pred, target_names=CATEGORIES))
        
        # 保存模型
        self.is_trained = True
        self.last_train_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._save_model()
        
        return True
    
    def predict(self, title, content, top_k=3):
        """预测分类"""
        if not self.is_trained or not self.vectorizer or not self.classifier:
            print("⚠ 模型未训练，使用规则分类")
            return self.rule_based_classify(title, content)
        
        # 预处理文本
        text = self.text_processor.preprocess(title, content)
        X = self.vectorizer.transform([text])
        
        # 预测
        prediction = self.classifier.predict(X)[0]
        
        # 获取决策函数分数
        try:
            scores = self.classifier.decision_function(X)[0]
            max_score = max(scores)
            min_score = min(scores)
            normalized_confidence = (max_score - min_score) / (max_score - min_score + 1e-10)
        except:
            normalized_confidence = 0.7  # 默认置信度
        
        self.stats['total_predictions'] += 1
        self._save_stats()
        
        return {
            'category': prediction,
            'confidence': normalized_confidence,
            'all_predictions': self._get_top_predictions(X)
        }
    
    def _get_top_predictions(self, X, top_k=3):
        """获取 Top-K 预测"""
        try:
            scores = self.classifier.decision_function(X)[0]
            indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
            return [
                {'category': CATEGORIES[i], 'score': float(scores[i])}
                for i in indices
            ]
        except:
            return []
    
    def rule_based_classify(self, title, content):
        """基于规则的分类（备选方案）"""
        from cron_collect import CATEGORY_KEYWORDS
        
        text = (title + " " + (content or "")).lower()
        scores = {}
        
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = 0
            for kw in keywords:
                if kw.lower() in text:
                    score += 1
                    # 标题中的关键词权重更高
                    if kw.lower() in title.lower():
                        score += 2
            if score > 0:
                scores[category] = score
        
        if not scores:
            return {
                'category': '科技头条',
                'confidence': 0.3,
                'all_predictions': []
            }
        
        # 返回最高分分类
        best_category = max(scores, key=scores.get)
        max_score = scores[best_category]
        confidence = min(max_score / 10.0, 0.95)
        
        return {
            'category': best_category,
            'confidence': confidence,
            'all_predictions': sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        }
    
    def learn_from_feedback(self, article_id, correct_category, admin_id='system'):
        """从反馈中学习"""
        conn = self.get_db()
        cur = conn.cursor()
        
        try:
            # 记录反馈
            cur.execute("""
                INSERT INTO article_feedback 
                (article_id, title, content, original_category, correct_category, 
                 admin_id, status, created_at)
                SELECT id, title, content, category, %s, %s, 'pending', NOW()
                FROM article WHERE id = %s
            """, (correct_category, admin_id, article_id))
            conn.commit()
            
            self.stats['feedback_count'] += 1
            self._save_stats()
            
            print(f"✓ 已记录反馈: 文章 {article_id} -> {correct_category}")
            
            # 检查是否需要重新训练
            if self.stats['feedback_count'] % 10 == 0:
                print("\n🔄 反馈累计 10 条，检查是否需要重新训练...")
                self.check_and_retrain()
            
            return True
            
        finally:
            cur.close()
            conn.close()
    
    def check_and_retrain(self, min_new_samples=10):
        """检查并自动重训练"""
        if not ML_AVAILABLE:
            return False
        
        # 获取新的反馈数据
        conn = self.get_db()
        cur = conn.cursor(DictCursor)
        
        try:
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM article_feedback 
                WHERE status = 'pending'
            """)
            new_feedback = cur.fetchone()['count']
            
            if new_feedback >= min_new_samples:
                print(f"📚 发现 {new_feedback} 条新反馈，开始重训练...")
                
                # 批准所有反馈
                cur.execute("""
                    UPDATE article_feedback 
                    SET status = 'approved'
                    WHERE status = 'pending'
                """)
                conn.commit()
                
                # 重训练
                success = self.train(force=True)
                
                if success:
                    self.stats['retrain_count'] += 1
                    self.stats['feedback_count'] = 0
                    self._save_stats()
                    print("✅ 重训练完成! AI 分类器已更新")
                
                return success
            else:
                print(f"ℹ 新反馈不足 ({new_feedback}/{min_new_samples})，暂不重训练")
                return False
                
        finally:
            cur.close()
            conn.close()
    
    def auto_train_if_needed(self):
        """如果模型不存在或过旧，自动训练"""
        if not ML_AVAILABLE:
            return False
        
        # 检查模型是否存在
        if not os.path.exists(CLASSIFIER_MODEL_PATH):
            print("📦 模型不存在，开始训练...")
            return self.train()
        
        # 检查最后训练时间
        if self.last_train_time:
            last_train = datetime.strptime(self.last_train_time, '%Y-%m-%d %H:%M:%S')
            days_since_train = (datetime.now() - last_train).days
            
            if days_since_train >= 7:
                print(f"⏰ 模型已训练超过 {days_since_train} 天，检查是否需要更新...")
                return self.check_and_retrain(min_new_samples=5)
        
        return False


# 全局分类器实例
classifier = AILearningClassifier()


def smart_classify(title, content):
    """智能分类接口"""
    return classifier.predict(title, content)


def init_learning_system():
    """初始化学习系统"""
    print("\n" + "="*50)
    print("🧠 AI 分类学习系统初始化")
    print("="*50)
    
    # 检查依赖
    print(f"\n📦 依赖检查:")
    print(f"   - scikit-learn: {'✓' if ML_AVAILABLE else '✗'}")
    print(f"   - jieba分词: {'✓' if JIEBA_AVAILABLE else '✗'}")
    
    # 自动训练（如果需要）
    if ML_AVAILABLE:
        classifier.auto_train_if_needed()
    
    # 显示统计
    print(f"\n📊 学习统计:")
    print(f"   - 总预测次数: {classifier.stats['total_predictions']}")
    print(f"   - 反馈记录数: {classifier.stats['feedback_count']}")
    print(f"   - 重训练次数: {classifier.stats['retrain_count']}")
    print(f"   - 模型状态: {'已训练' if classifier.is_trained else '未训练'}")
    
    print("="*50 + "\n")


if __name__ == "__main__":
    # 测试分类器
    init_learning_system()
    
    # 测试一些文章
    test_articles = [
        ("蔚来发布全新电动SUV，续航突破1000公里", "今日，蔚来汽车正式发布了旗下最新款电动SUV..."),
        ("科学家研发出新型抗癌药物，临床试验效果显著", "医学研究团队近日宣布..."),
        ("Python 3.12正式发布，性能大幅提升", "Python官方今日宣布..."),
        ("英菲克推出全新无线游戏鼠标，支持RGB灯效", "外设厂商英菲克..."),
        ("比特币价格突破10万美元大关", "加密货币市场今日迎来重大突破...")
    ]
    
    print("\n🧪 测试分类:")
    for title, content in test_articles:
        result = smart_classify(title, content)
        print(f"\n📰 {title}")
        print(f"   分类: {result['category']} (置信度: {result['confidence']:.2%})")
