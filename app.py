import dash
from dash import html, dcc, Output, Input, State, ctx, MATCH, ALL, callback
import dash_bootstrap_components as dbc
from models import CalculationGraph, Node, Parameter, CanvasLayoutManager, GridPosition
from session_graph import get_graph, set_graph, GraphProxy
from typing import Dict, Optional, List, Any
import json
from datetime import datetime
import uuid
import plotly.graph_objects as go
import numpy as np
import os
from layout import *
from examples import *
import traceback

# 删除 IDMapper 类的定义

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Flask session 需要 SECRET_KEY 才能正常工作
# 可以从环境变量读取，若不存在则生成随机值（仅开发环境适用）
app.server.secret_key = os.environ.get("SECRET_KEY", str(uuid.uuid4()))

# 使用会话级 CalculationGraph 代理
graph: CalculationGraph = GraphProxy()

# 创建布局管理器
layout_manager = CanvasLayoutManager(initial_cols=4, initial_rows=12)
graph.set_layout_manager(layout_manager)

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
        return """# 无依赖参数
# 设置置信度 (可选，范围 0.0-1.0)
# self.confidence = 0.9  # 示例：90% 置信度

result = value"""
    
    code_lines = ["# 计算函数"]
    for i, dep_info in enumerate(selected_dependencies):
        code_lines.append(f"# {dep_info['param_name']} = dependencies[{i}].value")
        code_lines.append(f"# {dep_info['param_name']}置信度 = dependencies[{i}].confidence")
    
    code_lines.extend([
        "",
        "# 置信度处理示例：",
        "# 可以根据依赖参数的置信度动态调整当前参数的置信度",
        "# min_confidence = min(dep.confidence for dep in dependencies)",
        "# self.confidence = min_confidence * 0.9  # 根据依赖降低置信度",
        "",
        "# 或者设置固定置信度：",
        "# self.confidence = 0.8  # 80% 置信度",
        "",
        "# 在这里编写计算逻辑",
        "result = value  # 修改这里",
        "",
        "# 注意：置信度会影响参数在依赖关系显示中的颜色标识"
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

def get_plotting_parameters():
    """获取所有可用于绘图的参数"""
    all_params = []
    for node_id, node in graph.nodes.items():
        for param in node.parameters:
            # 只允许数值类型的参数用于绘图 (float 和 int)
            # 要求参数必须有明确的类型信息
            if hasattr(param, 'param_type') and param.param_type in ['float', 'int'] and isinstance(param.value, (int, float)):
                all_params.append({
                    'label': f"{node.name}.{param.name}",
                    'value': f"{node_id}|{param.name}",
                    'node_id': node_id,
                    'param_name': param.name,
                    'current_value': param.value,
                    'unit': param.unit
                })
    return all_params

def perform_sensitivity_analysis(x_param_info, y_param_info, x_start, x_end, x_step):
    """执行参数敏感性分析"""
    try:
        x_node_id, x_param_name = x_param_info['value'].split('|')
        y_node_id, y_param_name = y_param_info['value'].split('|')
        
        # 获取参数对象
        x_node = graph.nodes.get(x_node_id)
        y_node = graph.nodes.get(y_node_id)
        
        if not x_node or not y_node:
            return {'success': False, 'message': '参数所属节点不存在'}
        
        x_param = None
        y_param = None
        
        # 找到对应的参数对象
        for param in x_node.parameters:
            if param.name == x_param_name:
                x_param = param
                break
        
        for param in y_node.parameters:
            if param.name == y_param_name:
                y_param = param
                break
        
        if not x_param or not y_param:
            return {'success': False, 'message': '参数对象不存在'}
        
        # 保存原始值
        original_x_value = x_param.value
        
        x_values = []
        y_values = []
        
        # 生成X轴取值范围
        x_range = np.arange(x_start, x_end + x_step, x_step)
        
        # 限制最大数据点数量以避免性能问题
        if len(x_range) > 1000:
            return {
                'success': False, 
                'message': f'数据点过多 ({len(x_range)} 点)，请减少范围或增大步长 (最大1000点)'
            }
        
        # 在相关性分析开始前，如果X参数有计算依赖，将其设置为unlinked
        x_was_unlinked = getattr(x_param, 'unlinked', False)
        if x_param.calculation_func and x_param.dependencies and not x_was_unlinked:
            x_param.set_manual_value(x_param.value)  # 保持当前值但断开计算
        
        for x_val in x_range:
            try:
                # 设置X参数值（相关性分析中的手动设置）
                x_param.value = float(x_val)
                
                # 如果Y参数有计算函数，触发重新计算并获取新值
                y_val = y_param.value # 默认值
                if y_param.calculation_func:
                    y_val = y_param.calculate()
                
                x_values.append(float(x_val))
                y_values.append(float(y_val))
                
            except Exception as e:
                print(f"计算错误 (X={x_val}): {e}")
                continue
        
        if not x_values:
            return {'success': False, 'message': '没有成功计算的数据点'}
        
        return {
            'x_values': x_values,
            'y_values': y_values,
            'x_label': f"{x_param_info['label']} ({x_param_info['unit']})" if x_param_info['unit'] else x_param_info['label'],
            'y_label': f"{y_param_info['label']} ({y_param_info['unit']})" if y_param_info['unit'] else y_param_info['label'],
            'success': True,
            'message': f"成功生成 {len(x_values)} 个数据点"
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"分析失败: {str(e)}"
        }
    finally:
        # 恢复原始值和连接状态
        try:
            if 'x_param' in locals() and 'original_x_value' in locals():
                x_param.value = original_x_value
                # 恢复原始的unlinked状态
                if 'x_was_unlinked' in locals() and not x_was_unlinked:
                    x_param.unlinked = False
        except Exception as e:
            print(f"恢复原始值和状态时出错: {e}")

def create_empty_plot():
    """创建空的绘图"""
    fig = go.Figure()
    fig.update_layout(
        title_text="请选择参数以生成图表",
        template="plotly_white",
        showlegend=True,
        xaxis=dict(showgrid=False, title=""),
        yaxis=dict(showgrid=False, title=""),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )
    return fig

# 自动删除空的最后一列的辅助函数
def auto_remove_empty_last_column():
    """检查并自动删除空的最后一列，但至少保留3列"""
    return graph.layout_manager.auto_remove_empty_last_columns()

def ensure_minimum_columns(min_cols: int = 3):
    """确保布局至少有 min_cols 列"""
    return graph.layout_manager.ensure_minimum_columns(min_cols)

# 画布更新函数 - 使用新的布局管理器
def update_canvas(node_data=None):
    """使用布局管理器渲染画布"""
    # 确保至少有3列的布局
    ensure_minimum_columns()
    
    canvas_content = []
    
    # 检查是否有节点，如果没有则显示空状态提示
    print(f"🔍 update_canvas调用: graph.nodes = {graph.nodes}")
    print(f"🔍 graph.nodes是否为空: {not graph.nodes}")
    print(f"🔍 graph.nodes长度: {len(graph.nodes)}")
    print(f"🔍 当前布局列数: {graph.layout_manager.cols}")
    
    if not graph.nodes:
        empty_state_content = html.Div([
            html.Div([
                html.Div([
                    html.I(className="fas fa-project-diagram", style={"fontSize": "4rem", "color": "#dee2e6", "marginBottom": "1rem"}),
                    html.P([
                        "开始构建计算图：",
                    ], className="text-muted mb-4"),
                    html.Div([
                        html.Div([
                            html.Span( style={"fontSize": "1.5rem", "marginRight": "0.5rem"}),
                            "点击右上角 ",
                            html.Strong("🎯", className="text-warning"),
                            " 按钮载入SoC示例计算图"
                        ], className="mb-3 p-3 border rounded bg-light"),
                        html.Div([
                            html.Span(style={"fontSize": "1.5rem", "marginRight": "0.5rem"}),
                            "点击右上角 ",
                            html.Strong("➕", className="text-primary"),
                            " 按钮添加新节点，并添加参数"
                        ], className="mb-3 p-3 border rounded bg-light"),
                        html.Div([
                            html.Span("📁", style={"fontSize": "1.5rem", "marginRight": "0.5rem"}),
                            "或从文件加载已有的计算图"
                        ], className="p-3 border rounded bg-light")
                    ])
                ], className="text-center p-5"),
            ], className="d-flex justify-content-center align-items-center", style={"minHeight": "400px"})
        ])
        
        # 创建画布内容，只包含空状态提示
        canvas_with_arrows = html.Div([
            # 空状态内容
            empty_state_content,
            # 箭头覆盖层（空状态下不需要，但保持结构一致）
            html.Div(
                [],
                style={
                    "position": "absolute",
                    "top": "0",
                    "left": "0", 
                    "width": "100%",
                    "height": "100%",
                    "pointerEvents": "none",
                    "zIndex": "10"
                },
                id="arrows-overlay"
            )
        ], style={"position": "relative"})
        
        print("🎨 空状态内容已创建并返回")
        
        # 添加JavaScript控制台打印
        canvas_with_arrows.children.append(
            html.Script("""
                console.log('🎨 ArchDash: 空状态提示已显示');
                console.log('✅ 如果您看到这条消息，说明空状态逻辑正常工作');
                console.log('📋 请检查页面是否显示了"计算图为空"和三个引导卡片');
            """)
        )
        
        return canvas_with_arrows
    
    # 按列组织内容
    print(f"🏗️ 渲染正常模式 - 有{len(graph.nodes)}个节点")
    for col in range(graph.layout_manager.cols):
        col_content = []
        col_nodes = graph.layout_manager.get_column_nodes(col)
        
        # 按行排序节点
        for node_id, row in sorted(col_nodes, key=lambda x: x[1]):
            node = graph.nodes.get(node_id)
            node_name = node.name if node else ""
            
            if not node:
                continue
                
            # 构建参数表格
            param_rows = []
            if hasattr(node, "parameters"):
                for param_idx, param in enumerate(node.parameters):
                    param_rows.append(
                        html.Tr([
                            html.Td(
                                html.Div([
                                    # Pin点
                                    html.Div(
                                        style={
                                            "width": "8px",
                                            "height": "8px",
                                            "borderRadius": "50%",
                                            "backgroundColor": "#007bff",
                                            "border": "2px solid #fff",
                                            "boxShadow": "0 0 0 1px #007bff",
                                            "marginRight": "4px",
                                            "marginTop": "6px",
                                            "flex": "none"
                                        },
                                        className="param-pin",
                                        id=f"pin-{node_id}-{param_idx}"
                                    ),
                                    # 参数名输入框，带有类型提示
                                    dbc.Tooltip(
                                        f"类型: {param.param_type if hasattr(param, 'param_type') else '未知'}",
                                        target={"type": "param-name", "node": node_id, "index": param_idx},
                                        placement="top",
                                        trigger="focus"
                                    ),
                                    dcc.Input(
                                        id={"type": "param-name", "node": node_id, "index": param_idx},
                                        value=param.name,
                                        debounce=True,  # 只在失去焦点或按回车时触发callback
                                        style={"flex": "1", "border": "1px solid transparent", "background": "transparent", "fontWeight": "bold", "borderRadius": "3px", "padding": "1px 3px"},
                                        className="param-input"
                                    )
                                ], style={"display": "flex", "alignItems": "center", "width": "100%"}),
                                style={"paddingRight": "2px", "width": "45%"}
                            ),
                            html.Td(
                                html.Div([
                                    dbc.Tooltip(
                                        f"类型: {param.param_type if hasattr(param, 'param_type') else '未知'}",
                                        target={"type": "param-value", "node": node_id, "index": param_idx},
                                        placement="top",
                                        trigger="focus"
                                    ),
                                    html.Div([
                                                                            dcc.Input(
                                        id={"type": "param-value", "node": node_id, "index": param_idx},
                                        value=str(param.value),
                                        debounce=True,  # 只在失去焦点或按回车时触发callback
                                        style={
                                            "width": "calc(100% - 25px)" if (param.calculation_func and param.dependencies and getattr(param, 'unlinked', False)) else "100%", 
                                            "border": "1px solid transparent", 
                                            "background": "lightgreen" if f"{node_id}-{param_idx}" in graph.recently_updated_params else "transparent",
                                            "borderRadius": "3px", 
                                            "padding": "1px 3px",
                                            "transition": "background-color 2s ease-out"
                                        },
                                        className="param-input"
                                    ),
                                        html.Span(
                                            param.unit,
                                            style={
                                                "marginLeft": "4px",
                                                "fontSize": "0.85em",
                                                "color": "#666",
                                                "whiteSpace": "nowrap"
                                            }
                                        ) if param.unit else None
                                    ], style={"display": "flex", "alignItems": "center", "width": "100%"}),
                                    # Unlink图标 - 只有有依赖计算且unlinked=True时显示
                                    html.Div(
                                        "🔓",
                                        id={"type": "unlink-icon", "node": node_id, "index": param_idx},
                                        className="unlink-icon",
                                        style={
                                            "cursor": "pointer",
                                            "fontSize": "12px",
                                            "opacity": "1",
                                            "marginLeft": "2px",
                                            "padding": "2px",
                                            "borderRadius": "3px",
                                            "display": "inline-block",
                                            "minWidth": "18px",
                                            "textAlign": "center",
                                            "userSelect": "none"
                                        },
                                        title="重新连接 (点击恢复自动计算)"
                                    ) if (param.calculation_func and param.dependencies and getattr(param, 'unlinked', False)) else None
                                ], style={"display": "flex", "alignItems": "center", "width": "100%"}),
                                style={"width": "40%", "paddingLeft": "2px", "paddingRight": "2px"}
                            ),
                            html.Td(
                                dbc.DropdownMenu(
                                    children=[
                                        dbc.DropdownMenuItem("编辑参数", id={"type": "edit-param", "node": node_id, "index": param_idx}, className="text-primary"),
                                        dbc.DropdownMenuItem(divider=True),
                                        dbc.DropdownMenuItem("删除参数", id={"type": "delete-param", "node": node_id, "index": param_idx}, className="text-danger"),
                                        dbc.DropdownMenuItem(divider=True),
                                        dbc.DropdownMenuItem("上移", id={"type": "move-param-up", "node": node_id, "index": param_idx}, disabled=param_idx==0),
                                        dbc.DropdownMenuItem("下移", id={"type": "move-param-down", "node": node_id, "index": param_idx}, disabled=param_idx==len(node.parameters)-1),
                                    ],
                                    toggle_class_name="param-menu-btn",
                                    label="",
                                    size="sm",
                                    direction="left"
                                ),
                                style={"width": "15%", "textAlign": "right", "paddingLeft": "2px"}
                            )
                        ])
                    )
            
            param_table = html.Table(param_rows, style={"width": "100%", "fontSize": "0.85em", "marginTop": "2px"}) if param_rows else None
            
            node_div = html.Div(
                [
                    html.Div([
                        html.Div([
                            html.Span(f"{node_name}", className="node-name")
                        ]),
                        html.Div([
                            # 添加参数按钮（标题栏）
                            html.Button(
                                html.Span(
                                    "➕",
                                    style={
                                        "fontSize": "14px",
                                        "fontWeight": "normal",
                                        "lineHeight": "1"
                                    }
                                ),
                                id={"type": "add-param-header", "node": node_id},
                                className="btn add-param-btn",
                                style={
                                    "padding": "4px",
                                    "borderRadius": "50%",
                                    "border": "none",
                                    "backgroundColor": "transparent",
                                    "minWidth": "24px",
                                    "height": "24px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                    "transition": "all 0.3s ease",
                                    "color": "#6c757d",
                                    "marginRight": "6px"
                                },
                                title="添加参数"
                            ),
                            dbc.DropdownMenu(
                                children=[
                                    dbc.DropdownMenuItem("编辑节点", id={"type": "edit-node", "node": node_id}, className="text-warning"),
                                    dbc.DropdownMenuItem(divider=True),
                                    dbc.DropdownMenuItem("上移", id={"type": "move-node-up", "node": node_id}, className="text-primary"),
                                    dbc.DropdownMenuItem("下移", id={"type": "move-node-down", "node": node_id}, className="text-primary"),
                                    dbc.DropdownMenuItem(divider=True),
                                    dbc.DropdownMenuItem("左移", id={"type": "move-node-left", "node": node_id}, className="text-info"),
                                    dbc.DropdownMenuItem("右移", id={"type": "move-node-right", "node": node_id}, className="text-info"),
                                    dbc.DropdownMenuItem(divider=True),
                                    dbc.DropdownMenuItem("添加参数", id={"type": "add-param", "node": node_id}, className="text-success"),
                                    dbc.DropdownMenuItem("删除节点", id={"type": "delete-node", "node": node_id}, className="text-danger"),
                                ],
                                toggle_class_name="node-menu-btn",
                                toggle_style={
                                    "border": "none",
                                    "background": "transparent",
                                    "padding": "4px",
                                    "fontSize": "12px",
                                    "color": "#6c757d",
                                    "height": "24px",
                                    "minWidth": "24px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                    "borderRadius": "3px"
                                },
                                label="",
                                size="sm",
                                direction="left"
                            )
                        ], style={"display": "flex", "alignItems": "center"})
                    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}),
                    param_table,
                    html.Div(id=f"node-content-{node_id}", className="node-content")
                ],
                className="p-2 node-container node-entrance fade-in",
                id=f"node-{node_id}",
                **{"data-row": row, "data-col": col, "data-dash-id": json.dumps({"type": "node", "index": node_id})}
            )
            col_content.append(node_div)
        
        # 计算列宽 - 优化布局，确保至少3列时有合理的宽度分布
        total_cols = max(3, graph.layout_manager.cols)  # 至少按3列计算宽度
        col_width = max(2, 12 // total_cols)  # 每列至少占2个Bootstrap列宽
        canvas_content.append(dbc.Col(col_content, width=col_width))
    
    # 创建箭头连接
    arrows = create_arrows()
    
    # 创建画布内容，包含节点和箭头覆盖层
    canvas_with_arrows = html.Div([
        # 节点内容
        dbc.Row(canvas_content),
        # 箭头覆盖层 - 使用普通div
        html.Div(
            arrows,
            style={
                "position": "absolute",
                "top": "0",
                "left": "0", 
                "width": "100%",
                "height": "100%",
                "pointerEvents": "none",  # 允许鼠标事件穿透到下层元素
                "zIndex": "10"
            },
            id="arrows-overlay"
        )
    ], style={"position": "relative"})
    
    return canvas_with_arrows

def create_arrows():
    return [
        html.Div(
            id="arrows-overlay-dynamic",
            style={
                "position": "absolute",
                "top": "0",
                "left": "0",
                "width": "100%",
                "height": "100%",
                "pointerEvents": "none",
                "zIndex": "10"
            }
        )
    ]

app.layout = app_layout
app.index_string = app_index_string

# 新的节点操作回调函数 - 使用布局管理器
@callback(
    Output("output-result", "children"),
    Output("node-data", "data"),
    Output("canvas-container", "children"),
    Input({"type": "move-node-up", "node": ALL}, "n_clicks"),
    Input({"type": "move-node-down", "node": ALL}, "n_clicks"),
    Input({"type": "move-node-left", "node": ALL}, "n_clicks"),
    Input({"type": "move-node-right", "node": ALL}, "n_clicks"),
    Input({"type": "add-param", "node": ALL}, "n_clicks"),
    Input({"type": "add-param-header", "node": ALL}, "n_clicks"),
    Input({"type": "delete-node", "node": ALL}, "n_clicks"),
    State("node-data", "data"),
    prevent_initial_call=True
)
def handle_node_operations(move_up_clicks, move_down_clicks, 
                          move_left_clicks, move_right_clicks, 
                          add_param_clicks, add_param_header_clicks, delete_node_clicks,
                          node_data):
    
    if isinstance(ctx.triggered_id, dict):
        operation_type = ctx.triggered_id.get("type")
        node_id = ctx.triggered_id.get("node")
        
        # 检查点击值，避免初始化误触发
        trigger_value = ctx.triggered[0]["value"]
        if not trigger_value or trigger_value == 0:
            return dash.no_update, dash.no_update, dash.no_update
        
        if not node_id:
            return "无效操作", node_data, update_canvas()
        
        node = graph.nodes.get(node_id)
        if not node:
            return "无效节点", node_data, update_canvas()
        node_name = node.name
        
        if operation_type == "move-node-up":
            success = graph.layout_manager.move_node_up(node_id)
            result_message = f"节点 {node_name} 已上移" if success else f"节点 {node_name} 无法上移"
            # 节点移动后检查并自动删除空的最后一列，但保持至少3列
            if success:
                auto_remove_result = auto_remove_empty_last_column()
                if auto_remove_result:
                    result_message += f"，{auto_remove_result}"
            return result_message, node_data, update_canvas()
        
        elif operation_type == "move-node-down":
            success = graph.layout_manager.move_node_down(node_id)
            result_message = f"节点 {node_name} 已下移" if success else f"节点 {node_name} 无法下移"
            # 节点移动后检查并自动删除空的最后一列，但保持至少3列
            if success:
                auto_remove_result = auto_remove_empty_last_column()
                if auto_remove_result:
                    result_message += f"，{auto_remove_result}"
            return result_message, node_data, update_canvas()
        
        elif operation_type == "move-node-left":
            success = graph.layout_manager.move_node_left(node_id)
            result_message = f"节点 {node_name} 已左移" if success else f"节点 {node_name} 无法左移"
            # 节点移动后检查并自动删除空的最后一列，但保持至少3列
            if success:
                auto_remove_result = auto_remove_empty_last_column()
                if auto_remove_result:
                    result_message += f"，{auto_remove_result}"
            return result_message, node_data, update_canvas()
        
        elif operation_type == "move-node-right":
            # 右移前先检查是否需要自动扩展列
            expand_result = graph.layout_manager.auto_expand_for_node_movement(node_id, "right")
            
            success = graph.layout_manager.move_node_right(node_id)
            result_message = f"节点 {node_name} 已右移" if success else f"节点 {node_name} 无法右移"
            
            if success and expand_result:
                result_message += f"，{expand_result}"
            elif success:
                # 节点移动后检查并自动删除空的最后一列，但保持至少3列
                auto_remove_result = auto_remove_empty_last_column()
                if auto_remove_result:
                    result_message += f"，{auto_remove_result}"
            return result_message, node_data, update_canvas()
        
        elif operation_type == "add-param":
            param = Parameter(name="new_param", value=0.0, unit="", description=f"新参数", param_type="float")
            
            # 添加参数到节点
            graph.add_parameter_to_node(node_id, param)
            
            return f"参数已添加到节点 {node_name}", node_data, update_canvas()
        
        elif operation_type == "add-param-header":
            # 标题栏加号按钮：添加参数功能，与下拉菜单中的"添加参数"功能相同
            param = Parameter(name="new_param", value=0.0, unit="", description=f"新参数", param_type="float")
            
            # 添加参数到节点
            graph.add_parameter_to_node(node_id, param)
            
            return f"参数已添加到节点 {node_name}", node_data, update_canvas()
        
        elif operation_type == "delete-node":
            # 检查节点的参数是否被其他参数依赖
            has_dependents, dependent_info = check_node_has_dependents(node_id)
            
            if has_dependents:
                # 构建详细的错误消息
                affected_params = dependent_info["affected_node_params"]
                dependent_params = dependent_info["dependent_params"]
                
                error_message = f"❌ 无法删除节点 {node_name}，因为该节点的以下参数被其他参数依赖：\n"
                
                # 按被依赖的参数分组显示信息
                for affected_param in affected_params:
                    deps_for_param = [dep for dep in dependent_params if dep["depends_on"] == affected_param]
                    dep_info_list = [f"{dep['node_name']}.{dep['param_name']}" for dep in deps_for_param]
                    error_message += f"• {affected_param} 被依赖于：{', '.join(dep_info_list)}\n"
                
                return error_message, node_data, update_canvas()
            
            # 从布局管理器移除节点
            graph.layout_manager.remove_node(node_id)
            # 从计算图移除节点
            if node_id in graph.nodes:
                del graph.nodes[node_id]
            # 节点删除清理已完成
            
            result_message = f"✅ 节点 {node_name} 已删除"
            # 删除节点后检查并自动删除空的最后一列，但保持至少3列
            auto_remove_result = auto_remove_empty_last_column()
            if auto_remove_result:
                result_message += f"，{auto_remove_result}"
            
            return result_message, node_data, update_canvas()
    
    return dash.no_update, dash.no_update, dash.no_update

# 移除旧的show_context_menu回调，现在使用直接的dropdown menu

# 添加参数更新回调 - 使用debounce确保只在输入完成后更新
@callback(
    Output("node-data", "data", allow_duplicate=True),
    Output("canvas-container", "children", allow_duplicate=True),
    Output("output-result", "children", allow_duplicate=True),
    Output("clear-highlight-timer", "disabled", allow_duplicate=True),
    Input({"type": "param-name", "node": ALL, "index": ALL}, "value"),
    Input({"type": "param-value", "node": ALL, "index": ALL}, "value"),
    State("node-data", "data"),
    prevent_initial_call=True
)
def update_parameter(param_names, param_values, node_data):
    if not ctx.triggered_id:
        return node_data, dash.no_update, dash.no_update, dash.no_update
    
    triggered_id = ctx.triggered_id
    if isinstance(triggered_id, dict):
        node_id = triggered_id["node"]
        param_index = triggered_id["index"]
        param_type = triggered_id["type"]
        
        # 直接从ctx.triggered获取新值（debounce确保只在输入完成后触发）
        new_value = ctx.triggered[0]["value"]
        
        # 🔍 调试信息：记录获取到的值
        print(f"🔍 调试：参数更新 - 节点:{node_id}, 索引:{param_index}, 类型:{param_type}, 获取值:{new_value}")
        
        # 检查值是否为空或无效
        if new_value is None or new_value == "":
            print(f"⚠️ 警告：未能获取到有效值，跳过更新")
            return node_data, dash.no_update, dash.no_update, dash.no_update
        
        # 获取节点
        node = graph.nodes.get(node_id)
        if not node:
            return node_data, dash.no_update, dash.no_update, dash.no_update
            
        # 检查参数索引是否有效
        if param_index >= len(node.parameters):
            return node_data, dash.no_update, dash.no_update, dash.no_update
            
        # 获取当前参数
        current_param = node.parameters[param_index]
        
        update_message = ""
        should_update_canvas = False
        
        if param_type == "param-name":
            # 更新参数名，检查是否真的有变化
            if new_value != current_param.name:
                print(f"🔄 参数名更新: {current_param.name} → {new_value}")
                current_param.name = new_value
                should_update_canvas = True
                update_message = f"参数名已更新为: {new_value}"
            else:
                print(f"📌 参数名无变化，跳过更新: {new_value}")
                return node_data, dash.no_update, dash.no_update, dash.no_update
        elif param_type == "param-value":
            # 更新参数值 - 要求明确的类型信息
            if not hasattr(current_param, 'param_type'):
                print(f"❌ 参数 {current_param.name} 缺少类型信息")
                return node_data, dash.no_update, f"❌ 参数 '{current_param.name}' 缺少类型信息，无法更新", dash.no_update
            
            param_data_type = current_param.param_type
            
            try:
                if new_value is not None and new_value != "":
                    if param_data_type == "string":
                        # 字符串类型 - 保持原始字符串值
                        new_value = str(new_value)
                    elif param_data_type == "float":
                        # 浮点数类型 - 转换为浮点数
                        new_value = float(new_value)
                    elif param_data_type == "int":
                        # 整数类型 - 转换为整数
                        new_value = int(new_value)
                    else:
                        print(f"❌ 不支持的参数类型: {param_data_type}")
                        return node_data, dash.no_update, f"❌ 不支持的参数类型: {param_data_type}", dash.no_update
                else:
                    # 空值处理
                    if param_data_type == "string":
                        new_value = ""
                    else:
                        new_value = 0
            except (ValueError, TypeError):
                # 类型转换失败的处理
                if param_data_type == "string":
                    new_value = str(new_value) if new_value is not None else ""
                else:
                    print(f"⚠️ 参数值类型转换失败: {new_value} -> {param_data_type}")
                    return node_data, dash.no_update, f"❌ 参数值 '{new_value}' 无法转换为 {param_data_type} 类型", dash.no_update
            
            # 检查参数值是否真的有变化
            if new_value == current_param.value:
                print(f"📌 参数值无变化，跳过更新: {current_param.name} = {new_value}")
                return node_data, dash.no_update, dash.no_update, dash.no_update
            
            print(f"🔄 参数值更新: {current_param.name}: {current_param.value} → {new_value}")
            
            # 手动修改参数值时，如果参数有计算函数和依赖，自动设置为unlinked
            if current_param.calculation_func and current_param.dependencies:
                current_param.set_manual_value(new_value)
                update_message = f"🔓 参数 {current_param.name} 已手动设置为 {new_value}（已断开自动计算）"
                should_update_canvas = True
                graph.recently_updated_params.add(f"{node_id}-{param_index}")
            else:
                # 无计算依赖的参数，正常更新
                # 清空之前的高亮标记
                graph.recently_updated_params.clear()
                
                # 使用新的数据流更新机制
                update_result = graph.set_parameter_value(current_param, new_value)
                should_update_canvas = True
                
                # 标记主参数为已更新
                graph.recently_updated_params.add(f"{node_id}-{param_index}")
                
                # 标记所有被级联更新的参数
                for update_info in update_result.get('cascaded_updates', []):
                    updated_param = update_info['param']
                    # 找到该参数所在的节点和索引
                    for check_node_id, check_node in graph.nodes.items():
                        for check_idx, check_param in enumerate(check_node.parameters):
                            if check_param is updated_param:
                                graph.recently_updated_params.add(f"{check_node_id}-{check_idx}")
                                break
                
                # 构建更新消息
                cascaded_info = ""
                if update_result['cascaded_updates']:
                    affected_params = [f"{update['param'].name}({update['old_value']}→{update['new_value']})" 
                                     for update in update_result['cascaded_updates']]
                    cascaded_info = f"，同时更新了 {len(affected_params)} 个关联参数: {', '.join(affected_params)}"
                
                update_message = f"🔄 参数 {current_param.name} 已更新为 {new_value}{cascaded_info}"
        
        # 返回更新结果
        if should_update_canvas:
            return node_data, update_canvas(), update_message, False  # 启用计时器
        else:
            return node_data, dash.no_update, update_message, False  # 启用计时器
    
    # 默认情况
    return node_data, dash.no_update, dash.no_update, dash.no_update

# 添加参数操作回调 - 完全独立于节点菜单
@callback(
    Output("node-data", "data", allow_duplicate=True),
    Output("canvas-container", "children", allow_duplicate=True),
    Output("output-result", "children", allow_duplicate=True),
    Output("clear-highlight-timer", "disabled", allow_duplicate=True),
    Input({"type": "delete-param", "node": ALL, "index": ALL}, "n_clicks"),
    Input({"type": "move-param-up", "node": ALL, "index": ALL}, "n_clicks"),
    Input({"type": "move-param-down", "node": ALL, "index": ALL}, "n_clicks"),
    State("node-data", "data"),
    prevent_initial_call=True
)
def handle_parameter_operations(delete_clicks, move_up_clicks, move_down_clicks, node_data):
    ctx = dash.callback_context  # 获取回调上下文
    if not ctx.triggered_id:
        return node_data, update_canvas(), dash.no_update, dash.no_update
    
    triggered_id = ctx.triggered_id
    if not isinstance(triggered_id, dict):
        return node_data, update_canvas(), dash.no_update, dash.no_update
    
    node_id = triggered_id.get("node")
    param_index = triggered_id.get("index")
    operation_type = triggered_id.get("type")
    
    # 检查点击数值，避免初始化时的误触发
    trigger_value = ctx.triggered[0]["value"]
    if not trigger_value or trigger_value == 0:
        return node_data, update_canvas(), dash.no_update, dash.no_update
    
    if not node_id or param_index is None:
        return node_data, update_canvas(), dash.no_update, dash.no_update
    
    # 获取节点
    node = graph.nodes.get(node_id)
    if not node:
        return node_data, update_canvas(), dash.no_update, dash.no_update
        
    if param_index >= len(node.parameters):
        return node_data, update_canvas(), dash.no_update, dash.no_update
    
    node_name = node.name
    param_name = node.parameters[param_index].name
    
    if operation_type == "delete-param":
        # 检查参数是否被其他参数依赖
        param_to_delete = node.parameters[param_index]
        has_dependents, dependent_list = check_parameter_has_dependents(param_to_delete)
        
        if has_dependents:
            # 构建依赖信息的错误消息
            dependent_info = []
            for dep in dependent_list:
                dependent_info.append(f"{dep['node_name']}.{dep['param_name']}")
            
            error_message = f"❌ 无法删除参数 {node_name}.{param_name}，因为以下参数依赖于它：\n{', '.join(dependent_info)}"
            return node_data, update_canvas(), error_message, dash.no_update
        
        # 删除参数
        deleted_param = node.parameters.pop(param_index)
        success_message = f"✅ 参数 {node_name}.{param_name} 已删除"
        
        return node_data, update_canvas(), success_message, dash.no_update
        
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
    return node_data, update_canvas(), dash.no_update, dash.no_update

# 处理unlink图标点击的回调函数
@callback(
    Output("node-data", "data", allow_duplicate=True),
    Output("canvas-container", "children", allow_duplicate=True),
    Output("output-result", "children", allow_duplicate=True),
    Output("clear-highlight-timer", "disabled", allow_duplicate=True),
    Input({"type": "unlink-icon", "node": ALL, "index": ALL}, "n_clicks"),
    State("node-data", "data"),
    prevent_initial_call=True
)
def handle_unlink_toggle(unlink_clicks, node_data):
    """处理unlink图标点击，重新连接参数并计算"""
    if not ctx.triggered_id:
        return node_data, dash.no_update, dash.no_update, dash.no_update
    
    triggered_id = ctx.triggered_id
    if not isinstance(triggered_id, dict):
        return node_data, dash.no_update, dash.no_update, dash.no_update
    
    node_id = triggered_id.get("node")
    param_index = triggered_id.get("index")
    
    # 检查点击数值，避免初始化时的误触发
    trigger_value = ctx.triggered[0]["value"]
    if not trigger_value or trigger_value == 0:
        return node_data, dash.no_update, dash.no_update, dash.no_update
    
    if not node_id or param_index is None:
        return node_data, dash.no_update, dash.no_update, dash.no_update
    
    # 获取节点和参数
    node = graph.nodes.get(node_id)
    if not node or param_index >= len(node.parameters):
        return node_data, dash.no_update, dash.no_update, dash.no_update
    
    param = node.parameters[param_index]
    node_name = node.name
    
    # 检查参数是否可以重新连接
    if not param.calculation_func or not param.dependencies:
        return node_data, dash.no_update, f"⚠️ 参数 {node_name}.{param.name} 无计算依赖"
    
    try:
        # 重新连接参数（设置unlinked=False并重新计算）
        new_value = param.relink_and_calculate()
        result_message = f"🔗 参数 {node_name}.{param.name} 已重新连接，新值: {new_value}"
        
        return node_data, update_canvas(), result_message, dash.no_update
        
    except Exception as e:
        return node_data, dash.no_update, f"❌ 重新连接失败: {str(e)}", dash.no_update

# 打开参数编辑模态窗口
@callback(
    Output("param-edit-modal", "is_open"),
    Output("param-edit-title", "children"),
    Output("param-edit-name", "value"),
    Output("param-edit-type", "value"),
    Output("param-edit-value-display", "children"),
    Output("param-edit-unit", "value"),
    Output("param-edit-description", "value"),
    Output("param-edit-confidence-display", "children"),
    Output("param-edit-calculation", "value"),
    Output("dependency-selector-container", "children"),
    Output("param-edit-data", "data"),
    Output("param-edit-preview", "children", allow_duplicate=True),
    Output("param-edit-preview", "color", allow_duplicate=True),
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
        node_name = node.name
        
        # 获取所有可用的依赖参数
        available_params = get_all_available_parameters(node_id, param.name)
        
        # 获取当前参数的依赖列表 - 需要构建完整的display_name格式
        current_dependencies = []
        for dep_param in param.dependencies:
            # 找到依赖参数所在的节点名称
            for check_node_id, check_node in graph.nodes.items():
                if dep_param in check_node.parameters:
                    current_dependencies.append(f"{check_node.name}.{dep_param.name}")
                    break
        
        # 创建依赖复选框
        dependency_checkboxes = create_dependency_checkboxes(available_params, current_dependencies)
        
        return (
            True,  # 打开模态窗口
            f"编辑参数: {node_name}.{param.name}",
            param.name,
            param.param_type if hasattr(param, 'param_type') else 'float',  # 参数类型，必须存在
            f"{param.value} {param.unit}",  # 显示值和单位
            param.unit,
            param.description,
            f"{param.confidence:.1%}",  # 显示百分比格式的置信度
            param.calculation_func or "",
            dependency_checkboxes,
            {"node_id": node_id, "param_index": param_index},
            "",  # 重置测试结果显示为空
            "secondary"  # 重置测试结果颜色为默认
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
    State({"type": "dependency-checkbox", "param": ALL}, "value"),
    State({"type": "dependency-checkbox", "param": ALL}, "id"),
    State("param-edit-data", "data"),
    prevent_initial_call=True
)
def test_calculation(test_clicks, calculation_code, checkbox_values, checkbox_ids, edit_data):
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
        
        # 获取当前参数对象及其值
        node_id = edit_data["node_id"]
        param_index = edit_data["param_index"]
        
        if node_id not in graph.nodes:
            return "错误: 节点不存在", "danger"
        
        node = graph.nodes[node_id]
        if param_index >= len(node.parameters):
            return "错误: 参数不存在", "danger"
        
        current_param = node.parameters[param_index]
        
        # 将计算函数临时设置到参数对象上进行测试
        original_calc_func = current_param.calculation_func
        original_dependencies = current_param.dependencies
        
        current_param.calculation_func = calculation_code
        current_param.dependencies = selected_deps
        
        # 执行计算
        try:
            result = current_param.calculate()
            # 成功后清除可能的旧回溯
            current_param._calculation_traceback = None 
            return f"计算结果: {result}", "success"
        except Exception as e:
            # 获取并显示回溯
            traceback_info = current_param._calculation_traceback or str(e)
            return html.Div([
                html.P(f"计算错误: {str(e)}", className="mb-1"),
                html.Details([
                    html.Summary("查看详细回溯"),
                    html.Pre(traceback_info, style={"fontSize": "0.7em", "color": "darkred"})
                ])
            ]), "danger"
        finally:
            # 恢复原始的计算函数和依赖，避免影响实际图结构
            current_param.calculation_func = original_calc_func
            current_param.dependencies = original_dependencies
        
    except Exception as e:
        import traceback
        full_traceback = traceback.format_exc()
        return html.Div([
            html.P(f"测试功能内部错误: {str(e)}", className="mb-1"),
            html.Details([
                html.Summary("查看详细回溯"),
                html.Pre(full_traceback, style={"fontSize": "0.7em", "color": "darkred"})
            ])
        ]), "danger"

# 保存参数修改
@callback(
    Output("param-edit-modal", "is_open", allow_duplicate=True),
    Output("canvas-container", "children", allow_duplicate=True),
    Output("output-result", "children", allow_duplicate=True),
    Input("param-edit-save", "n_clicks"),
    State("param-edit-name", "value"),
    State("param-edit-type", "value"),
    State("param-edit-unit", "value"),
    State("param-edit-description", "value"),
    State("param-edit-calculation", "value"),
    State({"type": "dependency-checkbox", "param": ALL}, "value"),
    State({"type": "dependency-checkbox", "param": ALL}, "id"),
    State("param-edit-data", "data"),
    State("node-data", "data"),
    prevent_initial_call=True
)
def save_parameter_changes(save_clicks, param_name, param_type, param_unit, param_description, 
                          calculation_code, checkbox_values, checkbox_ids, 
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
        param.param_type = param_type if param_type else "float"  # 更新参数类型
        param.unit = param_unit.strip() if param_unit else ""
        param.description = param_description.strip() if param_description else ""
        
        # 注意：参数值和置信度现在只显示，不允许编辑
        # 如果需要修改值，应该在主界面通过参数输入框进行
        cascaded_info = ""
        
        # 更新计算函数
        param.calculation_func = calculation_code.strip() if calculation_code else None
        
        # 清除旧的依赖关系
        param.dependencies.clear()
        
        # 添加新的依赖关系
        for dep_param in selected_deps:
            param.add_dependency(dep_param)
        
        # 确保依赖关系更新到计算图
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
        updated_canvas = update_canvas()
        
        return False, updated_canvas, success_msg, dash.no_update
        
    except Exception as e:
        return True, dash.no_update, f"保存失败: {str(e)}", dash.no_update

# 添加定时清理高亮的回调
@callback(
    Output("canvas-container", "children", allow_duplicate=True),
    Output("clear-highlight-timer", "disabled", allow_duplicate=True),
    Input("clear-highlight-timer", "n_intervals"),
    prevent_initial_call=True
)
def clear_parameter_highlights(n_intervals):
    """定时清除参数高亮"""
    if graph.recently_updated_params:
        graph.recently_updated_params.clear()
        return update_canvas(), True  # 清除高亮并禁用计时器
    return dash.no_update, dash.no_update

# 保存计算图
@callback(
    Output("download-graph", "data"),
    Output("output-result", "children", allow_duplicate=True),
    Input("save-graph-button", "n_clicks"),
    prevent_initial_call=True
)
def save_calculation_graph(n_clicks):
    """保存计算图到文件"""
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    try:
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"calculation_graph_{timestamp}.json"
        
        # 转换为字典数据
        graph_data = graph.to_dict(include_layout=True)
        
        # 创建JSON字符串
        json_str = json.dumps(graph_data, indent=2, ensure_ascii=False)
        
        # 返回下载数据
        return dict(
            content=json_str,
            filename=filename,
            type="application/json"
        ), f"✅ 计算图已保存为 {filename}"
        
    except Exception as e:
        return dash.no_update, f"❌ 保存失败: {str(e)}"



# 加载示例计算图
@app.callback(
    Output("canvas-container", "children", allow_duplicate=True),
    Output("output-result", "children", allow_duplicate=True),
    Input("load-example-graph-button", "n_clicks"),
    prevent_initial_call=True
)
def load_example_soc_graph_callback(n_clicks):
    """加载多核SoC示例计算图的回调函数"""
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    try:
        # 创建示例计算图
        result = create_example_soc_graph()
        
        # 更新画布显示
        updated_canvas = update_canvas()
        
        success_message = (
            f"✅ 已加载多核SoC示例计算图："
            f"{result['nodes_created']}个节点，"
            f"{result['total_params']}个参数，"
            f"其中{result['calculated_params']}个计算参数"
        )
        
        return updated_canvas, success_message
        
    except Exception as e:
        return dash.no_update, f"❌ 加载示例失败: {str(e)}"

# 加载计算图
@app.callback(
    Output("canvas-container", "children", allow_duplicate=True),
    Output("output-result", "children", allow_duplicate=True),
    Input("upload-graph", "contents"),
    State("upload-graph", "filename"),
    prevent_initial_call=True
)
def load_calculation_graph(contents, filename):
    """从上传的文件加载计算图"""
    if contents is None:
        raise dash.exceptions.PreventUpdate
    
    try:
        # 解析上传的内容
        import base64
        
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # 解析JSON数据
        try:
            data = json.loads(decoded.decode('utf-8'))
        except json.JSONDecodeError as e:
            return dash.no_update, f"❌ 文件格式错误: {str(e)}"
        
        # 验证数据格式
        if "nodes" not in data:
            return dash.no_update, "❌ 无效的计算图文件格式"
        
        # 清空现有数据
        # global graph  # 已废弃
        
        # 创建新的布局管理器并重新构建计算图
        new_layout = CanvasLayoutManager(initial_cols=3, initial_rows=10)
        new_graph = CalculationGraph.from_dict(data, new_layout)

        # 写入当前 session
        set_graph(new_graph)
        graph = get_graph()
        
        # 重新初始化列管理器 - 已集成于 CalculationGraph，无需额外操作
        
        # 更新画布显示
        updated_canvas = update_canvas()
        
        loaded_nodes = len(new_graph.nodes)
        total_params = sum(len(node.parameters) for node in new_graph.nodes.values())
        
        return updated_canvas, f"✅ 成功加载计算图 '{filename}'：{loaded_nodes}个节点，{total_params}个参数"
        
    except Exception as e:
        return dash.no_update, f"❌ 加载失败: {str(e)}"

# 更新箭头连接数据
@callback(
    Output("arrow-connections-data", "data"),
    Input("canvas-container", "children"),
    Input("node-data", "data"),
    prevent_initial_call=False
)
def update_arrow_connections_data(canvas_children, node_data):
    """更新箭头连接数据"""
    try:
        connections = get_arrow_connections_data()
        return connections
    except Exception as e:
        print(f"⚠️ 更新箭头连接数据失败: {e}")
        return []

# 空的Python回调，实际绘制由客户端回调处理
@callback(
    Output("arrows-overlay-dynamic", "children"),
    Input("arrow-connections-data", "data"),
    prevent_initial_call=True
)
def trigger_arrow_update_on_data_change(connections_data):
    """当箭头连接数据变化时触发更新，实际绘制由客户端回调处理"""
    return []

# 基于pin点悬停的动态箭头显示系统 - 事件驱动更新
app.clientside_callback(
    """
    function(connections_data, canvas_children) {
        try {
            var arrowContainer = document.getElementById('arrows-overlay-dynamic');
                if (!arrowContainer) {
                    console.log('箭头容器未找到');
                    return;
                }
                
                // 清除现有箭头
                arrowContainer.innerHTML = '';
                
                if (!connections_data || connections_data.length === 0) {
                    console.log('无依赖关系数据');
                    return;
                }
                
                console.log('初始化pin悬停箭头系统，连接数:', connections_data.length);
                
                // 存储连接数据到全局变量，供事件处理器使用
                window.arrowConnectionsData = connections_data;
                window.arrowContainer = arrowContainer;
                
                // 移除之前的事件监听器（避免重复绑定）
                var pinElements = document.querySelectorAll('[id^="pin-"]');
                for (var i = 0; i < pinElements.length; i++) {
                    var pin = pinElements[i];
                    pin.removeEventListener('mouseenter', window.pinMouseEnter);
                    pin.removeEventListener('mouseleave', window.pinMouseLeave);
                }
                
                // 定义鼠标进入pin的处理函数
                window.pinMouseEnter = function(event) {
                    var pinId = event.target.id;
                    console.log('鼠标进入pin:', pinId);
                    
                    // 添加active类
                    event.target.classList.add('active');
                    
                    // 清除现有箭头
                    window.arrowContainer.innerHTML = '';
                    
                    // 找到与当前pin相关的所有连接
                    var relevantConnections = window.arrowConnectionsData.filter(function(conn) {
                        return conn.source_pin_id === pinId || conn.target_pin_id === pinId;
                    });
                    
                    console.log('找到相关连接:', relevantConnections.length);
                    
                    // 绘制相关的箭头
                    drawArrows(relevantConnections, pinId);
                };
                
                // 定义鼠标离开pin的处理函数
                window.pinMouseLeave = function(event) {
                    var pinId = event.target.id;
                    console.log('鼠标离开pin:', pinId);
                    
                    // 移除active类
                    event.target.classList.remove('active');
                    
                    // 延迟清除箭头（给用户时间移动到箭头上）
                    setTimeout(function() {
                        // 检查是否还有active的pin
                        var activePins = document.querySelectorAll('.param-pin.active');
                        if (activePins.length === 0) {
                            window.arrowContainer.innerHTML = '';
                            console.log('清除所有箭头');
                        }
                    }, 200);
                };
                
                // 绘制箭头的函数 - 使用SVG路径
                function drawArrows(connections, activePinId) {
                    var containerRect = window.arrowContainer.getBoundingClientRect();
                    
                    for (var i = 0; i < connections.length; i++) {
                        var connection = connections[i];
                        
                        var sourcePin = document.getElementById(connection.source_pin_id);
                        var targetPin = document.getElementById(connection.target_pin_id);
                        
                        if (sourcePin && targetPin) {
                            var sourceRect = sourcePin.getBoundingClientRect();
                            var targetRect = targetPin.getBoundingClientRect();
                            
                            // 计算源pin的右边中点作为起始点
                            var x1 = sourceRect.right - containerRect.left;
                            var y1 = sourceRect.top + sourceRect.height / 2 - containerRect.top;
                            
                            // 计算目标pin的左边中点作为结束点
                            var x2 = targetRect.left - containerRect.left;
                            var y2 = targetRect.top + targetRect.height / 2 - containerRect.top;
                            
                            var dx = x2 - x1;
                            var dy = y2 - y1;
                            var length = Math.sqrt(dx * dx + dy * dy);
                            
                            if (length > 5) {
                                // 确定箭头颜色和样式
                                var isActiveConnection = (connection.source_pin_id === activePinId || connection.target_pin_id === activePinId);
                                var arrowColor = isActiveConnection ? '#e74c3c' : '#007bff';
                                var arrowOpacity = isActiveConnection ? '1' : '0.6';
                                var strokeWidth = isActiveConnection ? '3' : '2';
                                
                                // 创建SVG元素
                                var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                                svg.style.position = 'absolute';
                                svg.style.top = '0';
                                svg.style.left = '0';
                                svg.style.width = '100%';
                                svg.style.height = '100%';
                                svg.style.pointerEvents = 'none';
                                svg.style.zIndex = isActiveConnection ? '1002' : '1000';
                                svg.style.overflow = 'visible';
                                
                                // 创建定义区域（包含渐变、滤镜等）
                                var defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
                                
                                // 创建线性渐变
                                var gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
                                var gradientId = 'gradient-' + i + '-' + (isActiveConnection ? 'active' : 'normal');
                                gradient.setAttribute('id', gradientId);
                                gradient.setAttribute('x1', '0%');
                                gradient.setAttribute('y1', '0%');
                                gradient.setAttribute('x2', '100%');
                                gradient.setAttribute('y2', '0%');
                                
                                // 根据连接状态设置渐变色
                                var startColor, endColor;
                                if (isActiveConnection) {
                                    startColor = 'rgba(231, 76, 60, 0.8)';   // 活跃连接：半透明红色
                                    endColor = 'rgba(192, 57, 43, 0.9)';     // 到深红色
                                } else {
                                    startColor = 'rgba(52, 152, 219, 0.6)';  // 普通连接：半透明蓝色
                                    endColor = 'rgba(41, 128, 185, 0.7)';    // 到深蓝色
                                }
                                
                                var stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
                                stop1.setAttribute('offset', '0%');
                                stop1.setAttribute('stop-color', startColor);
                                
                                var stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
                                stop2.setAttribute('offset', '70%');
                                stop2.setAttribute('stop-color', endColor);
                                
                                var stop3 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
                                stop3.setAttribute('offset', '100%');
                                stop3.setAttribute('stop-color', startColor);
                                
                                gradient.appendChild(stop1);
                                gradient.appendChild(stop2);
                                gradient.appendChild(stop3);
                                defs.appendChild(gradient);
                                
                                // 创建箭头标记
                                var marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
                                var arrowId = 'arrow-' + i + '-' + (isActiveConnection ? 'active' : 'normal');
                                
                                marker.setAttribute('id', arrowId);
                                marker.setAttribute('viewBox', '0 0 12 12');
                                marker.setAttribute('refX', '11');
                                marker.setAttribute('refY', '6');
                                marker.setAttribute('markerWidth', '8');
                                marker.setAttribute('markerHeight', '8');
                                marker.setAttribute('orient', 'auto');
                                marker.setAttribute('markerUnits', 'strokeWidth');
                                
                                // 创建箭头路径（改为更优雅的形状）
                                var arrowPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                                arrowPath.setAttribute('d', 'M2,2 L10,6 L2,10 L4,6 Z');  // 更优雅的箭头形状
                                arrowPath.setAttribute('fill', 'url(#' + gradientId + ')');
                                
                                marker.appendChild(arrowPath);
                                defs.appendChild(marker);
                                svg.appendChild(defs);
                                
                                // 计算贝塞尔曲线控制点（可选：使用曲线让箭头更美观）
                                var useCurve = Math.abs(dx) > 100; // 距离较远时使用曲线
                                var pathData;
                                
                                if (useCurve) {
                                    // 修复：正确计算贝塞尔曲线控制点
                                    // 控制点应该在连线方向上偏移，而不是总是向右偏移
                                    var offsetX = dx * 0.3; // 保持dx的符号，确保控制点在正确方向
                                    var cp1x = x1 + offsetX;
                                    var cp1y = y1;
                                    var cp2x = x2 - offsetX;
                                    var cp2y = y2;
                                    
                                    // 对于水平线，添加一点垂直偏移让曲线更明显
                                    if (Math.abs(dy) < 1) {
                                        var verticalOffset = Math.min(Math.abs(dx) * 0.1, 20); // 最大20像素的垂直偏移
                                        cp1y = y1 - verticalOffset;
                                        cp2y = y2 - verticalOffset;
                                    }
                                    
                                    pathData = 'M' + x1 + ',' + y1 + ' C' + cp1x + ',' + cp1y + ' ' + cp2x + ',' + cp2y + ' ' + x2 + ',' + y2;
                                } else {
                                    // 使用直线
                                    pathData = 'M' + x1 + ',' + y1 + ' L' + x2 + ',' + y2;
                                }
                                
                                // 创建主路径
                                var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                                path.setAttribute('d', pathData);
                                path.setAttribute('stroke', 'url(#' + gradientId + ')');
                                path.setAttribute('stroke-width', strokeWidth);
                                path.setAttribute('fill', 'none');
                                path.setAttribute('stroke-linecap', 'round');
                                path.setAttribute('stroke-linejoin', 'round');
                                path.setAttribute('marker-end', 'url(#' + arrowId + ')');
                                path.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
                                
                                // 添加交互效果
                                path.style.cursor = 'pointer';
                                path.style.pointerEvents = 'stroke';
                                
                                // 添加流动动画（可选）
                                if (isActiveConnection) {
                                    var animationLength = length;
                                    path.style.strokeDasharray = '5 5';
                                    path.style.strokeDashoffset = '0';
                                    path.style.animation = 'flow-dash 2s linear infinite';
                                }
                                
                                // 增强的悬停效果
                                path.addEventListener('mouseenter', function() {
                                    this.setAttribute('stroke-width', parseFloat(strokeWidth) + 2);
                                    this.style.opacity = '1';
                                    
                                    // 添加脉冲动画
                                    this.style.animation = 'pulse-glow 1s ease-in-out infinite alternate';
                                });
                                
                                path.addEventListener('mouseleave', function() {
                                    this.setAttribute('stroke-width', strokeWidth);
                                    this.style.opacity = '';
                                    
                                    // 恢复原始动画
                                    if (isActiveConnection) {
                                        this.style.animation = 'flow-dash 2s linear infinite';
                                    } else {
                                        this.style.animation = 'none';
                                    }
                                });
                                
                                // 设置工具提示
                                var title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
                                title.textContent = connection.source_node_name + '.' + connection.source_param_name + 
                                                  ' → ' + connection.target_node_name + '.' + connection.target_param_name;
                                path.appendChild(title);
                                
                                svg.appendChild(path);
                                
                                // 添加箭头出现动画
                                svg.style.animation = 'arrow-appear 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards';
                                
                                window.arrowContainer.appendChild(svg);
                            }
                        }
                    }
                }
                
                // 为所有pin添加事件监听器
                for (var i = 0; i < pinElements.length; i++) {
                    var pin = pinElements[i];
                    pin.addEventListener('mouseenter', window.pinMouseEnter);
                    pin.addEventListener('mouseleave', window.pinMouseLeave);
                }
                
                console.log('Pin悬停事件监听器已设置，总pin数:', pinElements.length);
                
        } catch (error) {
            console.error('客户端回调错误:', error);
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output("arrows-overlay-dynamic", "style"),
    Input("arrow-connections-data", "data"),
    Input("canvas-container", "children"),
    prevent_initial_call=True
)

# =============== 绘图相关回调函数 ===============

# 更新参数选择器选项
@callback(
    Output("x-param-selector", "options"),
    Output("y-param-selector", "options"),
    Input("canvas-container", "children"),
    prevent_initial_call=True
)
def update_param_selectors(canvas_children):
    """动态更新参数选择器的选项"""
    params = get_plotting_parameters()
    # 为Dropdown组件创建简化的选项列表（只包含label和value）
    dropdown_options = [
        {
            'label': param['label'],
            'value': param['value']
        }
        for param in params
    ]
    return dropdown_options, dropdown_options

# 初始化空图表
@callback(
    Output("sensitivity-plot", "figure"),
    Input("x-param-selector", "id"),  # 使用ID作为触发器，只在初始化时运行
    prevent_initial_call=False
)
def initialize_plot(selector_id):
    """初始化空图表"""
    return create_empty_plot()



# 生成敏感性分析图表
@callback(
    Output("sensitivity-plot", "figure", allow_duplicate=True),
    Output("output-result", "children", allow_duplicate=True),
    Output("cumulative-plot-data", "data", allow_duplicate=True),
    Input("generate-plot-btn", "n_clicks"),
    State("x-param-selector", "value"),
    State("y-param-selector", "value"),
    State("x-start-value", "value"),
    State("x-end-value", "value"),
    State("x-step-value", "value"),
    State("cumulative-plot-checkbox", "value"),
    State("cumulative-plot-data", "data"),
    State("series-name-input", "value"),
    prevent_initial_call=True
)
def generate_sensitivity_plot(n_clicks, x_param, y_param, x_start, x_end, x_step, cumulative_checkbox, cumulative_data, series_name):
    """生成参数敏感性分析图表"""
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    if not x_param or not y_param:
        return create_empty_plot(), "❌ 请选择X轴和Y轴参数"
    
    if x_param == y_param:
        return create_empty_plot(), "❌ X轴和Y轴参数不能相同"
    
    # 验证输入值
    try:
        x_start = float(x_start) if x_start is not None else 0
        x_end = float(x_end) if x_end is not None else 100
        x_step = float(x_step) if x_step is not None else 1
        
        if x_step <= 0:
            return create_empty_plot(), "❌ 步长必须大于0"
        
        if x_start >= x_end:
            return create_empty_plot(), "❌ 起始值必须小于结束值"
            
    except (ValueError, TypeError):
        return create_empty_plot(), "❌ 请输入有效的数值"
    
    # 从参数值中解析节点ID和参数名
    try:
        x_node_id, x_param_name = x_param.split('|')
        y_node_id, y_param_name = y_param.split('|')
    except ValueError:
        return create_empty_plot(), "❌ 参数格式错误，请重新选择"
    
    # 从graph中获取节点和参数对象
    x_node = graph.nodes.get(x_node_id)
    y_node = graph.nodes.get(y_node_id)
    
    if not x_node or not y_node:
        return create_empty_plot(), "❌ 参数所属节点不存在，请重新选择"
    
    # 构建参数信息字典
    x_param_info = {
        'value': x_param,
        'label': f"{x_node.name}.{x_param_name}",
        'unit': next((p.unit for p in x_node.parameters if p.name == x_param_name), "")
    }
    
    y_param_info = {
        'value': y_param,
        'label': f"{y_node.name}.{y_param_name}",
        'unit': next((p.unit for p in y_node.parameters if p.name == y_param_name), "")
    }
    
    # 执行敏感性分析
    result = perform_sensitivity_analysis(
        x_param_info, y_param_info, 
        x_start, x_end, x_step
    )
    
    if not result['success']:
        return create_empty_plot(), f"❌ {result['message']}", cumulative_data
    
    # 检查是否启用累计绘图
    is_cumulative = "cumulative" in (cumulative_checkbox or [])
    
    # 确定系列名称：优先使用用户自定义名称，否则使用默认名称
    final_series_name = series_name.strip() if series_name and series_name.strip() else f"{y_param_info['label']}"
    
    # 创建当前分析的数据项
    current_trace_data = {
        'x_values': result['x_values'],
        'y_values': result['y_values'],
        'x_label': result['x_label'],
        'y_label': result['y_label'],
        'trace_name': final_series_name,
        'x_param': x_param,
        'y_param': y_param,
        'timestamp': datetime.now().isoformat()
    }
    
    # 创建Plotly图表
    fig = go.Figure()
    
    # 如果启用累计绘图，先添加历史数据
    if is_cumulative and cumulative_data:
        for i, trace_data in enumerate(cumulative_data):
            # 为历史曲线使用不同的颜色和透明度
            color_alpha = max(0.3, 1.0 - i * 0.1)  # 历史曲线逐渐变淡
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
            color = colors[i % len(colors)]
            
            fig.add_trace(go.Scatter(
                x=trace_data['x_values'],
                y=trace_data['y_values'],
                mode='lines+markers',
                name=f"{trace_data['trace_name']}",
                line=dict(width=1.5, color=color),
                marker=dict(size=4, color=color),
                opacity=color_alpha,
                hovertemplate='<b>%{fullData.name}</b><br>' +
                              'X: %{x}<br>' +
                              'Y: %{y}<br>' +
                              '<extra></extra>'
            ))
    
    # 添加当前数据曲线
    fig.add_trace(go.Scatter(
        x=result['x_values'],
        y=result['y_values'],
        mode='lines+markers',
        name=f"{final_series_name} (当前)",
        line=dict(width=2, color='#1f77b4'),
        marker=dict(size=6, color='#1f77b4'),
        hovertemplate='<b>%{fullData.name}</b><br>' +
                      'X: %{x}<br>' +
                      'Y: %{y}<br>' +
                      '<extra></extra>'
    ))
    
    # 更新累计数据
    new_cumulative_data = cumulative_data.copy() if is_cumulative else []
    if is_cumulative:
        new_cumulative_data.append(current_trace_data)
        # 限制最大存储数量，避免内存溢出
        if len(new_cumulative_data) > 10:
            new_cumulative_data = new_cumulative_data[-10:]
    
    fig.update_layout(
        title=dict(
            text=f"参数敏感性分析{'（累计模式）' if is_cumulative else ''}",
            x=0.5,
            font=dict(size=16)
        ),
        xaxis_title=result['x_label'],
        yaxis_title=result['y_label'],
        hovermode='x unified',
        template="plotly_white",
        showlegend=True,  # 始终显示图例
        margin=dict(l=40, r=40, t=60, b=40),
        height=350,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )
    
    # 添加网格线和样式优化
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.3)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.3)')
    
    message = f"✅ {result['message']}"
    if is_cumulative:
        message += f" (累计: {len(new_cumulative_data)} 条曲线)"
    
    return fig, message, new_cumulative_data

# 清除图表
@callback(
    Output("sensitivity-plot", "figure", allow_duplicate=True),
    Output("x-param-selector", "value"),
    Output("y-param-selector", "value"),
    Output("cumulative-plot-data", "data", allow_duplicate=True),
    Input("clear-plot-btn", "n_clicks"),
    prevent_initial_call=True
)
def clear_plot(n_clicks):
    """清除图表、选择器和累计数据"""
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    return create_empty_plot(), None, None, []

# 导出绘图数据
@callback(
    Output("download-plot-data", "data"),
    Input("export-plot-data-btn", "n_clicks"),
    State("sensitivity-plot", "figure"),
    State("x-param-selector", "value"),
    State("y-param-selector", "value"),
    prevent_initial_call=True
)
def export_plot_data(n_clicks, figure, x_param, y_param):
    """导出绘图数据为CSV文件"""
    if not n_clicks or not figure:
        raise dash.exceptions.PreventUpdate
    
    try:
        # 检查图表是否有数据
        if not figure.get('data') or len(figure['data']) == 0:
            raise dash.exceptions.PreventUpdate
        
        trace_data = figure['data'][0]
        if 'x' not in trace_data or 'y' not in trace_data:
            raise dash.exceptions.PreventUpdate
        
        # 从参数值中解析参数信息
        x_param_info = None
        y_param_info = None
        
        if x_param and y_param:
            try:
                x_node_id, x_param_name = x_param.split('|')
                y_node_id, y_param_name = y_param.split('|')
                
                x_node = graph.nodes.get(x_node_id)
                y_node = graph.nodes.get(y_node_id)
                
                if x_node and y_node:
                    x_param_info = {'label': f"{x_node.name}.{x_param_name}"}
                    y_param_info = {'label': f"{y_node.name}.{y_param_name}"}
            except ValueError:
                pass
        
        # 构建CSV内容
        csv_lines = []
        
        # 添加头部信息
        csv_lines.append("# ArchDash 参数敏感性分析数据")
        csv_lines.append(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if x_param_info and y_param_info:
            csv_lines.append(f"# X轴参数: {x_param_info['label']}")
            csv_lines.append(f"# Y轴参数: {y_param_info['label']}")
        csv_lines.append("")
        
        # 添加列标题
        x_title = figure['layout'].get('xaxis', {}).get('title', {}).get('text', 'X')
        y_title = figure['layout'].get('yaxis', {}).get('title', {}).get('text', 'Y')
        csv_lines.append(f"{x_title},{y_title}")
        
        # 添加数据行
        x_values = trace_data['x']
        y_values = trace_data['y']
        
        for x_val, y_val in zip(x_values, y_values):
            csv_lines.append(f"{x_val},{y_val}")
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sensitivity_analysis_{timestamp}.csv"
        
        # 创建CSV字符串
        csv_content = "\n".join(csv_lines)
        
        return dict(
            content=csv_content,
            filename=filename,
            type="text/csv"
        )
        
    except Exception as e:
        # 静默失败，不影响用户体验
        print(f"导出数据失败: {e}")
        raise dash.exceptions.PreventUpdate

# 自动更新系列名称输入框的默认值
@callback(
    Output("series-name-input", "value"),
    Input("y-param-selector", "value"),
    prevent_initial_call=True
)
def auto_update_series_name(y_param):
    """当Y轴参数改变时，自动设置系列名称为该参数的标签"""
    if not y_param:
        return ""
    
    try:
        # 从参数值中解析节点ID和参数名
        y_node_id, y_param_name = y_param.split('|')
        
        # 从graph中获取节点
        y_node = graph.nodes.get(y_node_id)
        if not y_node:
            return ""
        
        # 构建默认系列名称
        default_name = f"{y_node.name}.{y_param_name}"
        return default_name
        
    except (ValueError, AttributeError):
        return ""

# 自动更新范围值（当选择X轴参数时）
@callback(
    Output("x-start-value", "value"),
    Output("x-end-value", "value"),
    Input("x-param-selector", "value"),
    prevent_initial_call=True
)
def auto_update_range(x_param):
    """当选择X轴参数时，自动设置合理的范围值"""
    if not x_param:
        raise dash.exceptions.PreventUpdate
    
    try:
        # 从x_param值中解析节点ID和参数名
        x_node_id, x_param_name = x_param.split('|')
        
        # 从graph中获取参数对象
        x_node = graph.nodes.get(x_node_id)
        if not x_node:
            raise dash.exceptions.PreventUpdate
        
        x_param_obj = None
        for param in x_node.parameters:
            if param.name == x_param_name:
                x_param_obj = param
                break
        
        if not x_param_obj:
            raise dash.exceptions.PreventUpdate
        
        current_value = float(x_param_obj.value)
        
        # 设置合理的范围（当前值的50%到150%）
        start_value = max(0, current_value * 0.5)
        end_value = current_value * 1.5
        
        # 如果当前值为0，设置默认范围
        if current_value == 0:
            start_value = 0
            end_value = 100
        
        return start_value, end_value
        
    except (ValueError, TypeError):
        # 如果转换失败，返回默认值
        return 0, 100

def get_all_parameter_dependencies():
    """获取计算图中所有参数的依赖关系，包括计算过程和历史"""
    if not graph.nodes:
        return []
    
    dependencies_info = []
    
    # 遍历所有节点和参数
    for node_id, node in graph.nodes.items():
        node_name = node.name
        
        for param_idx, param in enumerate(node.parameters):

            

            
            param_info = {
                'node_id': node_id,
                'node_name': node_name,
                'param_name': param.name,
                'param_value': param.value,
                'param_unit': param.unit,
                'param_description': param.description,
                'param_confidence': getattr(param, 'confidence', 1.0),
                'has_calculation': bool(param.calculation_func),
                'calculation_func': param.calculation_func,
                'dependencies': [],
                'dependents': [],
                'calculation_chain': [],  # 完整的计算链条
                'execution_time': None,   # 计算执行时间
                'calculation_error': None # 计算错误信息
            }
            
            # 获取直接依赖（增强版）
            for dep_param in param.dependencies:
                # 找到依赖参数所在的节点
                dep_node_id = None
                dep_node_name = None
                for search_node_id, search_node in graph.nodes.items():
                    if dep_param in search_node.parameters:
                        dep_node_id = search_node_id
                        dep_node_name = search_node.name
                        break
                
                # 计算依赖强度（基于参数类型）
                dep_strength = "正常"
                if dep_param.calculation_func:
                    dep_strength = "计算参数"
                else:
                    dep_strength = "输入参数"
                
                param_info['dependencies'].append({
                    'node_id': dep_node_id,
                    'node_name': dep_node_name,
                    'param_name': dep_param.name,
                    'param_value': dep_param.value,
                    'param_unit': dep_param.unit,
                    'param_obj': dep_param,
                    'dependency_strength': dep_strength
                })
            
            # 获取依赖于当前参数的参数（反向依赖）
            for search_node_id, search_node in graph.nodes.items():
                for search_param in search_node.parameters:
                    if param in search_param.dependencies:
                        search_node_name = search_node.name
                        param_info['dependents'].append({
                            'node_id': search_node_id,
                            'node_name': search_node_name,
                            'param_name': search_param.name,
                            'param_value': search_param.value,
                            'param_unit': search_param.unit,
                            'param_obj': search_param,
                            'has_calculation': bool(search_param.calculation_func)
                        })
            
            # 构建完整的计算链条（如果存在计算函数）
            if param.calculation_func and param.dependencies:
                try:
                    calculation_chain = []
                    for i, dep_param in enumerate(param.dependencies):
                        dep_name = dep_param.name
                        dep_value = dep_param.value
                        calculation_chain.append(f"dependencies[{i}] = {dep_name} = {dep_value}")
                    
                    # 添加计算过程
                    calculation_chain.append("↓ 执行计算函数 ↓")
                    calculation_chain.append(f"result = {param.value}")
                    
                    param_info['calculation_chain'] = calculation_chain
                except Exception as e:
                    param_info['calculation_error'] = str(e)
            
            dependencies_info.append(param_info)
    
    return dependencies_info

def format_dependencies_display(dependencies_info):
    """格式化依赖关系显示，包括计算过程和结果"""
    if not dependencies_info:
        return [html.P("暂无参数依赖关系", className="text-muted")]
    
    display_components = []
    
    # 增强的统计信息
    total_params = len(dependencies_info)
    params_with_deps = sum(1 for p in dependencies_info if p['dependencies'])
    params_with_calc = sum(1 for p in dependencies_info if p['has_calculation'])
    calculation_errors = sum(1 for p in dependencies_info if p['calculation_error'])
    

    
    display_components.append(
        dbc.Alert([
            html.H6("📊 计算图统计分析", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.P(f"📈 总参数数量: {total_params}", className="mb-1"),
                    html.P(f"🔗 依赖参数: {params_with_deps}", className="mb-1"),
                    html.P(f"⚙️ 计算参数: {params_with_calc}", className="mb-0"),
                ], width=6),
                dbc.Col([
                    html.P(f"❌ 计算错误: {calculation_errors}", className="mb-1"),
                ], width=6),
            ]),

        ], color="info", className="mb-3")
    )
    
    # 按节点分组显示，增加更多细节
    nodes_dict = {}
    for param_info in dependencies_info:
        node_name = param_info['node_name']
        if node_name not in nodes_dict:
            nodes_dict[node_name] = []
        nodes_dict[node_name].append(param_info)
    
    for node_name, params in nodes_dict.items():
        node_card_content = []
        
        for param_info in params:
            param_card_items = []
            
            # 参数基本信息（增强版）
            confidence_color = "success" if param_info['param_confidence'] >= 0.8 else "warning" if param_info['param_confidence'] >= 0.5 else "danger"
            param_card_items.append(
                html.Div([
                    html.Div([
                        html.Strong(f"{param_info['param_name']}", className="me-2"),

                        dbc.Badge(f"置信度 {param_info['param_confidence']:.1%}", 
                                color=confidence_color, className="me-2"),
                    ], className="d-flex align-items-center mb-2"),
                    html.P([
                        html.Code(f"{param_info['param_value']} {param_info['param_unit']}", className="me-2"),
                        html.Small(param_info['param_description'], className="text-muted")
                    ], className="mb-2")
                ])
            )
            
            # 计算过程展示（新增）
            if param_info['has_calculation']:
                calc_details = []
                
                # 计算函数代码
                calc_details.append(
                    dbc.Accordion([
                        dbc.AccordionItem([
                            html.Pre(param_info['calculation_func'] or "无计算函数", 
                                   style={"fontSize": "0.8em", "backgroundColor": "#f8f9fa", "padding": "10px"})
                        ], title="📝 计算函数代码")
                    ], start_collapsed=True, className="mb-2")
                )
                
                # 计算链条展示
                if param_info['calculation_chain']:
                    chain_items = []
                    for step in param_info['calculation_chain']:
                        if "dependencies[" in step:
                            chain_items.append(html.Li(step, className="text-info"))
                        elif "执行计算函数" in step:
                            chain_items.append(html.Li(step, className="text-warning fw-bold"))
                        else:
                            chain_items.append(html.Li(step, className="text-success fw-bold"))
                    
                    calc_details.append(
                        html.Div([
                            html.H6("🔄 计算执行链条", className="mb-2"),
                            html.Ol(chain_items, className="mb-2")
                        ])
                    )
                

                
                # 计算错误展示
                if param_info['calculation_error']:
                    calc_details.append(
                        dbc.Alert([
                            html.H6("❌ 计算错误", className="mb-2"),
                            html.Code(param_info['calculation_error'])
                        ], color="danger", className="mb-2")
                    )
                
                param_card_items.append(
                    dbc.Card([
                        dbc.CardHeader("⚙️ 计算详情"),
                        dbc.CardBody(calc_details)
                    ], className="mb-2", outline=True, color="light")
                )
            
            # 依赖关系展示（增强版）
            if param_info['dependencies']:
                deps_details = []
                for dep in param_info['dependencies']:
                    strength_color = {
                        "计算参数": "success",
                        "输入参数": "secondary", 
                        "正常": "info"
                    }.get(dep['dependency_strength'], "info")
                    
                    deps_details.append(
                        html.Li([
                            html.Strong(f"{dep['node_name']}.{dep['param_name']}"),
                            f" = {dep['param_value']} {dep['param_unit']} ",
                            dbc.Badge(dep['dependency_strength'], color=strength_color, className="ms-2")
                        ], className="mb-2")
                    )
                
                param_card_items.append(
                    html.Div([
                        html.H6("⬅️ 输入依赖", className="mb-2 text-danger"),
                        html.Ul(deps_details)
                    ], className="mb-2")
                )
            
            # 被依赖关系展示（增强版）
            if param_info['dependents']:
                dependents_details = []
                for dep in param_info['dependents']:
                    calc_badge = dbc.Badge("计算", color="success") if dep['has_calculation'] else dbc.Badge("直接", color="secondary")
                    dependents_details.append(
                        html.Li([
                            html.Strong(f"{dep['node_name']}.{dep['param_name']}"),
                            f" = {dep['param_value']} {dep['param_unit']} ",
                            calc_badge
                        ], className="mb-1")
                    )
                
                param_card_items.append(
                    html.Div([
                        html.H6("➡️ 输出影响", className="mb-2 text-success"),
                        html.Ul(dependents_details)
                    ], className="mb-2")
                )
            
            # 独立参数标识
            if not param_info['dependencies'] and not param_info['dependents']:
                param_card_items.append(
                    dbc.Alert("🔸 独立参数（无依赖关系）", color="light", className="mb-2")
                )
            
            node_card_content.append(
                html.Div(param_card_items, className="border-start border-4 border-primary ps-3 mb-4", 
                        style={"backgroundColor": "#f8f9fa", "borderRadius": "0 5px 5px 0", "padding": "15px"})
            )
        
        display_components.append(
            dbc.Card([
                dbc.CardHeader([
                    html.H5([
                        "📦 ", node_name,
                        dbc.Badge(f"{len(params)} 参数", color="info", className="ms-2")
                    ], className="mb-0")
                ]),
                dbc.CardBody(node_card_content)
            ], className="mb-3")
        )
    
    return display_components



def create_calculation_flow_visualization(dependencies_info):
    """创建计算流程可视化组件"""
    if not dependencies_info:
        return html.Div()
    
    # 找出有计算函数的参数
    calc_params = [p for p in dependencies_info if p['has_calculation']]
    
    if not calc_params:
        return dbc.Alert("当前没有计算参数", color="info")
    
    flow_components = []
    
    for param_info in calc_params:
        # 创建计算流程图
        flow_steps = []
        
        # 输入步骤
        if param_info['dependencies']:
            input_step = html.Div([
                html.H6("📥 输入参数", className="text-primary"),
                html.Ul([
                    html.Li(f"{dep['node_name']}.{dep['param_name']} = {dep['param_value']} {dep['param_unit']}")
                    for dep in param_info['dependencies']
                ])
            ], className="border p-3 mb-3 rounded bg-light")
            flow_steps.append(input_step)
        
        # 计算步骤
        calc_step = html.Div([
            html.H6("⚙️ 计算过程", className="text-warning"),
            dbc.Accordion([
                dbc.AccordionItem([
                    html.Pre(param_info['calculation_func'], 
                           style={"fontSize": "0.85em", "background": "#f1f3f4"})
                ], title="查看计算函数")
            ], start_collapsed=True),

        ], className="border p-3 mb-3 rounded bg-warning bg-opacity-10")
        flow_steps.append(calc_step)
        
        # 输出步骤
        output_step = html.Div([
            html.H6("📤 输出结果", className="text-success"),
            html.P([
                html.Strong(f"{param_info['param_name']} = "),
                html.Code(f"{param_info['param_value']} {param_info['param_unit']}")
            ]),
            html.Small(f"置信度: {param_info['param_confidence']:.1%}", className="text-muted")
        ], className="border p-3 mb-3 rounded bg-success bg-opacity-10")
        flow_steps.append(output_step)
        
        # 影响步骤
        if param_info['dependents']:
            impact_step = html.Div([
                html.H6("🎯 影响范围", className="text-info"),
                html.Ul([
                    html.Li(f"{dep['node_name']}.{dep['param_name']}")
                    for dep in param_info['dependents']
                ])
            ], className="border p-3 mb-3 rounded bg-info bg-opacity-10")
            flow_steps.append(impact_step)
        
        # 组装完整的流程卡片
        flow_card = dbc.Card([
            dbc.CardHeader([
                html.H5([
                    "🔄 ", f"{param_info['node_name']}.{param_info['param_name']}",
                    " 计算流程"
                ])
            ]),
            dbc.CardBody(flow_steps)
        ], className="mb-4")
        
        flow_components.append(flow_card)
    
    return html.Div(flow_components)

# =============== 增强的依赖关系和计算流程显示回调函数 ===============

# 初始化依赖关系显示
@callback(
    Output("dependencies-display", "children"),
    Input("canvas-container", "children"),
    prevent_initial_call=False
)
def initialize_dependencies_display(canvas_children):
    """初始化依赖关系显示"""
    try:
        dependencies_info = get_all_parameter_dependencies()
        return format_dependencies_display(dependencies_info)
    except Exception as e:
        return [
            dbc.Alert([
                html.H6("⚠️ 加载依赖关系失败", className="mb-2"),
                html.P(f"错误信息: {str(e)}", className="mb-0")
            ], color="warning")
        ]

# 初始化计算流程显示
@callback(
    Output("calculation-flow-display", "children"),
    Input("canvas-container", "children"),
    prevent_initial_call=False
)
def initialize_calculation_flow_display(canvas_children):
    """初始化计算流程显示"""
    try:
        dependencies_info = get_all_parameter_dependencies()
        return create_calculation_flow_visualization(dependencies_info)
    except Exception as e:
        return [
            dbc.Alert([
                html.H6("⚠️ 加载计算流程失败", className="mb-2"),
                html.P(f"错误信息: {str(e)}", className="mb-0")
            ], color="warning")
        ]



# 手动刷新依赖关系和计算流程
@callback(
    Output("dependencies-display", "children", allow_duplicate=True),
    Output("calculation-flow-display", "children", allow_duplicate=True),
    Input("refresh-dependencies-btn", "n_clicks"),
    prevent_initial_call=True
)
def refresh_all_displays(n_clicks):
    """手动刷新所有显示面板"""
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    try:
        dependencies_info = get_all_parameter_dependencies()
        
        # 刷新依赖关系显示
        deps_display = format_dependencies_display(dependencies_info)
        
        # 刷新计算流程显示
        flow_display = create_calculation_flow_visualization(dependencies_info)
        
        return deps_display, flow_display
        
    except Exception as e:
        error_alert = [
            dbc.Alert([
                html.H6("⚠️ 刷新失败", className="mb-2"),
                html.P(f"错误信息: {str(e)}", className="mb-0")
            ], color="danger")
        ]
        return error_alert, error_alert

# 当节点/参数发生变化时自动更新所有显示
@callback(
    Output("dependencies-display", "children", allow_duplicate=True),
    Output("calculation-flow-display", "children", allow_duplicate=True),
    Input("node-data", "data"),
    prevent_initial_call=True
)
def auto_update_all_displays_on_change(node_data):
    """当节点或参数发生变化时自动更新所有显示"""
    try:
        dependencies_info = get_all_parameter_dependencies()
        
        # 更新依赖关系显示
        deps_display = format_dependencies_display(dependencies_info)
        
        # 更新计算流程显示
        flow_display = create_calculation_flow_visualization(dependencies_info)
        
        return deps_display, flow_display
        
    except Exception as e:
        error_alert = [
            dbc.Alert([
                html.H6("⚠️ 自动更新失败", className="mb-2"),
                html.P(f"错误信息: {str(e)}", className="mb-0")
            ], color="warning")
        ]
        return error_alert, error_alert



def get_arrow_connections_data():
    """获取用于绘制箭头的连接数据"""
    connections = []
    
    if not graph.nodes:
        return connections
    
    # 遍历所有节点和参数，生成连接数据
    for node_id, node in graph.nodes.items():
        for param_idx, param in enumerate(node.parameters):
            # 为每个有依赖的参数创建连接
            for dep_param in param.dependencies:
                # 找到依赖参数所在的节点和索引
                source_node_id = None
                source_param_idx = None
                
                for search_node_id, search_node in graph.nodes.items():
                    for search_param_idx, search_param in enumerate(search_node.parameters):
                        if search_param is dep_param:
                            source_node_id = search_node_id
                            source_param_idx = search_param_idx
                            break
                    if source_node_id:
                        break
                
                if source_node_id is not None and source_param_idx is not None:
                    connection = {
                        'source_pin_id': f"pin-{source_node_id}-{source_param_idx}",
                        'target_pin_id': f"pin-{node_id}-{param_idx}",
                        'source_node_id': source_node_id,
                        'target_node_id': node_id,
                        'source_param_name': dep_param.name,
                        'target_param_name': param.name,
                        'source_node_name': graph.nodes[source_node_id].name,
                        'target_node_name': graph.nodes[node_id].name
                    }
                    connections.append(connection)
    
    return connections

# 下拉菜单z-index管理的客户端回调
app.clientside_callback(
    """
    function() {
        // 监听所有下拉菜单的显示/隐藏事件
        function setupDropdownListeners() {
            // 移除所有现有的监听器
            document.querySelectorAll('.dropdown-toggle').forEach(btn => {
                btn.removeEventListener('click', handleDropdownToggle);
            });
            
            // 添加新的监听器
            document.querySelectorAll('.dropdown-toggle').forEach(btn => {
                btn.addEventListener('click', handleDropdownToggle);
            });
            
            // 监听点击外部区域关闭下拉菜单
            document.addEventListener('click', handleOutsideClick);
        }
        
        function handleDropdownToggle(event) {
            const toggle = event.target.closest('.dropdown-toggle');
            const dropdown = toggle ? toggle.closest('.dropdown') : null;
            const nodeContainer = toggle ? toggle.closest('.node-container') : null;
            
            if (nodeContainer) {
                // 重置所有节点的z-index
                document.querySelectorAll('.node-container').forEach(node => {
                    node.classList.remove('dropdown-active');
                });
                
                // 立即提升当前节点的层级，不等待菜单显示
                nodeContainer.classList.add('dropdown-active');
            }
        }
        
        function handleOutsideClick(event) {
            if (!event.target.closest('.dropdown')) {
                // 如果点击在下拉菜单外部，重置所有节点的z-index
                document.querySelectorAll('.node-container').forEach(node => {
                    node.classList.remove('dropdown-active');
                });
            }
        }
        
        // 初始化监听器
        setupDropdownListeners();
        
        // 使用MutationObserver监听DOM变化，重新设置监听器
        const observer = new MutationObserver(function(mutations) {
            let needsUpdate = false;
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1 && (
                            node.classList.contains('node-container') ||
                            node.querySelector('.dropdown-toggle')
                        )) {
                            needsUpdate = true;
                        }
                    });
                }
            });
            if (needsUpdate) {
                setTimeout(setupDropdownListeners, 100);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        return window.dash_clientside.no_update;
    }
    """,
    Output("canvas-container", "id"),  # 虚拟输出
    Input("canvas-container", "children")
)

# 深色主题切换回调
# 折叠依赖关系面板的回调
@callback(
    Output("dependencies-collapse", "is_open"),
    Output("collapse-dependencies-btn", "children"),
    Input("collapse-dependencies-btn", "n_clicks"),
    State("dependencies-collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_dependencies_collapse(n_clicks, is_open):
    """切换依赖关系面板的展开/折叠状态"""
    if n_clicks:
        new_state = not is_open
        if new_state:
            return new_state, ["🔼 ", html.Span("折叠")]
        else:
            return new_state, ["🔽 ", html.Span("展开")]
    return is_open, ["🔽 ", html.Span("展开")]

# 参数编辑模态窗口中依赖参数模块的折叠回调
@callback(
    Output("dependencies-collapse-modal", "is_open"),
    Output("dependencies-collapse-btn-modal", "children"),
    Input("dependencies-collapse-btn-modal", "n_clicks"),
    State("dependencies-collapse-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_dependencies_collapse_modal(n_clicks, is_open):
    """切换参数编辑模态窗口中依赖参数模块的展开/折叠状态"""
    if n_clicks:
        new_state = not is_open
        if new_state:
            return new_state, ["🔼 ", html.Span("依赖参数")]
        else:
            return new_state, ["🔽 ", html.Span("依赖参数")]
    return is_open, ["🔽 ", html.Span("依赖参数")]

# 放大图表功能
@callback(
    Output("enlarged-plot-modal", "is_open"),
    Output("enlarged-plot", "figure"),
    Input("enlarge-plot-btn", "n_clicks"),
    Input("close-enlarged-plot", "n_clicks"),
    State("sensitivity-plot", "figure"),
    State("enlarged-plot-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_enlarged_plot(enlarge_clicks, close_clicks, current_figure, is_open):
    """打开/关闭放大的图表模态窗口"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "enlarge-plot-btn" and enlarge_clicks:
        if current_figure and current_figure.get('data'):
            # 创建放大版本的图表
            enlarged_figure = current_figure.copy()
            
            # 增强放大图表的样式
            enlarged_figure['layout'].update({
                'height': None,  # 让模态窗口控制高度
                'font': {'size': 14},
                'title': {
                    'font': {'size': 20},
                    'x': 0.5,
                    'xanchor': 'center'
                },
                'xaxis': {
                    **enlarged_figure['layout'].get('xaxis', {}),
                    'title': {
                        **enlarged_figure['layout'].get('xaxis', {}).get('title', {}),
                        'font': {'size': 16}
                    },
                    'tickfont': {'size': 12}
                },
                'yaxis': {
                    **enlarged_figure['layout'].get('yaxis', {}),
                    'title': {
                        **enlarged_figure['layout'].get('yaxis', {}).get('title', {}),
                        'font': {'size': 16}
                    },
                    'tickfont': {'size': 12}
                },
                'showlegend': True,  # 放大图表显示图例
                'margin': {'l': 80, 'r': 50, 't': 80, 'b': 80}
            })
            
            return True, enlarged_figure
        else:
            return False, dash.no_update
    
    elif button_id == "close-enlarged-plot" and close_clicks:
        return False, dash.no_update
    
    return is_open, dash.no_update

@callback(
    Output("theme-toggle", "children"),
    Input("theme-toggle", "n_clicks"),
    prevent_initial_call=True
)
def toggle_theme(n_clicks):
    """切换深色/浅色主题"""
    if n_clicks is None:
        return "🌙"
    
    # 切换主题图标
    return "☀️" if n_clicks % 2 == 1 else "🌙"

# 客户端回调用于实际切换主题
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks === null) {
            return window.dash_clientside.no_update;
        }
        
        const body = document.body;
        const isDark = n_clicks % 2 === 1;
        
        if (isDark) {
            body.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            body.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output("theme-toggle", "id"),  # 虚拟输出
    Input("theme-toggle", "n_clicks")
)

# 页面加载时恢复主题设置
app.clientside_callback(
    """
    function() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.setAttribute('data-theme', 'dark');
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("theme-toggle", "title"),  # 虚拟输出
    Input("theme-toggle", "id")
)

# 节点编辑相关回调函数

# 打开节点编辑模态窗口
@callback(
    Output("node-edit-modal", "is_open"),
    Output("node-edit-title", "children"),
    Output("node-edit-name", "value"),
    Output("node-edit-description", "value"),
    Output("node-edit-data", "data"),
    Input({"type": "edit-node", "node": ALL}, "n_clicks"),
    State("node-edit-modal", "is_open"),
    prevent_initial_call=True
)
def open_node_edit_modal(edit_clicks, is_open):
    if not ctx.triggered_id:
        raise dash.exceptions.PreventUpdate
    
    # 检查触发值，避免重新创建组件时的误触发
    trigger_value = ctx.triggered[0]["value"]
    if not trigger_value or trigger_value == 0:
        raise dash.exceptions.PreventUpdate
    
    # 获取被点击的节点信息
    triggered_id = ctx.triggered_id
    if isinstance(triggered_id, dict) and triggered_id["type"] == "edit-node":
        node_id = triggered_id["node"]
        
        # 获取节点对象
        if node_id not in graph.nodes:
            raise dash.exceptions.PreventUpdate
        
        node = graph.nodes[node_id]
        node_name = node.name
        
        return (
            True,  # 打开模态窗口
            f"编辑节点: {node_name}",
            node.name,
            node.description,
            {"node_id": node_id}
        )
    
    raise dash.exceptions.PreventUpdate

# 关闭节点编辑模态窗口
@callback(
    Output("node-edit-modal", "is_open", allow_duplicate=True),
    Input("node-edit-cancel", "n_clicks"),
    prevent_initial_call=True
)
def close_node_edit_modal(cancel_clicks):
    if cancel_clicks:
        return False
    raise dash.exceptions.PreventUpdate

# 保存节点编辑
@callback(
    Output("node-edit-modal", "is_open", allow_duplicate=True),
    Output("canvas-container", "children", allow_duplicate=True),
    Output("output-result", "children", allow_duplicate=True),
    Input("node-edit-save", "n_clicks"),
    State("node-edit-name", "value"),
    State("node-edit-description", "value"),
    State("node-edit-data", "data"),
    prevent_initial_call=True
)
def save_node_changes(save_clicks, node_name, node_description, edit_data):
    if not save_clicks:
        raise dash.exceptions.PreventUpdate
    
    try:
        # 验证输入
        if not node_name or not node_name.strip():
            return True, dash.no_update, "错误: 节点名称不能为空"
        
        node_id = edit_data["node_id"]
        
        if node_id not in graph.nodes:
            return True, dash.no_update, "错误: 节点不存在"
        
        node = graph.nodes[node_id]
        old_name = node.name
        
        # 检查节点名称是否与其他节点重复（排除当前节点）
        for other_node_id, other_node in graph.nodes.items():
            if other_node_id != node_id and other_node.name == node_name.strip():
                return True, dash.no_update, f"错误: 节点名称 '{node_name.strip()}' 已存在，请使用不同的名称"
        
        # 更新节点信息
        node.name = node_name.strip()
        node.description = node_description or ""
        
        # 关闭模态窗口并更新界面
        success_message = f"节点 '{old_name}' 已更新为 '{node.name}'"
        return False, update_canvas(), success_message
        
    except Exception as e:
        return True, dash.no_update, f"错误: {str(e)}"

# 添加节点模态窗口相关回调函数

# 打开添加节点模态窗口
@callback(
    Output("node-add-modal", "is_open"),
    Output("node-add-name", "value"),
    Output("node-add-description", "value"),
    Input("add-node-from-graph-button", "n_clicks"),
    Input("node-add-cancel", "n_clicks"),
    State("node-add-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_node_add_modal(add_clicks, cancel_clicks, is_open):
    if not ctx.triggered_id:
        raise dash.exceptions.PreventUpdate
    
    if ctx.triggered_id == "add-node-from-graph-button":
        # 打开模态窗口并清空输入
        return True, "", ""
    elif ctx.triggered_id == "node-add-cancel":
        # 关闭模态窗口
        return False, "", ""
    
    raise dash.exceptions.PreventUpdate

# 创建新节点
@callback(
    Output("node-add-modal", "is_open", allow_duplicate=True),
    Output("canvas-container", "children", allow_duplicate=True),
    Output("output-result", "children", allow_duplicate=True),
    Input("node-add-save", "n_clicks"),
    State("node-add-name", "value"),
    State("node-add-description", "value"),
    prevent_initial_call=True
)
def create_new_node(save_clicks, node_name, node_description):
    if not save_clicks:
        raise dash.exceptions.PreventUpdate
    
    try:
        # 验证输入
        if not node_name or not node_name.strip():
            return True, dash.no_update, "错误: 节点名称不能为空"
        
        node_name = node_name.strip()
        
        # 检查节点名称是否与其他节点重复
        for existing_node in graph.nodes.values():
            if existing_node.name == node_name:
                return True, dash.no_update, f"错误: 节点名称 '{node_name}' 已存在，请使用不同的名称"
        
        # 创建新节点
        from models import Node
        node_id = graph.get_next_node_id()
        node = Node(
            id=node_id,
            name=node_name,
            description=node_description or f"节点 {node_name}"
        )
        
        # 添加到计算图
        graph.add_node(node)
        
        # 使用布局管理器放置节点
        position = graph.layout_manager.place_node(node.id)
        
        # 关闭模态窗口并更新界面
        success_message = f"节点 '{node_name}' 已创建并添加到位置 ({position.row}, {position.col})"
        return False, update_canvas(), success_message
        
    except Exception as e:
        return True, dash.no_update, f"错误: {str(e)}"

# 列管理回调函数
@callback(
    Output("canvas-container", "children", allow_duplicate=True),
    Output("output-result", "children", allow_duplicate=True),
    Output("remove-column-btn", "disabled"),
    Input("add-column-btn", "n_clicks"),
    Input("remove-column-btn", "n_clicks"),
    State("canvas-container", "children"),  # 添加状态以获取当前列信息
    prevent_initial_call=True
)
def handle_column_management(add_clicks, remove_clicks, canvas_children):
    """处理手动添加/删除列操作"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # 判断当前是否可以删除列
    can_remove, remove_msg = graph.layout_manager.can_remove_column()

    # 添加列
    if button_id == "add-column-btn" and add_clicks:
        can_add, add_msg = graph.layout_manager.can_add_column()
        if not can_add:
            return dash.no_update, f"❌ {add_msg}", not can_remove

        graph.layout_manager.add_column()
        return update_canvas(), f"✅ 已添加新列 (当前 {graph.layout_manager.cols} 列)", False

    # 删除列
    if button_id == "remove-column-btn" and remove_clicks:
        if not can_remove:
            return dash.no_update, f"❌ {remove_msg}", True

        success = graph.layout_manager.remove_column()
        if success:
            msg = f"✅ 已删除最后一列 (当前 {graph.layout_manager.cols} 列)"
        else:
            msg = "❌ 无法删除最后一列，可能不为空"

        # 再次检查是否还能继续删除
        can_remove_after, _ = graph.layout_manager.can_remove_column()
        return update_canvas(), msg, not can_remove_after

    raise dash.exceptions.PreventUpdate

# 初始化删除按钮状态
@callback(
    Output("remove-column-btn", "disabled", allow_duplicate=True),
    Input("canvas-container", "children"),
    prevent_initial_call=True
)
def update_remove_button_status(canvas_children):
    """更新删除列按钮的禁用状态"""
    # 检查是否可以删除列
    can_remove, _ = graph.layout_manager.can_remove_column()
    return not can_remove

# 添加依赖检查工具函数
def check_parameter_has_dependents(param_obj, graph_instance):
    """检查参数是否被其他参数依赖
    
    Args:
        param_obj: 要检查的参数对象
        graph_instance: 要在其中检查的 CalculationGraph 实例
        
    Returns:
        tuple: (has_dependents: bool, dependent_list: list)
            has_dependents: 是否有其他参数依赖此参数
            dependent_list: 依赖此参数的参数列表，格式为[{"node_name": str, "param_name": str, "param_obj": Parameter}, ...]
    """
    dependent_list = []
    
    # 遍历所有节点和参数，查找依赖关系
    for node_id, node in graph_instance.nodes.items():
        node_name = node.name
        
        for param in node.parameters:
            if param_obj in param.dependencies:
                dependent_list.append({
                    "node_name": node_name,
                    "param_name": param.name,
                    "param_obj": param
                })
    
    return len(dependent_list) > 0, dependent_list

def check_node_has_dependents(node_id, graph_instance):
    """检查节点的所有参数是否被其他参数依赖
    
    Args:
        node_id: 要检查的节点ID
        graph_instance: 要在其中检查的 CalculationGraph 实例
        
    Returns:
        tuple: (has_dependents: bool, dependent_info: dict)
            has_dependents: 是否有其他参数依赖此节点的参数
            dependent_info: 依赖信息字典，格式为 {
                "dependent_params": [{"node_name": str, "param_name": str, "depends_on": str}, ...],
                "affected_node_params": [str, ...]  # 本节点中被依赖的参数名列表
            }
    """
    if node_id not in graph_instance.nodes:
        return False, {"dependent_params": [], "affected_node_params": []}
    
    node = graph_instance.nodes[node_id]
    dependent_params = []
    affected_node_params = []
    
    # 检查该节点的每个参数是否被其他参数依赖
    for param in node.parameters:
        has_deps, dep_list = check_parameter_has_dependents(param, graph_instance)
        if has_deps:
            affected_node_params.append(param.name)
            for dep_info in dep_list:
                dependent_params.append({
                    "node_name": dep_info["node_name"],
                    "param_name": dep_info["param_name"],
                    "depends_on": param.name
                })
    
    dependent_info = {
        "dependent_params": dependent_params,
        "affected_node_params": affected_node_params
    }
    
    return len(dependent_params) > 0, dependent_info

# 清空计算图功能
@callback(
    Output("canvas-container", "children", allow_duplicate=True),
    Output("output-result", "children", allow_duplicate=True),
    Input("clear-graph-btn", "n_clicks"),
    prevent_initial_call=True
)
def clear_calculation_graph(n_clicks):
    """清空当前的计算图，重置为空白状态"""
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    try:
        # 清空全局数据模型
        # global graph  # 已废弃
        
        # 重新创建空的计算图和布局管理器
        new_graph = CalculationGraph()
        new_graph.set_layout_manager(CanvasLayoutManager(initial_cols=3, initial_rows=10))
        set_graph(new_graph)
        graph = get_graph()
        
        # 清空最近更新的参数集合
        graph.recently_updated_params.clear()
        
        # 更新画布显示
        updated_canvas = update_canvas()
        
        return updated_canvas, "✅ 计算图已清空，可以重新开始构建"
        
    except Exception as e:
        return dash.no_update, f"❌ 清空失败: {str(e)}"

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='启动计算图应用')
    parser.add_argument('--port', type=int, default=8050, help='服务端口号(默认:8050)')
    args = parser.parse_args()
    
    app.run(debug=True, host="0.0.0.0", port=args.port)