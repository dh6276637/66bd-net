#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新管理API接口 - 版本管理和自动更新
"""

from flask import Blueprint, jsonify, request, Response
import json
import os
import sys
from datetime import datetime

update_bp = Blueprint('update', __name__, url_prefix='/api')

UPDATE_MANAGER = None
VERSION_MANAGER = None

def init_update_system(project_root=None):
    """初始化更新系统"""
    global UPDATE_MANAGER, VERSION_MANAGER
    
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        
        from version_manager import VersionManager, UpdateTracker
        from auto_updater import create_auto_updater
        
        VERSION_MANAGER = VersionManager(project_root)
        
        class DBWrapper:
            def __init__(self):
                self.connection = None
                self.config = {}
        
        db_wrapper = DBWrapper()
        tracker = UpdateTracker(db_wrapper)
        
        UPDATE_MANAGER = create_auto_updater(
            repo_owner='dh6276637',
            repo_name='66bd-net',
            token=None
        )
        
        print("\n" + "="*60)
        print("📦 版本管理与自动更新系统已初始化")
        print("="*60)
        print(f"当前版本: {VERSION_MANAGER.get_current_version()}")
        print("="*60 + "\n")
        
        return True
    except Exception as e:
        print(f"\n⚠️  更新系统初始化失败: {e}\n")
        return False

def require_update_manager(f):
    """更新管理器检查装饰器"""
    def wrapper(*args, **kwargs):
        if UPDATE_MANAGER is None:
            return jsonify({
                'success': False,
                'error': '更新系统未初始化'
            }), 500
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


@update_bp.route('/version', methods=['GET'])
def get_version():
    """获取版本信息"""
    try:
        if VERSION_MANAGER is None:
            return jsonify({
                'success': False,
                'error': '版本系统未初始化'
            }), 500
        
        version_info = VERSION_MANAGER.get_full_version_info()
        
        current_sha = None
        try:
            import subprocess
            result = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                text=True,
                stderr=subprocess.DEVNULL
            )
            current_sha = result.strip()
        except:
            pass
        
        return jsonify({
            'success': True,
            'version': version_info['version'],
            'codename': version_info['codename'],
            'release_date': version_info['release_date'],
            'build_sha': current_sha,
            'components': version_info['components']
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@update_bp.route('/version/changelog', methods=['GET'])
def get_changelog():
    """获取变更日志"""
    try:
        if VERSION_MANAGER is None:
            return jsonify({
                'success': False,
                'error': '版本系统未初始化'
            }), 500
        
        limit = request.args.get('limit', 10, type=int)
        history = VERSION_MANAGER.get_version_history(limit)
        
        return jsonify({
            'success': True,
            'changelog': history
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@update_bp.route('/version/bump', methods=['POST'])
@require_update_manager
def bump_version():
    """升级版本号"""
    try:
        data = request.get_json() or {}
        level = data.get('level', 'patch')
        change_text = data.get('change', '版本更新')
        change_type = data.get('type', 'feature')
        
        if level not in ['major', 'minor', 'patch']:
            return jsonify({
                'success': False,
                'error': '无效的版本级别'
            }), 400
        
        new_version = VERSION_MANAGER.bump_version(level)
        VERSION_MANAGER.add_change(change_text, change_type)
        VERSION_MANAGER.save_version()
        VERSION_MANAGER.save_changelog()
        
        return jsonify({
            'success': True,
            'old_version': VERSION_MANAGER.get_current_version(),
            'new_version': new_version,
            'change': change_text,
            'change_type': change_type
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@update_bp.route('/update/check', methods=['GET'])
@require_update_manager
def check_updates():
    """检查更新"""
    try:
        result = UPDATE_MANAGER.check_for_updates()
        
        return jsonify({
            'success': True,
            'has_update': result.get('has_update', False),
            'current_version': result.get('current_version'),
            'latest_version': result.get('latest_version'),
            'comparison': result.get('comparison'),
            'message': result.get('message', ''),
            'error': result.get('error')
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@update_bp.route('/update/perform', methods=['POST'])
@require_update_manager
def perform_update():
    """执行更新"""
    try:
        data = request.get_json() or {}
        create_backup = data.get('create_backup', True)
        
        check_result = UPDATE_MANAGER.check_for_updates()
        
        if not check_result.get('has_update', False):
            return jsonify({
                'success': True,
                'message': '已是最新版本，无需更新',
                'updated': False
            })
        
        result = UPDATE_MANAGER.perform_update(create_backup=create_backup)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result.get('message', '更新成功'),
                'updated': True,
                'steps': result.get('steps', []),
                'new_version': result.get('new_version')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', '更新失败'),
                'steps': result.get('steps', [])
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@update_bp.route('/update/backup', methods=['POST'])
@require_update_manager
def create_backup():
    """创建备份"""
    try:
        result = UPDATE_MANAGER.create_backup()
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': '备份创建成功',
                'backup_path': result.get('backup_path'),
                'timestamp': result.get('timestamp')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', '备份失败')
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@update_bp.route('/update/rollback', methods=['POST'])
@require_update_manager
def rollback():
    """回滚"""
    try:
        data = request.get_json() or {}
        backup_name = data.get('backup_name')
        
        result = UPDATE_MANAGER.rollback(backup_name)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result.get('message', '回滚成功'),
                'backup_path': result.get('backup_path'),
                'restored_files': result.get('restored_files', 0)
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', '回滚失败')
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@update_bp.route('/update/backups', methods=['GET'])
@require_update_manager
def list_backups():
    """列出备份"""
    try:
        backups = UPDATE_MANAGER.list_backups()
        
        return jsonify({
            'success': True,
            'backups': backups
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@update_bp.route('/update/stats', methods=['GET'])
def get_update_stats():
    """获取更新统计"""
    try:
        stats = {
            'total_updates': 0,
            'auto_updates': 0,
            'manual_updates': 0,
            'total_backups': 0
        }
        
        if UPDATE_MANAGER:
            backups = UPDATE_MANAGER.list_backups()
            stats['total_backups'] = len(backups)
        
        if VERSION_MANAGER:
            history = VERSION_MANAGER.get_version_history(100)
            stats['total_updates'] = len(history)
        
        return jsonify({
            'success': True,
            **stats
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@update_bp.route('/update/history', methods=['GET'])
def get_update_history():
    """获取更新历史"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        history = []
        if VERSION_MANAGER:
            version_history = VERSION_MANAGER.get_version_history(limit)
            for entry in version_history:
                history.append({
                    'version': entry.get('version'),
                    'date': entry.get('date'),
                    'changes': entry.get('changes', []),
                    'type': 'version_bump'
                })
        
        return jsonify({
            'success': True,
            'history': history
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@update_bp.route('/update/record-change', methods=['POST'])
@require_update_manager
def record_change():
    """记录变更"""
    try:
        data = request.get_json() or {}
        change_text = data.get('change', '系统更新')
        change_type = data.get('type', 'feature')
        
        VERSION_MANAGER.add_change(change_text, change_type)
        VERSION_MANAGER.save_version()
        
        return jsonify({
            'success': True,
            'version': VERSION_MANAGER.get_current_version(),
            'change': change_text,
            'change_type': change_type
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def register_update_routes(app):
    """注册更新路由"""
    app.register_blueprint(update_bp)
    print("✅ 更新管理API路由已注册")


if __name__ == '__main__':
    print("🚀 更新管理API测试")
    print("\n可用端点:")
    print("  GET  /api/version - 获取版本信息")
    print("  GET  /api/version/changelog - 获取变更日志")
    print("  POST /api/version/bump - 升级版本号")
    print("  GET  /api/update/check - 检查更新")
    print("  POST /api/update/perform - 执行更新")
    print("  POST /api/update/backup - 创建备份")
    print("  POST /api/update/rollback - 回滚")
    print("  GET  /api/update/backups - 列出备份")
    print("  GET  /api/update/stats - 获取统计")
    print("  GET  /api/update/history - 获取历史")
    print("  POST /api/update/record-change - 记录变更")
