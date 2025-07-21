"""
国际化支持 - 多语言翻译系统
Internationalization support - Multi-language translation system
"""

# 语言配置字典
LANGUAGES = {
    'en': {
        'name': 'English',
        'flag': '🇺🇸',
        'translations': {
            # 按钮文本
            'refresh_graph': 'Refresh Graph',
            'load_sample': 'Load Sample',
            'clear_code': 'Clear Code',
            'save_html': 'Save HTML',
            'jump_to_code': '🔍 Jump to Code',
            'copy_name': '📋 Copy Name',
            'close': '❌ Close',
            
            # 界面标题和标签
            'app_title': 'Plotly Graph Visualizer - Online Mode',
            'code_editor': 'Code Editor',
            'dependency_graph': 'Interactive Dependency Graph',
            'language': 'Language',
            'examples': 'Examples',
            'select_example': 'Select an example...',
            
            # 状态消息
            'graph_updated_success': 'Graph updated successfully!',
            'parse_error': 'Parse Error',
            'graph_saved': 'Graph saved to:',
            'cannot_save': 'Cannot save - fix parse errors first',
            'enter_graph_code': 'Enter Graph code to visualize dependencies.',
            
            # 参数计数
            'found_parameters': 'Found {count} parameters: {basic} basic, {computed} computed.',
            'basic_parameters': 'basic',
            'computed_parameters': 'computed',
            
            # 提示信息
            'edit_code_hint': 'Edit code and click \'Refresh Graph\' to update visualization.',
            'interaction_hints': 'Drag to pan, scroll to zoom, hover for details, click node for context menu.',
            
            # 错误信息
            'execution_error': 'Execution Error',
            'import_error': 'Cannot import Graph class',
            'no_graph_instance': 'No Graph instance found',
            
            # 控制台启动信息
            'online_mode': 'Starting Online Mode (Dash Web Application)...',
            'offline_mode': 'Starting Offline Mode (HTML File Generation)...',
            'features': 'Features:',
            'monaco_editor_feature': 'Monaco Editor with Python syntax highlighting',
            'interactive_features': 'Interactive node dragging and context menus',
            'hover_effects': 'Hover effects and detailed tooltips',
            'layout_features': 'Smart dependency-level layout',
            'visual_features': 'Bezier curve arrows and dynamic node sizing',
            'manual_updates': 'Manual graph updates (auto-update disabled)',
            'tips': 'Tips:',
            'edit_tip': 'Edit code in Monaco Editor with syntax highlighting',
            'refresh_tip': 'Click \'Refresh Graph\' button to update visualization',
            'interaction_tip': 'Click nodes for context menu, hover for details',
            'buttons_tip': 'Use \'Load Sample\' and \'Clear Code\' for quick actions',
            
            # 模式切换
            'mode_online': 'online',
            'mode_offline': 'offline',
            'browser_opening': 'Opening browser at:',
            'manual_update_enabled': 'Manual update mode ENABLED!',
            
            # 示例切换确认对话框
            'confirm_example_title': 'Overwrite Current Code?',
            'confirm_example_message': 'Loading this example will replace your current code. Are you sure you want to continue?',
            'confirm_yes': 'Yes, Replace Code',
            'confirm_no': 'Cancel',
        }
    },
    'zh': {
        'name': '中文',
        'flag': '🇨🇳',
        'translations': {
            # 按钮文本
            'refresh_graph': '刷新图表',
            'load_sample': '加载示例',
            'clear_code': '清空代码',
            'save_html': '保存HTML',
            'jump_to_code': '🔍 跳转到代码',
            'copy_name': '📋 复制名称',
            'close': '❌ 关闭',
            
            # 界面标题和标签
            'app_title': 'Plotly图表可视化器 - 在线模式',
            'code_editor': '代码编辑器',
            'dependency_graph': '交互式依赖关系图',
            'language': '语言',
            'examples': '示例',
            'select_example': '选择示例...',
            
            # 状态消息
            'graph_updated_success': '图表更新成功！',
            'parse_error': '解析错误',
            'graph_saved': '图表已保存到：',
            'cannot_save': '无法保存 - 请先修复解析错误',
            'enter_graph_code': '输入Graph代码以可视化依赖关系。',
            
            # 参数计数
            'found_parameters': '找到{count}个参数：{basic}个基础参数，{computed}个计算参数。',
            'basic_parameters': '基础',
            'computed_parameters': '计算',
            
            # 提示信息
            'edit_code_hint': '编辑代码并点击"刷新图表"以更新可视化。',
            'interaction_hints': '拖拽平移，滚轮缩放，悬停查看详情，点击节点显示菜单。',
            
            # 错误信息
            'execution_error': '执行错误',
            'import_error': '无法导入Graph类',
            'no_graph_instance': '未找到Graph实例',
            
            # 控制台启动信息
            'online_mode': '启动在线模式（Dash Web应用）...',
            'offline_mode': '启动离线模式（HTML文件生成）...',
            'features': '功能特性：',
            'monaco_editor_feature': 'Monaco编辑器，支持Python语法高亮',
            'interactive_features': '交互式节点拖拽和上下文菜单',
            'hover_effects': '悬停效果和详细提示',
            'layout_features': '智能依赖层级布局',
            'visual_features': '贝塞尔曲线箭头和动态节点大小',
            'manual_updates': '手动图表更新（已禁用自动更新）',
            'tips': '使用提示：',
            'edit_tip': '在Monaco编辑器中编辑代码，支持语法高亮',
            'refresh_tip': '点击"刷新图表"按钮更新可视化',
            'interaction_tip': '点击节点显示菜单，悬停查看详情',
            'buttons_tip': '使用"加载示例"和"清空代码"快速操作',
            
            # 模式切换
            'mode_online': '在线',
            'mode_offline': '离线',
            'browser_opening': '正在打开浏览器：',
            'manual_update_enabled': '手动更新模式已启用！',
            
            # 示例切换确认对话框
            'confirm_example_title': '覆盖当前代码？',
            'confirm_example_message': '加载此示例将替换您当前的代码。您确定要继续吗？',
            'confirm_yes': '是的，替换代码',
            'confirm_no': '取消',
        }
    },
}

def get_translation(key: str, lang: str = 'en', **kwargs) -> str:
    """
    获取翻译文本
    Get translated text
    
    Args:
        key: 翻译键名
        lang: 语言代码 ('en', 'zh', 'ja')
        **kwargs: 格式化参数
    
    Returns:
        翻译后的文本
    """
    if lang not in LANGUAGES:
        lang = 'en'  # 默认使用英文
    
    translations = LANGUAGES[lang]['translations']
    text = translations.get(key, LANGUAGES['en']['translations'].get(key, key))
    
    # 格式化文本（如果有参数）
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass  # 如果格式化失败，返回原文本
    
    return text

def get_available_languages():
    """获取可用语言列表"""
    return [
        {
            'code': code,
            'name': info['name'],
            'flag': info['flag']
        }
        for code, info in LANGUAGES.items()
    ]