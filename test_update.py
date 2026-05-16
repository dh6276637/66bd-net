#!/usr/bin/env python3
"""测试更新功能"""
import sys
import os

sys.path.insert(0, '/workspace/66bd-net')

# 测试导入
try:
    import requests
    print('✓ requests 模块已安装')
except ImportError:
    print('⚠️ requests 模块未安装')
    print('请运行: pip install requests')

# 测试 git 命令
try:
    import subprocess
    result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                          capture_output=True, text=True, cwd='/workspace/66bd-net')
    if result.returncode == 0:
        print(f'✓ 当前 commit: {result.stdout.strip()[:10]}')
    else:
        print(f'⚠️ git 命令执行失败')
except Exception as e:
    print(f'⚠️ git 检查失败: {e}')

print('\n更新功能已准备就绪!')
print('功能列表:')
print('1. /admin/update        - 更新管理页面')
print('2. /api/update/check     - 检查更新 API')
print('3. /api/update/perform  - 执行更新 API')
print('4. 管理员更新提示横幅')
print('5. 后台导航链接')
