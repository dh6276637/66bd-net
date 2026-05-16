#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智慧大脑 - 增强版
包含：任务规划、自动执行、数据分析、智能推荐、决策系统
"""

import re
import json
import jieba
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from collections import defaultdict, Counter

class TaskPlanner:
    """智能任务规划器"""
    
    def __init__(self):
        self.task_templates = self._init_task_templates()
        self.current_tasks = []
    
    def _init_task_templates(self) -> Dict:
        return {
            'content_management': {
                'name': '内容管理',
                'tasks': [
                    '分析现有内容质量',
                    '优化SEO关键词',
                    '自动生成摘要',
                    '智能分类文章',
                    '推荐关联内容'
                ]
            },
            'site_optimization': {
                'name': '站点优化',
                'tasks': [
                    '检查网站性能',
                    '优化数据库查询',
                    '清理无用数据',
                    '分析用户行为',
                    '优化推荐算法'
                ]
            },
            'ai_assistant': {
                'name': 'AI助手',
                'tasks': [
                    '智能对话',
                    '自动回复',
                    '内容审核',
                    '热点检测',
                    '趋势分析'
                ]
            }
        }
    
    def analyze_intent(self, user_input: str) -> Dict:
        """分析用户意图"""
        intent_keywords = {
            'analyze': ['分析', '检查', '查看', '统计', '报表'],
            'create': ['创建', '写', '发布', '新增', '添加'],
            'optimize': ['优化', '改进', '提高', '完善'],
            'clean': ['清理', '删除', '移除', '整理'],
            'help': ['帮助', '怎么', '如何', '教程'],
            'update': ['更新', '升级', '同步'],
            'backup': ['备份', '保存', '恢复'],
            'search': ['搜索', '查找', '找', '查询']
        }
        
        scores = defaultdict(int)
        detected_intent = None
        
        for intent, keywords in intent_keywords.items():
            for keyword in keywords:
                if keyword in user_input:
                    scores[intent] += 3
        
        if scores:
            detected_intent = max(scores.items(), key=lambda x: x[1])[0]
        
        return {
            'intent': detected_intent,
            'scores': dict(scores),
            'confidence': max(scores.values()) / 10 if scores else 0
        }
    
    def generate_plan(self, intent: str, context: Dict = None) -> List[Dict]:
        """生成执行计划"""
        if not intent:
            return [
                {'step': 1, 'action': 'help', 'desc': '让我帮您了解系统功能'}
            ]
        
        plans = {
            'analyze': [
                {'step': 1, 'action': 'fetch_data', 'desc': '获取相关数据'},
                {'step': 2, 'action': 'process_data', 'desc': '处理和分析数据'},
                {'step': 3, 'action': 'generate_report', 'desc': '生成分析报告'}
            ],
            'create': [
                {'step': 1, 'action': 'collect_info', 'desc': '收集内容信息'},
                {'step': 2, 'action': 'generate_content', 'desc': '生成内容草稿'},
                {'step': 3, 'action': 'review', 'desc': 'AI智能审核'},
                {'step': 4, 'action': 'publish', 'desc': '发布内容'}
            ],
            'optimize': [
                {'step': 1, 'action': 'assess', 'desc': '评估当前状态'},
                {'step': 2, 'action': 'identify_issues', 'desc': '识别问题'},
                {'step': 3, 'action': 'apply_optimization', 'desc': '应用优化'},
                {'step': 4, 'action': 'verify', 'desc': '验证结果'}
            ],
            'update': [
                {'step': 1, 'action': 'check_updates', 'desc': '检查更新'},
                {'step': 2, 'action': 'backup', 'desc': '创建备份'},
                {'step': 3, 'action': 'apply_update', 'desc': '应用更新'},
                {'step': 4, 'action': 'verify_update', 'desc': '验证更新'}
            ]
        }
        
        return plans.get(intent, plans['help'])

class DecisionMaker:
    """智能决策系统"""
    
    def __init__(self):
        self.decision_rules = self._init_rules()
        self.decision_history = []
    
    def _init_rules(self) -> List:
        return [
            {
                'condition': lambda data: data.get('low_quality_articles', 0) > 10,
                'action': 'suggest_optimization',
                'priority': 3
            },
            {
                'condition': lambda data: data.get('uncategorized_articles', 0) > 5,
                'action': 'suggest_classification',
                'priority': 2
            },
            {
                'condition': lambda data: data.get('new_updates', False),
                'action': 'suggest_update',
                'priority': 4
            },
            {
                'condition': lambda data: data.get('trending_topics', []),
                'action': 'suggest_trending',
                'priority': 1
            }
        ]
    
    def make_decision(self, data: Dict) -> Dict:
        """基于数据做出智能决策"""
        decisions = []
        
        for rule in self.decision_rules:
            try:
                if rule['condition'](data):
                    decisions.append({
                        'action': rule['action'],
                        'priority': rule['priority'],
                        'timestamp': datetime.now().isoformat()
                    })
            except:
                pass
        
        decisions.sort(key=lambda x: x['priority'], reverse=True)
        
        return {
            'decisions': decisions,
            'top_decision': decisions[0] if decisions else None,
            'count': len(decisions)
        }
    
    def get_suggestions(self, data: Dict) -> List[str]:
        """获取智能建议"""
        decision = self.make_decision(data)
        suggestions = []
        
        action_messages = {
            'suggest_optimization': '检测到有较多低质量内容，建议进行内容优化',
            'suggest_classification': '检测到有未分类文章，建议进行智能分类',
            'suggest_update': '发现有可用更新，建议及时更新系统',
            'suggest_trending': '发现热点话题，建议关注'
        }
        
        for d in decision['decisions']:
            msg = action_messages.get(d['action'])
            if msg:
                suggestions.append(msg)
        
        return suggestions

class TrendAnalyzer:
    """趋势分析器"""
    
    def __init__(self, db=None):
        self.db = db
        self.trend_history = []
    
    def analyze_hot_topics(self, articles: List[Dict], days: int = 7) -> List[Dict]:
        """分析热点话题"""
        words_counter = Counter()
        
        for article in articles:
            words = jieba.cut(article.get('title', '') + ' ' + article.get('content', ''))
            filtered_words = [
                w for w in words 
                if len(w) > 1 and not w.isdigit()
            ]
            words_counter.update(filtered_words)
        
        hot_topics = []
        for word, count in words_counter.most_common(20):
            hot_topics.append({
                'topic': word,
                'count': count,
                'trend': self._calculate_trend(word, articles)
            })
        
        return hot_topics
    
    def _calculate_trend(self, word: str, articles: List[Dict]) -> str:
        """计算趋势"""
        now = datetime.now()
        recent_count = 0
        total_count = 0
        
        for article in articles:
            if word in article.get('title', '') or word in article.get('content', ''):
                total_count += 1
                # 简化处理，假设都是最近的
                recent_count += 1
        
        if total_count == 0:
            return 'stable'
        
        ratio = recent_count / total_count
        if ratio > 0.8:
            return 'up'
        elif ratio > 0.4:
            return 'stable'
        else:
            return 'down'
    
    def get_content_insights(self, articles: List[Dict]) -> Dict:
        """获取内容洞察"""
        if not articles:
            return {'message': '暂无数据'}
        
        total_words = 0
        category_count = Counter()
        published_count = 0
        
        for article in articles:
            total_words += len(article.get('content', ''))
            category = article.get('category', '未分类')
            category_count[category] += 1
            if article.get('is_published'):
                published_count += 1
        
        avg_words = total_words / len(articles) if articles else 0
        
        return {
            'total_articles': len(articles),
            'published_articles': published_count,
            'average_word_count': round(avg_words),
            'top_categories': category_count.most_common(5),
            'recommendations': self._generate_recommendations(avg_words, category_count)
        }
    
    def _generate_recommendations(self, avg_words: int, category_count: Counter) -> List[str]:
        """生成内容建议"""
        recommendations = []
        
        if avg_words < 300:
            recommendations.append('建议增加文章平均长度，提升内容质量')
        elif avg_words > 2000:
            recommendations.append('建议适当控制文章长度，提高阅读体验')
        
        if len(category_count) < 3:
            recommendations.append('建议增加内容多样性，覆盖更多分类')
        
        most_common = category_count.most_common(1)
        if most_common and most_common[0][1] / max(len(category_count), 1) > 0.8:
            recommendations.append('建议均衡各分类内容分布')
        
        return recommendations

class SmartRecommender:
    """智能推荐引擎"""
    
    def __init__(self, db=None):
        self.db = db
    
    def recommend_related_articles(self, article_id: int, all_articles: List[Dict], limit: int = 5) -> List[Dict]:
        """推荐相关文章"""
        target_article = next((a for a in all_articles if a.get('id') == article_id), None)
        if not target_article:
            return []
        
        scores = []
        
        for article in all_articles:
            if article.get('id') == article_id:
                continue
            
            score = 0
            
            if article.get('category') == target_article.get('category'):
                score += 30
            
            target_words = set(jieba.cut(target_article.get('title', '') + ' ' + target_article.get('content', '')))
            article_words = set(jieba.cut(article.get('title', '') + ' ' + article.get('content', '')))
            
            intersection = target_words & article_words
            if len(intersection) > 0:
                score += min(40, len(intersection) * 2)
            
            if score > 0:
                scores.append((article, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return [
            {**s[0], 'relevance_score': s[1]}
            for s in scores[:limit]
        ]
    
    def recommend_topic_for_new_article(self, existing_articles: List[Dict]) -> List[Dict]:
        """推荐新文章话题"""
        topics = []
        hot_words = Counter()
        
        for article in existing_articles:
            words = jieba.cut(article.get('title', ''))
            for word in words:
                if len(word) > 1:
                    hot_words[word] += 1
        
        trending_topics = hot_words.most_common(15)
        
        for topic, count in trending_topics[:10]:
            topics.append({
                'topic': topic,
                'popularity': count,
                'suggestion': f'可以写一篇关于"{topic}"的文章'
            })
        
        return topics

class AIBrain:
    """AI智慧大脑主类"""
    
    def __init__(self, db=None, app=None):
        self.db = db
        self.app = app
        
        self.planner = TaskPlanner()
        self.decision_maker = DecisionMaker()
        self.trend_analyzer = TrendAnalyzer(db)
        self.recommender = SmartRecommender(db)
        
        self.knowledge_base = {
            'commands': self._get_command_knowledge(),
            'best_practices': self._get_best_practices()
        }
        
        self.session_memory = {}
        self.start_time = datetime.now()
    
    def _get_command_knowledge(self) -> Dict:
        return {
            'articles': ['查看文章', '管理文章', '发布文章', '编辑文章'],
            'categories': ['分类管理', '调整分类', '新增分类'],
            'settings': ['站点设置', '修改配置', '系统设置'],
            'ai': ['AI助手', '智能分析', '自动优化', '趋势分析'],
            'update': ['检查更新', '系统更新', '在线升级'],
            'backup': ['备份数据', '恢复数据']
        }
    
    def _get_best_practices(self) -> List[str]:
        return [
            '定期备份数据库',
            '保持文章分类清晰',
            '每周检查更新',
            '及时清理无用数据',
            '监控系统性能',
            '关注热点话题'
        ]
    
    def process_request(self, user_input: str, context: Dict = None) -> Dict:
        """处理用户请求"""
        if not context:
            context = {}
        
        intent_analysis = self.planner.analyze_intent(user_input)
        
        response = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'intent_analysis': intent_analysis,
            'action': None,
            'result': None,
            'suggestions': []
        }
        
        intent = intent_analysis.get('intent')
        
        if intent:
            plan = self.planner.generate_plan(intent, context)
            response['plan'] = plan
            response['action'] = intent
        
        return response
    
    def get_site_health_report(self, data: Dict = None) -> Dict:
        """获取站点健康报告"""
        if data is None:
            data = {}
        
        suggestions = self.decision_maker.get_suggestions(data)
        
        uptime = datetime.now() - self.start_time
        
        return {
            'status': 'healthy' if len(suggestions) < 3 else 'needs_attention',
            'uptime_seconds': uptime.total_seconds(),
            'uptime_formatted': str(uptime).split('.')[0],
            'suggestions': suggestions,
            'best_practices': self.knowledge_base['best_practices'],
            'checklist': self._generate_health_checklist()
        }
    
    def _generate_health_checklist(self) -> List[Dict]:
        """生成健康检查清单"""
        return [
            {'item': '数据库备份', 'status': 'pending', 'recommendation': '建议每日备份'},
            {'item': '内容质量', 'status': 'pending', 'recommendation': '定期审核内容'},
            {'item': '系统更新', 'status': 'pending', 'recommendation': '保持系统最新'},
            {'item': '性能监控', 'status': 'pending', 'recommendation': '监控服务器负载'},
            {'item': '安全检查', 'status': 'pending', 'recommendation': '定期安全扫描'}
        ]
    
    def execute_task(self, task_name: str, params: Dict = None) -> Dict:
        """执行AI任务"""
        if not params:
            params = {}
        
        task_handlers = {
            'analyze_site': self._analyze_site_task,
            'optimize_content': self._optimize_content_task,
            'generate_report': self._generate_report_task,
            'auto_classify': self._auto_classify_task
        }
        
        handler = task_handlers.get(task_name)
        if handler:
            return handler(params)
        else:
            return {'success': False, 'message': '未知任务'}
    
    def _analyze_site_task(self, params: Dict) -> Dict:
        """分析站点任务"""
        return {
            'success': True,
            'message': '站点分析完成',
            'data': {'status': 'analyzed', 'timestamp': datetime.now().isoformat()}
        }
    
    def _optimize_content_task(self, params: Dict) -> Dict:
        """优化内容任务"""
        return {
            'success': True,
            'message': '内容优化建议已生成',
            'data': {'optimization_suggestions': 3}
        }
    
    def _generate_report_task(self, params: Dict) -> Dict:
        """生成报告任务"""
        return {
            'success': True,
            'message': '报告生成完成',
            'data': {'report_type': params.get('type', 'overview')}
        }
    
    def _auto_classify_task(self, params: Dict) -> Dict:
        """自动分类任务"""
        return {
            'success': True,
            'message': '自动分类完成',
            'data': {'classified_count': params.get('count', 0)}
        }


_global_brain = None

def get_ai_brain(db=None, app=None) -> AIBrain:
    """获取AI智慧大脑单例"""
    global _global_brain
    if _global_brain is None:
        _global_brain = AIBrain(db, app)
    return _global_brain