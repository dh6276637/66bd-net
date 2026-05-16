#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI功能API接口 - 为网站提供AI智能服务
"""

from flask import Blueprint, jsonify, request
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

AI_SYSTEM = None

def init_ai_system(db):
    """初始化AI系统"""
    global AI_SYSTEM
    try:
        from ai_enhance import init_ai_system
        AI_SYSTEM = init_ai_system(db)
        return True
    except ImportError:
        print("警告: AI增强模块未安装，智能功能将不可用")
        return False

def require_ai(f):
    """AI功能检查装饰器"""
    def wrapper(*args, **kwargs):
        if AI_SYSTEM is None:
            return jsonify({
                'success': False,
                'error': 'AI系统未初始化'
            }), 500
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


@ai_bp.route('/classify', methods=['POST'])
def ai_classify():
    """AI智能分类"""
    try:
        data = request.get_json()
        title = data.get('title', '')
        content = data.get('content', '')
        
        if not title:
            return jsonify({
                'success': False,
                'error': '标题不能为空'
            }), 400
        
        classifier = AI_SYSTEM['classifier']
        result = classifier.classify(title, content)
        
        return jsonify({
            'success': True,
            'result': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/analyze', methods=['POST'])
def ai_analyze():
    """AI文章分析"""
    try:
        data = request.get_json()
        article_id = data.get('article_id')
        
        if not article_id:
            return jsonify({
                'success': False,
                'error': '文章ID不能为空'
            }), 400
        
        analyzer = AI_SYSTEM['analyzer']
        result = analyzer.analyze_article(article_id)
        
        if not result:
            return jsonify({
                'success': False,
                'error': '文章不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'result': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/similar/<int:article_id>')
@require_ai
def ai_similar(article_id):
    """查找相似文章"""
    try:
        top_n = request.args.get('top_n', 5, type=int)
        
        similarity_engine = AI_SYSTEM['similarity']
        similar_articles = similarity_engine.find_similar_articles(article_id, top_n)
        
        return jsonify({
            'success': True,
            'article_id': article_id,
            'similar_articles': similar_articles
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/recommend')
@require_ai
def ai_recommend():
    """获取推荐文章"""
    try:
        article_id = request.args.get('article_id', type=int)
        top_n = request.args.get('top_n', 10, type=int)
        
        recommender = AI_SYSTEM['recommender']
        
        if article_id:
            recommendations = recommender.get_personalized_recommendations(
                article_id=article_id,
                top_n=top_n
            )
        else:
            recommendations = recommender.get_personalized_recommendations(top_n=top_n)
        
        result = []
        for article in recommendations:
            result.append({
                'id': article[0],
                'title': article[1],
                'content': article[2][:200] + '...' if article[2] and len(article[2]) > 200 else (article[2] or ''),
                'category': article[3],
                'view_count': article[4]
            })
        
        return jsonify({
            'success': True,
            'recommendations': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/search')
@require_ai
def ai_search():
    """AI智能搜索"""
    try:
        query = request.args.get('q', '')
        category = request.args.get('category', '')
        status = request.args.get('status', 'published')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if not query:
            return jsonify({
                'success': False,
                'error': '搜索关键词不能为空'
            }), 400
        
        filters = {
            'category': category if category else None,
            'status': status
        }
        
        search_engine = AI_SYSTEM['search']
        result = search_engine.smart_search(query, filters, page, per_page)
        
        return jsonify({
            'success': True,
            'result': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/trends')
@require_ai
def ai_trends():
    """获取AI趋势分析"""
    try:
        days = request.args.get('days', 30, type=int)
        
        trend_analyzer = AI_SYSTEM['trends']
        
        category_trends = trend_analyzer.get_category_trends(days)
        hot_topics = trend_analyzer.get_hot_topics(days)
        insights = trend_analyzer.get_content_insights()
        
        hot_topics_list = []
        for topic in hot_topics:
            hot_topics_list.append({
                'title': topic[0],
                'view_count': topic[1],
                'category': topic[2],
                'created_at': topic[3].strftime('%Y-%m-%d') if hasattr(topic[3], 'strftime') else str(topic[3])
            })
        
        return jsonify({
            'success': True,
            'category_trends': category_trends,
            'hot_topics': hot_topics_list,
            'insights': insights
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/auto-tags/<int:article_id>', methods=['POST'])
@require_ai
def ai_auto_tags(article_id):
    """为文章自动生成标签"""
    try:
        auto_tagger = AI_SYSTEM['auto_tagger']
        tags = auto_tagger.generate_tags_for_article(article_id)
        
        return jsonify({
            'success': True,
            'article_id': article_id,
            'tags': tags
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/tags/<int:article_id>')
@require_ai
def ai_get_tags(article_id):
    """获取文章标签"""
    try:
        auto_tagger = AI_SYSTEM['auto_tagger']
        tags = auto_tagger.get_article_tags(article_id)
        
        return jsonify({
            'success': True,
            'article_id': article_id,
            'tags': tags
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/popular-tags')
@require_ai
def ai_popular_tags():
    """获取热门标签"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        auto_tagger = AI_SYSTEM['auto_tagger']
        tags = auto_tagger.get_popular_tags(limit)
        
        return jsonify({
            'success': True,
            'popular_tags': tags
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/text/summary', methods=['POST'])
@require_ai
def ai_text_summary():
    """生成文本摘要"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        max_length = data.get('max_length', 200)
        
        if not content:
            return jsonify({
                'success': False,
                'error': '内容不能为空'
            }), 400
        
        text_processor = AI_SYSTEM['text_processor']
        summary = text_processor.generate_summary(content, max_length)
        
        return jsonify({
            'success': True,
            'summary': summary
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/text/keywords', methods=['POST'])
@require_ai
def ai_text_keywords():
    """提取关键词"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        top_k = data.get('top_k', 10)
        
        if not text:
            return jsonify({
                'success': False,
                'error': '文本不能为空'
            }), 400
        
        text_processor = AI_SYSTEM['text_processor']
        keywords = text_processor.extract_keywords(text, top_k)
        
        return jsonify({
            'success': True,
            'keywords': keywords
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/text/sentiment', methods=['POST'])
@require_ai
def ai_text_sentiment():
    """情感分析"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({
                'success': False,
                'error': '文本不能为空'
            }), 400
        
        text_processor = AI_SYSTEM['text_processor']
        sentiment = text_processor.analyze_sentiment(text)
        
        return jsonify({
            'success': True,
            'sentiment': sentiment
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/batch/analyze', methods=['POST'])
@require_ai
def ai_batch_analyze():
    """批量分析文章"""
    try:
        data = request.get_json()
        limit = data.get('limit', 100)
        
        analyzer = AI_SYSTEM['analyzer']
        results = analyzer.batch_analyze(limit)
        
        return jsonify({
            'success': True,
            'analyzed_count': len(results),
            'results': results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/status')
def ai_status():
    """AI系统状态"""
    if AI_SYSTEM is None:
        return jsonify({
            'success': False,
            'status': 'not_initialized',
            'message': 'AI系统未初始化'
        }), 500
    
    return jsonify({
        'success': True,
        'status': 'running',
        'message': 'AI系统运行正常',
        'features': {
            'classifier': '智能文章分类',
            'analyzer': '文章深度分析',
            'similarity': '相似文章推荐',
            'recommender': '个性化推荐',
            'search': '智能语义搜索',
            'trends': '趋势分析',
            'auto_tagger': '自动标签生成',
            'text_processor': '文本处理引擎'
        }
    })


def register_ai_routes(app):
    """注册AI路由"""
    app.register_blueprint(ai_bp)
    print("✅ AI API路由已注册")


if __name__ == '__main__':
    print("🚀 AI API接口测试")
    print("\n可用端点:")
    print("  POST /api/ai/classify - AI智能分类")
    print("  POST /api/ai/analyze - 文章分析")
    print("  GET  /api/ai/similar/<id> - 相似文章")
    print("  GET  /api/ai/recommend - 推荐文章")
    print("  GET  /api/ai/search - 智能搜索")
    print("  GET  /api/ai/trends - 趋势分析")
    print("  POST /api/ai/auto-tags/<id> - 自动标签")
    print("  GET  /api/ai/tags/<id> - 获取标签")
    print("  GET  /api/ai/popular-tags - 热门标签")
    print("  POST /api/ai/text/summary - 文本摘要")
    print("  POST /api/ai/text/keywords - 关键词提取")
    print("  POST /api/ai/text/sentiment - 情感分析")
    print("  POST /api/ai/batch/analyze - 批量分析")
    print("  GET  /api/ai/status - 系统状态")
