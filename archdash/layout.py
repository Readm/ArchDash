from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_ace

app_layout = dbc.Container([
    html.H1([
        "🎨 ArchDash"
    ], className="text-center my-2 fade-in"),

    dbc.Row([
        dbc.Col([
            # 计算图卡片
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.H6([ 
                            html.Span("计算图", className="fw-bold")
                        ], className="mb-0"),
                        html.Div([
                            # 添加节点按钮（移到前面）
                            html.Button(
                                html.Span(
                                    "➕",  # 使用加号emoji图标
                                    style={
                                        "fontSize": "18px",
                                        "fontWeight": "normal",
                                        "lineHeight": "1"
                                    }
                                ),
                                id="add-node-from-graph-button",
                                className="btn add-node-btn",
                                style={
                                    "padding": "6px",
                                    "borderRadius": "50%",
                                    "border": "1px solid rgba(108, 117, 125, 0.3)",
                                    "backgroundColor": "transparent",
                                    "minWidth": "32px",
                                    "height": "32px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                    "transition": "all 0.3s ease",
                                    "color": "#6c757d",
                                    "marginRight": "8px"
                                },
                                title="添加新节点",
                                **{"data-testid": "add-node-button"}
                            ),
                            # 列管理下拉菜单（移到后面）
                            dbc.DropdownMenu([
                                dbc.DropdownMenuItem("➕ 添加列", id="add-column-btn", className="text-success"),
                                dbc.DropdownMenuItem("➖ 删除列", id="remove-column-btn", className="text-danger"),
                                dbc.DropdownMenuItem(divider=True),
                                dbc.DropdownMenuItem("🗑️ 清空图", id="clear-graph-btn", className="text-warning"),
                            ], 
                            label="",
                            color="outline-secondary",
                            size="sm"
                            )
                        ], style={"display": "flex", "alignItems": "center"})
                    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "width": "100%"})
                ]),
                dbc.CardBody([
                    html.Div(
                        id="canvas-container", 
                        className="position-relative",
                        style={"minHeight": "500px"},
                        children=[],  # 初始为空，由initialize_canvas回调填充
                        **{"data-testid": "canvas-container"}
                    ),
                ], className="p-1")
            ], className="glass-card mb-2"),
            
            # 操作状态卡片
            dbc.Card([
                dbc.CardBody([
                    html.Label("操作状态", className="fw-bold mb-2"),
                    html.Div(id="output-result", className="text-muted"),
                ])
            ], className="glass-card fade-in"),
        ], width=8),
        dbc.Col([
            # 文件操作卡片
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        dcc.Upload(
                            id="upload-graph",
                            children=html.Button(
                                "📁", 
                                className="btn btn-info btn-sm",
                                title="加载文件",
                                **{"data-testid": "load-file-button"}
                            ),
                            accept=".json",
                            multiple=False
                        ),
                        html.Button(
                            "💾", 
                            id="save-graph-button", 
                            className="btn btn-success btn-sm",
                            title="保存文件",
                            **{"data-testid": "save-file-button"}
                        ),
                        # 分隔符1
                        html.Div(
                            style={
                                "borderLeft": "1px solid #dee2e6",
                                "height": "24px",
                                "margin": "0 12px"
                            }
                        ),
                        html.Button(
                            "🎯", 
                            id="load-example-graph-button", 
                            className="btn btn-warning btn-sm",
                            title="加载示例计算图",
                            **{"data-testid": "load-example-button"}
                        ),
                        # 帮助按钮
                        html.Button(
                            "❓", 
                            id="help-tutorial-button", 
                            className="btn btn-info btn-sm",
                            title="使用教程",
                            style={"marginLeft": "8px"},
                            **{"data-testid": "help-tutorial-button"}
                        ),
                        # 分隔符2
                        html.Div(
                            style={
                                "borderLeft": "1px solid #dee2e6",
                                "height": "24px",
                                "margin": "0 12px"
                            }
                        ),
                        # 主题切换按钮
                        html.Button(
                            "🌙", 
                            id="theme-toggle", 
                            className="btn btn-outline-secondary btn-sm",
                            title="切换深色/浅色主题",
                            style={"minWidth": "32px"},
                            **{"data-testid": "theme-toggle-button"}
                        ),
                    ], className="d-flex align-items-center justify-content-around w-100"),
                ])
            ], className="glass-card fade-in mb-2"),
            
            # 相关性分析卡片
            dbc.Card([
                dbc.CardHeader([
                    html.H5([
                        html.Span("相关性分析", className="fw-bold")
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    # 图表显示区域 - 移到上方，增加高度与计算图保持一致
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(
                                id="sensitivity-plot",
                                style={"height": "280px"},
                                config={
                                    'displayModeBar': True,
                                    'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
                                    'displaylogo': False
                                }
                            )
                        ], className="p-1")
                    ], className="glass-card mb-1"),
                    
                    # 参数选择区域 - 移到下方，减少间距
                    dbc.Card([
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("X轴参数:", className="mb-1"),
                                    dbc.InputGroup([
                                        dbc.Input(
                                            id="x-param-display",
                                            placeholder="点击选择X轴参数",
                                            readonly=True,
                                            className="mb-1"
                                        ),
                                        dbc.Button(
                                            "选择",
                                            id="x-param-select-btn",
                                            color="primary",
                                            size="sm",
                                            outline=True
                                        )
                                    ])
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Y轴参数:", className="mb-1"),
                                    dbc.InputGroup([
                                        dbc.Input(
                                            id="y-param-display",
                                            placeholder="点击选择Y轴参数",
                                            readonly=True,
                                            className="mb-1"
                                        ),
                                        dbc.Button(
                                            "选择",
                                            id="y-param-select-btn",
                                            color="primary",
                                            size="sm",
                                            outline=True
                                        )
                                    ])
                                ], width=6),
                            ], className="mb-2"),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("起始值:", className="mb-1"),
                                    dbc.Input(
                                        id="x-start-value", 
                                        type="number", 
                                        value=0,
                                        size="sm",
                                        debounce=True,
                                        className="form-control"
                                    )
                                ], width=4),
                                dbc.Col([
                                    dbc.Label("结束值:", className="mb-1"),
                                    dbc.Input(
                                        id="x-end-value", 
                                        type="number", 
                                        value=100,
                                        size="sm",
                                        debounce=True,
                                        className="form-control"
                                    )
                                ], width=4),
                                dbc.Col([
                                    dbc.Label("步长:", className="mb-1"),
                                    dbc.Input(
                                        id="x-step-value", 
                                        type="number", 
                                        value=1,
                                        size="sm",
                                        min=0.1,
                                        debounce=True,
                                        className="form-control"
                                    )
                                ], width=4),
                            ], className="mb-2"),
                            
                            # 系列名称和累计绘图选项
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        dbc.InputGroup([
                                            dbc.InputGroupText("系列名称:", style={"fontSize": "0.8rem", "minWidth": "75px"}),
                                            dbc.Input(
                                                id="series-name-input",
                                                placeholder="自定义系列名称",
                                                size="sm",
                                                debounce=True,
                                                style={"fontSize": "0.8rem"}
                                            )
                                        ], size="sm"),
                                        dbc.Tooltip(
                                            "留空则使用默认名称",
                                            target="series-name-input",
                                            placement="top"
                                        )
                                    ]),
                                ], width=8),
                                dbc.Col([
                                    html.Div([
                                        dbc.Checklist(
                                            options=[
                                                {"label": "累计绘图", "value": "cumulative"}
                                            ],
                                            value=[],
                                            id="cumulative-plot-checkbox",
                                            inline=True,
                                            style={"fontSize": "0.8rem"}
                                        ),
                                        dbc.Tooltip(
                                            "每次生成累积在图表中",
                                            target="cumulative-plot-checkbox",
                                            placement="top"
                                        )
                                    ]),
                                ], width=4, className="d-flex justify-content-end align-items-center"),
                            ], className="mb-2"),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.ButtonGroup([
                                        dbc.Button(
                                            [html.Span("生成")], 
                                            id="generate-plot-btn", 
                                            color="primary", 
                                            size="sm"
                                        ),
                                        dbc.Button(
                                            [html.Span("放大")], 
                                            id="enlarge-plot-btn", 
                                            color="success", 
                                            size="sm"
                                        ),
                                        dbc.Button(
                                            [html.Span("清除")], 
                                            id="clear-plot-btn", 
                                            color="secondary", 
                                            size="sm"
                                        ),
                                        dbc.Button(
                                            [html.Span("导出csv")], 
                                            id="export-plot-data-btn", 
                                            color="info", 
                                            size="sm"
                                        )
                                    ], className="w-100")
                                ])
                            ])
                        ], className="p-2 dropdown-container")
                    ], className="glass-card dropdown-safe-card")
                ], className="p-1 sensitivity-analysis-card", style={"minHeight": "450px"})
            ], className="glass-card sensitivity-analysis-container"),
        ], width=4),
    ]),
    

    
    # 参数依赖关系模块 - 可折叠，独立一行
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.H5([ 
                            html.Span("计算过程", className="fw-bold"),
                        ], className="mb-0 d-inline-flex align-items-center"),
                        html.Div([
                            dbc.Button(
                                "🔄", 
                                id="refresh-dependencies-btn", 
                                color="outline-primary", 
                                size="sm", 
                                className="me-2",
                                title="刷新"
                            ),
                            dbc.Button(
                                ["🔽 ", html.Span("展开")], 
                                id="collapse-dependencies-btn", 
                                color="outline-secondary", 
                                size="sm",
                                className="collapse-btn",
                                title="展开/折叠"
                            ),
                        ], className="d-flex")
                    ], className="d-flex justify-content-between align-items-center w-100")
                ], className="dependencies-header py-2"),
                dbc.Collapse([
                    dbc.CardBody([
                        # 仅显示依赖关系视图
                        html.Div(
                            id="dependencies-display",
                            style={"height": "350px", "overflowY": "auto"},
                            children=[html.P("📊 加载依赖关系中...", className="text-muted text-center")]
                        )
                    ], className="p-2 dropdown-container")
                ], id="dependencies-collapse", is_open=False)
            ], className="glass-card dependencies-panel dropdown-safe-card"),
        ], width=12),
    ], className="mt-2"),

    dcc.Store(id="node-data", data={}),  # 简化为空字典，布局由layout_manager管理
    dcc.Store(id="arrow-connections-data", data=[]),  # 存储箭头连接数据
    dcc.Store(id="dependencies-collapse-state", data={"is_open": False}),  # 存储依赖关系面板折叠状态
    dcc.Store(id="cumulative-plot-data", data=[]),  # 存储累计绘图数据
    dcc.Store(id="selected-x-param", data=None),  # 存储选中的X轴参数
    dcc.Store(id="selected-y-param", data=None),  # 存储选中的Y轴参数
    dcc.Store(id="current-param-type", data="x"),  # 存储当前选择的参数类型
    dcc.Store(id="canvas-events", data=[]),  # 存储画布更新事件
    dcc.Store(id="app-messages", data={"messages": [], "timestamp": 0}),  # 统一消息管理
    dcc.Download(id="download-graph"),  # 用于下载计算图文件
    dcc.Download(id="download-plot-data"),  # 新增：用于下载绘图数据
# 移除旧的context menu，使用新的dropdown menu
    
    # 参数编辑模态窗口
    dbc.Modal([
        dbc.ModalHeader([
            html.H4("编辑参数", id="param-edit-title", style={"fontSize": "1.2rem"})
        ]),
        dbc.ModalBody([
            # 基本参数信息
            dbc.Row([
                dbc.Col([
                    dbc.Label("参数名称:", style={"fontSize": "0.9rem"}),
                    dbc.Input(id="param-edit-name", placeholder="参数名称", debounce=True, style={"fontSize": "0.85rem"})
                ], width=6),
                dbc.Col([
                    dbc.Label("类型:", style={"fontSize": "0.9rem"}),
                    dcc.Dropdown(
                        id="param-edit-type",
                        options=[
                            {"label": "🔢 浮点数 (float)", "value": "float"},
                            {"label": "#️⃣ 整数 (int)", "value": "int"},
                            {"label": "📝 字符串 (string)", "value": "string"}
                        ],
                        value="float",
                        clearable=False,
                        style={"fontSize": "0.85rem"}
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("单位:", style={"fontSize": "0.9rem"}),
                    dbc.Input(id="param-edit-unit", placeholder="单位", debounce=True, style={"fontSize": "0.85rem"})
                ], width=3),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("参数值:", style={"fontSize": "0.9rem"}),
                    html.Div(id="param-edit-value-display", style={
                        "padding": "6px 12px",
                        "backgroundColor": "#f8f9fa",
                        "border": "1px solid #dee2e6",
                        "borderRadius": "4px",
                        "fontSize": "0.85rem",
                        "color": "#495057"
                    })
                ], width=6),
                dbc.Col([
                    dbc.Label("置信度:", style={"fontSize": "0.9rem"}),
                    html.Div(id="param-edit-confidence-display", style={
                        "padding": "6px 12px",
                        "backgroundColor": "#f8f9fa",
                        "border": "1px solid #dee2e6",
                        "borderRadius": "4px",
                        "fontSize": "0.85rem",
                        "color": "#495057"
                    })
                ], width=6),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("描述:", style={"fontSize": "0.9rem"}),
                    dbc.Textarea(id="param-edit-description", placeholder="参数描述", rows=2, debounce=True, style={"fontSize": "0.85rem"})
                ])
            ], className="mb-3"),
            
            html.Hr(),
            
            # 依赖参数选择 - 可折叠
            dbc.Row([
                dbc.Col([
                    html.Div([
                        dbc.Button(
                            ["🔽 ", html.Span("依赖参数")],
                            id="dependencies-collapse-btn-modal",
                            color="outline-secondary",
                            size="sm",
                            className="mb-2",
                            style={"fontSize": "0.85rem"}
                        ),
                        dbc.Collapse([
                            html.Div(id="dependency-selector-container", style={"fontSize": "0.85rem"}),
                            html.Small("选择此参数计算时依赖的其他参数", className="text-muted", style={"fontSize": "0.8rem"})
                        ], id="dependencies-collapse-modal", is_open=False)
                    ])
                ])
            ], className="mb-3"),
            
            html.Hr(),
            
            # 计算函数编辑
            dbc.Row([
                dbc.Col([
                    html.Div([
                        dbc.Label("计算函数:", className="d-inline", style={"fontSize": "0.9rem"}),
                        dbc.ButtonGroup([
                            dbc.Button("Reset", id="param-edit-reset", size="sm", color="secondary", className="ms-2", style={"fontSize": "0.8rem"}),
                            dbc.Button("测试", id="param-edit-test", size="sm", color="info", className="ms-1", style={"fontSize": "0.8rem"}),
                        ], className="float-end")
                    ]),
                    dash_ace.DashAceEditor(
                        id="param-edit-calculation",
                        value="# 计算函数\n# 在这里编写计算逻辑\nresult = value",
                        theme='monokai',
                        mode='python',
                        tabSize=4,
                        enableBasicAutocompletion=True,
                        enableLiveAutocompletion=True,
                        height='500px',
                        style={"width": "100%", "fontFamily": "monospace", "fontSize": "12px"}
                    ),
                    html.Small("使用 dependencies[i].value 访问依赖参数值，将结果赋值给 result 变量", className="text-muted", style={"fontSize": "0.8rem"})
                ])
            ], className="mb-3"),
            
            # 计算结果预览
            dbc.Row([
                dbc.Col([
                    dbc.Label("计算结果预览:", style={"fontSize": "0.9rem"}),
                    dbc.Alert(id="param-edit-preview", color="light", children="点击'测试'按钮查看计算结果", style={"fontSize": "0.85rem"})
                ])
            ], className="mb-3"),
        ]),
        dbc.ModalFooter([
            dbc.Button("取消", id="param-edit-cancel", color="secondary", className="me-2", style={"fontSize": "0.85rem"}),
            dbc.Button("保存", id="param-edit-save", color="primary", style={"fontSize": "0.85rem"})
        ])
    ], id="param-edit-modal", size="lg", is_open=False),
    
    # 存储当前编辑的参数信息
    dcc.Store(id="param-edit-data", data={"node_id": None, "param_index": None}),
    
    # 节点编辑模态窗口
    dbc.Modal([
        dbc.ModalHeader([
            html.H4("编辑节点", id="node-edit-title")
        ]),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("节点名称:"),
                    dbc.Input(id="node-edit-name", placeholder="节点名称", debounce=True)
                ], width=12),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("节点描述:"),
                    dbc.Textarea(id="node-edit-description", placeholder="节点描述", rows=3, debounce=True)
                ])
            ], className="mb-3"),
        ]),
        dbc.ModalFooter([
            dbc.Button("取消", id="node-edit-cancel", color="secondary", className="me-2"),
            dbc.Button("保存", id="node-edit-save", color="primary")
        ])
    ], id="node-edit-modal", size="md", is_open=False),
    
    # 存储当前编辑的节点信息
    dcc.Store(id="node-edit-data", data={"node_id": None}),
    
    # 添加节点模态窗口
    dbc.Modal([
        dbc.ModalHeader([
            html.H4("添加新节点", id="node-add-title")
        ]),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("节点名称:"),
                    dbc.Input(id="node-add-name", placeholder="输入节点名称", debounce=True)
                ], width=12),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("节点描述:"),
                    dbc.Textarea(id="node-add-description", placeholder="节点描述（可选）", rows=3, debounce=True)
                ])
            ], className="mb-3"),
        ]),
        dbc.ModalFooter([
            dbc.Button("取消", id="node-add-cancel", color="secondary", className="me-2"),
            dbc.Button("创建", id="node-add-save", color="primary")
        ])
    ], id="node-add-modal", size="md", is_open=False),
    
    # 放大图表模态窗口
    dbc.Modal([
        dbc.ModalHeader([
            html.H4("📈 参数敏感性分析 - 详细视图", className="modal-title")
        ]),
        dbc.ModalBody([
            dcc.Graph(
                id="enlarged-plot",
                style={"height": "70vh"},
                config={
                    'displayModeBar': True,
                    'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
                    'displaylogo': False,
                    'toImageButtonOptions': {
                        'format': 'png',
                        'filename': 'sensitivity_analysis',
                        'height': 800,
                        'width': 1200,
                        'scale': 2
                    }
                }
            )
        ], className="p-1"),
        dbc.ModalFooter([
            dbc.Button("关闭", id="close-enlarged-plot", color="secondary")
        ])
    ], id="enlarged-plot-modal", size="xl", is_open=False),
    
    # 参数选择弹窗
    dbc.Modal([
        dbc.ModalHeader([
            html.H4("📊 选择绘图参数", className="modal-title")
        ]),
        dbc.ModalBody([
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H6(id="param-type-display", className="mb-3", style={"color": "#0d6efd", "fontWeight": "bold"})
                    ])
                ]),
                dbc.Row([
                    dbc.Col([
                        html.H6("搜索参数:", className="mb-2"),
                        dbc.Input(
                            id="param-search",
                            placeholder="输入参数名称进行搜索...",
                            className="mb-3"
                        )
                    ])
                ]),
                dbc.Row([
                    dbc.Col([
                        html.H6("可用参数:", className="mb-2"),
                        html.Div(
                            id="param-list-container",
                            style={
                                "height": "400px",
                                "overflowY": "auto",
                                "border": "1px solid #dee2e6",
                                "borderRadius": "0.375rem",
                                "padding": "10px"
                            }
                        )
                    ])
                ])
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("取消", id="param-select-cancel", color="secondary")
        ])
    ], id="param-select-modal", size="lg", is_open=False),

    # 使用教程模态窗口
    dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle("📚 ArchDash 使用教程")
        ]),
        dbc.ModalBody([
            html.Div([
                html.H5("🚀 快速开始", className="text-primary mb-3"),
                html.P("ArchDash 是一个强大的架构计算工具，帮您构建和分析复杂的计算图。"),
                
                html.H6("1️⃣ 创建节点", className="mt-4 mb-2"),
                html.Ul([
                    html.Li("点击左上角 ➕ 按钮创建新节点"),
                    html.Li("双击节点可以编辑节点名称和描述"),
                    html.Li("使用节点标题栏的 ➕ 按钮添加参数")
                ]),
                
                html.H6("2️⃣ 管理参数", className="mt-4 mb-2"),
                html.Ul([
                    html.Li("直接编辑参数名称和数值"),
                    html.Li("双击参数可以打开详细编辑面板"),
                    html.Li("在编辑面板中设置参数类型、单位、描述和计算函数"),
                    html.Li("通过依赖关系建立参数间的计算链条")
                ]),
                
                html.H6("3️⃣ 建立依赖关系", className="mt-4 mb-2"),
                html.Ul([
                    html.Li("在参数编辑面板中选择依赖参数"),
                    html.Li("编写计算函数（支持 Python 语法）"),
                    html.Li("点击 🔗 图标重新计算依赖参数"),
                    html.Li("系统会自动检测并防止循环依赖")
                ]),
                
                html.H6("4️⃣ 移动和布局", className="mt-4 mb-2"),
                html.Ul([
                    html.Li("使用节点菜单中的方向键移动节点"),
                    html.Li("通过列管理按钮添加或删除画布列"),
                    html.Li("系统会自动管理节点布局和画布大小")
                ]),
                
                html.H6("5️⃣ 分析和导出", className="mt-4 mb-2"),
                html.Ul([
                    html.Li("使用相关性分析工具研究参数敏感性"),
                    html.Li("支持累计绘图模式对比多个分析结果"),
                    html.Li("通过保存按钮导出完整计算图"),
                    html.Li("支持加载保存的图文件继续编辑")
                ]),
                
                html.Hr(),
                html.Div([
                    html.P([
                        html.Strong("💡 提示："),
                        " 点击 🎯 按钮可以加载一个多核SoC示例，快速了解系统功能。"
                    ], className="text-info"),
                    html.P([
                        html.Strong("⚡ 快捷键："),
                        " 大部分操作都有工具提示，鼠标悬停即可查看详细说明。"
                    ], className="text-success")
                ])
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("开始使用", id="tutorial-close", color="primary", className="me-2"),
            dbc.Button("加载示例", id="tutorial-load-example", color="warning")
        ])
    ], id="tutorial-modal", size="lg", is_open=False),
], fluid=True)

app_index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>🎨 ArchDash </title>
        {%favicon%}
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        {%css%}
        <style>
            /* 保留必要的覆盖样式 */
            .node-name {
                font-weight: bold;
                margin-bottom: 4px;
                color: var(--text-primary);
            }
            .node-content {
                font-size: 0.9em;
                color: var(--text-secondary);
            }
            .param-menu-btn {
                border: none !important;
                background: transparent !important;
                padding: 2px 6px !important;
                font-size: 12px !important;
                color: var(--text-secondary) !important;
                transition: all 0.2s ease !important;
            }
            .param-menu-btn:hover {
                background: var(--glass-bg) !important;
                color: var(--text-primary) !important;
                border-radius: 3px !important;
            }
            
            /* 节点标题栏加号按钮样式 */
            .add-param-btn:hover {
                background: rgba(0, 123, 255, 0.1) !important;
                color: #007bff !important;
                transform: scale(1.05);
            }
            
            /* 节点菜单按钮悬停样式优化 */
            .node-menu-btn:hover {
                background: rgba(108, 117, 125, 0.1) !important;
                color: #495057 !important;
            }
            
            /* SVG箭头样式 - 美化版 */
            #arrows-overlay {
                pointer-events: none;
                z-index: 10;
            }
            
            #arrows-overlay svg {
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            /* 流动虚线动画 - 修正方向 */
            @keyframes flow-dash {
                0% {
                    stroke-dashoffset: 20;
                }
                100% {
                    stroke-dashoffset: 0;
                }
            }
            
            /* 脉冲动画 */
            @keyframes pulse-glow {
                0% {
                    opacity: 0.8;
                }
                100% {
                    opacity: 1;
                }
            }
            
            /* 箭头出现动画 */
            @keyframes arrow-appear {
                0% {
                    opacity: 0;
                    stroke-dasharray: 1000;
                    stroke-dashoffset: 1000;
                }
                60% {
                    opacity: 0.8;
                }
                100% {
                    opacity: 1;
                    stroke-dasharray: none;
                    stroke-dashoffset: 0;
                }
            }
            
            /* 美化pin点的悬停效果 */
            .param-pin {
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            .param-pin:hover {
                transform: scale(1.2);
                background-color: #007bff !important;
            }
            
            .param-pin.active {
                animation: pin-pulse 1.5s ease-in-out infinite;
                background-color: #e74c3c !important;
            }
            
            @keyframes pin-pulse {
                0%, 100% {
                    transform: scale(1);
                }
                50% {
                    transform: scale(1.15);
                }
            }
            
            /* 深色模式下的箭头效果 */
            [data-theme="dark"] #arrows-overlay svg {
                opacity: 0.9;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''
