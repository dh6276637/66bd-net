// ===== 66必读后台管理功能 =====
// 包含：深色模式、键盘快捷键、批量操作、导出功能

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
            NotificationManager.show('success', '主题切换', `已切换到${newTheme === 'dark' ? '深色' : '浅色'}模式`);
        },
        
        createToggleButton() {
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

    // ==================== 键盘快捷键动画系统 ====================
    const KeyboardAnimation = {
        animationContainer: null,
        
        init() {
            this.createAnimationContainer();
            this.createToastContainer();
        },
        
        createAnimationContainer() {
            const container = document.createElement('div');
            container.id = 'keyboard-animation-container';
            container.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                z-index: 10000;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.15s ease;
            `;
            document.body.appendChild(container);
            this.animationContainer = container;
        },
        
        createToastContainer() {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 12px;
                max-width: 380px;
            `;
            document.body.appendChild(container);
        },
        
        showKeyAnimation(key, description) {
            if (!this.animationContainer) return;
            
            this.animationContainer.innerHTML = `
                <div style="
                    background: var(--bg-card);
                    border: 2px solid var(--primary);
                    border-radius: 12px;
                    padding: 20px 32px;
                    box-shadow: var(--shadow-lg);
                    text-align: center;
                    transform: scale(0.8);
                    transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
                ">
                    <div style="
                        font-size: 48px;
                        font-weight: 700;
                        color: var(--primary);
                        margin-bottom: 8px;
                        text-transform: uppercase;
                        font-family: monospace;
                    ">${key}</div>
                    <div style="
                        font-size: 14px;
                        color: var(--text-secondary);
                    ">${description}</div>
                </div>
            `;
            
            this.animationContainer.style.opacity = '1';
            
            setTimeout(() => {
                const box = this.animationContainer.querySelector('div');
                if (box) box.style.transform = 'scale(1)';
            }, 10);
            
            setTimeout(() => {
                this.animationContainer.style.opacity = '0';
            }, 800);
        },
        
        showPrefixAnimation(prefix) {
            if (!this.animationContainer) return;
            
            this.animationContainer.innerHTML = `
                <div style="
                    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
                    border-radius: 12px;
                    padding: 24px 40px;
                    box-shadow: var(--shadow-lg);
                    text-align: center;
                ">
                    <div style="
                        font-size: 64px;
                        font-weight: 700;
                        color: white;
                        margin-bottom: 8px;
                    ">${prefix}</div>
                    <div style="
                        font-size: 16px;
                        color: rgba(255,255,255,0.9);
                    ">等待下一个按键...</div>
                </div>
            `;
            
            this.animationContainer.style.opacity = '1';
            
            setTimeout(() => {
                const box = this.animationContainer.querySelector('div');
                if (box) box.style.transform = 'scale(1)';
            }, 10);
        },
        
        hideAnimation() {
            if (!this.animationContainer) return;
            this.animationContainer.style.opacity = '0';
        }
    };

    // ==================== 通知系统 ====================
    const NotificationManager = {
        show(type, title, message, duration = 3000) {
            const container = document.getElementById('toast-container');
            if (!container) return;
            
            const icons = {
                success: '✅',
                error: '❌',
                warning: '⚠️',
                info: 'ℹ️'
            };
            
            const toast = document.createElement('div');
            toast.style.cssText = `
                background: var(--bg-card);
                border-left: 4px solid var(--${type === 'success' ? 'success' : type === 'error' ? 'danger' : type === 'warning' ? 'warning' : 'info'});
                border-radius: 8px;
                padding: 16px 20px;
                box-shadow: var(--shadow-lg);
                display: flex;
                align-items: flex-start;
                gap: 12px;
                animation: slideInRight 0.3s ease;
                opacity: 0;
                transform: translateX(100%);
            `;
            
            toast.innerHTML = `
                <div style="font-size: 24px;">${icons[type] || icons.info}</div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 4px;">${title}</div>
                    <div style="font-size: 14px; color: var(--text-secondary);">${message}</div>
                </div>
                <button onclick="this.parentElement.remove()" style="
                    background: none;
                    border: none;
                    font-size: 18px;
                    cursor: pointer;
                    color: var(--text-muted);
                    padding: 0;
                ">✕</button>
            `;
            
            container.appendChild(toast);
            
            // 触发动画
            requestAnimationFrame(() => {
                toast.style.opacity = '1';
                toast.style.transform = 'translateX(0)';
            });
            
            // 自动移除
            if (duration > 0) {
                setTimeout(() => {
                    toast.style.opacity = '0';
                    toast.style.transform = 'translateX(100%)';
                    setTimeout(() => toast.remove(), 300);
                }, duration);
            }
        }
    };

    // 添加动画样式
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(100%);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        .batch-actions {
            display: none;
            align-items: center;
            justify-content: space-between;
            padding: 16px 24px;
            background: var(--bg-card);
            border: 2px solid var(--primary);
            border-radius: 12px;
            margin-bottom: 20px;
            gap: 16px;
            flex-wrap: wrap;
            animation: slideDown 0.3s ease;
        }
        
        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .progress-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9998;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }
        
        .progress-overlay.active {
            opacity: 1;
            visibility: visible;
        }
        
        .progress-box {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 32px;
            min-width: 400px;
            box-shadow: var(--shadow-lg);
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: var(--bg-page);
            border-radius: 4px;
            overflow: hidden;
            margin: 16px 0;
        }
        
        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%);
            border-radius: 4px;
            transition: width 0.3s ease;
            width: 0%;
        }
    `;
    document.head.appendChild(style);

    // ==================== 快捷键管理器 ====================
    const ShortcutManager = {
        STORAGE_KEY: 'admin_shortcuts',
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
        customShortcuts: {},
        
        init() {
            this.loadCustomShortcuts();
            this.bindEvents();
            this.createHelpModal();
            this.detectContext();
        },
        
        loadCustomShortcuts() {
            try {
                const saved = localStorage.getItem(this.STORAGE_KEY);
                if (saved) {
                    this.customShortcuts = JSON.parse(saved);
                }
            } catch (e) {
                console.error('加载自定义快捷键失败:', e);
            }
        },
        
        saveCustomShortcuts() {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.customShortcuts));
        },
        
        bindEvents() {
            document.addEventListener('keydown', (e) => this.handleKeydown(e));
        },
        
        handleKeydown(e) {
            const activeEl = document.activeElement;
            if (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA' || activeEl.isContentEditable) {
                return;
            }
            
            const key = this.getKeyString(e);
            
            if (this.pendingKey) {
                const combo = this.pendingKey + ' ' + key;
                if (this.executeShortcut(combo)) {
                    this.pendingKey = null;
                    KeyboardAnimation.hideAnimation();
                    e.preventDefault();
                    return;
                }
                this.pendingKey = null;
                KeyboardAnimation.hideAnimation();
            }
            
            const contextKeys = this.getEffectiveShortcuts(this.activeContext);
            const globalKeys = this.getEffectiveShortcuts('global');
            
            if (contextKeys[key] && this.executeShortcut(key, this.activeContext)) {
                e.preventDefault();
                return;
            }
            
            if (globalKeys[key]) {
                if (globalKeys[key].isPrefix) {
                    this.pendingKey = key;
                    KeyboardAnimation.showPrefixAnimation(key);
                    setTimeout(() => {
                        if (this.pendingKey === key) {
                            this.pendingKey = null;
                            KeyboardAnimation.hideAnimation();
                        }
                    }, 2000);
                } else if (this.executeShortcut(key, 'global')) {
                    e.preventDefault();
                }
            }
        },
        
        getEffectiveShortcuts(context) {
            const defaults = this.SHORTCUTS[context] || {};
            const custom = this.customShortcuts[context] || {};
            return { ...defaults, ...custom };
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
            const shortcuts = this.getEffectiveShortcuts(context);
            const shortcut = shortcuts[key];
            
            if (!shortcut) return false;
            
            // 显示动画
            KeyboardAnimation.showKeyAnimation(key, shortcut.desc);
            
            setTimeout(() => {
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
                        if (shortcut.confirm) {
                            this.deleteSelectedRow();
                        }
                        break;
                    case 'toggleBatch':
                        this.toggleBatchSelection();
                        break;
                    case 'exportSelected':
                        ExportManager.showExportModal();
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
            }, 100);
            
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
                <div class="modal" style="max-width: 700px; max-height: 80vh;">
                    <div class="modal-header">
                        <div class="modal-title">⌨️ 键盘快捷键</div>
                        <button class="modal-close" onclick="ShortcutManager.hideHelp()">✕</button>
                    </div>
                    <div class="modal-body" style="max-height: 60vh; overflow-y: auto;">
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
            
            let html = `
                <div style="margin-bottom: 24px;">
                    <h4 style="color: var(--text-primary); margin-bottom: 12px;">全局快捷键</h4>
            `;
            this.addShortcutsToHelp(html, this.getEffectiveShortcuts('global'));
            html += '</div>';
            
            if (this.activeContext !== 'global') {
                html += `<div style="margin-bottom: 24px;">
                    <h4 style="color: var(--text-primary); margin-bottom: 12px;">当前页面快捷键</h4>`;
                this.addShortcutsToHelp(html, this.getEffectiveShortcuts(this.activeContext));
                html += '</div>';
            }
            
            html += `
                <div style="margin-top: 24px; padding-top: 24px; border-top: 1px solid var(--border);">
                    <button class="btn btn-primary btn-sm" onclick="ShortcutManager.showCustomizePanel()">
                        ⚙️ 自定义快捷键
                    </button>
                </div>
            `;
            
            content.innerHTML = html;
            this.helpModal.classList.add('active');
        },
        
        addShortcutsToHelp(html, shortcuts) {
            html += '<div style="display: grid; gap: 8px;">';
            for (const [key, shortcut] of Object.entries(shortcuts)) {
                if (shortcut.isPrefix) continue;
                const displayKey = key.replace('+', ' + ');
                html += `
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        padding: 10px 14px;
                        background: var(--bg-page);
                        border-radius: 8px;
                        transition: all 0.2s ease;
                    " onmouseover="this.style.background='var(--bg-hover)'" onmouseout="this.style.background='var(--bg-page)'">
                        <span style="color: var(--text-secondary);">${shortcut.desc}</span>
                        <kbd style="
                            background: var(--bg-card);
                            padding: 6px 10px;
                            border-radius: 6px;
                            font-family: monospace;
                            font-size: 13px;
                            border: 1px solid var(--border);
                            box-shadow: 0 2px 0 var(--border);
                        ">${displayKey}</kbd>
                    </div>
                `;
            }
            html += '</div>';
        },
        
        showCustomizePanel() {
            this.hideHelp();
            setTimeout(() => {
                alert('自定义快捷键功能开发中...\n\n您可以在弹出的设置面板中配置个人偏好的快捷键组合。');
            }, 300);
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
                    row.classList.remove('selected');
                }
            });
            
            const newIndex = Math.max(0, Math.min(rows.length - 1, currentIndex === -1 ? 0 : currentIndex + direction));
            rows[newIndex].classList.add('selected');
            rows[newIndex].style.background = 'var(--primary-alpha-10)';
            rows[newIndex].scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // 清除其他选中行的样式
            rows.forEach((row, idx) => {
                if (idx !== newIndex) {
                    row.style.background = '';
                }
            });
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
                if (deleteBtn && deleteBtn.tagName === 'BUTTON') {
                    if (confirm('确定要删除这篇选中的文章吗？')) {
                        deleteBtn.click();
                    }
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
            
            BatchActions.updateBatchActions();
            NotificationManager.show('info', '批量选择', `已${checkAll ? '全选' : '取消全选'} ${checkboxes.length} 项`);
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

    // ==================== 导出管理器 ====================
    const ExportManager = {
        init() {
            this.bindExportButtons();
        },
        
        bindExportButtons() {
            document.querySelectorAll('.export-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const type = btn.dataset.exportType;
                    const format = btn.dataset.exportFormat || 'csv';
                    this.exportData(type, format);
                });
            });
        },
        
        showExportModal() {
            const selectedCount = document.querySelectorAll('.batch-select:checked').length;
            if (selectedCount === 0) {
                NotificationManager.show('warning', '导出提示', '请先选择要导出的文章');
                return;
            }
            
            const modal = document.createElement('div');
            modal.className = 'modal-overlay active';
            modal.innerHTML = `
                <div class="modal" style="max-width: 400px;">
                    <div class="modal-header">
                        <div class="modal-title">📥 导出文章</div>
                        <button class="modal-close" onclick="this.closest('.modal-overlay').classList.remove('active')">✕</button>
                    </div>
                    <div class="modal-body">
                        <p style="margin-bottom: 20px; color: var(--text-secondary);">
                            已选择 <strong style="color: var(--primary);">${selectedCount}</strong> 篇文章
                        </p>
                        <div style="display: grid; gap: 12px;">
                            <button class="btn btn-primary btn-block" onclick="ExportManager.doExport('csv')">
                                📄 导出为 CSV 格式
                            </button>
                            <button class="btn btn-secondary btn-block" onclick="ExportManager.doExport('json')">
                                📋 导出为 JSON 格式
                            </button>
                            <button class="btn btn-secondary btn-block" onclick="ExportManager.doExport('xlsx')">
                                📊 导出为 Excel 格式
                            </button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        },
        
        doExport(format) {
            const ids = Array.from(document.querySelectorAll('.batch-select:checked')).map(cb => cb.value);
            const type = document.querySelector('.batch-select')?.closest('[data-export-type]')?.dataset.exportType || 'articles';
            
            // 关闭弹窗
            document.querySelector('.modal-overlay.active')?.classList.remove('active');
            
            // 显示进度
            ProgressManager.show('正在准备导出...', 0);
            
            setTimeout(() => {
                window.location.href = `/admin/export/${type}?ids=${ids.join(',')}&format=${format}`;
                ProgressManager.update(100, '导出完成！');
                
                setTimeout(() => {
                    ProgressManager.hide();
                    NotificationManager.show('success', '导出成功', `已导出 ${ids.length} 篇文章（${format.toUpperCase()}格式）`);
                }, 500);
            }, 500);
        },
        
        exportData(type, format) {
            const url = `/admin/export/${type}?format=${format}`;
            ProgressManager.show('正在导出...', 0);
            
            setTimeout(() => {
                window.location.href = url;
                ProgressManager.update(100, '导出完成！');
                setTimeout(() => {
                    ProgressManager.hide();
                    NotificationManager.show('success', '导出成功', `已导出完成（${format.toUpperCase()}格式）`);
                }, 500);
            }, 300);
        }
    };

    // ==================== 进度管理器 ====================
    const ProgressManager = {
        overlay: null,
        
        show(message, progress = 0) {
            if (!this.overlay) {
                this.overlay = document.createElement('div');
                this.overlay.className = 'progress-overlay';
                this.overlay.innerHTML = `
                    <div class="progress-box">
                        <div class="progress-title" style="font-size: 18px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px;">处理中</div>
                        <div class="progress-message" style="font-size: 14px; color: var(--text-secondary);">${message}</div>
                        <div class="progress-bar">
                            <div class="progress-bar-fill"></div>
                        </div>
                        <div class="progress-percent" style="font-size: 24px; font-weight: 700; color: var(--primary); text-align: center;">0%</div>
                    </div>
                `;
                document.body.appendChild(this.overlay);
            }
            
            this.update(progress, message);
            this.overlay.classList.add('active');
        },
        
        update(progress, message) {
            const fill = this.overlay?.querySelector('.progress-bar-fill');
            const percent = this.overlay?.querySelector('.progress-percent');
            const msg = this.overlay?.querySelector('.progress-message');
            
            if (fill) fill.style.width = `${progress}%`;
            if (percent) percent.textContent = `${progress}%`;
            if (msg && message) msg.textContent = message;
        },
        
        hide() {
            if (this.overlay) {
                this.overlay.classList.remove('active');
            }
        }
    };

    // ==================== 批量操作管理器 ====================
    const BatchActions = {
        init() {
            this.bindEvents();
            this.createBatchBar();
        },
        
        bindEvents() {
            document.addEventListener('change', (e) => {
                if (e.target.classList.contains('batch-select')) {
                    ShortcutManager.updateBatchActions();
                }
            });
        },
        
        createBatchBar() {
            const tableWrapper = document.querySelector('.table-wrapper');
            if (!tableWrapper) return;
            
            const batchBar = document.createElement('div');
            batchBar.className = 'batch-actions';
            batchBar.innerHTML = `
                <div style="display: flex; align-items: center; gap: 12px;">
                    <input type="checkbox" id="select-all-top" class="batch-select-all" style="width: 18px; height: 18px;">
                    <label for="select-all-top" style="color: var(--text-secondary); cursor: pointer;">
                        全选
                    </label>
                    <span style="color: var(--text-muted);">|</span>
                    <span style="color: var(--text-secondary);">
                        已选择 <strong id="selected-count" style="color: var(--primary);">0</strong> 项
                    </span>
                </div>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <select id="batch-category" class="form-select" style="min-width: 140px; padding: 8px 12px;">
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
                    <button class="btn btn-sm btn-secondary" onclick="BatchActions.updateCategory()">📂 更新分类</button>
                    <button class="btn btn-sm btn-success" onclick="BatchActions.publishArticles(true)">✅ 发布</button>
                    <button class="btn btn-sm btn-secondary" onclick="BatchActions.publishArticles(false)">❌ 取消发布</button>
                    <button class="btn btn-sm btn-primary" onclick="ExportManager.showExportModal()">📥 导出</button>
                    <button class="btn btn-sm btn-danger" onclick="BatchActions.deleteArticles()">🗑️ 删除</button>
                </div>
            `;
            
            tableWrapper.parentNode.insertBefore(batchBar, tableWrapper);
            
            // 绑定全选
            document.querySelectorAll('.batch-select-all').forEach(cb => {
                cb.addEventListener('change', (e) => {
                    document.querySelectorAll('.batch-select').forEach(cb => {
                        cb.checked = e.target.checked;
                    });
                    this.updateBatchActions();
                });
            });
        },
        
        getSelectedIds() {
            return Array.from(document.querySelectorAll('.batch-select:checked')).map(cb => cb.value);
        },
        
        updateBatchActions() {
            const checkedCount = document.querySelectorAll('.batch-select:checked').length;
            const batchActions = document.querySelector('.batch-actions');
            
            if (batchActions) {
                const countEl = batchActions.querySelector('#selected-count');
                if (countEl) countEl.textContent = checkedCount;
                
                if (checkedCount > 0) {
                    batchActions.style.display = 'flex';
                } else {
                    batchActions.style.display = 'none';
                }
            }
        },
        
        async updateCategory() {
            const ids = this.getSelectedIds();
            const category = document.getElementById('batch-category').value;
            
            if (ids.length === 0) {
                NotificationManager.show('warning', '操作提示', '请选择要更新的文章');
                return;
            }
            
            if (!category) {
                NotificationManager.show('warning', '操作提示', '请选择目标分类');
                return;
            }
            
            if (!confirm(`确定要将 ${ids.length} 篇文章的分类修改为 "${category}" 吗？`)) {
                return;
            }
            
            await this.sendBatchRequest('/admin/batch/update-category', { ids, category });
        },
        
        async publishArticles(publish) {
            const ids = this.getSelectedIds();
            
            if (ids.length === 0) {
                NotificationManager.show('warning', '操作提示', '请选择要操作的文章');
                return;
            }
            
            const action = publish ? '发布' : '取消发布';
            if (!confirm(`确定要${action} ${ids.length} 篇文章吗？`)) {
                return;
            }
            
            await this.sendBatchRequest('/admin/batch/publish', { ids, publish });
        },
        
        async deleteArticles() {
            const ids = this.getSelectedIds();
            
            if (ids.length === 0) {
                NotificationManager.show('warning', '操作提示', '请选择要删除的文章');
                return;
            }
            
            if (!confirm(`确定要删除 ${ids.length} 篇文章吗？此操作不可恢复！`)) {
                return;
            }
            
            await this.sendBatchRequest('/admin/batch/delete', { ids });
        },
        
        async sendBatchRequest(url, data) {
            ProgressManager.show('正在处理...', 0);
            
            try {
                // 模拟进度
                let progress = 0;
                const progressInterval = setInterval(() => {
                    progress += 20;
                    if (progress <= 80) {
                        ProgressManager.update(progress, '正在处理请求...');
                    }
                }, 100);
                
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                clearInterval(progressInterval);
                ProgressManager.update(100, '处理完成！');
                
                setTimeout(() => {
                    ProgressManager.hide();
                    
                    if (result.success) {
                        NotificationManager.show('success', '操作成功', result.message);
                        setTimeout(() => window.location.reload(), 500);
                    } else {
                        NotificationManager.show('error', '操作失败', result.message);
                    }
                }, 300);
                
            } catch (error) {
                ProgressManager.hide();
                NotificationManager.show('error', '操作失败', error.message);
            }
        }
    };

    // ==================== 初始化 ====================
    document.addEventListener('DOMContentLoaded', () => {
        ThemeManager.init();
        KeyboardAnimation.init();
        ShortcutManager.init();
        ExportManager.init();
        
        if (window.location.pathname.includes('/admin/articles') && !window.location.pathname.includes('/new')) {
            BatchActions.init();
        }
    });

    // 全局暴露
    window.ThemeManager = ThemeManager;
    window.ShortcutManager = ShortcutManager;
    window.KeyboardAnimation = KeyboardAnimation;
    window.NotificationManager = NotificationManager;
    window.ExportManager = ExportManager;
    window.ProgressManager = ProgressManager;
    window.BatchActions = BatchActions;
})();
