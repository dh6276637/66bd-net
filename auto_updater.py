#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动更新系统 - 智能检测和应用GitHub更新
"""

import os
import re
import json
import time
import shutil
import hashlib
import zipfile
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

try:
    import github
    from github import Github
except ImportError:
    github = None


class GitHubUpdateChecker:
    """GitHub更新检查器"""
    
    def __init__(self, repo_owner, repo_name, branch='master', token=None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch
        self.token = token
        self.api_base = f'https://api.github.com/repos/{repo_owner}/{repo_name}'
        
        self.session = requests.Session() if requests else None
        if token:
            self.session.headers.update({'Authorization': f'token {token}'})
    
    def get_latest_commit(self):
        """获取最新提交信息"""
        try:
            if github and self.token:
                g = Github(self.token)
                repo = g.get_repo(f"{self.repo_owner}/{self.repo_name}")
                commit = repo.get_commit(sha=self.branch)
                return {
                    'sha': commit.sha,
                    'message': commit.commit.message,
                    'date': commit.commit.author.date.strftime('%Y-%m-%d %H:%M:%S'),
                    'author': commit.commit.author.name,
                    'url': commit.html_url
                }
            elif self.session:
                response = self.session.get(
                    f"{self.api_base}/commits/{self.branch}",
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'sha': data['sha'],
                        'message': data['commit']['message'],
                        'date': data['commit']['author']['date'],
                        'author': data['commit']['author']['name'],
                        'url': data['html_url']
                    }
        except Exception as e:
            print(f"获取最新提交失败: {e}")
        return None
    
    def get_file_content(self, file_path):
        """获取文件内容"""
        try:
            if github and self.token:
                g = Github(self.token)
                repo = g.get_repo(f"{self.repo_owner}/{self.repo_name}")
                contents = repo.get_contents(file_path, ref=self.branch)
                return contents.decoded_content.decode('utf-8')
            elif self.session:
                url = f"{self.api_base}/contents/{file_path}?ref={self.branch}"
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    import base64
                    data = response.json()
                    return base64.b64decode(data['content']).decode('utf-8')
        except Exception as e:
            print(f"获取文件 {file_path} 失败: {e}")
        return None
    
    def get_file_list(self):
        """获取文件列表"""
        try:
            if github and self.token:
                g = Github(self.token)
                repo = g.get_repo(f"{self.repo_owner}/{self.repo_name}")
                contents = repo.get_contents("", ref=self.branch)
                return [{'path': c.path, 'type': c.type} for c in contents]
            elif self.session:
                response = self.session.get(
                    f"{self.api_base}/contents?ref={self.branch}",
                    timeout=10
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"获取文件列表失败: {e}")
        return []
    
    def compare_commits(self, base_sha, head_sha):
        """比较两个提交之间的差异"""
        try:
            if github and self.token:
                g = Github(self.token)
                repo = g.get_repo(f"{self.repo_owner}/{self.repo_name}")
                comparison = repo.compare(base_sha, head_sha)
                return {
                    'ahead_by': comparison.ahead_by,
                    'behind_by': comparison.behind_by,
                    'total_changes': len(comparison.commits),
                    'files_changed': [f.filename for f in comparison.files],
                    'commits': [{
                        'sha': c.sha,
                        'message': c.commit.message,
                        'author': c.commit.author.name
                    } for c in comparison.commits]
                }
            elif self.session:
                url = f"{self.api_base}/compare/{base_sha}...{head_sha}"
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'ahead_by': data.get('ahead_by', 0),
                        'behind_by': data.get('behind_by', 0),
                        'total_changes': len(data.get('commits', [])),
                        'files_changed': [f['filename'] for f in data.get('files', [])],
                        'commits': [{
                            'sha': c['sha'],
                            'message': c['commit']['message'],
                            'author': c['commit']['author']['name']
                        } for c in data.get('commits', [])[:10]]
                    }
        except Exception as e:
            print(f"比较提交失败: {e}")
        return None


class AutoUpdater:
    """自动更新器"""
    
    def __init__(self, project_root=None, github_checker=None):
        if project_root is None:
            project_root = os.path.dirname(os.path.abspath(__file__))
        
        self.project_root = project_root
        self.backup_dir = os.path.join(project_root, '.backups')
        self.temp_dir = os.path.join(project_root, '.temp_updates')
        
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.github_checker = github_checker
        self.current_sha = self._get_current_sha()
    
    def _get_current_sha(self):
        """获取当前版本的SHA"""
        try:
            result = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.project_root,
                text=True,
                stderr=subprocess.DEVNULL
            )
            return result.strip()
        except:
            return None
    
    def check_for_updates(self):
        """检查更新"""
        if not self.github_checker:
            return {
                'has_update': False,
                'error': 'GitHub检查器未初始化'
            }
        
        latest = self.github_checker.get_latest_commit()
        if not latest:
            return {
                'has_update': False,
                'error': '无法获取GitHub最新提交'
            }
        
        current_sha = self.current_sha
        if not current_sha:
            return {
                'has_update': True,
                'latest_version': latest,
                'error': '无法获取本地版本'
            }
        
        if current_sha == latest['sha']:
            return {
                'has_update': False,
                'current_version': current_sha,
                'latest_version': latest,
                'message': '已是最新版本'
            }
        
        comparison = self.github_checker.compare_commits(current_sha, latest['sha'])
        
        return {
            'has_update': True,
            'current_version': current_sha,
            'latest_version': latest,
            'comparison': comparison
        }
    
    def create_backup(self):
        """创建备份"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            os.makedirs(backup_path, exist_ok=True)
            
            git_dir = os.path.join(self.project_root, '.git')
            
            for item in os.listdir(self.project_root):
                if item.startswith('.') and item not in ['.gitignore']:
                    continue
                
                item_path = os.path.join(self.project_root, item)
                
                if os.path.isfile(item_path):
                    shutil.copy2(item_path, os.path.join(backup_path, item))
                elif os.path.isdir(item_path) and item not in ['.git', 'venv', '__pycache__', 'node_modules', '.backups', '.temp_updates']:
                    dest_dir = os.path.join(backup_path, item)
                    shutil.copytree(item_path, dest_dir, 
                                 ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', 'venv', 'node_modules'))
            
            manifest = {
                'timestamp': timestamp,
                'git_sha': self.current_sha,
                'backup_path': backup_path
            }
            
            with open(os.path.join(backup_path, 'manifest.json'), 'w') as f:
                json.dump(manifest, f, indent=2)
            
            return {
                'success': True,
                'backup_path': backup_path,
                'timestamp': timestamp
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_update(self, latest_sha):
        """下载更新"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            update_dir = os.path.join(self.temp_dir, f"update_{timestamp}")
            os.makedirs(update_dir, exist_ok=True)
            
            url = f"https://github.com/{self.github_checker.repo_owner}/{self.github_checker.repo_name}/archive/{latest_sha}.zip"
            
            response = requests.get(url, timeout=60, stream=True)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'下载失败: HTTP {response.status_code}'
                }
            
            zip_path = os.path.join(update_dir, 'update.zip')
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            extract_dir = os.path.join(update_dir, 'extracted')
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            extracted_items = os.listdir(extract_dir)
            if len(extracted_items) == 1:
                source_dir = os.path.join(extract_dir, extracted_items[0])
            else:
                source_dir = extract_dir
            
            return {
                'success': True,
                'update_dir': source_dir,
                'timestamp': timestamp
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def apply_update(self, update_dir, files_to_update=None):
        """应用更新"""
        try:
            if files_to_update is None:
                files_to_update = []
                for root, dirs, files in os.walk(update_dir):
                    dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', 'node_modules']]
                    for file in files:
                        if not file.startswith('.'):
                            rel_path = os.path.relpath(os.path.join(root, file), update_dir)
                            files_to_update.append(rel_path)
            
            updated_files = []
            skipped_files = []
            
            for file_path in files_to_update:
                src_path = os.path.join(update_dir, file_path)
                dest_path = os.path.join(self.project_root, file_path)
                
                if not os.path.exists(src_path):
                    continue
                
                dest_dir = os.path.dirname(dest_path)
                os.makedirs(dest_dir, exist_ok=True)
                
                try:
                    shutil.copy2(src_path, dest_path)
                    updated_files.append(file_path)
                except Exception as e:
                    skipped_files.append({
                        'file': file_path,
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'updated_files': updated_files,
                'skipped_files': skipped_files,
                'total_updated': len(updated_files),
                'total_skipped': len(skipped_files)
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def perform_update(self, create_backup=True):
        """执行完整更新流程"""
        result = {
            'success': False,
            'steps': []
        }
        
        print("\n" + "="*60)
        print("🚀 开始自动更新")
        print("="*60)
        
        print("\n📋 步骤1: 检查更新...")
        check_result = self.check_for_updates()
        result['steps'].append({
            'step': 'check',
            'result': check_result
        })
        
        if not check_result['has_update']:
            result['success'] = True
            result['message'] = '已是最新版本，无需更新'
            print("✅ 已是最新版本")
            return result
        
        latest = check_result['latest_version']
        print(f"   发现新版本: {latest['sha'][:8]}")
        print(f"   提交信息: {latest['message'][:50]}...")
        
        if create_backup:
            print("\n📦 步骤2: 创建备份...")
            backup_result = self.create_backup()
            result['steps'].append({
                'step': 'backup',
                'result': backup_result
            })
            
            if backup_result['success']:
                print(f"   ✅ 备份已创建: {backup_result['backup_path']}")
            else:
                print(f"   ⚠️  备份失败: {backup_result.get('error', '未知错误')}")
                print("   继续更新...")
        else:
            print("\n⏭️  步骤2: 跳过备份（已禁用）")
        
        print("\n📥 步骤3: 下载更新...")
        download_result = self.download_update(latest['sha'])
        result['steps'].append({
            'step': 'download',
            'result': download_result
        })
        
        if not download_result['success']:
            result['error'] = f"下载失败: {download_result.get('error')}"
            print(f"   ❌ 下载失败: {download_result.get('error')}")
            return result
        
        print(f"   ✅ 更新包已下载")
        
        print("\n📝 步骤4: 应用更新...")
        apply_result = self.apply_update(download_result['update_dir'])
        result['steps'].append({
            'step': 'apply',
            'result': apply_result
        })
        
        if apply_result['success']:
            print(f"   ✅ 已更新 {apply_result['total_updated']} 个文件")
            if apply_result.get('skipped_files'):
                print(f"   ⚠️  跳过 {apply_result['total_skipped']} 个文件")
        else:
            result['error'] = f"应用更新失败: {apply_result.get('error')}"
            print(f"   ❌ 应用更新失败: {apply_result.get('error')}")
            return result
        
        print("\n🔄 步骤5: 更新版本信息...")
        try:
            new_sha = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.project_root,
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()
            
            result['new_version'] = new_sha
            print(f"   ✅ 版本已更新: {new_sha[:8]}")
        except:
            print("   ⚠️  无法获取新版本信息")
        
        result['success'] = True
        result['message'] = f"成功更新到版本 {latest['sha'][:8]}"
        
        print("\n" + "="*60)
        print("✅ 自动更新完成!")
        print("="*60 + "\n")
        
        return result
    
    def rollback(self, backup_path=None):
        """回滚到指定备份"""
        try:
            if backup_path is None:
                backups = self.list_backups()
                if backups:
                    backup_path = backups[0]['path']
                else:
                    return {
                        'success': False,
                        'error': '没有可用的备份'
                    }
            
            if not os.path.exists(backup_path):
                return {
                    'success': False,
                    'error': f'备份不存在: {backup_path}'
                }
            
            manifest_path = os.path.join(backup_path, 'manifest.json')
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
            else:
                manifest = {'path': backup_path}
            
            current_sha = self.current_sha
            backup_sha = manifest.get('git_sha', 'unknown')
            
            backup_files = []
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    if file == 'manifest.json':
                        continue
                    rel_path = os.path.relpath(os.path.join(root, file), backup_path)
                    backup_files.append(rel_path)
            
            restored_count = 0
            for file_path in backup_files:
                src_path = os.path.join(backup_path, file_path)
                dest_path = os.path.join(self.project_root, file_path)
                dest_dir = os.path.dirname(dest_path)
                
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copy2(src_path, dest_path)
                restored_count += 1
            
            return {
                'success': True,
                'backup_path': backup_path,
                'from_sha': current_sha,
                'to_sha': backup_sha,
                'restored_files': restored_count,
                'message': f'成功回滚到 {backup_sha[:8]}，恢复了 {restored_count} 个文件'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_backups(self):
        """列出所有备份"""
        try:
            backups = []
            
            if not os.path.exists(self.backup_dir):
                return backups
            
            for item in os.listdir(self.backup_dir):
                item_path = os.path.join(self.backup_dir, item)
                
                if os.path.isdir(item_path):
                    manifest_path = os.path.join(item_path, 'manifest.json')
                    
                    if os.path.exists(manifest_path):
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                        backups.append({
                            'name': item,
                            'path': item_path,
                            'timestamp': manifest.get('timestamp'),
                            'git_sha': manifest.get('git_sha'),
                            'created_at': datetime.fromtimestamp(
                                os.path.getctime(item_path)
                            ).strftime('%Y-%m-%d %H:%M:%S')
                        })
                    else:
                        backups.append({
                            'name': item,
                            'path': item_path,
                            'timestamp': None,
                            'git_sha': None,
                            'created_at': datetime.fromtimestamp(
                                os.path.getctime(item_path)
                            ).strftime('%Y-%m-%d %H:%M:%S')
                        })
            
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            return backups
        
        except Exception as e:
            print(f"列出备份失败: {e}")
            return []
    
    def cleanup_old_backups(self, keep_count=5):
        """清理旧备份"""
        try:
            backups = self.list_backups()
            
            if len(backups) <= keep_count:
                return {
                    'success': True,
                    'deleted': 0,
                    'message': f'备份数量({len(backups)})未超过保留数量({keep_count})'
                }
            
            to_delete = backups[keep_count:]
            deleted_count = 0
            
            for backup in to_delete:
                try:
                    shutil.rmtree(backup['path'])
                    deleted_count += 1
                except Exception as e:
                    print(f"删除备份失败 {backup['path']}: {e}")
            
            return {
                'success': True,
                'deleted': deleted_count,
                'kept': keep_count,
                'message': f'已删除 {deleted_count} 个旧备份，保留最近 {keep_count} 个'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


def create_auto_updater(repo_owner='dh6276637', repo_name='66bd-net', token=None):
    """创建自动更新器"""
    github_checker = GitHubUpdateChecker(repo_owner, repo_name, token=token)
    return AutoUpdater(github_checker=github_checker)


if __name__ == '__main__':
    print("="*60)
    print("🔄 自动更新系统测试")
    print("="*60)
    
    updater = create_auto_updater()
    
    print("\n📋 检查更新...")
    check_result = updater.check_for_updates()
    
    if check_result['has_update']:
        print(f"\n🎉 发现新版本!")
        print(f"   最新提交: {check_result['latest_version']['sha'][:8]}")
        print(f"   提交信息: {check_result['latest_version']['message'][:80]}")
        
        if 'comparison' in check_result and check_result['comparison']:
            comp = check_result['comparison']
            print(f"   变更文件: {comp.get('total_changes', 0)} 个")
            print(f"   新提交: {comp.get('ahead_by', 0)} 个")
    else:
        print("\n✅ 已是最新版本")
    
    print("\n📦 备份列表:")
    backups = updater.list_backups()
    for i, backup in enumerate(backups[:5], 1):
        print(f"   {i}. {backup['created_at']} - {backup.get('git_sha', 'N/A')[:8]}")
    
    print("\n" + "="*60)
