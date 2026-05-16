#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能自动更新系统 - 支持自动检测、备份、更新、回滚
"""

import os
import subprocess
import json
import shutil
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

class AutoUpdater:
    """自动更新管理器"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.backup_dir = os.path.join(project_root, '.backups')
        self.update_lock = threading.Lock()
        self.is_updating = False
        self.update_status = {}
        
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def check_local_changes(self) -> Tuple[bool, List[str]]:
        """检查本地是否有未提交的更改"""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            changes = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        changes.append(line.strip())
            return len(changes) > 0, changes
        except Exception as e:
            return False, []
    
    def stash_local_changes(self) -> Tuple[bool, str]:
        """暂存本地修改"""
        try:
            result = subprocess.run(
                ['git', 'stash', 'push', '-m', f'auto_stash_{datetime.now().strftime("%Y%m%d_%H%M%S")}'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout
        except Exception as e:
            return False, str(e)
    
    def pop_stashed_changes(self) -> Tuple[bool, str]:
        """恢复暂存的修改"""
        try:
            result = subprocess.run(
                ['git', 'stash', 'pop'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout
        except Exception as e:
            return False, str(e)
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """创建项目备份"""
        if not backup_name:
            backup_name = f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        exclude_dirs = ['.git', '__pycache__', '.pytest_cache', '.backups', 'node_modules']
        
        def ignore_patterns(path, names):
            ignored = []
            for name in names:
                if name in exclude_dirs:
                    ignored.append(name)
            return ignored
        
        try:
            shutil.copytree(
                self.project_root,
                backup_path,
                symlinks=True,
                ignore=ignore_patterns
            )
            return backup_path
        except Exception as e:
            return f"Backup failed: {str(e)}"
    
    def restore_from_backup(self, backup_path: str) -> Tuple[bool, str]:
        """从备份恢复"""
        try:
            if not os.path.exists(backup_path):
                return False, "Backup not found"
            
            for item in os.listdir(self.project_root):
                item_path = os.path.join(self.project_root, item)
                if item not in ['.git', '.backups']:
                    try:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    except:
                        pass
            
            for item in os.listdir(backup_path):
                src = os.path.join(backup_path, item)
                dst = os.path.join(self.project_root, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            
            return True, "Restore completed"
        except Exception as e:
            return False, f"Restore failed: {str(e)}"
    
    def get_current_commit(self) -> Optional[str]:
        """获取当前commit hash"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None
    
    def get_remote_changes(self) -> Dict[str, Any]:
        """获取远程变更信息"""
        try:
            subprocess.run(
                ['git', 'fetch', 'origin', 'master'],
                cwd=self.project_root,
                capture_output=True,
                timeout=60
            )
            
            result = subprocess.run(
                ['git', 'log', 'HEAD..origin/master', '--oneline'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            commits = []
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(' ', 1)
                        commits.append({
                            'hash': parts[0] if len(parts) > 0 else '',
                            'message': parts[1] if len(parts) > 1 else ''
                        })
            
            return {
                'has_updates': len(commits) > 0,
                'commits': commits,
                'count': len(commits)
            }
        except Exception as e:
            return {
                'has_updates': False,
                'commits': [],
                'count': 0,
                'error': str(e)
            }
    
    def perform_update(self, force: bool = False, create_backup: bool = True) -> Dict[str, Any]:
        """执行更新"""
        with self.update_lock:
            if self.is_updating:
                return {'success': False, 'message': 'Update already in progress'}
            
            self.is_updating = True
            self.update_status = {
                'status': 'starting',
                'message': '开始更新...',
                'progress': 0,
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                backup_path = None
                stashed = False
                
                if create_backup:
                    self.update_status = {
                        'status': 'backing_up',
                        'message': '创建备份...',
                        'progress': 10
                    }
                    backup_path = self.create_backup()
                    if backup_path.startswith('Backup failed'):
                        return {'success': False, 'message': backup_path}
                
                self.update_status = {
                    'status': 'checking_changes',
                    'message': '检查本地变更...',
                    'progress': 20
                }
                has_changes, changes = self.check_local_changes()
                
                if has_changes and not force:
                    self.update_status = {
                        'status': 'stashing',
                        'message': '暂存本地变更...',
                        'progress': 30
                    }
                    stashed, stash_msg = self.stash_local_changes()
                
                self.update_status = {
                    'status': 'pulling',
                    'message': '下载更新...',
                    'progress': 50
                }
                
                result = subprocess.run(
                    ['git', 'pull', '--rebase', 'origin', 'master'],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                self.update_status = {
                    'status': 'restoring',
                    'message': '恢复本地变更...',
                    'progress': 80
                }
                
                if stashed:
                    self.pop_stashed_changes()
                
                self.update_status = {
                    'status': 'complete',
                    'message': '更新完成!',
                    'progress': 100
                }
                
                self.is_updating = False
                
                return {
                    'success': result.returncode == 0,
                    'message': '更新成功' if result.returncode == 0 else '更新过程中有问题',
                    'output': result.stdout,
                    'stderr': result.stderr,
                    'backup_path': backup_path,
                    'stashed': stashed
                }
                
            except Exception as e:
                self.is_updating = False
                self.update_status = {
                    'status': 'error',
                    'message': f'更新失败: {str(e)}',
                    'progress': 0
                }
                return {
                    'success': False,
                    'message': f'更新失败: {str(e)}',
                    'error': str(e)
                }
    
    def get_update_status(self) -> Dict[str, Any]:
        """获取当前更新状态"""
        return self.update_status
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        if os.path.exists(self.backup_dir):
            for name in os.listdir(self.backup_dir):
                path = os.path.join(self.backup_dir, name)
                if os.path.isdir(path):
                    stat = os.stat(path)
                    backups.append({
                        'name': name,
                        'path': path,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'size': self._get_dir_size(path)
                    })
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def _get_dir_size(self, path: str) -> int:
        """获取目录大小"""
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.isfile(filepath):
                    total += os.path.getsize(filepath)
        return total
    
    def delete_backup(self, backup_name: str) -> Tuple[bool, str]:
        """删除备份"""
        backup_path = os.path.join(self.backup_dir, backup_name)
        if os.path.exists(backup_path):
            try:
                shutil.rmtree(backup_path)
                return True, "Backup deleted"
            except Exception as e:
                return False, str(e)
        return False, "Backup not found"


_global_updater = None

def get_auto_updater(project_root: str) -> AutoUpdater:
    """获取全局更新器实例"""
    global _global_updater
    if _global_updater is None:
        _global_updater = AutoUpdater(project_root)
    return _global_updater