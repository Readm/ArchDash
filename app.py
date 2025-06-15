import dash
from dash import html, dcc, callback, Output, Input, State, ctx, MATCH, ALL
import dash_bootstrap_components as dbc
from models import CalculationGraph, Node, Parameter
from typing import Dict, Optional
import json
from datetime import datetime

class IDMapper:
    """管理 Model ID 到 Dash ID 和 HTML ID 的映射"""
    def __init__(self):
        self._node_mapping: Dict[str, Dict] = {}

    def register_node(self, node_id: str, name: str) -> None:
        """注册节点 ID 映射"""
        self._node_mapping[node_id] = {
            "name": name,
            "dash_id": {"type": "node", "index": node_id},
            "html_id": f"node-{node_id}"
        }

    def get_dash_id(self, node_id: str) -> Dict:
        """获取 Dash ID"""
        return self._node_mapping[node_id]["dash_id"]

    def get_html_id(self, node_id: str) -> str:
        """获取 HTML ID"""
        return self._node_mapping[node_id]["html_id"]

    def get_node_name(self, node_id: str) -> str:
        """获取节点名称"""
        return self._node_mapping[node_id]["name"]

    def get_node_id_from_dash(self, dash_id: Dict) -> Optional[str]:
        """从 Dash ID 获取节点 ID"""
        try:
            return dash_id["index"]
        except (KeyError, TypeError):
            return None

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# 全局数据模型
graph = CalculationGraph()
id_mapper = IDMapper()

# 辅助函数
def get_all_available_parameters(current_node_id, current_param_name):
    """获取所有可用的参数，排除当前参数自身"""
    available_params = []
    for node_id, node in graph.nodes.items():
        for param in node.parameters:
            if not (node_id == current_node_id and param.name == current_param_name):
                available_params.append({
                    'node_id': node_id,
                    'node_name': node.name,
                    'param_name': param.name,
                    'param_obj': param,
                    'display_name': f"{node.name}.{param.name}",
                    'value': f"节点:{node.name} 参数:{param.name} 值:{param.value} {param.unit}"
                })
    return available_params

def generate_code_template(selected_dependencies):
    """生成基础计算函数模板"""
    if not selected_dependencies:
        return "# 无依赖参数\nresult = value"
    
    code_lines = ["# 计算函数"]
    for i, dep_info in enumerate(selected_dependencies):
        code_lines.append(f"# {dep_info['param_name']} = dependencies[{i}].value")
    
    code_lines.extend([
        "",
        "# 在这里编写计算逻辑",
        "result = value  # 修改这里"
    ])
    
    return "\n".join(code_lines)

def create_dependency_checkboxes(available_params, selected_deps=None):
    """创建依赖参数复选框列表"""
    if selected_deps is None:
        selected_deps = []
    
    checkboxes = []
    for param_info in available_params:
        is_checked = param_info['display_name'] in selected_deps
        checkbox = dbc.Checkbox(
            id={"type": "dependency-checkbox", "param": param_info['display_name']},
            label=param_info['value'],
            value=is_checked,
            className="mb-2"
        )
        checkboxes.append(checkbox)
    
    if not checkboxes:
        return [html.P("暂无可用的依赖参数", className="text-muted")]
    
    return checkboxes

# 画布更新函数
def update_canvas(node_data):
    canvas_content = []
    for i in range(node_data["columns"]):
        col_content = []
        for node_id, data in node_data["nodes"].items():
            if data["col"] == i:
                node_name = id_mapper.get_node_name(node_id)
                # 获取参数列表
                node = graph.nodes.get(node_id)
                param_rows = []
                if node and hasattr(node, "parameters"):
                    for i, param in enumerate(node.parameters):
                        param_rows.append(
                            html.Tr([
                                html.Td(
                                    dcc.Input(
                                        id={"type": "param-name", "node": node_id, "index": i},
                                        value=param.name,
                                        style={"width": "100%", "border": "1px solid transparent", "background": "transparent", "fontWeight": "bold", "borderRadius": "3px", "padding": "2px 4px"},
                                        className="param-input"
                                    ),
                                    style={"paddingRight": "8px", "width": "40%"}
                                ),
                                html.Td(
                                    dcc.Input(
                                        id={"type": "param-value", "node": node_id, "index": i},
                                        value=str(param.value),
                                        style={"width": "100%", "border": "1px solid transparent", "background": "transparent", "borderRadius": "3px", "padding": "2px 4px"},
                                        className="param-input"
                                    ),
                                    style={"width": "40%"}
                                ),
                                html.Td(
                                    dbc.DropdownMenu(
                                        children=[
                                            dbc.DropdownMenuItem("编辑参数", id={"type": "edit-param", "node": node_id, "index": i}, className="text-primary"),
                                            dbc.DropdownMenuItem(divider=True),
                                            dbc.DropdownMenuItem("删除参数", id={"type": "delete-param", "node": node_id, "index": i}, className="text-danger"),
                                            dbc.DropdownMenuItem(divider=True),
                                            dbc.DropdownMenuItem("上移", id={"type": "move-param-up", "node": node_id, "index": i}, disabled=i==0),
                                            dbc.DropdownMenuItem("下移", id={"type": "move-param-down", "node": node_id, "index": i}, disabled=i==len(node.parameters)-1),
                                        ],
                                        toggle_class_name="param-menu-btn",
                                        label="⋮",
                                        size="sm",
                                        direction="left"
                                    ),
                                    style={"width": "20%", "textAlign": "right", "paddingLeft": "4px"}
                                )
                            ])
                        )
                param_table = html.Table(param_rows, style={"width": "100%", "fontSize": "0.95em", "marginTop": "4px"}) if param_rows else None
                node_div = html.Div(
                    [
                        html.Div([
                            html.Div(f"节点: {node_name}", className="node-name"),
                            html.Button("⋮", id={"type": "node-menu", "index": node_id}, className="btn btn-sm btn-link", style={"float": "right", "padding": "0 4px"})
                        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}),
                        param_table,
                        html.Div(id=f"node-content-{node_id}", className="node-content")
                    ],
                    className="p-2 border m-2 node-container",
                    id=id_mapper.get_html_id(node_id),  # 使用HTML ID作为主ID
                    **{"data-col": data["col"], "data-dash-id": json.dumps(id_mapper.get_dash_id(node_id))}
                )
                col_content.append(node_div)
        canvas_content.append(dbc.Col(col_content, width=12 // node_data["columns"]))
    return dbc.Row(canvas_content)

app.layout = dbc.Container([
    html.H1("ArchDash", className="text-center my-4"),
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Label("节点名称："),
                dcc.Input(id="node-name", type="text", placeholder="请输入节点名称"),
                html.Button("添加节点", id="add-node-button", className="btn btn-primary mt-2"),
            ]),
        ], width=6),
        dbc.Col([
            html.Div(id="output-result", className="mt-4"),
        ], width=6),
    ]),
    dbc.Row([
        dbc.Col([
            html.Div(id="canvas-container", className="border p-3 mt-4", style={"height": "400px", "background-color": "#f8f9fa"}),
        ], width=12),
    ]),
    dbc.Row([
        dbc.Col([
            html.Button("添加列", id="add-column-button", className="btn btn-primary mt-2"),
        ], width=12),
    ]),
    dcc.Store(id="node-data", data={"nodes": {}, "columns": 1}),
    dcc.Store(id="context-menu-data", data={"node": None, "action": None}),
    dbc.Modal([
        dbc.ModalHeader("节点操作"),
        dbc.ModalBody([
            dbc.Button("左移", id="move-left", className="btn btn-primary m-2"),
            dbc.Button("右移", id="move-right", className="btn btn-primary m-2"),
            dbc.Button("添加参数", id="add-param", className="btn btn-primary m-2"),
        ]),
    ], id="context-menu", is_open=False),
    
    # 参数编辑模态窗口
    dbc.Modal([
        dbc.ModalHeader([
            html.H4("编辑参数", id="param-edit-title")
        ]),
        dbc.ModalBody([
            # 基本参数信息
            dbc.Row([
                dbc.Col([
                    dbc.Label("参数名称:"),
                    dbc.Input(id="param-edit-name", placeholder="参数名称")
                ], width=8),
                dbc.Col([
                    dbc.Label("单位:"),
                    dbc.Input(id="param-edit-unit", placeholder="单位")
                ], width=4),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("参数值:"),
                    dbc.Input(id="param-edit-value", placeholder="参数值", type="number")
                ], width=6),
                dbc.Col([
                    dbc.Label("置信度:"),
                    dbc.Input(id="param-edit-confidence", placeholder="0.0-1.0", type="number", min=0, max=1, step=0.1)
                ], width=6),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("描述:"),
                    dbc.Textarea(id="param-edit-description", placeholder="参数描述", rows=2)
                ])
            ], className="mb-3"),
            
            html.Hr(),
            
            # 依赖参数选择
            dbc.Row([
                dbc.Col([
                    dbc.Label("依赖参数:"),
                    html.Div(id="dependency-selector-container"),
                    html.Small("选择此参数计算时依赖的其他参数", className="text-muted")
                ])
            ], className="mb-3"),
            
            html.Hr(),
            
            # 计算函数编辑
            dbc.Row([
                dbc.Col([
                    html.Div([
                        dbc.Label("计算函数:", className="d-inline"),
                        dbc.ButtonGroup([
                            dbc.Button("Reset", id="param-edit-reset", size="sm", color="secondary", className="ms-2"),
                            dbc.Button("测试", id="param-edit-test", size="sm", color="info", className="ms-1"),
                        ], className="float-end")
                    ]),
                    dbc.Textarea(
                        id="param-edit-calculation", 
                        placeholder="# 计算函数\n# 在这里编写计算逻辑\nresult = value",
                        rows=8,
                        style={"fontFamily": "monospace", "fontSize": "12px"}
                    ),
                    html.Small("使用 dependencies[i].value 访问依赖参数值，将结果赋值给 result 变量", className="text-muted")
                ])
            ], className="mb-3"),
            
            # 计算结果预览
            dbc.Row([
                dbc.Col([
                    dbc.Label("计算结果预览:"),
                    dbc.Alert(id="param-edit-preview", color="light", children="点击'测试'按钮查看计算结果")
                ])
            ], className="mb-3"),
        ]),
        dbc.ModalFooter([
            dbc.Button("取消", id="param-edit-cancel", color="secondary", className="me-2"),
            dbc.Button("保存", id="param-edit-save", color="primary")
        ])
    ], id="param-edit-modal", size="lg", is_open=False),
    
    # 存储当前编辑的参数信息
    dcc.Store(id="param-edit-data", data={"node_id": None, "param_index": None}),
], fluid=True)

# 添加自定义CSS样式
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .node-container {
                background-color: white;
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            }
            .node-container:hover {
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            .param-input:hover {
                border: 1px solid #ddd !important;
                background: #f8f9fa !important;
            }
            .param-input:focus {
                outline: none !important;
                border: 2px solid #007bff !important;
                background: white !important;
                box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25) !important;
            }
            .node-name {
                font-weight: bold;
                margin-bottom: 4px;
            }
            .node-content {
                font-size: 0.9em;
                color: #666;
            }
            .param-menu-btn {
                border: none !important;
                background: transparent !important;
                padding: 2px 6px !important;
                font-size: 12px !important;
                color: #666 !important;
                transition: all 0.2s ease !important;
            }
            .param-menu-btn:hover {
                background: #f8f9fa !important;
                color: #333 !important;
                border-radius: 3px !important;
            }
            .dropdown-menu {
                font-size: 0.9em !important;
                min-width: 120px !important;
                border: 1px solid #dee2e6 !important;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
            }
            .dropdown-item {
                padding: 6px 12px !important;
                font-size: 0.9em !important;
            }
            .dropdown-item:hover {
                background-color: #f8f9fa !important;
            }
            .dropdown-item.text-danger:hover {
                background-color: #f5c6cb !important;
                color: #721c24 !important;
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

@callback(
    Output("output-result", "children"),
    Output("node-data", "data"),
    Output("canvas-container", "children"),
    Output("context-menu", "is_open"),
    Input("add-node-button", "n_clicks"),
    Input("add-column-button", "n_clicks"),
    Input("context-menu-data", "data"),
    Input("move-left", "n_clicks"),
    Input("move-right", "n_clicks"),
    Input("add-param", "n_clicks"),
    State("node-name", "value"),
    State("node-data", "data"),
    prevent_initial_call=True
)
def update_output(n_clicks, add_column, context_menu_data, move_left, move_right, add_param, node_name, node_data):
    if ctx.triggered_id == "add-node-button":
        if not node_name:
            return "请输入节点名称", node_data, [], False
        
        # 添加节点到数据模型
        node = Node(name=node_name, description=f"节点 {node_name}")
        graph.add_node(node)
        id_mapper.register_node(node.id, node_name)
        
        # 更新节点数据
        node_data["nodes"][node.id] = {"col": 0}
        
        # 更新画布
        return f"节点 {node_name} 已添加", node_data, update_canvas(node_data), False
    
    elif ctx.triggered_id == "add-column-button":
        node_data["columns"] += 1
        return f"已添加新列，当前列数: {node_data['columns']}", node_data, update_canvas(node_data), False
    
    elif ctx.triggered_id == "context-menu-data":
        node_id = context_menu_data.get("node")
        if not node_id:
            return "无效操作", node_data, update_canvas(node_data), False
        return "请选择操作", node_data, update_canvas(node_data), True
    
    elif ctx.triggered_id == "move-left":
        node_id = context_menu_data.get("node")
        if not node_id:
            return "无效操作", node_data, update_canvas(node_data), False
        if node_data["nodes"][node_id]["col"] > 0:
            node_data["nodes"][node_id]["col"] -= 1
        node_name = id_mapper.get_node_name(node_id)
        return f"节点 {node_name} 已左移", node_data, update_canvas(node_data), False
    
    elif ctx.triggered_id == "move-right":
        node_id = context_menu_data.get("node")
        if not node_id:
            return "无效操作", node_data, update_canvas(node_data), False
        if node_data["nodes"][node_id]["col"] < node_data["columns"] - 1:
            node_data["nodes"][node_id]["col"] += 1
        node_name = id_mapper.get_node_name(node_id)
        return f"节点 {node_name} 已右移", node_data, update_canvas(node_data), False
    
    elif ctx.triggered_id == "add-param":
        node_id = context_menu_data.get("node")
        if not node_id:
            return "无效操作", node_data, update_canvas(node_data), False
        node_name = id_mapper.get_node_name(node_id)
        param = Parameter(name="test_param", value=0.0, unit="V", description=f"参数 {node_name}")
        
        # 使用计算图的方法添加参数，确保正确设置graph引用
        if hasattr(graph, 'add_parameter_to_node'):
            graph.add_parameter_to_node(node_id, param)
        else:
            # 兼容旧方法
            graph.nodes[node_id].add_parameter(param)
            # 手动设置graph引用
            param.set_graph(graph)
        
        return f"参数 test_param 已添加到节点 {node_name}", node_data, update_canvas(node_data), False

@callback(
    Output("context-menu-data", "data"),
    Input({"type": "node-menu", "index": ALL}, "n_clicks"),
    State({"type": "node-menu", "index": ALL}, "id"),
    prevent_initial_call=True
)
def show_context_menu(menu_clicks_list, menu_ids):
    if not ctx.triggered_id:
        return {"node": None, "action": None}
    
    # 检查触发值，避免重新创建组件时的误触发
    trigger_value = ctx.triggered[0]["value"]
    if not trigger_value or trigger_value == 0:
        return {"node": None, "action": None}
    
    # 获取被点击的节点ID
    triggered_id = ctx.triggered_id
    if isinstance(triggered_id, dict):
        if triggered_id["type"] == "node-menu":
            node_id = triggered_id["index"]
        else:
            node_id = None
    else:
        import ast
        try:
            node_id = ast.literal_eval(triggered_id.replace(".n_clicks", ""))["index"]
        except Exception:
            node_id = None
    
    if node_id is None:
        return {"node": None, "action": None}
    
    return {"node": node_id, "action": "show-menu"}

# 添加参数更新回调
@callback(
    Output("node-data", "data", allow_duplicate=True),
    Input({"type": "param-name", "node": ALL, "index": ALL}, "value"),
    Input({"type": "param-value", "node": ALL, "index": ALL}, "value"),
    State("node-data", "data"),
    prevent_initial_call=True
)
def update_parameter(param_names, param_values, node_data):
    if not ctx.triggered_id:
        return node_data
    
    triggered_id = ctx.triggered_id
    if isinstance(triggered_id, dict):
        node_id = triggered_id["node"]
        param_index = triggered_id["index"]
        param_type = triggered_id["type"]
        
        # 获取触发的新值
        new_value = ctx.triggered[0]["value"]
        
        # 检查值是否为空或无效
        if new_value is None or new_value == "":
            return node_data
        
        # 获取节点
        node = graph.nodes.get(node_id)
        if not node:
            return node_data
            
        # 检查参数索引是否有效
        if param_index >= len(node.parameters):
            return node_data
            
        # 获取当前参数
        current_param = node.parameters[param_index]
        
        if param_type == "param-name":
            # 更新参数名，检查是否真的有变化
            if new_value != current_param.name:
                current_param.name = new_value
        elif param_type == "param-value":
            # 更新参数值
            try:
                if new_value is not None and new_value != "":
                    if isinstance(new_value, str) and '.' in new_value:
                        new_value = float(new_value)
                    elif isinstance(new_value, str):
                        new_value = int(new_value)
                    else:
                        new_value = param_value
                else:
                    new_value = 0
            except (ValueError, TypeError):
                new_value = str(param_value) if param_value is not None else ""
            
            # 使用数据流机制更新参数值，这会自动触发依赖参数的重新计算
            if hasattr(graph, 'set_parameter_value'):
                # 使用新的数据流更新机制
                update_result = graph.set_parameter_value(current_param, new_value)
                cascaded_info = ""
                if update_result['cascaded_updates']:
                    affected_params = [update['param'].name for update in update_result['cascaded_updates']]
                    cascaded_info = f"，同时更新了 {len(affected_params)} 个关联参数: {', '.join(affected_params)}"
            else:
                # 兼容旧方法
                current_param.value = new_value
    
    # 不重新渲染画布，只更新数据
    return node_data

# 添加参数操作回调 - 完全独立于节点菜单
@callback(
    Output("node-data", "data", allow_duplicate=True),
    Output("canvas-container", "children", allow_duplicate=True),
    Input({"type": "delete-param", "node": ALL, "index": ALL}, "n_clicks"),
    Input({"type": "move-param-up", "node": ALL, "index": ALL}, "n_clicks"),
    Input({"type": "move-param-down", "node": ALL, "index": ALL}, "n_clicks"),
    State("node-data", "data"),
    prevent_initial_call=True
)
def handle_parameter_operations(delete_clicks, move_up_clicks, move_down_clicks, node_data):
    if not ctx.triggered_id:
        return node_data, update_canvas(node_data)
    
    triggered_id = ctx.triggered_id
    if not isinstance(triggered_id, dict):
        return node_data, update_canvas(node_data)
    
    node_id = triggered_id.get("node")
    param_index = triggered_id.get("index")
    operation_type = triggered_id.get("type")
    
    # 检查点击数值，避免初始化时的误触发
    trigger_value = ctx.triggered[0]["value"]
    if not trigger_value or trigger_value == 0:
        return node_data, update_canvas(node_data)
    
    if not node_id or param_index is None:
        return node_data, update_canvas(node_data)
    
    # 获取节点
    node = graph.nodes.get(node_id)
    if not node:
        return node_data, update_canvas(node_data)
        
    if param_index >= len(node.parameters):
        return node_data, update_canvas(node_data)
    
    node_name = id_mapper.get_node_name(node_id)
    param_name = node.parameters[param_index].name
    
    if operation_type == "delete-param":
        # 删除参数
        deleted_param = node.parameters.pop(param_index)
        # 可以添加一个静默的操作记录（如果需要）
        
    elif operation_type == "move-param-up":
        # 上移参数
        if param_index > 0:
            node.parameters[param_index], node.parameters[param_index - 1] = \
                node.parameters[param_index - 1], node.parameters[param_index]
            
    elif operation_type == "move-param-down":
        # 下移参数
        if param_index < len(node.parameters) - 1:
            node.parameters[param_index], node.parameters[param_index + 1] = \
                node.parameters[param_index + 1], node.parameters[param_index]
    
    # 参数操作完成，只更新数据和画布，不影响任何其他UI组件
    return node_data, update_canvas(node_data)

# 打开参数编辑模态窗口
@callback(
    Output("param-edit-modal", "is_open"),
    Output("param-edit-title", "children"),
    Output("param-edit-name", "value"),
    Output("param-edit-value", "value"),
    Output("param-edit-unit", "value"),
    Output("param-edit-description", "value"),
    Output("param-edit-confidence", "value"),
    Output("param-edit-calculation", "value"),
    Output("dependency-selector-container", "children"),
    Output("param-edit-data", "data"),
    Input({"type": "edit-param", "node": ALL, "index": ALL}, "n_clicks"),
    State("param-edit-modal", "is_open"),
    prevent_initial_call=True
)
def open_param_edit_modal(edit_clicks, is_open):
    if not ctx.triggered_id:
        raise dash.exceptions.PreventUpdate
    
    # 检查触发值，避免重新创建组件时的误触发
    trigger_value = ctx.triggered[0]["value"]
    if not trigger_value or trigger_value == 0:
        raise dash.exceptions.PreventUpdate
    
    # 获取被点击的参数信息
    triggered_id = ctx.triggered_id
    if isinstance(triggered_id, dict) and triggered_id["type"] == "edit-param":
        node_id = triggered_id["node"]
        param_index = triggered_id["index"]
        
        # 获取参数对象
        if node_id not in graph.nodes:
            raise dash.exceptions.PreventUpdate
        
        node = graph.nodes[node_id]
        if param_index >= len(node.parameters):
            raise dash.exceptions.PreventUpdate
        
        param = node.parameters[param_index]
        node_name = id_mapper.get_node_name(node_id)
        
        # 获取所有可用的依赖参数
        available_params = get_all_available_parameters(node_id, param.name)
        
        # 获取当前参数的依赖列表
        current_dependencies = [f"{dep_param.name}" for dep_param in param.dependencies]
        
        # 创建依赖复选框
        dependency_checkboxes = create_dependency_checkboxes(available_params, current_dependencies)
        
        return (
            True,  # 打开模态窗口
            f"编辑参数: {node_name}.{param.name}",
            param.name,
            param.value,
            param.unit,
            param.description,
            param.confidence,
            param.calculation_func or "",
            dependency_checkboxes,
            {"node_id": node_id, "param_index": param_index}
        )
    
    raise dash.exceptions.PreventUpdate

# 关闭参数编辑模态窗口
@callback(
    Output("param-edit-modal", "is_open", allow_duplicate=True),
    Input("param-edit-cancel", "n_clicks"),
    prevent_initial_call=True
)
def close_param_edit_modal(cancel_clicks):
    if cancel_clicks:
        return False
    raise dash.exceptions.PreventUpdate

# Reset按钮：生成代码模板
@callback(
    Output("param-edit-calculation", "value", allow_duplicate=True),
    Input("param-edit-reset", "n_clicks"),
    State({"type": "dependency-checkbox", "param": ALL}, "value"),
    State({"type": "dependency-checkbox", "param": ALL}, "id"),
    State("param-edit-data", "data"),
    prevent_initial_call=True
)
def reset_calculation_code(reset_clicks, checkbox_values, checkbox_ids, edit_data):
    if not reset_clicks:
        raise dash.exceptions.PreventUpdate
    
    # 获取选中的依赖
    selected_dependencies = []
    if checkbox_values and checkbox_ids:
        for value, checkbox_id in zip(checkbox_values, checkbox_ids):
            if value:  # 如果复选框被选中
                param_name = checkbox_id["param"]
                selected_dependencies.append({"param_name": param_name.split(".")[-1]})
    
    # 生成代码模板
    template_code = generate_code_template(selected_dependencies)
    return template_code

# 测试计算功能
@callback(
    Output("param-edit-preview", "children"),
    Output("param-edit-preview", "color"),
    Input("param-edit-test", "n_clicks"),
    State("param-edit-calculation", "value"),
    State("param-edit-value", "value"),
    State({"type": "dependency-checkbox", "param": ALL}, "value"),
    State({"type": "dependency-checkbox", "param": ALL}, "id"),
    State("param-edit-data", "data"),
    prevent_initial_call=True
)
def test_calculation(test_clicks, calculation_code, current_value, checkbox_values, checkbox_ids, edit_data):
    if not test_clicks:
        raise dash.exceptions.PreventUpdate
    
    try:
        # 获取选中的依赖参数
        selected_deps = []
        if checkbox_values and checkbox_ids:
            for value, checkbox_id in zip(checkbox_values, checkbox_ids):
                if value:  # 如果复选框被选中
                    param_display_name = checkbox_id["param"]
                    # 找到对应的参数对象
                    node_id = edit_data["node_id"]
                    available_params = get_all_available_parameters(node_id, "")
                    for param_info in available_params:
                        if param_info["display_name"] == param_display_name:
                            selected_deps.append(param_info["param_obj"])
                            break
        
        # 如果没有计算函数，直接返回当前值
        if not calculation_code or calculation_code.strip() == "":
            return f"当前值: {current_value}", "info"
        
        # 创建计算环境
        local_env = {
            'dependencies': selected_deps,
            'value': current_value or 0,
            'datetime': datetime
        }
        
        # 执行计算代码
        exec(calculation_code, {"__builtins__": {}}, local_env)
        result = local_env.get('result', None)
        
        if result is None:
            return "错误: 计算函数未设置result变量", "warning"
        
        return f"计算结果: {result}", "success"
        
    except Exception as e:
        return f"计算错误: {str(e)}", "danger"

# 保存参数修改
@callback(
    Output("param-edit-modal", "is_open", allow_duplicate=True),
    Output("canvas-container", "children", allow_duplicate=True),
    Output("output-result", "children", allow_duplicate=True),
    Input("param-edit-save", "n_clicks"),
    State("param-edit-name", "value"),
    State("param-edit-value", "value"),
    State("param-edit-unit", "value"),
    State("param-edit-description", "value"),
    State("param-edit-confidence", "value"),
    State("param-edit-calculation", "value"),
    State({"type": "dependency-checkbox", "param": ALL}, "value"),
    State({"type": "dependency-checkbox", "param": ALL}, "id"),
    State("param-edit-data", "data"),
    State("node-data", "data"),
    prevent_initial_call=True
)
def save_parameter_changes(save_clicks, param_name, param_value, param_unit, param_description, 
                          param_confidence, calculation_code, checkbox_values, checkbox_ids, 
                          edit_data, node_data):
    if not save_clicks:
        raise dash.exceptions.PreventUpdate
    
    try:
        # 验证输入
        if not param_name or not param_name.strip():
            return True, dash.no_update, "错误: 参数名称不能为空"
        
        node_id = edit_data["node_id"]
        param_index = edit_data["param_index"]
        
        if node_id not in graph.nodes:
            return True, dash.no_update, "错误: 节点不存在"
        
        node = graph.nodes[node_id]
        if param_index >= len(node.parameters):
            return True, dash.no_update, "错误: 参数不存在"
        
        param = node.parameters[param_index]
        
        # 获取选中的依赖参数
        selected_deps = []
        if checkbox_values and checkbox_ids:
            for value, checkbox_id in zip(checkbox_values, checkbox_ids):
                if value:  # 如果复选框被选中
                    param_display_name = checkbox_id["param"]
                    # 找到对应的参数对象
                    available_params = get_all_available_parameters(node_id, param_name)
                    for param_info in available_params:
                        if param_info["display_name"] == param_display_name:
                            selected_deps.append(param_info["param_obj"])
                            break
        
        # 检查循环依赖
        def has_circular_dependency(target_param, dep_param, visited=None):
            """检查是否存在循环依赖"""
            if visited is None:
                visited = set()
            
            if dep_param is target_param:
                return True
            
            if id(dep_param) in visited:
                return False
            
            visited.add(id(dep_param))
            
            for sub_dep in dep_param.dependencies:
                if has_circular_dependency(target_param, sub_dep, visited.copy()):
                    return True
            
            return False
        
        # 检查所有选中的依赖是否会造成循环依赖
        for dep_param in selected_deps:
            if has_circular_dependency(param, dep_param):
                return True, dash.no_update, f"错误: 添加依赖 {dep_param.name} 会造成循环依赖"
        
        # 更新参数基本信息
        param.name = param_name.strip()
        param.unit = param_unit.strip() if param_unit else ""
        param.description = param_description.strip() if param_description else ""
        
        # 更新参数值
        try:
            if param_value is not None and param_value != "":
                if isinstance(param_value, str) and '.' in param_value:
                    new_value = float(param_value)
                elif isinstance(param_value, str):
                    new_value = int(param_value)
                else:
                    new_value = param_value
            else:
                new_value = 0
        except (ValueError, TypeError):
            new_value = str(param_value) if param_value is not None else ""
        
        # 使用数据流机制更新参数值，这会自动触发依赖参数的重新计算
        if hasattr(graph, 'set_parameter_value'):
            # 使用新的数据流更新机制
            update_result = graph.set_parameter_value(param, new_value)
            cascaded_info = ""
            if update_result['cascaded_updates']:
                affected_params = [update['param'].name for update in update_result['cascaded_updates']]
                cascaded_info = f"，同时更新了 {len(affected_params)} 个关联参数: {', '.join(affected_params)}"
        else:
            # 兼容旧方法
            param.value = new_value
        
        # 更新置信度
        try:
            param.confidence = float(param_confidence) if param_confidence is not None else 1.0
            param.confidence = max(0.0, min(1.0, param.confidence))  # 限制在0-1之间
        except (ValueError, TypeError):
            param.confidence = 1.0
        
        # 更新计算函数
        param.calculation_func = calculation_code.strip() if calculation_code else None
        
        # 清除旧的依赖关系
        param.dependencies.clear()
        
        # 添加新的依赖关系
        for dep_param in selected_deps:
            param.add_dependency(dep_param)
        
        # 确保依赖关系更新到计算图
        if hasattr(graph, 'update_parameter_dependencies'):
            graph.update_parameter_dependencies(param)
        
        # 如果有计算函数，尝试执行计算
        if param.calculation_func:
            try:
                result = param.calculate()
                success_msg = f"参数 {param_name} 已保存并计算，结果: {result}{cascaded_info}"
            except Exception as calc_error:
                success_msg = f"参数 {param_name} 已保存，但计算失败: {str(calc_error)}"
        else:
            success_msg = f"参数 {param_name} 已保存{cascaded_info}"
        
        # 更新画布显示
        updated_canvas = update_canvas(node_data)
        
        return False, updated_canvas, success_msg
        
    except Exception as e:
        return True, dash.no_update, f"保存失败: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050) 