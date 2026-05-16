#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量更新后台模板到新的UI系统
"""

import os
import re

# 项目根目录
PROJECT_ROOT = '/workspace/66bd-net'
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, 'templates', 'admin')

def update_template_file(filepath):
    """更新单个模板文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 1. 更新CSS引用
    if '/static/css/admin.css' in content:
        content = content.replace('/static/css/admin.css', '/static/css/admin_new.css')
        print(f"  ✓ 更新CSS引用")

    # 2. 添加响应式meta标签（如果没有）
    if 'name="viewport"' not in content:
        content = content.replace(
            '<meta charset="UTF-8">',
            '<meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">'
        )
        print(f"  ✓ 添加viewport meta标签")

    # 3. 检查是否已有移动端菜单，如果没有则添加
    if 'mobile-menu-btn' not in content:
        # 在 </head> 前添加样式
        mobile_menu_style = '''
    <style>
        /* 移动端菜单按钮（如果模板没有） */
        .mobile-menu-btn {
            display: none;
            position: fixed;
            top: 16px;
            left: 16px;
            z-index: 1001;
            width: 44px;
            height: 44px;
            background: var(--bg-card);
            border-radius: var(--radius);
            box-shadow: var(--shadow-md);
            align-items: center;
            justify-content: center;
            font-size: 20px;
            cursor: pointer;
        }

        .sidebar-overlay {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 999;
        }

        .sidebar-overlay.active {
            display: block;
        }

        @media (max-width: 768px) {
            .mobile-menu-btn {
                display: flex;
            }

            .admin-sidebar {
                transform: translateX(-100%);
            }

            .admin-sidebar.open {
                transform: translateX(0);
            }

            .admin-main {
                margin-left: 0 !important;
            }
        }
    </style>
'''
        if '</head>' in content:
            content = content.replace('</head>', mobile_menu_style + '\n</head>')
            print(f"  ✓ 添加移动端菜单样式")

    # 4. 检查是否有移动端菜单按钮HTML，如果没有则添加
    if 'mobile-menu-btn' not in content and '<body>' in content:
        mobile_menu_html = '    <button class="mobile-menu-btn" onclick="toggleSidebar()">☰</button>\n'
        content = content.replace('<body>', '<body>\n' + mobile_menu_html)
        print(f"  ✓ 添加移动端菜单按钮")

    # 5. 检查是否有侧边栏遮罩，如果没有则添加
    if 'sidebar-overlay' not in content:
        overlay_html = '    <div class="sidebar-overlay" onclick="toggleSidebar()"></div>\n'
        content = content.replace('<body>', '<body>\n' + overlay_html)
        print(f"  ✓ 添加侧边栏遮罩")

    # 6. 添加移动端菜单切换脚本
    if 'toggleSidebar' not in content:
        sidebar_script = '''
    <script>
        function toggleSidebar() {
            const sidebar = document.querySelector('.admin-sidebar');
            const overlay = document.querySelector('.sidebar-overlay');
            if (sidebar) sidebar.classList.toggle('open');
            if (overlay) overlay.classList.toggle('active');
        }

        function handleResize() {
            if (window.innerWidth > 768) {
                const sidebar = document.querySelector('.admin-sidebar');
                const overlay = document.querySelector('.sidebar-overlay');
                if (sidebar) sidebar.classList.remove('open');
                if (overlay) overlay.classList.remove('active');
            }
        }

        window.addEventListener('resize', handleResize);
        document.addEventListener('DOMContentLoaded', handleResize);
    </script>
'''
        if '</body>' in content:
            content = content.replace('</body>', sidebar_script + '\n</body>')
            print(f"  ✓ 添加移动端菜单脚本")

    # 7. 检查并添加响应式表格样式
    if 'table-responsive' not in content and '<table' in content:
        responsive_table_style = '''
    <style>
        .table-responsive {
            overflow-x: auto;
            margin: 0 -24px;
            padding: 0 24px;
        }

        @media (max-width: 768px) {
            .table-responsive {
                margin: 0 -16px;
                padding: 0 16px;
            }
        }
    </style>
'''
        if '</head>' in content:
            content = content.replace('</head>', responsive_table_style + '\n</head>')
            print(f"  ✓ 添加响应式表格样式")

        # 包裹表格
        content = re.sub(
            r'(<table[^>]*>)',
            r'<div class="table-responsive">\n            \1',
            content
        )
        content = re.sub(
            r'(</table>)',
            r'\1\n        </div>',
            content
        )
        print(f"  ✓ 包裹表格为响应式容器")

    # 8. 改进卡片样式
    if 'card mb-4' not in content and '<div class="card"' in content:
        # 改进card的margin
        content = re.sub(
            r'<div class="card">',
            r'<div class="card" style="margin-bottom: 24px;">',
            content
        )
        print(f"  ✓ 改进卡片间距")

    # 如果有修改则保存
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ 已保存更新")
        return True
    else:
        print(f"  - 无需更新")
        return False


def main():
    print("=" * 60)
    print("🚀 批量更新后台模板到新UI系统")
    print("=" * 60)

    # 获取所有模板文件
    template_files = []
    for filename in os.listdir(TEMPLATES_DIR):
        if filename.endswith('.html'):
            filepath = os.path.join(TEMPLATES_DIR, filename)
            template_files.append((filename, filepath))

    print(f"\n📁 找到 {len(template_files)} 个模板文件\n")

    updated_count = 0
    for filename, filepath in sorted(template_files):
        print(f"\n处理: {filename}")
        if update_template_file(filepath):
            updated_count += 1

    print("\n" + "=" * 60)
    print(f"✅ 更新完成! 共更新 {updated_count}/{len(template_files)} 个文件")
    print("=" * 60)

    print("\n📋 更新说明:")
    print("  1. CSS引用已更新为 admin_new.css")
    print("  2. 添加了响应式viewport标签")
    print("  3. 添加了移动端菜单按钮和遮罩")
    print("  4. 添加了移动端菜单切换脚本")
    print("  5. 表格已包裹为响应式容器")
    print("  6. 卡片间距已优化")

    print("\n⚠️  注意事项:")
    print("  - 请检查每个模板的实际效果")
    print("  - 可能需要手动调整一些细节样式")
    print("  - 建议在不同尺寸的屏幕上测试")


if __name__ == '__main__':
    main()
