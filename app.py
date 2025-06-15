import dash
from dash import html, dcc, callback, Output, Input, State, ctx, MATCH, ALL
import dash_bootstrap_components as dbc
from models import CalculationGraph, Node, Parameter
from typing import Dict, Optional
import json

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

# 画布更新函数
def update_canvas(node_data):
    # 确保所有节点都有row属性
    for node_id, data in node_data["nodes"].items():
        if "row" not in data:
            data["row"] = 0
    
    canvas_content = []
    for col_index in range(node_data["columns"]):
        col_content = []
        # 获取当前列的所有节点并按row排序
        nodes_in_col = [(node_id, data) for node_id, data in node_data["nodes"].items() 
                       if data["col"] == col_index]
        nodes_in_col.sort(key=lambda x: x[1].get("row", 0))
        
        for node_id, data in nodes_in_col:
            node_name = id_mapper.get_node_name(node_id)
            # 获取参数列表
            node = graph.nodes.get(node_id)
            param_rows = []
            if node and hasattr(node, "parameters"):
                for param_index, param in enumerate(node.parameters):
                    param_rows.append(
                        html.Tr([
                            html.Td(
                                dcc.Input(
                                    id={"type": "param-name", "node": node_id, "index": param_index},
                                    value=param.name,
                                    style={"width": "100%", "border": "1px solid transparent", "background": "transparent", "fontWeight": "bold", "borderRadius": "3px", "padding": "2px 4px"},
                                    className="param-input"
                                ),
                                style={"paddingRight": "8px", "width": "40%"}
                            ),
                            html.Td(
                                dcc.Input(
                                    id={"type": "param-value", "node": node_id, "index": param_index},
                                    value=str(param.value),
                                    style={"width": "100%", "border": "1px solid transparent", "background": "transparent", "borderRadius": "3px", "padding": "2px 4px"},
                                    className="param-input"
                                ),
                                style={"width": "40%"}
                            ),
                            html.Td(
                                dbc.DropdownMenu(
                                    children=[
                                        dbc.DropdownMenuItem("删除参数", id={"type": "delete-param", "node": node_id, "index": param_index}, className="text-danger"),
                                        dbc.DropdownMenuItem(divider=True),
                                        dbc.DropdownMenuItem("上移", id={"type": "move-param-up", "node": node_id, "index": param_index}, disabled=param_index==0),
                                        dbc.DropdownMenuItem("下移", id={"type": "move-param-down", "node": node_id, "index": param_index}, disabled=param_index==len(node.parameters)-1),
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
                **{"data-col": data["col"], "data-row": data.get("row", 0), "data-dash-id": json.dumps(id_mapper.get_dash_id(node_id))}
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
            html.Hr(),
            dbc.Button("上移", id="move-node-up", className="btn btn-secondary m-2"),
            dbc.Button("下移", id="move-node-down", className="btn btn-secondary m-2"),
            html.Hr(),
            dbc.Button("添加参数", id="add-param", className="btn btn-success m-2"),
            dbc.Button("删除节点", id="delete-node", className="btn btn-danger m-2"),
        ]),
    ], id="context-menu", is_open=False),
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
    Input("move-node-up", "n_clicks"),
    Input("move-node-down", "n_clicks"),
    Input("add-param", "n_clicks"),
    Input("delete-node", "n_clicks"),
    State("node-name", "value"),
    State("node-data", "data"),
    prevent_initial_call=True
)
def update_output(n_clicks, add_column, context_menu_data, move_left, move_right, move_node_up, move_node_down, add_param, delete_node, node_name, node_data):
    if ctx.triggered_id == "add-node-button":
        if not node_name or not node_name.strip():
            return "请输入节点名称", node_data, update_canvas(node_data), False
        
        # 添加节点到数据模型（CalculationGraph会自动检查重名）
        try:
            node = Node(name=node_name, description=f"节点 {node_name}")
            graph.add_node(node)
            id_mapper.register_node(node.id, node_name)
            
            # 更新节点数据，添加row属性来跟踪节点在列中的位置
            max_row = 0
            for existing_node_data in node_data["nodes"].values():
                if existing_node_data["col"] == 0:
                    max_row = max(max_row, existing_node_data.get("row", 0))
            
            node_data["nodes"][node.id] = {"col": 0, "row": max_row + 1}
            
            # 更新画布
            return f"节点 {node_name} 已添加", node_data, update_canvas(node_data), False
        except ValueError as e:
            # 捕获重名或其他错误
            if "already exists" in str(e):
                return f"错误：节点名称 '{node_name}' 已存在，请使用不同的名称", node_data, update_canvas(node_data), False
            else:
                return f"错误：{str(e)}", node_data, update_canvas(node_data), False
    
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
            new_col = node_data["nodes"][node_id]["col"] - 1
            # 计算目标列的最大row值
            max_row = 0
            for ndata in node_data["nodes"].values():
                if ndata["col"] == new_col:
                    max_row = max(max_row, ndata.get("row", 0))
            
            node_data["nodes"][node_id]["col"] = new_col
            node_data["nodes"][node_id]["row"] = max_row + 1
        node_name = id_mapper.get_node_name(node_id)
        return f"节点 {node_name} 已左移", node_data, update_canvas(node_data), False
    
    elif ctx.triggered_id == "move-right":
        node_id = context_menu_data.get("node")
        if not node_id:
            return "无效操作", node_data, update_canvas(node_data), False
        if node_data["nodes"][node_id]["col"] < node_data["columns"] - 1:
            new_col = node_data["nodes"][node_id]["col"] + 1
            # 计算目标列的最大row值
            max_row = 0
            for ndata in node_data["nodes"].values():
                if ndata["col"] == new_col:
                    max_row = max(max_row, ndata.get("row", 0))
            
            node_data["nodes"][node_id]["col"] = new_col
            node_data["nodes"][node_id]["row"] = max_row + 1
        node_name = id_mapper.get_node_name(node_id)
        return f"节点 {node_name} 已右移", node_data, update_canvas(node_data), False
    
    elif ctx.triggered_id == "move-node-up":
        node_id = context_menu_data.get("node")
        if not node_id:
            return "无效操作", node_data, update_canvas(node_data), False
        
        current_node = node_data["nodes"][node_id]
        current_col = current_node["col"]
        current_row = current_node.get("row", 0)
        
        # 找到同一列中可以交换的上一个节点
        nodes_in_same_col = [(nid, ndata) for nid, ndata in node_data["nodes"].items() 
                           if ndata["col"] == current_col and ndata.get("row", 0) < current_row]
        
        if nodes_in_same_col:
            # 按row排序，找到最接近的上一个节点
            nodes_in_same_col.sort(key=lambda x: x[1].get("row", 0), reverse=True)
            swap_node_id, swap_node_data = nodes_in_same_col[0]
            
            # 交换两个节点的row位置
            node_data["nodes"][node_id]["row"], node_data["nodes"][swap_node_id]["row"] = \
                swap_node_data.get("row", 0), current_row
            
            node_name = id_mapper.get_node_name(node_id)
            return f"节点 {node_name} 已上移", node_data, update_canvas(node_data), False
        else:
            node_name = id_mapper.get_node_name(node_id)
            return f"节点 {node_name} 已经在最上方", node_data, update_canvas(node_data), False
    
    elif ctx.triggered_id == "move-node-down":
        node_id = context_menu_data.get("node")
        if not node_id:
            return "无效操作", node_data, update_canvas(node_data), False
        
        current_node = node_data["nodes"][node_id]
        current_col = current_node["col"]
        current_row = current_node.get("row", 0)
        
        # 找到同一列中可以交换的下一个节点
        nodes_in_same_col = [(nid, ndata) for nid, ndata in node_data["nodes"].items() 
                           if ndata["col"] == current_col and ndata.get("row", 0) > current_row]
        
        if nodes_in_same_col:
            # 按row排序，找到最接近的下一个节点
            nodes_in_same_col.sort(key=lambda x: x[1].get("row", 0))
            swap_node_id, swap_node_data = nodes_in_same_col[0]
            
            # 交换两个节点的row位置
            node_data["nodes"][node_id]["row"], node_data["nodes"][swap_node_id]["row"] = \
                swap_node_data.get("row", 0), current_row
            
            node_name = id_mapper.get_node_name(node_id)
            return f"节点 {node_name} 已下移", node_data, update_canvas(node_data), False
        else:
            node_name = id_mapper.get_node_name(node_id)  
            return f"节点 {node_name} 已经在最下方", node_data, update_canvas(node_data), False
    
    elif ctx.triggered_id == "add-param":
        node_id = context_menu_data.get("node")
        if not node_id:
            return "无效操作", node_data, update_canvas(node_data), False
        node_name = id_mapper.get_node_name(node_id)
        param = Parameter(name="test_param", value=0.0, unit="V", description=f"参数 {node_name}")
        graph.nodes[node_id].add_parameter(param)
        return f"参数 test_param 已添加到节点 {node_name}", node_data, update_canvas(node_data), False
    
    elif ctx.triggered_id == "delete-node":
        node_id = context_menu_data.get("node")
        if not node_id:
            return "无效操作", node_data, update_canvas(node_data), False
        
        node_name = id_mapper.get_node_name(node_id)
        
        # 从数据模型中删除节点
        if node_id in graph.nodes:
            graph.remove_node(graph.nodes[node_id])
        
        # 从ID映射中删除节点
        if node_id in id_mapper._node_mapping:
            del id_mapper._node_mapping[node_id]
        
        # 从节点数据中删除节点
        if node_id in node_data["nodes"]:
            del node_data["nodes"][node_id]
        
        return f"节点 {node_name} 已删除", node_data, update_canvas(node_data), False

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
            # 更新参数值，检查是否真的有变化
            current_value_str = str(current_param.value)
            if new_value != current_value_str:
                try:
                    # 尝试转换为数字
                    if '.' in str(new_value):
                        current_param.value = float(new_value)
                    else:
                        current_param.value = int(new_value)
                except (ValueError, TypeError):
                    # 如果转换失败，保存为字符串
                    current_param.value = str(new_value)
    
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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050) 