#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台管理功能模块
包含：深色模式、键盘快捷键、数据导出、批量操作
"""

import json
import csv
from io import StringIO
from datetime import datetime
from flask import Response

# ==================== 深色模式功能 ====================

def init_dark_mode(app):
    """初始化深色模式功能"""
    @app.context_processor
    def inject_theme():
        return dict(current_theme='light')  # 默认浅色模式

# ==================== 键盘快捷键功能 ====================

# 快捷键映射
KEYBOARD_SHORTCUTS = {
    'global': {
        'Escape': {'action': 'close_modal', 'description': '关闭弹窗'},
        'g d': {'action': 'go_dashboard', 'description': '跳转到数据看板', 'key': 'G + D'},
        'g a': {'action': 'go_articles', 'description': '跳转到文章管理', 'key': 'G + A'},
        'g n': {'action': 'go_new_article', 'description': '跳转到发布文章', 'key': 'G + N'},
        'g c': {'action': 'go_categories', 'description': '跳转到分类管理', 'key': 'G + C'},
        'g l': {'action': 'go_logs', 'description': '跳转到操作日志', 'key': 'G + L'},
        'g s': {'action': 'go_settings', 'description': '跳转到系统设置', 'key': 'G + S'},
        '?': {'action': 'show_shortcuts', 'description': '显示快捷键帮助', 'key': '?'},
    },
    'article_list': {
        'j': {'action': 'select_next', 'description': '选择下一行'},
        'k': {'action': 'select_prev', 'description': '选择上一行'},
        'Enter': {'action': 'edit_selected', 'description': '编辑选中项'},
        'd': {'action': 'delete_selected', 'description': '删除选中项', 'confirm': True},
        'b': {'action': 'batch_select', 'description': '批量选择'},
        'e': {'action': 'export_selected', 'description': '导出选中项'},
    },
    'article_edit': {
        'Ctrl+s': {'action': 'save_article', 'description': '保存文章', 'key': 'Ctrl + S'},
        'Ctrl+d': {'action': 'draft_article', 'description': '保存草稿', 'key': 'Ctrl + D'},
        'Escape': {'action': 'cancel_edit', 'description': '取消编辑'},
    }
}

def get_shortcuts_by_context(context='global'):
    """获取指定上下文的快捷键"""
    return KEYBOARD_SHORTCUTS.get(context, {})

# ==================== 数据导出功能 ====================

def export_to_csv(data, filename=None):
    """将数据导出为CSV格式"""
    if not data:
        return None
    
    output = StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    
    # 写入表头
    if isinstance(data, list) and len(data) > 0:
        headers = data[0].keys()
        writer.writerow(headers)
        
        # 写入数据
        for row in data:
            writer.writerow(row.values())
    
    output.seek(0)
    
    # 生成文件名
    if not filename:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # 创建响应
    response = Response(output, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    
    return response

def export_to_json(data, filename=None):
    """将数据导出为JSON格式"""
    if not data:
        return None
    
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    if not filename:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    response = Response(json_str, mimetype='application/json')
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    
    return response

def export_to_excel(data, filename=None):
    """将数据导出为Excel格式"""
    if not data:
        return None
    
    if not filename:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    # 生成HTML表格作为Excel文件（XML格式）
    html = '''<?xml version="1.0" encoding="UTF-8"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
<Worksheet ss:Name="Data">
<table>
'''
    
    if isinstance(data, list) and len(data) > 0:
        # 写入表头
        html += '<Row>\n'
        for header in data[0].keys():
            html += f'<Cell><Data ss:Type="String">{header}</Data></Cell>\n'
        html += '</Row>\n'
        
        # 写入数据
        for row in data:
            html += '<Row>\n'
            for value in row.values():
                if isinstance(value, bool):
                    html += f'<Cell><Data ss:Type="String">{"是" if value else "否"}</Data></Cell>\n'
                elif isinstance(value, (int, float)):
                    html += f'<Cell><Data ss:Type="Number">{value}</Data></Cell>\n'
                else:
                    value_str = str(value) if value else ''
                    value_str = value_str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    html += f'<Cell><Data ss:Type="String">{value_str}</Data></Cell>\n'
            html += '</Row>\n'
    
    html += '''</table>
</Worksheet>
</Workbook>'''
    
    response = Response(html, mimetype='application/vnd.ms-excel')
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Type'] = 'application/vnd.ms-excel; charset=utf-8'
    
    return response

def get_export_data(db, export_type, article_ids=None):
    """获取导出数据"""
    conn = db.connection
    cur = conn.cursor()
    
    try:
        if export_type == 'articles':
            if article_ids:
                placeholders = ','.join(['%s'] * len(article_ids))
                query = f"SELECT * FROM article WHERE id IN ({placeholders})"
                cur.execute(query, article_ids)
            else:
                cur.execute("SELECT * FROM article ORDER BY created_at DESC")
        elif export_type == 'users':
            cur.execute("SELECT * FROM users ORDER BY created_at DESC")
        elif export_type == 'logs':
            cur.execute("SELECT * FROM admin_action_log ORDER BY created_at DESC")
        else:
            return None
        
        columns = [desc[0] for desc in cur.description]
        result = []
        
        for row in cur.fetchall():
            row_dict = dict(zip(columns, row))
            for key, value in row_dict.items():
                if isinstance(value, datetime):
                    row_dict[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            result.append(row_dict)
        
        return result
    
    finally:
        cur.close()

def export_data(db, export_type, export_format, article_ids=None):
    """根据格式导出数据"""
    data = get_export_data(db, export_type, article_ids)
    
    if not data:
        return None
    
    filename = f"{export_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if export_format == 'json':
        return export_to_json(data, f"{filename}.json")
    elif export_format == 'xlsx':
        return export_to_excel(data, f"{filename}.xlsx")
    else:  # csv
        return export_to_csv(data, f"{filename}.csv")

def export_articles(db, article_ids=None):
    """导出文章数据"""
    conn = db.connection
    cur = conn.cursor()
    
    try:
        if article_ids:
            placeholders = ','.join(['%s'] * len(article_ids))
            query = f"SELECT * FROM article WHERE id IN ({placeholders})"
            cur.execute(query, article_ids)
        else:
            cur.execute("SELECT * FROM article")
        
        columns = [desc[0] for desc in cur.description]
        articles = []
        
        for row in cur.fetchall():
            article_dict = dict(zip(columns, row))
            # 处理datetime对象
            for key, value in article_dict.items():
                if isinstance(value, datetime):
                    article_dict[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            articles.append(article_dict)
        
        return export_to_csv(articles, 'articles_export.csv')
    
    finally:
        cur.close()

def export_users(db):
    """导出用户数据"""
    conn = db.connection
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM users")
        
        columns = [desc[0] for desc in cur.description]
        users = []
        
        for row in cur.fetchall():
            user_dict = dict(zip(columns, row))
            for key, value in user_dict.items():
                if isinstance(value, datetime):
                    user_dict[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            users.append(user_dict)
        
        return export_to_csv(users, 'users_export.csv')
    
    finally:
        cur.close()

def export_action_logs(db):
    """导出操作日志"""
    conn = db.connection
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM admin_action_log ORDER BY created_at DESC")
        
        columns = [desc[0] for desc in cur.description]
        logs = []
        
        for row in cur.fetchall():
            log_dict = dict(zip(columns, row))
            for key, value in log_dict.items():
                if isinstance(value, datetime):
                    log_dict[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            logs.append(log_dict)
        
        return export_to_csv(logs, 'action_logs_export.csv')
    
    finally:
        cur.close()

# ==================== 批量操作功能 ====================

def batch_delete_articles(db, article_ids):
    """批量删除文章"""
    if not article_ids:
        return {'success': False, 'message': '请选择要删除的文章'}
    
    conn = db.connection
    cur = conn.cursor()
    
    try:
        placeholders = ','.join(['%s'] * len(article_ids))
        query = f"DELETE FROM article WHERE id IN ({placeholders})"
        cur.execute(query, article_ids)
        conn.commit()
        
        deleted_count = cur.rowcount
        return {
            'success': True,
            'message': f'成功删除 {deleted_count} 篇文章',
            'deleted_count': deleted_count
        }
    
    except Exception as e:
        conn.rollback()
        return {'success': False, 'message': f'删除失败: {str(e)}'}
    
    finally:
        cur.close()

def batch_update_category(db, article_ids, new_category):
    """批量更新文章分类"""
    if not article_ids:
        return {'success': False, 'message': '请选择要更新的文章'}
    
    if not new_category:
        return {'success': False, 'message': '请选择新分类'}
    
    conn = db.connection
    cur = conn.cursor()
    
    try:
        placeholders = ','.join(['%s'] * len(article_ids))
        query = f"UPDATE article SET category = %s WHERE id IN ({placeholders})"
        
        params = [new_category] + article_ids
        cur.execute(query, params)
        conn.commit()
        
        updated_count = cur.rowcount
        return {
            'success': True,
            'message': f'成功更新 {updated_count} 篇文章的分类为 "{new_category}"',
            'updated_count': updated_count
        }
    
    except Exception as e:
        conn.rollback()
        return {'success': False, 'message': f'更新失败: {str(e)}'}
    
    finally:
        cur.close()

def batch_publish_articles(db, article_ids, is_published=True):
    """批量发布/取消发布文章"""
    if not article_ids:
        return {'success': False, 'message': '请选择要操作的文章'}
    
    conn = db.connection
    cur = conn.cursor()
    
    try:
        placeholders = ','.join(['%s'] * len(article_ids))
        query = f"UPDATE article SET is_published = %s WHERE id IN ({placeholders})"
        
        params = [1 if is_published else 0] + article_ids
        cur.execute(query, params)
        conn.commit()
        
        updated_count = cur.rowcount
        action = '发布' if is_published else '取消发布'
        return {
            'success': True,
            'message': f'成功{action} {updated_count} 篇文章',
            'updated_count': updated_count
        }
    
    except Exception as e:
        conn.rollback()
        return {'success': False, 'message': f'{action}失败: {str(e)}'}
    
    finally:
        cur.close()

# ==================== 集成到Flask应用 ====================

def register_admin_features(app):
    """注册所有管理功能"""
    init_dark_mode(app)
    
    # 导出路由
    @app.route('/admin/export/<export_type>')
    @login_required
    def admin_export(export_type):
        from flask import request
        article_ids = request.args.get('ids')
        if article_ids:
            article_ids = [int(id.strip()) for id in article_ids.split(',')]
        export_format = request.args.get('format', 'csv')
        return export_data(app.config['DB'], export_type, export_format, article_ids)
    
    @app.route('/admin/export/users')
    @login_required
    def admin_export_users():
        from flask import request
        export_format = request.args.get('format', 'csv')
        return export_data(app.config['DB'], 'users', export_format)
    
    @app.route('/admin/export/logs')
    @login_required
    def admin_export_logs():
        from flask import request
        export_format = request.args.get('format', 'csv')
        return export_data(app.config['DB'], 'logs', export_format)
    
    # 批量操作路由
    @app.route('/admin/batch/delete', methods=['POST'])
    @login_required
    def admin_batch_delete():
        from flask import request, jsonify
        data = request.get_json()
        article_ids = data.get('ids', [])
        result = batch_delete_articles(app.config['DB'], article_ids)
        return jsonify(result)
    
    @app.route('/admin/batch/update-category', methods=['POST'])
    @login_required
    def admin_batch_update_category():
        from flask import request, jsonify
        data = request.get_json()
        article_ids = data.get('ids', [])
        new_category = data.get('category', '')
        result = batch_update_category(app.config['DB'], article_ids, new_category)
        return jsonify(result)
    
    @app.route('/admin/batch/publish', methods=['POST'])
    @login_required
    def admin_batch_publish():
        from flask import request, jsonify
        data = request.get_json()
        article_ids = data.get('ids', [])
        is_published = data.get('publish', True)
        result = batch_publish_articles(app.config['DB'], article_ids, is_published)
        return jsonify(result)
    
    # 快捷键帮助路由
    @app.route('/api/shortcuts')
    def api_get_shortcuts():
        from flask import request, jsonify
        context = request.args.get('context', 'global')
        shortcuts = get_shortcuts_by_context(context)
        return jsonify({'shortcuts': shortcuts, 'context': context})
    
    print("✅ 管理功能模块已注册")

# 需要导入的装饰器
try:
    from flask_login import login_required
except ImportError:
    # 如果没有flask_login，创建一个装饰器存根
    def login_required(f):
        return f
