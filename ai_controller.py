#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI网站操控系统 - 让AI可以智能操控整个网站
包含：命令解析、操作执行、自动化流程、智能决策
"""

import re
import json
import jieba
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import random


class CommandType(Enum):
    """命令类型枚举"""
    CREATE_ARTICLE = "create_article"
    EDIT_ARTICLE = "edit_article"
    DELETE_ARTICLE = "delete_article"
    PUBLISH_ARTICLE = "publish_article"
    CATEGORIZE_ARTICLE = "categorize_article"
    SETTINGS = "settings"
    ANALYZE = "analyze"
    REPORT = "report"
    AUTO_PILOT = "auto_pilot"
    SCHEDULE = "schedule"
    SEARCH = "search"
    STATISTICS = "statistics"
    BACKUP = "backup"
    UPDATE = "update"
    HELP = "help"
    UNKNOWN = "unknown"


class AIActionExecutor:
    """AI操作执行器 - 负责执行具体的网站操作"""
    
    def __init__(self, db, app=None):
        self.db = db
        self.app = app
        from ai_enhance import init_ai_system
        self.ai_system = init_ai_system(db)
        self.action_history = []
    
    def execute(self, command_type: CommandType, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行命令"""
        try:
            action_id = f"action_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000,9999)}"
            
            result = {
                'action_id': action_id,
                'command_type': command_type.value,
                'params': params,
                'success': False,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            handler = getattr(self, f"_handle_{command_type.value}", None)
            if handler:
                handler_result = handler(params)
                result.update(handler_result)
                result['success'] = True
            else:
                result['error'] = f"不支持的命令类型: {command_type}"
            
            self.action_history.append(result)
            return result
            
        except Exception as e:
            return {
                'action_id': f"error_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'command_type': command_type.value,
                'params': params,
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _handle_create_article(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """创建文章"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            title = params.get('title', '')
            content = params.get('content', '')
            category = params.get('category', '科技头条')
            source = params.get('source', 'AI创作')
            is_published = params.get('is_published', False)
            
            if not title:
                raise ValueError("文章标题不能为空")
            
            keywords = self.ai_system['text_processor'].extract_tags(title, content, topK=10)
            summary = self.ai_system['text_processor'].generate_summary(content, max_length=300)
            
            cur.execute("""
                INSERT INTO article (title, content, category, source, is_published, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (title, content, category, source, 1 if is_published else 0))
            conn.commit()
            
            article_id = cur.lastrowid
            
            for tag in keywords:
                try:
                    cur.execute("""
                        INSERT INTO article_tags (article_id, tag, weight)
                        VALUES (%s, %s, 1.0)
                    """, (article_id, tag))
                except:
                    pass
            conn.commit()
            
            return {
                'article_id': article_id,
                'title': title,
                'category': category,
                'keywords': keywords,
                'summary': summary,
                'message': f'成功创建文章: {title}'
            }
        finally:
            cur.close()
    
    def _handle_edit_article(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """编辑文章"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            article_id = params.get('article_id')
            if not article_id:
                raise ValueError("需要指定文章ID")
            
            updates = []
            update_params = []
            
            if 'title' in params:
                updates.append("title = %s")
                update_params.append(params['title'])
            if 'content' in params:
                updates.append("content = %s")
                update_params.append(params['content'])
            if 'category' in params:
                updates.append("category = %s")
                update_params.append(params['category'])
            
            if not updates:
                raise ValueError("没有提供要更新的字段")
            
            update_params.append(article_id)
            
            cur.execute(f"""
                UPDATE article 
                SET {', '.join(updates)}, updated_at = NOW()
                WHERE id = %s
            """, update_params)
            conn.commit()
            
            return {
                'article_id': article_id,
                'updated_fields': [u.split(' = ')[0] for u in updates],
                'message': f'成功更新文章 ID: {article_id}'
            }
        finally:
            cur.close()
    
    def _handle_publish_article(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """发布文章"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            article_id = params.get('article_id')
            if not article_id:
                raise ValueError("需要指定文章ID")
            
            cur.execute("""
                UPDATE article 
                SET is_published = 1, updated_at = NOW()
                WHERE id = %s
            """, (article_id,))
            conn.commit()
            
            return {
                'article_id': article_id,
                'message': f'成功发布文章 ID: {article_id}'
            }
        finally:
            cur.close()
    
    def _handle_categorize_article(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """智能分类文章"""
        article_id = params.get('article_id')
        
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT title, content FROM article WHERE id = %s", (article_id,))
            article = cur.fetchone()
            
            if not article:
                raise ValueError(f"找不到文章 ID: {article_id}")
            
            title, content = article
            classification = self.ai_system['classifier'].classify(title, content)
            
            cur.execute("""
                UPDATE article 
                SET category = %s, updated_at = NOW()
                WHERE id = %s
            """, (classification['category'], article_id))
            conn.commit()
            
            return {
                'article_id': article_id,
                'category': classification['category'],
                'confidence': classification['confidence'],
                'matched_keywords': classification['matched_keywords'],
                'message': f'成功将文章分类为: {classification["category"]}'
            }
        finally:
            cur.close()
    
    def _handle_analyze(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析网站状态"""
        analyze_type = params.get('type', 'overview')
        
        if analyze_type == 'overview':
            return self._analyze_overview()
        elif analyze_type == 'trends':
            return self._analyze_trends()
        else:
            return self._analyze_overview()
    
    def _analyze_overview(self) -> Dict[str, Any]:
        """分析网站概览"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT COUNT(*) FROM article WHERE is_published = 1")
            total_articles = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM article WHERE DATE(created_at) = CURDATE()")
            today_articles = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM article WHERE is_published = 0")
            draft_articles = cur.fetchone()[0]
            
            cur.execute("SELECT SUM(view_count) FROM article WHERE is_published = 1")
            total_views = cur.fetchone()[0] or 0
            
            cur.execute("SELECT category, COUNT(*) FROM article GROUP BY category ORDER BY COUNT(*) DESC LIMIT 5")
            top_categories = [{'category': c[0], 'count': c[1]} for c in cur.fetchall()]
            
            return {
                'overview': {
                    'total_articles': total_articles,
                    'today_articles': today_articles,
                    'draft_articles': draft_articles,
                    'total_views': total_views,
                    'top_categories': top_categories
                },
                'message': '网站分析完成'
            }
        finally:
            cur.close()
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """分析趋势"""
        trends = self.ai_system['trends'].get_category_trends(days=7)
        hot_topics = self.ai_system['trends'].get_hot_topics(days=7, top_n=10)
        
        return {
            'trends': trends,
            'hot_topics': hot_topics,
            'message': '趋势分析完成'
        }
    
    def _handle_statistics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取统计数据"""
        insights = self.ai_system['trends'].get_content_insights()
        popular_tags = self.ai_system['auto_tagger'].get_popular_tags(limit=20)
        
        return {
            'insights': insights,
            'popular_tags': popular_tags,
            'message': '统计数据获取完成'
        }
    
    def _handle_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """智能搜索"""
        query = params.get('query', '')
        if not query:
            raise ValueError("搜索查询不能为空")
        
        results = self.ai_system['search'].smart_search(query, page=1, per_page=20)
        return {
            'query': query,
            'results': results,
            'message': f'找到 {results["total"]} 个相关结果'
        }
    
    def _handle_help(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取帮助信息"""
        help_info = {
            'available_commands': [
                {'command': 'create_article', 'description': '创建新文章', 'params': ['title', 'content', 'category', 'is_published']},
                {'command': 'edit_article', 'description': '编辑现有文章', 'params': ['article_id', 'title', 'content', 'category']},
                {'command': 'publish_article', 'description': '发布文章', 'params': ['article_id']},
                {'command': 'categorize_article', 'description': '智能分类文章', 'params': ['article_id']},
                {'command': 'analyze', 'description': '分析网站状态', 'params': ['type']},
                {'command': 'statistics', 'description': '获取统计数据', 'params': []},
                {'command': 'search', 'description': '搜索文章', 'params': ['query']},
                {'command': 'auto_pilot', 'description': 'AI自动驾驶模式', 'params': ['duration']},
                {'command': 'help', 'description': '获取帮助信息', 'params': []}
            ],
            'usage_tips': [
                '可以用自然语言描述您想要的操作',
                'AI会自动理解并执行相应的命令',
                '支持的操作包括文章管理、分析、搜索等',
                '复杂任务可以分步骤执行'
            ]
        }
        
        return help_info
    
    def _handle_auto_pilot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """AI自动驾驶模式 - 自动执行优化任务"""
        duration = params.get('duration', 'quick')
        
        actions = []
        
        if duration == 'quick':
            actions.append(self._quick_optimization())
        elif duration == 'full':
            actions.append(self._quick_optimization())
            actions.append(self._analyze_all_articles())
        
        return {
            'actions': actions,
            'message': f'AI自动驾驶模式执行完成，共执行 {len(actions)} 个操作'
        }
    
    def _quick_optimization(self) -> Dict[str, Any]:
        """快速优化"""
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT id, title, content 
                FROM article 
                WHERE category = '未分类' OR category IS NULL
                LIMIT 10
            """)
            articles = cur.fetchall()
            
            results = []
            for article in articles:
                article_id, title, content = article
                try:
                    classification = self.ai_system['classifier'].classify(title, content)
                    if classification['confidence'] > 30:
                        cur.execute("""
                            UPDATE article 
                            SET category = %s, updated_at = NOW()
                            WHERE id = %s
                        """, (classification['category'], article_id))
                        results.append({
                            'article_id': article_id,
                            'title': title,
                            'category': classification['category']
                        })
                except:
                    pass
            
            conn.commit()
            
            return {
                'type': 'auto_categorization',
                'articles_processed': len(results),
                'results': results,
                'message': f'自动分类了 {len(results)} 篇未分类文章'
            }
        finally:
            cur.close()
    
    def _analyze_all_articles(self) -> Dict[str, Any]:
        """分析所有文章"""
        results = self.ai_system['analyzer'].batch_analyze(limit=50)
        return {
            'type': 'batch_analysis',
            'articles_analyzed': len(results),
            'results': results,
            'message': f'批量分析了 {len(results)} 篇文章'
        }
    
    def get_action_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取操作历史"""
        return self.action_history[-limit:]


class AICommandParser:
    """AI命令解析器 - 理解自然语言并转换为可执行命令"""
    
    def __init__(self):
        self.keywords = self._init_keywords()
        jieba.initialize()
    
    def _init_keywords(self) -> Dict[CommandType, List[str]]:
        """初始化关键词库"""
        return {
            CommandType.CREATE_ARTICLE: [
                '写文章', '发布', '创建', '新增', '写', '创作', '发表', '新建', '添加',
                '写一篇', '发布文章', 'create article', 'new article'
            ],
            CommandType.EDIT_ARTICLE: [
                '编辑', '修改', '更新', '改写', '修正', '调整', 'edit', 'update', 'modify'
            ],
            CommandType.PUBLISH_ARTICLE: [
                '发布', '上线', '公开', 'publish', 'release', '上线文章'
            ],
            CommandType.DELETE_ARTICLE: [
                '删除', '移除', '删掉', 'delete', 'remove', 'drop'
            ],
            CommandType.CATEGORIZE_ARTICLE: [
                '分类', '归类', '分类文章', 'categorize', 'classify'
            ],
            CommandType.ANALYZE: [
                '分析', '分析一下', '查看状态', '网站状态', '分析网站', 'analyze', 'status'
            ],
            CommandType.STATISTICS: [
                '统计', '数据', '报表', '查看统计', 'statistics', 'stats', 'report'
            ],
            CommandType.SEARCH: [
                '搜索', '查找', '找', '查询', 'search', 'find', 'look for'
            ],
            CommandType.AUTO_PILOT: [
                '自动', '自动驾驶', '自动模式', 'auto pilot', 'automation', '自动优化'
            ],
            CommandType.HELP: [
                '帮助', '怎么用', '命令', 'help', '帮助信息'
            ]
        }
    
    def parse(self, user_input: str) -> Dict[str, Any]:
        """解析用户输入"""
        user_input = user_input.strip()
        if not user_input:
            return {
                'command_type': CommandType.UNKNOWN,
                'params': {},
                'confidence': 0.0,
                'message': '请输入有效的命令'
            }
        
        scores = {}
        words = list(jieba.cut(user_input.lower()))
        
        for cmd_type, keywords in self.keywords.items():
            score = 0
            matched = []
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                if keyword_lower in user_input.lower():
                    score += 3
                    matched.append(keyword)
                
                if keyword_lower in [w.lower() for w in words]:
                    score += 2
                    matched.append(keyword)
            
            if score > 0:
                scores[cmd_type] = {
                    'score': score,
                    'matched_keywords': list(set(matched))
                }
        
        if not scores:
            return {
                'command_type': CommandType.UNKNOWN,
                'params': {},
                'confidence': 0.0,
                'message': '无法理解您的命令，请尝试使用更明确的描述'
            }
        
        best_cmd = max(scores.items(), key=lambda x: x[1]['score'])
        command_type = best_cmd[0]
        score_data = best_cmd[1]
        
        total_possible = 3 * len(self.keywords[command_type])
        confidence = min(score_data['score'] / total_possible, 1.0) if total_possible > 0 else 0
        
        params = self._extract_params(user_input, command_type)
        
        return {
            'command_type': command_type,
            'params': params,
            'confidence': round(confidence * 100, 1),
            'matched_keywords': score_data['matched_keywords'],
            'message': f'识别为: {command_type.value}'
        }
    
    def _extract_params(self, user_input: str, command_type: CommandType) -> Dict[str, Any]:
        """从输入中提取参数"""
        params = {}
        
        title_match = re.search(r'标题[是：:]\s*(.+?)(?:\s+|$)', user_input)
        if title_match:
            params['title'] = title_match.group(1).strip()
        
        content_match = re.search(r'内容[是：:]\s*(.+)', user_input, re.DOTALL)
        if content_match:
            params['content'] = content_match.group(1).strip()
        
        category_match = re.search(r'分类[是：:]\s*(\w+)', user_input)
        if category_match:
            params['category'] = category_match.group(1).strip()
        
        id_match = re.search(r'ID[是：:\s]*(\d+)', user_input, re.IGNORECASE)
        if id_match:
            params['article_id'] = int(id_match.group(1))
        
        query_match = re.search(r'搜索[：:]\s*(.+)', user_input)
        if query_match:
            params['query'] = query_match.group(1).strip()
        
        if '马上' in user_input or '立即' in user_input or '发布' in user_input:
            params['is_published'] = True
        
        if '完整' in user_input or '全面' in user_input:
            params['type'] = 'full'
        
        if '趋势' in user_input:
            params['type'] = 'trends'
        
        return params


class AISiteController:
    """AI网站控制器 - 整合解析和执行，提供统一接口"""
    
    def __init__(self, db, app=None):
        self.db = db
        self.parser = AICommandParser()
        self.executor = AIActionExecutor(db, app)
        self.conversation_history = []
    
    def process(self, user_input: str) -> Dict[str, Any]:
        """处理用户输入的完整流程"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        result = {
            'session_id': session_id,
            'user_input': user_input,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'steps': []
        }
        
        self.conversation_history.append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        parse_result = self.parser.parse(user_input)
        result['parse'] = parse_result
        result['steps'].append('parse')
        
        if parse_result['command_type'] == CommandType.UNKNOWN:
            result['response'] = "抱歉，我无法理解您的命令。请尝试用更明确的方式描述，或者说'帮助'查看可用命令。"
            return result
        
        if parse_result['confidence'] < 30:
            result['response'] = f"我不太确定您想要做什么（置信度: {parse_result['confidence']}%）。请尝试更明确地描述您的需求。"
            return result
        
        result['steps'].append('execute')
        execute_result = self.executor.execute(
            parse_result['command_type'],
            parse_result['params']
        )
        result['execution'] = execute_result
        
        response = self._generate_response(parse_result, execute_result)
        result['response'] = response
        
        self.conversation_history.append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        return result
    
    def _generate_response(self, parse_result: Dict[str, Any], execute_result: Dict[str, Any]) -> str:
        """生成自然语言响应"""
        if not execute_result.get('success'):
            error_msg = execute_result.get('error', '未知错误')
            return f"操作失败了: {error_msg}\n请稍后重试或检查输入是否正确。"
        
        command_type = parse_result['command_type']
        message = execute_result.get('message', '操作完成')
        
        response_parts = [f"✅ {message}"]
        
        if command_type == CommandType.CREATE_ARTICLE:
            if 'keywords' in execute_result:
                response_parts.append(f"\n🏷️ 自动生成的标签: {', '.join(execute_result['keywords'][:5])}")
            if 'article_id' in execute_result:
                response_parts.append(f"📄 文章ID: {execute_result['article_id']}")
        
        elif command_type == CommandType.ANALYZE:
            if 'overview' in execute_result:
                overview = execute_result['overview']
                response_parts.append(f"\n📊 网站概览:")
                response_parts.append(f"   • 总文章数: {overview['total_articles']}")
                response_parts.append(f"   • 今日新增: {overview['today_articles']}")
                response_parts.append(f"   • 总浏览量: {overview['total_views']}")
        
        elif command_type == CommandType.SEARCH:
            if 'results' in execute_result:
                results = execute_result['results']
                response_parts.append(f"\n🔍 找到 {results['total']} 个相关结果")
                for i, article in enumerate(results['articles'][:3], 1):
                    response_parts.append(f"   {i}. {article['title']} (相关度: {article['relevance']}%)")
        
        elif command_type == CommandType.HELP:
            if 'available_commands' in execute_result:
                response_parts = ["🤖 我可以帮您做以下事情:"]
                for cmd in execute_result['available_commands']:
                    response_parts.append(f"   • {cmd['command']} - {cmd['description']}")
        
        return '\n'.join(response_parts)
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self.conversation_history[-limit:]


def init_ai_controller(db, app=None):
    """初始化AI控制器"""
    print("\n" + "="*60)
    print("🤖 AI网站操控系统初始化")
    print("="*60)
    
    print("\n📋 系统组件:")
    print("   ✓ AICommandParser - 自然语言解析器")
    print("   ✓ AIActionExecutor - 操作执行引擎")
    print("   ✓ AISiteController - 统一控制器")
    
    controller = AISiteController(db, app)
    
    print("\n✅ AI操控系统初始化完成")
    print("="*60 + "\n")
    
    return controller


if __name__ == "__main__":
    print("🚀 AI网站操控系统测试")
    
    class MockDB:
        def __init__(self):
            import sqlite3
            self.connection = sqlite3.connect(':memory:')
            cur = self.connection.cursor()
            cur.execute("""
                CREATE TABLE article (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    content TEXT,
                    category TEXT,
                    source TEXT,
                    is_published INTEGER DEFAULT 0,
                    view_count INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            self.connection.commit()
    
    mock_db = MockDB()
    controller = init_ai_controller(mock_db)
    
    test_inputs = [
        "帮我写一篇关于AI发展的文章，标题: AI技术的未来发展趋势，内容: 人工智能正在快速发展...，分类: 智能AI",
        "分析一下网站现状",
        "搜索 人工智能",
        "帮助",
        "自动优化一下"
    ]
    
    for user_input in test_inputs:
        print(f"\n{'='*60}")
        print(f"👤 用户: {user_input}")
        result = controller.process(user_input)
        print(f"🤖 AI: {result['response']}")
