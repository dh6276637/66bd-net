#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本管理系统 - 追踪和管理项目版本变更
"""

import json
import os
from datetime import datetime
from pathlib import Path

class VersionManager:
    """版本管理器"""
    
    def __init__(self, project_root=None):
        if project_root is None:
            project_root = os.path.dirname(os.path.abspath(__file__))
        self.project_root = project_root
        self.version_file = os.path.join(project_root, 'VERSION.json')
        self.changelog_file = os.path.join(project_root, 'CHANGELOG.md')
        self.current_version = self._load_version()
    
    def _load_version(self):
        """加载版本信息"""
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._get_default_version()
        except Exception as e:
            print(f"加载版本文件失败: {e}")
            return self._get_default_version()
    
    def _get_default_version(self):
        """获取默认版本"""
        return {
            "version": "1.0.0",
            "codename": "66必读",
            "release_date": datetime.now().strftime('%Y-%m-%d'),
            "changelog": [],
            "components": {}
        }
    
    def save_version(self):
        """保存版本信息"""
        try:
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_version, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存版本文件失败: {e}")
            return False
    
    def get_current_version(self):
        """获取当前版本"""
        return self.current_version.get('version', '1.0.0')
    
    def get_full_version_info(self):
        """获取完整版本信息"""
        return {
            'version': self.current_version.get('version', '1.0.0'),
            'codename': self.current_version.get('codename', ''),
            'release_date': self.current_version.get('release_date', ''),
            'components': self.current_version.get('components', {}),
            'total_changes': sum(len(entry.get('changes', [])) for entry in self.current_version.get('changelog', []))
        }
    
    def bump_version(self, level='patch'):
        """
        升级版本号
        level: 'major'(主版本), 'minor'(次版本), 'patch'(修订版本)
        """
        version = self.current_version.get('version', '1.0.0')
        parts = version.split('.')
        
        if len(parts) != 3:
            parts = [1, 0, 0]
        else:
            parts = [int(p) for p in parts]
        
        if level == 'major':
            parts[0] += 1
            parts[1] = 0
            parts[2] = 0
        elif level == 'minor':
            parts[1] += 1
            parts[2] = 0
        else:  # patch
            parts[2] += 1
        
        new_version = '.'.join(map(str, parts))
        self.current_version['version'] = new_version
        self.current_version['release_date'] = datetime.now().strftime('%Y-%m-%d')
        
        return new_version
    
    def add_change(self, change_text, change_type='feature'):
        """
        添加变更记录
        change_type: 'feature', 'fix', 'improvement', 'breaking', 'security'
        """
        if 'changelog' not in self.current_version:
            self.current_version['changelog'] = []
        
        current_version_str = self.current_version.get('version', '1.0.0')
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        if self.current_version['changelog'] and \
           self.current_version['changelog'][0]['version'] == current_version_str:
            self.current_version['changelog'][0]['changes'].insert(0, f"[{change_type.upper()}] {change_text}")
        else:
            self.current_version['changelog'].insert(0, {
                'version': current_version_str,
                'date': today,
                'changes': [f"[{change_type.upper()}] {change_text}"]
            })
        
        if len(self.current_version['changelog']) > 50:
            self.current_version['changelog'] = self.current_version['changelog'][:50]
    
    def update_component_version(self, component_name, version):
        """更新组件版本"""
        if 'components' not in self.current_version:
            self.current_version['components'] = {}
        self.current_version['components'][component_name] = version
    
    def get_change_types(self):
        """获取变更类型统计"""
        types = {
            'feature': 0,
            'fix': 0,
            'improvement': 0,
            'breaking': 0,
            'security': 0
        }
        
        for entry in self.current_version.get('changelog', []):
            for change in entry.get('changes', []):
                for key in types.keys():
                    if f'[{key.upper()}]' in change:
                        types[key] += 1
        
        return types
    
    def generate_changelog_markdown(self):
        """生成Markdown格式的变更日志"""
        md = []
        md.append("# 66必读 变更日志\n")
        
        for entry in self.current_version.get('changelog', []):
            version = entry.get('version', '1.0.0')
            date = entry.get('date', '')
            changes = entry.get('changes', [])
            
            md.append(f"## v{version} ({date})\n")
            
            for change in changes:
                md.append(f"- {change}")
            
            md.append("")
        
        return '\n'.join(md)
    
    def save_changelog(self):
        """保存变更日志"""
        try:
            changelog_content = self.generate_changelog_markdown()
            with open(self.changelog_file, 'w', encoding='utf-8') as f:
                f.write(changelog_content)
            return True
        except Exception as e:
            print(f"保存变更日志失败: {e}")
            return False
    
    def get_release_notes(self, version=None):
        """获取指定版本的发布说明"""
        if version is None:
            version = self.get_current_version()
        
        for entry in self.current_version.get('changelog', []):
            if entry.get('version') == version:
                return {
                    'version': version,
                    'date': entry.get('date', ''),
                    'changes': entry.get('changes', [])
                }
        
        return None
    
    def compare_versions(self, version1, version2):
        """
        比较两个版本号
        返回: 1 (v1>v2), -1 (v1<v2), 0 (相等)
        """
        def parse_version(v):
            return [int(x) for x in v.split('.')]
        
        v1_parts = parse_version(version1)
        v2_parts = parse_version(version2)
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            p1 = v1_parts[i] if i < len(v1_parts) else 0
            p2 = v2_parts[i] if i < len(v2_parts) else 0
            
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        
        return 0
    
    def is_newer_version(self, new_version):
        """检查是否是新版本"""
        current = self.get_current_version()
        return self.compare_versions(new_version, current) > 0
    
    def get_version_history(self, limit=10):
        """获取版本历史"""
        changelog = self.current_version.get('changelog', [])
        return changelog[:limit]
    
    def create_release(self, release_notes='', level='patch'):
        """
        创建新版本发布
        level: 'major', 'minor', 'patch'
        """
        new_version = self.bump_version(level)
        self.add_change(release_notes, 'feature')
        self.save_version()
        self.save_changelog()
        
        return {
            'new_version': new_version,
            'level': level,
            'release_date': self.current_version['release_date']
        }


class UpdateTracker:
    """更新追踪器"""
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.table_name = 'update_records'
    
    def init_table(self):
        """初始化更新记录表"""
        if not self.db:
            return False
        
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    from_version VARCHAR(50),
                    to_version VARCHAR(50) NOT NULL,
                    update_type ENUM('auto', 'manual', 'rollback') NOT NULL,
                    files_changed TEXT,
                    status ENUM('pending', 'downloading', 'installed', 'failed', 'rolled_back') DEFAULT 'pending',
                    error_message TEXT,
                    changelog TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    INDEX idx_status (status),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()
            return True
        except Exception as e:
            print(f"初始化更新记录表失败: {e}")
            return False
        finally:
            cur.close()
    
    def record_update(self, from_version, to_version, update_type, files_changed, changelog=''):
        """记录一次更新"""
        if not self.db:
            return None
        
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            files_json = json.dumps(files_changed, ensure_ascii=False) if files_changed else '[]'
            
            cur.execute(f"""
                INSERT INTO {self.table_name} 
                (from_version, to_version, update_type, files_changed, changelog, status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
            """, (from_version, to_version, update_type, files_json, changelog))
            
            conn.commit()
            return cur.lastrowid
        
        except Exception as e:
            print(f"记录更新失败: {e}")
            return None
        finally:
            cur.close()
    
    def update_record_status(self, record_id, status, error_message=None):
        """更新记录状态"""
        if not self.db:
            return False
        
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            if status in ['installed', 'failed', 'rolled_back']:
                cur.execute(f"""
                    UPDATE {self.table_name}
                    SET status = %s, error_message = %s, completed_at = NOW()
                    WHERE id = %s
                """, (status, error_message, record_id))
            else:
                cur.execute(f"""
                    UPDATE {self.table_name}
                    SET status = %s
                    WHERE id = %s
                """, (status, record_id))
            
            conn.commit()
            return True
        
        except Exception as e:
            print(f"更新记录状态失败: {e}")
            return False
        finally:
            cur.close()
    
    def get_update_history(self, limit=20):
        """获取更新历史"""
        if not self.db:
            return []
        
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            cur.execute(f"""
                SELECT * FROM {self.table_name}
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
        
        except Exception as e:
            print(f"获取更新历史失败: {e}")
            return []
        finally:
            cur.close()
    
    def get_latest_update(self):
        """获取最新一次更新"""
        if not self.db:
            return None
        
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            cur.execute(f"""
                SELECT * FROM {self.table_name}
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
            return None
        
        except Exception as e:
            print(f"获取最新更新失败: {e}")
            return None
        finally:
            cur.close()
    
    def get_pending_updates(self):
        """获取待处理的更新"""
        if not self.db:
            return []
        
        conn = self.db.connection
        cur = conn.cursor()
        
        try:
            cur.execute(f"""
                SELECT * FROM {self.table_name}
                WHERE status = 'pending'
                ORDER BY created_at DESC
            """)
            
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
        
        except Exception as e:
            print(f"获取待处理更新失败: {e}")
            return []
        finally:
            cur.close()


def get_version_manager():
    """获取版本管理器单例"""
    if not hasattr(get_version_manager, '_instance'):
        get_version_manager._instance = VersionManager()
    return get_version_manager._instance


def record_change(change_text, change_type='feature'):
    """快捷函数：记录变更"""
    vm = get_version_manager()
    vm.add_change(change_text, change_type)
    vm.save_version()
    return vm.get_current_version()


if __name__ == '__main__':
    vm = VersionManager()
    
    print("="*60)
    print("📦 版本管理测试")
    print("="*60)
    
    print(f"\n当前版本: {vm.get_current_version()}")
    print(f"完整信息: {vm.get_full_version_info()}")
    
    print("\n📝 添加变更记录...")
    vm.add_change("新增AI智能分类功能", "feature")
    vm.add_change("修复后台登录问题", "fix")
    vm.add_change("优化移动端显示效果", "improvement")
    
    print(f"变更类型统计: {vm.get_change_types()}")
    
    print("\n📄 生成变更日志:")
    print(vm.generate_changelog_markdown()[:500])
    
    print("\n💾 保存变更日志...")
    vm.save_changelog()
    vm.save_version()
    
    print("\n✅ 版本管理测试完成")
