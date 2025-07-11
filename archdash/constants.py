"""
应用程序常量定义

包含所有数值常量、限制和阈值设置
"""


class AppConstants:
    """应用程序核心常量"""
    
    # ============ 事件和消息管理 ============
    MAX_RECENT_EVENTS = 9           # 保持最近事件数量
    MAX_RECENT_MESSAGES = 19        # 保持最近消息数量
    
    # ============ 数据处理限制 ============
    MAX_DATA_POINTS = 1000          # 敏感性分析最大数据点数
    MAX_CHART_DATA_POINTS = 1000    # 图表显示最大数据点数
    
    # ============ 布局管理 ============
    DEFAULT_INITIAL_COLUMNS = 4     # 默认初始列数
    DEFAULT_INITIAL_ROWS = 12       # 默认初始行数
    MIN_LAYOUT_COLUMNS = 3          # 最小列数限制
    
    # ============ 参数管理 ============
    DEFAULT_PARAMETER_VALUE = 0.0   # 新参数默认值
    DEFAULT_CONFIDENCE = 1.0        # 默认置信度
    
    # ============ 敏感性分析 ============
    SENSITIVITY_START_MULTIPLIER = 0.5   # 敏感性分析起始值倍数
    SENSITIVITY_END_MULTIPLIER = 1.5     # 敏感性分析结束值倍数
    SENSITIVITY_DEFAULT_START = 0        # 敏感性分析默认起始值
    SENSITIVITY_DEFAULT_END = 100        # 敏感性分析默认结束值
    
    # ============ 置信度阈值 ============
    CONFIDENCE_HIGH_THRESHOLD = 0.8      # 高置信度阈值
    CONFIDENCE_MEDIUM_THRESHOLD = 0.5    # 中等置信度阈值
    
    # ============ 图表配置 ============
    CHART_DEFAULT_HEIGHT = 280           # 默认图表高度
    CHART_MARGIN_LEFT = 40               # 图表左边距
    CHART_MARGIN_RIGHT = 40              # 图表右边距
    CHART_MARGIN_TOP = 60                # 图表上边距
    CHART_MARGIN_BOTTOM = 40             # 图表下边距
    
    # ============ 参数Pin点样式数值 ============
    PARAM_PIN_SIZE = 8                   # 参数连接点大小(px)
    PARAM_PIN_BORDER_WIDTH = 2           # 参数连接点边框宽度(px)
    PARAM_PIN_MARGIN_RIGHT = 4           # 参数连接点右边距(px)
    PARAM_PIN_MARGIN_TOP = 6             # 参数连接点上边距(px)
    
    # ============ 输入框宽度计算 ============
    PARAM_INPUT_UNLINK_OFFSET = 25       # 有unlink图标时输入框宽度偏移(px)
    
    # ============ 空状态容器配置 ============
    EMPTY_STATE_MIN_HEIGHT = 400         # 空状态容器最小高度(px)
    
    # ============ Z-Index 层级 ============
    ARROWS_OVERLAY_Z_INDEX = 10          # 箭头覆盖层z-index
    DROPDOWN_MENU_Z_INDEX = 99999        # 下拉菜单z-index
    NODE_ACTIVE_Z_INDEX = 10000          # 活跃节点z-index


class ValidationConstants:
    """数据验证相关常量"""
    
    # ============ 参数验证 ============
    MIN_PARAMETER_NAME_LENGTH = 1
    MAX_PARAMETER_NAME_LENGTH = 100
    
    # ============ 节点验证 ============
    MIN_NODE_NAME_LENGTH = 1
    MAX_NODE_NAME_LENGTH = 100
    
    # ============ 数值验证 ============
    MIN_CONFIDENCE_VALUE = 0.0
    MAX_CONFIDENCE_VALUE = 1.0


class PerformanceConstants:
    """性能相关常量"""
    
    # ============ 更新频率 ============
    CANVAS_UPDATE_DEBOUNCE_MS = 200      # 画布更新防抖时间(毫秒)
    PARAM_UPDATE_DEBOUNCE_MS = 300       # 参数更新防抖时间(毫秒)
    
    # ============ 动画时间 ============
    PARAM_HIGHLIGHT_DURATION_S = 2       # 参数高亮持续时间(秒)
    TRANSITION_DURATION_MS = 300         # 通用过渡动画时间(毫秒)