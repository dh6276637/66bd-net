#!/usr/bin/env python3
import os

TEMPLATES_DIR = '/workspace/66bd-net/templates/admin'
SEARCH_PATTERN = '采集日志'
INSERT_AFTER = '''                <a href="/admin/cron-log" class="nav-item"><span class="nav-icon">📜</span><span class="nav-text">采集日志</span></a>
                <a href="/admin/update" class="nav-item"><span class="nav-icon">🔄</span><span class="nav-text">在线更新</span></a>'''

FILES_TO_UPDATE = [
    'articles.html',
    'cats.html',
    'dashboard.html',
    'edit.html',
    'article_form.html',
    'log.html',
    'settings.html',
    'monitor.html',
    'users.html',
    'action_log.html'
]

for filename in FILES_TO_UPDATE:
    filepath = os.path.join(TEMPLATES_DIR, filename)
    if not os.path.exists(filepath):
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the line with 采集日志
    if SEARCH_PATTERN in content:
        # Find the complete line
        lines = content.split('\n')
        new_lines = []
        found = False
        
        for line in lines:
            new_lines.append(line)
            
            if not found and SEARCH_PATTERN in line:
                # Insert the online update link after this line
                if 'update.html' not in filename:  # don't process the update page itself
                    new_lines.append('                <a href="/admin/update" class="nav-item"><span class="nav-icon">🔄</span><span class="nav-text">在线更新</span></a>')
                found = True
        
        new_content = '\n'.join(new_lines)
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Updated {filename}')

print('Done!')
#!/usr/bin/env python3
import os

TEMPLATES_DIR = '/workspace/66bd-net/templates/admin'
SEARCH_PATTERN = '采集日志'
INSERT_AFTER = '''                <a href="/admin/cron-log" class="nav-item"><span class="nav-icon">📜</span><span class="nav-text">采集日志</span></a>
                <a href="/admin/update" class="nav-item"><span class="nav-icon">🔄</span><span class="nav-text">在线更新</span></a>'''

FILES_TO_UPDATE = [
    'articles.html',
    'cats.html',
    'dashboard.html',
    'edit.html',
    'article_form.html',
    'log.html',
    'settings.html',
    'monitor.html',
    'users.html',
    'action_log.html'
]

for filename in FILES_TO_UPDATE:
    filepath = os.path.join(TEMPLATES_DIR, filename)
    if not os.path.exists(filepath):
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the line with 采集日志
    if SEARCH_PATTERN in content:
        # Find the complete line
        lines = content.split('\n')
        new_lines = []
        found = False
        
        for line in lines:
            new_lines.append(line)
            
            if not found and SEARCH_PATTERN in line:
                # Insert the online update link after this line
                if 'update.html' not in filename:  # don't process the update page itself
                    new_lines.append('                <a href="/admin/update" class="nav-item"><span class="nav-icon">🔄</span><span class="nav-text">在线更新</span></a>')
                found = True
        
        new_content = '\n'.join(new_lines)
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Updated {filename}')

print('Done!')
