// ===== 66必读后台管理功能 =====
// 包含：深色模式、键盘快捷键、批量操作

(function() {
    'use strict';

    // ==================== 深色模式切换 ====================
    const ThemeManager = {
        STORAGE_KEY: 'admin_theme',
        THEME_ATTR: 'data-theme',
        
        init() {
            this.loadTheme();
            this.createToggleButton();
        },
        
        loadTheme() {
            const savedTheme = localStorage.getItem(this.STORAGE_KEY);
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            const theme = savedTheme || (prefersDark ? 'dark' : 'light');
            this.setTheme(theme);
        },
        
        setTheme(theme) {
            document.documentElement.setAttribute(this.THEME_ATTR, theme);
            localStorage.setItem(this.STORAGE_KEY, theme);
            this.updateToggleButton(theme);
        },
        
        toggleTheme() {
            const currentTheme = document.documentElement.getAttribute(this.THEME_ATTR);
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            this.setTheme(newTheme);
        },
        
        createToggleButton() {
            // 在头部右侧添加切换按钮
            const headerRight = document.querySelector('.header-right');
            if (!headerRight) return;
            
            const toggleBtn = document.createElement('button');
            toggleBtn.className = 'btn btn-icon theme-toggle-btn';
            toggleBtn.style.marginRight = '8px';
            toggleBtn.style.fontSize = '18px';
            toggleBtn.title = '切换深色模式';
            toggleBtn.addEventListener('click', () => this.toggleTheme());
            
            headerRight.insertBefore(toggleBtn, headerRight.firstChild);
            this.updateToggleButton(this.getCurrentTheme());
        },
        
        updateToggleButton(theme) {
            const toggleBtn = document.querySelector('.theme-toggle-btn');
            if (!toggleBtn) return;
            
            toggleBtn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
            toggleBtn.title = theme === 'dark' ? '切换到浅色模式' : '切换到深色模式';
        },
        
        getCurrentTheme() {
            return document.documentElement.getAttribute(this.THEME_ATTR) || 'light';
        }
    };

    // ==================== 键盘快捷键系统 ====================
    const ShortcutManager = {
        SHORTCUTS: {
            global: {
                'Escape': { action: 'closeModal', desc: '关闭弹窗' },
                'g': { action: 'startGNavigation', desc: '开始全局导航', isPrefix: true },
                'g d': { action: 'navigateTo', url: '/admin/', desc: '数据看板' },
                'g a': { action: 'navigateTo', url: '/admin/articles', desc: '文章管理' },
                'g n': { action: 'navigateTo', url: '/admin/articles/new', desc: '发布文章' },
                'g c': { action: 'navigateTo', url: '/admin/categories', desc: '分类管理' },
                'g l': { action: 'navigateTo', url: '/admin/action-log', desc: '操作日志' },
                'g s': { action: 'navigateTo', url: '/admin/settings', desc: '系统设置' },
                '?': { action: 'showHelp', desc: '显示快捷键帮助' },
                'Ctrl+s': { action: 'saveForm', desc: '保存表单' },
            },
            articleList: {
                'j': { action: 'selectNext', desc: '选择下一行' },
                'k': { action: 'selectPrev', desc: '选择上一行' },
                'Enter': { action: 'editSelected', desc: '编辑选中项' },
                'd': { action: 'deleteSelected', desc: '删除选中项', confirm: true },
                'b': { action: 'toggleBatch', desc: '批量选择' },
                'e': { action: 'exportSelected', desc: '导出选中项' },
            },
            articleEdit: {
                'Ctrl+s': { action: 'submitForm', desc: '保存文章' },
                'Ctrl+d': { action: 'saveDraft', desc: '保存草稿' },
                'Escape': { action: 'cancelEdit', desc: '取消编辑' },
            }
        },
        
        activeContext: 'global',
        pendingKey: null,
        helpModal: null,
        
        init() {
            this.bindEvents();
            this.createHelpModal();
            this.detectContext();
        },
        
        bindEvents() {
            document.addEventListener('keydown', (e) => this.handleKeydown(e));
        },
        
        handleKeydown(e) {
            // 忽略输入框内的按键
            const activeEl = document.activeElement;
            if (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA' || activeEl.isContentEditable) {
                return;
            }
            
            const key = this.getKeyString(e);
            
            // 处理组合键
            if (this.pendingKey) {
                const combo = this.pendingKey + ' ' + key;
                if (this.executeShortcut(combo)) {
                    this.pendingKey = null;
                    return;
                }
                this.pendingKey = null;
            }
            
            // 检查当前上下文的快捷键
            const contextKeys = this.SHORTCUTS[this.activeContext] || {};
            
            // 检查全局快捷键
            const globalKeys = this.SHORTCUTS.global || {};
            
            // 先检查上下文快捷键，再检查全局快捷键
            if (contextKeys[key] && this.executeShortcut(key, this.activeContext)) {
                e.preventDefault();
                return;
            }
            
            if (globalKeys[key]) {
                if (globalKeys[key].isPrefix) {
                    this.pendingKey = key;
                    setTimeout(() => { this.pendingKey = null; }, 2000);
                } else if (this.executeShortcut(key, 'global')) {
                    e.preventDefault();
                }
            }
        },
        
        getKeyString(e) {
            const parts = [];
            if (e.ctrlKey || e.metaKey) parts.push('Ctrl');
            if (e.shiftKey) parts.push('Shift');
            if (e.altKey) parts.push('Alt');
            
            const key = e.key;
            if (!['Control', 'Shift', 'Alt', 'Meta'].includes(key)) {
                parts.push(key);
            }
            
            return parts.join('+');
        },
        
        executeShortcut(key, context = 'global') {
            const shortcuts = this.SHORTCUTS[context] || {};
            const shortcut = shortcuts[key];
            
            if (!shortcut) return false;
            
            switch (shortcut.action) {
                case 'navigateTo':
                    window.location.href = shortcut.url;
                    break;
                case 'closeModal':
                    this.closeAllModals();
                    break;
                case 'showHelp':
                    this.showHelp();
                    break;
                case 'saveForm':
                    this.saveCurrentForm();
                    break;
                case 'selectNext':
                    this.selectTableRow(1);
                    break;
                case 'selectPrev':
                    this.selectTableRow(-1);
                    break;
                case 'editSelected':
                    this.editSelectedRow();
                    break;
                case 'deleteSelected':
                    this.deleteSelectedRow();
                    break;
                case 'toggleBatch':
                    this.toggleBatchSelection();
                    break;
                case 'exportSelected':
                    this.exportSelected();
                    break;
                case 'submitForm':
                    this.submitForm('publish');
                    break;
                case 'saveDraft':
                    this.submitForm('draft');
                    break;
                case 'cancelEdit':
                    if (confirm('确定要放弃编辑吗？')) {
                        window.history.back();
                    }
                    break;
                default:
                    return false;
            }
            
            return true;
        },
        
        detectContext() {
            const path = window.location.pathname;
            if (path.includes('/admin/articles') && !path.includes('/new')) {
                this.activeContext = 'articleList';
            } else if (path.includes('/admin/articles/') || path.includes('/admin/articles/new')) {
                this.activeContext = 'articleEdit';
            } else {
                this.activeContext = 'global';
            }
        },
        
        createHelpModal() {
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.innerHTML = `
                <div class="modal" style="max-width: 600px;">
                    <div class="modal-header">
                        <div class="modal-title">⌨️ 键盘快捷键</div>
                        <button class="modal-close" onclick="ShortcutManager.hideHelp()">✕</button>
                    </div>
                    <div class="modal-body" style="max-height: 60vh;">
                        <div id="shortcuts-content"></div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="ShortcutManager.hideHelp()">关闭</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            this.helpModal = modal;
        },
        
        showHelp() {
            const content = document.getElementById('shortcuts-content');
            if (!content) return;
            
            let html = '';
            
            // 全局快捷键
            html += '<h3 style="margin-bottom: 16px; color: var(--text-primary);">全局快捷键</h3>';
            html += '<div style="display: grid; gap: 8px; margin-bottom: 24px;">';
            this.addShortcutsToHelp(html, this.SHORTCUTS.global);
            html += '</div>';
            
            // 文章列表快捷键
            html += '<h3 style="margin-bottom: 16px; color: var(--text-primary);">文章列表</h3>';
            html += '<div style="display: grid; gap: 8px; margin-bottom: 24px;">';
            this.addShortcutsToHelp(html, this.SHORTCUTS.articleList);
            html += '</div>';
            
            // 文章编辑快捷键
            html += '<h3 style="margin-bottom: 16px; color: var(--text-primary);">文章编辑</h3>';
            html += '<div style="display: grid; gap: 8px;">';
            this.addShortcutsToHelp(html, this.SHORTCUTS.articleEdit);
            html += '</div>';
            
            content.innerHTML = html;
            this.helpModal.classList.add('active');
        },
        
        addShortcutsToHelp(html, shortcuts) {
            for (const [key, shortcut] of Object.entries(shortcuts)) {
                if (shortcut.isPrefix) continue;
                const displayKey = key.replace('+', ' + ');
                html += `
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: var(--bg-page); border-radius: var(--radius);">
                        <span style="color: var(--text-secondary);">${shortcut.desc}</span>
                        <kbd style="background: var(--bg-card); padding: 4px 8px; border-radius: var(--radius-sm); font-family: monospace; border: 1px solid var(--border);">${displayKey}</kbd>
                    </div>
                `;
            }
        },
        
        hideHelp() {
            if (this.helpModal) {
                this.helpModal.classList.remove('active');
            }
        },
        
        closeAllModals() {
            document.querySelectorAll('.modal-overlay.active').forEach(modal => {
                modal.classList.remove('active');
            });
        },
        
        saveCurrentForm() {
            const form = document.querySelector('form');
            if (form) {
                form.dispatchEvent(new Event('submit'));
            }
        },
        
        selectTableRow(direction) {
            const rows = document.querySelectorAll('table tbody tr');
            if (rows.length === 0) return;
            
            let currentIndex = -1;
            rows.forEach((row, idx) => {
                if (row.classList.contains('selected')) {
                    currentIndex = idx;
                }
            });
            
            if (currentIndex === -1) {
                rows[0].classList.add('selected');
            } else {
                rows[currentIndex].classList.remove('selected');
                const newIndex = Math.max(0, Math.min(rows.length - 1, currentIndex + direction));
                rows[newIndex].classList.add('selected');
                rows[newIndex].scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        },
        
        editSelectedRow() {
            const selectedRow = document.querySelector('table tbody tr.selected');
            if (selectedRow) {
                const editLink = selectedRow.querySelector('a[href*="/edit"]');
                if (editLink) {
                    window.location.href = editLink.href;
                }
            }
        },
        
        deleteSelectedRow() {
            const selectedRow = document.querySelector('table tbody tr.selected');
            if (selectedRow) {
                const deleteBtn = selectedRow.querySelector('.btn-danger');
                if (deleteBtn) {
                    deleteBtn.click();
                }
            }
        },
        
        toggleBatchSelection() {
            const checkboxes = document.querySelectorAll('input[type="checkbox"].batch-select');
            const checkedCount = document.querySelectorAll('input[type="checkbox"].batch-select:checked').length;
            const checkAll = checkedCount < checkboxes.length;
            
            checkboxes.forEach(cb => {
                cb.checked = checkAll;
            });
            
            this.updateBatchActions();
        },
        
        exportSelected() {
            const checkedBoxes = document.querySelectorAll('input[type="checkbox"].batch-select:checked');
            if (checkedBoxes.length === 0) {
                alert('请先选择要导出的文章');
                return;
            }
            
            const ids = Array.from(checkedBoxes).map(cb => cb.value);
            window.location.href = `/admin/export/articles?ids=${ids.join(',')}`;
        },
        
        updateBatchActions() {
            const checkedCount = document.querySelectorAll('input[type="checkbox"].batch-select:checked').length;
            const batchActions = document.querySelector('.batch-actions');
            
            if (batchActions) {
                if (checkedCount > 0) {
                    batchActions.style.display = 'flex';
                    batchActions.setAttribute('data-count', checkedCount);
                } else {
                    batchActions.style.display = 'none';
                }
            }
        },
        
        submitForm(action) {
            const form = document.querySelector('form');
            if (!form) return;
            
            const actionInput = document.createElement('input');
            actionInput.type = 'hidden';
            actionInput.name = 'action';
            actionInput.value = action;
            form.appendChild(actionInput);
            
            form.submit();
        }
    };

    // ==================== 批量操作系统 ====================
    const BatchActions = {
        init() {
            this.bindEvents();
            this.createBatchBar();
        },
        
        bindEvents() {
            // 监听复选框变化
            document.addEventListener('change', (e) => {
                if (e.target.classList.contains('batch-select')) {
                    ShortcutManager.updateBatchActions();
                }
            });
        },
        
        createBatchBar() {
            // 在文章列表页面添加批量操作栏
            const tableWrapper = document.querySelector('.table-wrapper');
            if (!tableWrapper) return;
            
            const batchBar = document.createElement('div');
            batchBar.className = 'batch-actions';
            batchBar.style.cssText = `
                display: none;
                align-items: center;
                justify-content: space-between;
                padding: 16px 24px;
                background: var(--bg-card);
                border: 1px solid var(--border);
                border-radius: var(--radius);
                margin-bottom: 16px;
                gap: 16px;
                flex-wrap: wrap;
            `;
            
            batchBar.innerHTML = `
                <div style="display: flex; align-items: center; gap: 12px;">
                    <input type="checkbox" id="select-all" class="batch-select-all" style="width: 18px; height: 18px;">
                    <label for="select-all" style="color: var(--text-secondary);">
                        已选择 <span class="selected-count">0</span> 项
                    </label>
                </div>
                <div style="display: flex; gap: 8px;">
                    <select id="batch-category" class="form-select" style="min-width: 140px;">
                        <option value="">批量修改分类</option>
                        <option value="时政热点">时政热点</option>
                        <option value="科技头条">科技头条</option>
                        <option value="智能AI">智能AI</option>
                        <option value="安全攻防">安全攻防</option>
                        <option value="开发者生态">开发者生态</option>
                        <option value="数码硬件">数码硬件</option>
                        <option value="社会热点">社会热点</option>
                        <option value="汽车">汽车</option>
                        <option value="游戏">游戏</option>
                        <option value="开源推荐">开源推荐</option>
                        <option value="医疗健康">医疗健康</option>
                    </select>
                    <button class="btn btn-sm btn-secondary" onclick="BatchActions.updateCategory()">更新分类</button>
                    <button class="btn btn-sm btn-success" onclick="BatchActions.publishArticles(true)">发布</button>
                    <button class="btn btn-sm btn-secondary" onclick="BatchActions.publishArticles(false)">取消发布</button>
                    <button class="btn btn-sm btn-danger" onclick="BatchActions.deleteArticles()">删除</button>
                    <button class="btn btn-sm btn-secondary" onclick="BatchActions.exportArticles()">导出</button>
                </div>
            `;
            
            tableWrapper.parentNode.insertBefore(batchBar, tableWrapper);
            
            // 绑定全选复选框
            document.querySelector('.batch-select-all')?.addEventListener('change', (e) => {
                document.querySelectorAll('.batch-select').forEach(cb => {
                    cb.checked = e.target.checked;
                });
                ShortcutManager.updateBatchActions();
            });
        },
        
        getSelectedIds() {
            return Array.from(document.querySelectorAll('.batch-select:checked'))
                .map(cb => cb.value);
        },
        
        updateCategory() {
            const ids = this.getSelectedIds();
            const category = document.getElementById('batch-category').value;
            
            if (ids.length === 0) {
                alert('请选择要更新的文章');
                return;
            }
            
            if (!category) {
                alert('请选择目标分类');
                return;
            }
            
            if (!confirm(`确定要将 ${ids.length} 篇文章的分类修改为 "${category}" 吗？`)) {
                return;
            }
            
            this.sendBatchRequest('/admin/batch/update-category', { ids, category });
        },
        
        publishArticles(publish) {
            const ids = this.getSelectedIds();
            
            if (ids.length === 0) {
                alert('请选择要操作的文章');
                return;
            }
            
            const action = publish ? '发布' : '取消发布';
            if (!confirm(`确定要${action} ${ids.length} 篇文章吗？`)) {
                return;
            }
            
            this.sendBatchRequest('/admin/batch/publish', { ids, publish });
        },
        
        deleteArticles() {
            const ids = this.getSelectedIds();
            
            if (ids.length === 0) {
                alert('请选择要删除的文章');
                return;
            }
            
            if (!confirm(`确定要删除 ${ids.length} 篇文章吗？此操作不可恢复！`)) {
                return;
            }
            
            this.sendBatchRequest('/admin/batch/delete', { ids });
        },
        
        exportArticles() {
            const ids = this.getSelectedIds();
            
            if (ids.length === 0) {
                alert('请选择要导出的文章');
                return;
            }
            
            window.location.href = `/admin/export/articles?ids=${ids.join(',')}`;
        },
        
        sendBatchRequest(url, data) {
            fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(r => r.json())
            .then(d => {
                if (d.success) {
                    alert(d.message);
                    window.location.reload();
                } else {
                    alert('操作失败: ' + d.message);
                }
            })
            .catch(e => {
                alert('操作失败: ' + e.message);
            });
        }
    };

    // ==================== 导出功能 ====================
    const ExportManager = {
        init() {
            this.bindExportButtons();
        },
        
        bindExportButtons() {
            // 绑定页面上的导出按钮
            document.querySelectorAll('.export-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const type = btn.dataset.exportType;
                    this.exportData(type);
                });
            });
        },
        
        exportData(type) {
            const urls = {
                articles: '/admin/export/articles',
                users: '/admin/export/users',
                logs: '/admin/export/logs'
            };
            
            const url = urls[type];
            if (url) {
                window.location.href = url;
            }
        }
    };

    // ==================== 初始化 ====================
    document.addEventListener('DOMContentLoaded', () => {
        ThemeManager.init();
        ShortcutManager.init();
        ExportManager.init();
        
        // 只在文章列表页面初始化批量操作
        if (window.location.pathname.includes('/admin/articles') && !window.location.pathname.includes('/new')) {
            BatchActions.init();
        }
    });

    // 暴露全局方法供HTML调用
    window.ThemeManager = ThemeManager;
    window.ShortcutManager = ShortcutManager;
    window.BatchActions = BatchActions;
    window.ExportManager = ExportManager;
})();
