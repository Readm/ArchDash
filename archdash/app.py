import dash
from dash import html, dcc, Output, Input, State, ctx, MATCH, ALL, callback
import dash_bootstrap_components as dbc
from .models import CalculationGraph, Node, Parameter, CanvasLayoutManager, GridPosition
from .session_graph import get_graph, set_graph, GraphProxy
from typing import Dict, Optional, List, Any
import json
from datetime import datetime
import uuid
import plotly.graph_objects as go
import numpy as np
import os
from .layout import *
from .examples import *
import traceback
from .clientside_callbacks import register_all_clientside_callbacks
from .constants import AppConstants, ValidationConstants, PerformanceConstants
import time

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

app.server.secret_key = os.environ.get("SECRET_KEY", str(uuid.uuid4()))

graph: CalculationGraph = GraphProxy()

# 创建布局管理器
layout_manager = CanvasLayoutManager(
    initial_cols=AppConstants.DEFAULT_INITIAL_COLUMNS, 
    initial_rows=AppConstants.DEFAULT_INITIAL_ROWS
)
graph.set_layout_manager(layout_manager)

# 画布事件处理辅助函数
def create_canvas_event(event_type, data=None):
    """创建画布更新事件"""
    return {
        "type": event_type,
        "timestamp": time.time(),
        "data": data or {}
    }

def add_canvas_event(current_events, new_event):
    """添加新事件到事件列表，支持批量事件"""
    try:
        # 确保current_events是list类型
        if current_events is None:
            events = []
        elif isinstance(current_events, list):
            events = current_events[-AppConstants.MAX_RECENT_EVENTS:]  # 保持最近事件
        else:
            # 如果不是list，创建新的list
            print(f"Warning: current_events is not a list, type: {type(current_events)}, value: {current_events}")
            events = []
        
        # 支持批量添加事件
        if isinstance(new_event, list):
            events.extend(new_event)
            print(f"Debug: Added {len(new_event)} batch events, total events: {len(events)}")
        else:
            events.append(new_event)
            print(f"Debug: Added event {new_event['type']}, total events: {len(events)}")
        
        return events
    except Exception as e:
        print(f"Error in add_canvas_event: {e}")
        print(f"current_events type: {type(current_events)}")
        print(f"current_events value: {current_events}")
        # 出错时创建新的事件列表
        if isinstance(new_event, list):
            return new_event
        else:
            return [new_event]

# 消息管理辅助函数
def create_message(message_type, content, level="info"):
    """创建标准化消息对象"""
    return {
        "type": message_type,
        "content": content,
        "level": level,  # info, success, warning, error
        "timestamp": time.time()
    }

def add_app_message(current_messages, new_message):
    """添加新消息到消息系统"""
    try:
        if current_messages is None:
            messages_data = {"messages": [], "timestamp": 0}
        else:
            messages_data = current_messages
        
        # 保持最近20条消息
        messages = messages_data.get("messages", [])[-AppConstants.MAX_RECENT_MESSAGES:]
        
        # 添加新消息
        if isinstance(new_message, list):
            messages.extend(new_message)
        else:
            messages.append(new_message)
        
        return {
            "messages": messages,
            "timestamp": time.time()
        }
    except Exception as e:
        print(f"Error in add_app_message: {e}")
        return {
            "messages": [new_message] if not isinstance(new_message, list) else new_message,
            "timestamp": time.time()
        }

def format_message_display(messages_data):
    """格式化消息为显示组件"""
    if not messages_data or not messages_data.get("messages"):
        return ""
    
    # 显示最新消息
    latest_message = messages_data["messages"][-1]
    content = latest_message.get("content", "")
    level = latest_message.get("level", "info")
    
    # 根据级别设置样式
    if level == "error":
        return html.Div(content, className="message-error")
    elif level == "success":
        return html.Div(content, className="message-success")
    elif level == "warning":
        return html.Div(content, className="message-warning")
    else:
        return html.Div(content)

# 统一的画布更新处理器
@callback(
    Output("canvas-container", "children"),
    Input("canvas-events", "data"),
    prevent_initial_call=False
)
def unified_canvas_update(events):
    """统一的画布更新处理器"""
    try:
        # 初始化时或无事件时，进行全量更新
        if not events:
            return update_canvas()
        
        # 获取最新事件
        latest_event = events[-1]
        event_type = latest_event.get("type")
        
        # 目前所有事件都使用全量更新，后续可以优化为增量更新
        return update_canvas()
    except Exception as e:
        print(f"Error in unified_canvas_update: {e}")
        return update_canvas()

# 统一的消息渲染处理器
@callback(
    Output("output-result", "children"),
    Input("app-messages", "data"),
    prevent_initial_call=False
)
def unified_message_display(messages_data):
    """统一的消息显示处理器"""
    try:
        return format_message_display(messages_data)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in unified_message_display: {e}")
        print(f"Traceback:\n{error_details}")
        return html.Div(f"消息显示错误: {str(e)}", className="message-error")

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

result = value"""

    code_lines = ["# 计算函数"]
    for i, dep_info in enumerate(selected_dependencies):
        code_lines.append(f"# {dep_info['param_name']} = dependencies[{i}].value")
        code_lines.append(f"# {dep_info['param_name']}置信度 = dependencies[{i}].confidence")

    code_lines.extend([
        "",
        "# 设置固定置信度：",
        "# self.confidence = 0.8  # 80% 置信度",
        "",
        "# 编写计算逻辑",
        "result = value  # 修改这里",
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

        x_node = graph.nodes.get(x_node_id)
        y_node = graph.nodes.get(y_node_id)

        if not x_node or not y_node:
            return {'success': False, 'message': '参数所属节点不存在'}

        x_param = None
        y_param = None

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

        original_x_value = x_param.value

        x_values = []
        y_values = []

        x_range = np.arange(x_start, x_end + x_step, x_step)

        if len(x_range) > AppConstants.MAX_DATA_POINTS:
            return {
                'success': False, 
                'message': f'数据点过多 ({len(x_range)} 点)，请减少范围或增大步长 (最大1000点)'
            }

        x_was_unlinked = getattr(x_param, 'unlinked', False)
        if x_param.calculation_func and x_param.dependencies and not x_was_unlinked:
            x_param.set_manual_value(x_param.value)  # 保持当前值但断开计算

        for x_val in x_range:
            try:
                update_result = graph.set_parameter_value(x_param, float(x_val))

                y_val = y_param.value

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
        margin=dict(
            l=AppConstants.CHART_MARGIN_LEFT, 
            r=AppConstants.CHART_MARGIN_RIGHT, 
            t=AppConstants.CHART_MARGIN_TOP, 
            b=AppConstants.CHART_MARGIN_BOTTOM
        ),
        height=AppConstants.CHART_DEFAULT_HEIGHT,
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

def ensure_minimum_columns(min_cols: int = AppConstants.MIN_LAYOUT_COLUMNS):
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
                    html.I(className="fas fa-project-diagram empty-state-icon"),
                    html.P([
                        "开始构建计算图：",
                    ], className="text-muted mb-4"),
                    html.Div([
                        html.Div([
                            html.Span(className="empty-state-emoji"),
                            "点击右上角 ",
                            html.Strong("🎯", className="text-warning"),
                            " 按钮载入SoC示例计算图"
                        ], className="mb-3 p-3 border rounded bg-light"),
                        html.Div([
                            html.Span(className="empty-state-emoji"),
                            "点击右上角 ",
                            html.Strong("➕", className="text-primary"),
                            " 按钮添加新节点，并添加参数"
                        ], className="mb-3 p-3 border rounded bg-light"),
                        html.Div([
                            html.Span("📁", className="empty-state-emoji"),
                            "或从文件加载已有的计算图"
                        ], className="p-3 border rounded bg-light")
                    ])
                ], className="text-center p-5"),
            ], className="d-flex justify-content-center align-items-center empty-state-container")
        ])

        canvas_with_arrows = html.Div([
            empty_state_content,
            html.Div(
                [],
                className="arrows-overlay",
                id="arrows-overlay"
            )
        ], className="relative-container")

        print("🎨 空状态内容已创建并返回")

        canvas_with_arrows.children.append(
            html.Script("""
                console.log('🎨 ArchDash: 空状态提示已显示');
                console.log('✅ 如果您看到这条消息，说明空状态逻辑正常工作');
                console.log('📋 请检查页面是否显示了"计算图为空"和三个引导卡片');
            """)
        )

        return canvas_with_arrows

    print(f"🏗️ 渲染正常模式 - 有{len(graph.nodes)}个节点")
    for col in range(graph.layout_manager.cols):
        col_content = []
        col_nodes = graph.layout_manager.get_column_nodes(col)

        for node_id, row in sorted(col_nodes, key=lambda x: x[1]):
            node = graph.nodes.get(node_id)
            node_name = node.name if node else ""

            if not node:
                continue

            param_rows = []
            if hasattr(node, "parameters"):
                for param_idx, param in enumerate(node.parameters):
                    param_rows.append(
                        html.Tr([
                            html.Td(
                                html.Div([
                                    html.Div(
                                        className="param-pin param-pin-style",
                                        id=f"pin-{node_id}-{param_idx}"
                                    ),
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
                                        className="param-input param-name-input"
                                    )
                                ], className="param-row-container"),
                                className="param-name-cell"
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
                                            "width": f"calc(100% - {AppConstants.PARAM_INPUT_UNLINK_OFFSET}px)" if (param.calculation_func and param.dependencies and getattr(param, 'unlinked', False)) else "100%", 
                                            "background": "lightgreen" if f"{node_id}-{param_idx}" in graph.recently_updated_params else "transparent"
                                        },
                                        className="param-input param-value-input"
                                    ),
                                        html.Span(
                                            param.unit,
                                            className="param-unit"
                                        ) if param.unit else None
                                    ], className="param-value-container"),
                                    html.Div(
                                        "🔓",
                                        id={"type": "unlink-icon", "node": node_id, "index": param_idx},
                                        className="unlink-icon unlink-icon-style",
                                        title="重新连接 (点击恢复自动计算)"
                                    ) if (param.calculation_func and param.dependencies and getattr(param, 'unlinked', False)) else None
                                ], className="param-value-container"),
                                className="param-value-cell"
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
                                    direction="start"
                                ),
                                className="param-dropdown-cell"
                            )
                        ])
                    )

            param_table = html.Table(param_rows, className="param-table") if param_rows else None

            node_div = html.Div(
                [
                    html.Div([
                        html.Div([
                            html.Span(f"{node_name}", className="node-name")
                        ]),
                        html.Div([
                            html.Button(
                                html.Span("➕"),
                                id={"type": "add-param-header", "node": node_id},
                                className="btn add-param-btn",
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
                                label="",
                                size="sm",
                                direction="start"
                            )
                        ], className="node-header-controls")
                    ], className="node-header"),
                    param_table,
                    html.Div(id=f"node-content-{node_id}", className="node-content")
                ],
                className="p-2 node-container node-entrance fade-in",
                id=f"node-{node_id}",
                **{"data-row": row, "data-col": col, "data-dash-id": json.dumps({"type": "node", "index": node_id})}
            )
            col_content.append(node_div)

        # 计算列宽 - 优化布局，确保至少3列时有合理的宽度分布
        total_cols = max(AppConstants.MIN_LAYOUT_COLUMNS, graph.layout_manager.cols)  # 至少按最小列数计算宽度
        col_width = max(2, 12 // total_cols)  # 每列至少占2个Bootstrap列宽
        canvas_content.append(dbc.Col(col_content, width=col_width))

    arrows = create_arrows()

    canvas_with_arrows = html.Div([
        dbc.Row(canvas_content),
        html.Div(
            arrows,
            className="arrows-overlay",
            id="arrows-overlay"
        )
    ], className="relative-container")

    return canvas_with_arrows

def create_arrows():
    return [
        html.Div(
            id="arrows-overlay-dynamic",
            className="arrows-overlay-dynamic"
        )
    ]

app.layout = app_layout
app.index_string = app_index_string

# 新的节点操作回调函数 - 使用布局管理器
@callback(
    Output("node-data", "data"),
    Output("canvas-events", "data"),
    Output("app-messages", "data", allow_duplicate=True),
    Input({"type": "move-node-up", "node": ALL}, "n_clicks"),
    Input({"type": "move-node-down", "node": ALL}, "n_clicks"),
    Input({"type": "move-node-left", "node": ALL}, "n_clicks"),
    Input({"type": "move-node-right", "node": ALL}, "n_clicks"),
    Input({"type": "add-param", "node": ALL}, "n_clicks"),
    Input({"type": "add-param-header", "node": ALL}, "n_clicks"),
    Input({"type": "delete-node", "node": ALL}, "n_clicks"),
    State("node-data", "data"),
    State("canvas-events", "data"),
    State("app-messages", "data"),
    prevent_initial_call=True
)
def handle_node_operations(move_up_clicks, move_down_clicks, 
                          move_left_clicks, move_right_clicks, 
                          add_param_clicks, add_param_header_clicks, delete_node_clicks,
                          node_data, current_events, current_messages):
    try:
        if isinstance(ctx.triggered_id, dict):
            operation_type = ctx.triggered_id.get("type")
            node_id = ctx.triggered_id.get("node")

            trigger_value = ctx.triggered[0]["value"]
            if not trigger_value or trigger_value == 0:
                return dash.no_update, dash.no_update, dash.no_update

            if not node_id:
                canvas_event = create_canvas_event("error", {"message": "无效操作"})
                message = create_message("error", "无效操作", "error")
                return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)

            node = graph.nodes.get(node_id)
            if not node:
                canvas_event = create_canvas_event("error", {"message": "无效节点"})
                message = create_message("error", "无效节点", "error")
                return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)
            node_name = node.name

        if operation_type == "move-node-up":
            success = graph.layout_manager.move_node_up(node_id)
            result_message = f"节点 {node_name} 已上移" if success else f"节点 {node_name} 无法上移"
            # 节点移动后检查并自动删除空的最后一列，但保持至少3列
            if success:
                auto_remove_result = auto_remove_empty_last_column()
                if auto_remove_result:
                    result_message += f"，{auto_remove_result}"
            canvas_event = create_canvas_event("node_moved", {"node_id": node_id, "direction": operation_type})
            message = create_message("node_operation", result_message, "success" if "已" in result_message else "warning")
            return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)

        elif operation_type == "move-node-down":
            success = graph.layout_manager.move_node_down(node_id)
            result_message = f"节点 {node_name} 已下移" if success else f"节点 {node_name} 无法下移"
            # 节点移动后检查并自动删除空的最后一列，但保持至少3列
            if success:
                auto_remove_result = auto_remove_empty_last_column()
                if auto_remove_result:
                    result_message += f"，{auto_remove_result}"
            canvas_event = create_canvas_event("node_moved", {"node_id": node_id, "direction": operation_type})
            message = create_message("node_operation", result_message, "success" if "已" in result_message else "warning")
            return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)

        elif operation_type == "move-node-left":
            success = graph.layout_manager.move_node_left(node_id)
            result_message = f"节点 {node_name} 已左移" if success else f"节点 {node_name} 无法左移"
            # 节点移动后检查并自动删除空的最后一列，但保持至少3列
            if success:
                auto_remove_result = auto_remove_empty_last_column()
                if auto_remove_result:
                    result_message += f"，{auto_remove_result}"
            canvas_event = create_canvas_event("node_moved", {"node_id": node_id, "direction": operation_type})
            message = create_message("node_operation", result_message, "success" if "已" in result_message else "warning")
            return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)

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
            canvas_event = create_canvas_event("node_moved", {"node_id": node_id, "direction": operation_type})
            message = create_message("node_operation", result_message, "success" if "已" in result_message else "warning")
            return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)

        elif operation_type == "add-param":
            param = Parameter(
                name="new_param", 
                value=AppConstants.DEFAULT_PARAMETER_VALUE, 
                unit="", 
                description=f"新参数", 
                param_type="float"
            )

            # 添加参数到节点
            graph.add_parameter_to_node(node_id, param)

            canvas_event = create_canvas_event("param_added", {"node_id": node_id})
            message = create_message("param_operation", f"参数已添加到节点 {node_name}", "success")
            return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)

        elif operation_type == "add-param-header":
            # 标题栏加号按钮：添加参数功能，与下拉菜单中的"添加参数"功能相同
            param = Parameter(
                name="new_param", 
                value=AppConstants.DEFAULT_PARAMETER_VALUE, 
                unit="", 
                description=f"新参数", 
                param_type="float"
            )

            # 添加参数到节点
            graph.add_parameter_to_node(node_id, param)

            canvas_event = create_canvas_event("param_added", {"node_id": node_id})
            message = create_message("param_operation", f"参数已添加到节点 {node_name}", "success")
            return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)

        elif operation_type == "delete-node":
            # 检查节点的参数是否被其他参数依赖
            has_dependents, dependent_info = check_node_has_dependents(node_id, graph)

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

                canvas_event = create_canvas_event("error", {"message": error_message})
                message = create_message("error", error_message, "error")
                return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)

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

            canvas_event = create_canvas_event("node_moved", {"node_id": node_id, "direction": operation_type})
            message = create_message("node_operation", result_message, "success" if "已" in result_message else "warning")
            return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)

        return dash.no_update, dash.no_update, dash.no_update
    
    except Exception as e:
        print(f"Error in handle_node_operations: {e}")
        canvas_event = create_canvas_event("error", {"message": f"操作出错: {str(e)}"})
        message = create_message("error", f"❌ 操作出错: {str(e)}", "error")
        return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)


# 添加参数更新回调 - 使用debounce确保只在输入完成后更新
@callback(
    Output("node-data", "data", allow_duplicate=True),
    Output("canvas-events", "data", allow_duplicate=True),
    Output("app-messages", "data", allow_duplicate=True),
    Input({"type": "param-name", "node": ALL, "index": ALL}, "value"),
    Input({"type": "param-value", "node": ALL, "index": ALL}, "value"),
    State("node-data", "data"),
    State("canvas-events", "data"),
    State("app-messages", "data"),
    prevent_initial_call=True
)
def update_parameter(param_names, param_values, node_data, current_events, current_messages):
    if not ctx.triggered_id:
        return node_data, dash.no_update, dash.no_update

    triggered_id = ctx.triggered_id
    if isinstance(triggered_id, dict):
        node_id = triggered_id["node"]
        param_index = triggered_id["index"]
        param_type = triggered_id["type"]

        # 直接从ctx.triggered获取新值（debounce确保只在输入完成后触发）
        new_value = ctx.triggered[0]["value"]

        print(f"🔍 调试：参数更新 - 节点:{node_id}, 索引:{param_index}, 类型:{param_type}, 获取值:{new_value}")

        if new_value is None or new_value == "":
            print(f"⚠️ 警告：未能获取到有效值，跳过更新")
            return node_data, dash.no_update, dash.no_update

        node = graph.nodes.get(node_id)
        if not node:
            return node_data, dash.no_update, dash.no_update

        if param_index >= len(node.parameters):
            return node_data, dash.no_update, dash.no_update

        current_param = node.parameters[param_index]

        update_message = ""
        should_update_canvas = False

        if param_type == "param-name":
            if new_value != current_param.name:
                print(f"🔄 参数名更新: {current_param.name} → {new_value}")
                current_param.name = new_value
                should_update_canvas = True
                update_message = f"参数名已更新为: {new_value}"
            else:
                print(f"📌 参数名无变化，跳过更新: {new_value}")
                return node_data, dash.no_update, dash.no_update
        elif param_type == "param-value":
            if not hasattr(current_param, 'param_type'):
                print(f"❌ 参数 {current_param.name} 缺少类型信息")
                message = create_message("error", f"❌ 参数 '{current_param.name}' 缺少类型信息，无法更新", "error")
                return node_data, dash.no_update, add_app_message(current_messages, message)

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
                        message = create_message("error", f"❌ 不支持的参数类型: {param_data_type}", "error")
                        return node_data, dash.no_update, add_app_message(current_messages, message)
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
                    canvas_event = create_canvas_event("param_error", {"message": f"参数值转换失败: {new_value}"})
                    message = create_message("error", f"❌ 参数值 '{new_value}' 无法转换为 {param_data_type} 类型", "error")
                    return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)

            # 检查参数值是否真的有变化
            if new_value == current_param.value:
                print(f"📌 参数值无变化，跳过更新: {current_param.name} = {new_value}")
                return node_data, dash.no_update, dash.no_update

            print(f"🔄 参数值更新: {current_param.name}: {current_param.value} → {new_value}")

            # 无论是否有计算函数，都要触发级联更新
            graph.recently_updated_params.clear()
            
            if current_param.calculation_func and current_param.dependencies:
                # 对于有计算函数的参数，先手动设置值，然后触发级联更新
                current_param.set_manual_value(new_value)
                # 手动触发级联更新到依赖这个参数的其他参数
                cascaded_updates = graph.propagate_updates(current_param)
                update_result = {
                    'primary_change': {'param': current_param, 'old_value': current_param.value, 'new_value': new_value},
                    'cascaded_updates': cascaded_updates,
                    'total_updated_params': 1 + len(cascaded_updates)
                }
                update_message = f"🔓 参数 {current_param.name} 已手动设置为 {new_value}（已断开自动计算）"
            else:
                # 对于普通参数，使用标准的级联更新流程
                update_result = graph.set_parameter_value(current_param, new_value)
                update_message = f"🔄 参数 {current_param.name} 已更新为 {new_value}"

            should_update_canvas = True
            graph.recently_updated_params.add(f"{node_id}-{param_index}")

            # 处理级联更新
            for update_info in update_result.get('cascaded_updates', []):
                updated_param = update_info['param']
                for check_node_id, check_node in graph.nodes.items():
                    for check_idx, check_param in enumerate(check_node.parameters):
                        if check_param is updated_param:
                            graph.recently_updated_params.add(f"{check_node_id}-{check_idx}")
                            break

            # 添加级联更新信息到消息
            cascaded_info = ""
            if update_result.get('cascaded_updates'):
                affected_params = [f"{update['param'].name}({update['old_value']}→{update['new_value']})" 
                                 for update in update_result['cascaded_updates']]
                cascaded_info = f"，同时更新了 {len(affected_params)} 个关联参数: {', '.join(affected_params)}"

            update_message += cascaded_info

        if should_update_canvas:
            canvas_event = create_canvas_event("param_updated", {"node_id": node_id, "param_index": param_index, "new_value": new_value})
            message = create_message("param_update", update_message, "success")
            return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)
        else:
            message = create_message("param_update", update_message, "success")
            return node_data, current_events, add_app_message(current_messages, message)

    return node_data, dash.no_update, dash.no_update

# 添加参数操作回调 - 完全独立于节点菜单
@callback(
    Output("node-data", "data", allow_duplicate=True),
    Output("canvas-events", "data", allow_duplicate=True),
    Output("app-messages", "data", allow_duplicate=True),
    Input({"type": "delete-param", "node": ALL, "index": ALL}, "n_clicks"),
    Input({"type": "move-param-up", "node": ALL, "index": ALL}, "n_clicks"),
    Input({"type": "move-param-down", "node": ALL, "index": ALL}, "n_clicks"),
    State("node-data", "data"),
    State("canvas-events", "data"),
    State("app-messages", "data"),
    prevent_initial_call=True
)
def handle_parameter_operations(delete_clicks, move_up_clicks, move_down_clicks, node_data, current_events, current_messages):
    ctx = dash.callback_context  # 获取回调上下文
    if not ctx.triggered_id:
        canvas_event = create_canvas_event("no_trigger", {})
        return node_data, add_canvas_event(current_events, canvas_event), dash.no_update

    triggered_id = ctx.triggered_id
    if not isinstance(triggered_id, dict):
        canvas_event = create_canvas_event("invalid_trigger", {})
        return node_data, add_canvas_event(current_events, canvas_event), dash.no_update

    node_id = triggered_id.get("node")
    param_index = triggered_id.get("index")
    operation_type = triggered_id.get("type")

    trigger_value = ctx.triggered[0]["value"]
    if not trigger_value or trigger_value == 0:
        canvas_event = create_canvas_event("no_value", {})
        return node_data, add_canvas_event(current_events, canvas_event), dash.no_update

    if not node_id or param_index is None:
        canvas_event = create_canvas_event("invalid_params", {})
        return node_data, add_canvas_event(current_events, canvas_event), dash.no_update

    node = graph.nodes.get(node_id)
    if not node:
        canvas_event = create_canvas_event("invalid_node", {})
        return node_data, add_canvas_event(current_events, canvas_event), dash.no_update

    if param_index >= len(node.parameters):
        canvas_event = create_canvas_event("invalid_param_index", {})
        return node_data, add_canvas_event(current_events, canvas_event), dash.no_update

    node_name = node.name
    param_name = node.parameters[param_index].name

    if operation_type == "delete-param":
        param_to_delete = node.parameters[param_index]
        has_dependents, dependent_list = check_parameter_has_dependents(param_to_delete, graph)

        if has_dependents:
            # 构建依赖信息的错误消息
            dependent_info = []
            for dep in dependent_list:
                dependent_info.append(f"{dep['node_name']}.{dep['param_name']}")

            error_message = f"❌ 无法删除参数 {node_name}.{param_name}，因为以下参数依赖于它：\n{', '.join(dependent_info)}"
            canvas_event = create_canvas_event("delete_param_error", {"node_id": node_id, "param_index": param_index, "error": error_message})
            message = create_message("error", error_message, "error")
            return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)

        deleted_param = node.parameters.pop(param_index)
        success_message = f"✅ 参数 {node_name}.{param_name} 已删除"
        canvas_event = create_canvas_event("param_deleted", {"node_id": node_id, "param_index": param_index})
        message = create_message("param_operation", success_message, "success")
        return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)

    elif operation_type == "move-param-up":
        if param_index > 0:
            node.parameters[param_index], node.parameters[param_index - 1] = \
                node.parameters[param_index - 1], node.parameters[param_index]
            success_message = f"✅ 参数 {node_name}.{param_name} 已上移"
            canvas_event = create_canvas_event("param_moved", {"node_id": node_id, "param_index": param_index, "operation": operation_type})
            message = create_message("param_operation", success_message, "success")
            return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)
        else:
            error_message = f"⚠️ 参数 {node_name}.{param_name} 已在最顶端，无法上移"
            canvas_event = create_canvas_event("param_move_error", {"node_id": node_id, "param_index": param_index, "operation": operation_type})
            message = create_message("warning", error_message, "warning")
            return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)

    elif operation_type == "move-param-down":
        if param_index < len(node.parameters) - 1:
            node.parameters[param_index], node.parameters[param_index + 1] = \
                node.parameters[param_index + 1], node.parameters[param_index]
            success_message = f"✅ 参数 {node_name}.{param_name} 已下移"
            canvas_event = create_canvas_event("param_moved", {"node_id": node_id, "param_index": param_index, "operation": operation_type})
            message = create_message("param_operation", success_message, "success")
            return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)
        else:
            error_message = f"⚠️ 参数 {node_name}.{param_name} 已在最底端，无法下移"
            canvas_event = create_canvas_event("param_move_error", {"node_id": node_id, "param_index": param_index, "operation": operation_type})
            message = create_message("warning", error_message, "warning")
            return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)

    # 默认情况（不应该到达这里）
    canvas_event = create_canvas_event("param_operation_unknown", {"node_id": node_id, "param_index": param_index, "operation": operation_type})
    return node_data, add_canvas_event(current_events, canvas_event), dash.no_update

# 处理unlink图标点击的回调函数
@callback(
    Output("node-data", "data", allow_duplicate=True),
    Output("canvas-events", "data", allow_duplicate=True),
    Output("app-messages", "data", allow_duplicate=True),
    Input({"type": "unlink-icon", "node": ALL, "index": ALL}, "n_clicks"),
    State("node-data", "data"),
    State("canvas-events", "data"),
    State("app-messages", "data"),
    prevent_initial_call=True
)
def handle_unlink_toggle(unlink_clicks, node_data, current_events, current_messages):
    """处理unlink图标点击，重新连接参数并计算"""
    if not ctx.triggered_id:
        return node_data, current_events, dash.no_update

    triggered_id = ctx.triggered_id
    if not isinstance(triggered_id, dict):
        return node_data, current_events, dash.no_update

    node_id = triggered_id.get("node")
    param_index = triggered_id.get("index")

    trigger_value = ctx.triggered[0]["value"]
    if not trigger_value or trigger_value == 0:
        return node_data, current_events, dash.no_update

    if not node_id or param_index is None:
        return node_data, current_events, dash.no_update

    node = graph.nodes.get(node_id)
    if not node or param_index >= len(node.parameters):
        return node_data, current_events, dash.no_update

    param = node.parameters[param_index]
    node_name = node.name

    if not param.calculation_func or not param.dependencies:
        message = create_message("warning", f"⚠️ 参数 {node_name}.{param.name} 无计算依赖", "warning")
        return node_data, current_events, add_app_message(current_messages, message)

    try:
        new_value = param.relink_and_calculate()
        result_message = f"🔗 参数 {node_name}.{param.name} 已重新连接并计算，新值: {new_value}"
        canvas_event = create_canvas_event("param_relinked", {"node_id": node_id, "param_index": param_index, "new_value": new_value})
        message = create_message("param_relink", result_message, "success")
        return node_data, add_canvas_event(current_events, canvas_event), add_app_message(current_messages, message)

    except Exception as e:
        message = create_message("error", f"❌ 重新连接失败: {str(e)}", "error")
        return node_data, current_events, add_app_message(current_messages, message)

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

    trigger_value = ctx.triggered[0]["value"]
    if not trigger_value or trigger_value == 0:
        raise dash.exceptions.PreventUpdate

    triggered_id = ctx.triggered_id
    if isinstance(triggered_id, dict) and triggered_id["type"] == "edit-param":
        node_id = triggered_id["node"]
        param_index = triggered_id["index"]

        if node_id not in graph.nodes:
            raise dash.exceptions.PreventUpdate

        node = graph.nodes[node_id]
        if param_index >= len(node.parameters):
            raise dash.exceptions.PreventUpdate

        param = node.parameters[param_index]
        node_name = node.name

        available_params = get_all_available_parameters(node_id, param.name)

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
    try:
        if cancel_clicks:
            return False
        raise dash.exceptions.PreventUpdate
    except Exception as e:
        print(f"Error in close_param_edit_modal: {e}")
        return False  # 确保模态框关闭

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
    try:
        if not reset_clicks:
            raise dash.exceptions.PreventUpdate

        selected_dependencies = []
        if checkbox_values and checkbox_ids:
            for value, checkbox_id in zip(checkbox_values, checkbox_ids):
                if value:  # 如果复选框被选中
                    param_name = checkbox_id["param"]
                    selected_dependencies.append({"param_name": param_name.split(".")[-1]})

        # 生成代码模板
        template_code = generate_code_template(selected_dependencies)
        return template_code
    except Exception as e:
        print(f"Error in reset_calculation_code: {e}")
        return "# 生成代码模板时出错"

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
        selected_deps = []
        if checkbox_values and checkbox_ids:
            for value, checkbox_id in zip(checkbox_values, checkbox_ids):
                if value:  # 如果复选框被选中
                    param_display_name = checkbox_id["param"]
                    node_id = edit_data["node_id"]
                    available_params = get_all_available_parameters(node_id, "")
                    for param_info in available_params:
                        if param_info["display_name"] == param_display_name:
                            selected_deps.append(param_info["param_obj"])
                            break

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
            traceback_info = current_param._calculation_traceback or str(e)
            return html.Div([
                html.P(f"计算错误: {str(e)}", className="mb-1"),
                html.Details([
                    html.Summary("查看详细回溯"),
                    html.Pre(traceback_info, className="code-display")
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
                html.Pre(full_traceback, className="code-display")
            ])
        ]), "danger"

@callback(
    Output("param-edit-modal", "is_open", allow_duplicate=True),
    Output("canvas-container", "children", allow_duplicate=True),
    Output("app-messages", "data", allow_duplicate=True),
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
    State("app-messages", "data"),
    prevent_initial_call=True
)
def save_parameter_changes(save_clicks, param_name, param_type, param_unit, param_description, 
                          calculation_code, checkbox_values, checkbox_ids, 
                          edit_data, node_data, current_messages):
    if not save_clicks:
        raise dash.exceptions.PreventUpdate

    try:
        # 验证输入
        if not param_name or not param_name.strip():
            error_msg = create_message("param_save_error", "参数名称不能为空", "error")
            return True, dash.no_update, add_app_message(current_messages, error_msg)

        node_id = edit_data["node_id"]
        param_index = edit_data["param_index"]

        if node_id not in graph.nodes:
            error_msg = create_message("param_save_error", "节点不存在", "error")
            return True, dash.no_update, add_app_message(current_messages, error_msg)

        node = graph.nodes[node_id]
        if param_index >= len(node.parameters):
            error_msg = create_message("param_save_error", "参数不存在", "error")
            return True, dash.no_update, add_app_message(current_messages, error_msg)

        param = node.parameters[param_index]

        selected_deps = []
        if checkbox_values and checkbox_ids:
            for value, checkbox_id in zip(checkbox_values, checkbox_ids):
                if value:  # 如果复选框被选中
                    param_display_name = checkbox_id["param"]
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
                error_msg = create_message("param_save_error", f"添加依赖 {dep_param.name} 会造成循环依赖", "error")
                return True, dash.no_update, add_app_message(current_messages, error_msg)

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
        
        success_message = create_message("param_save_success", success_msg, "success")
        return False, updated_canvas, add_app_message(current_messages, success_message)

    except Exception as e:
        error_msg = create_message("param_save_error", f"保存失败: {str(e)}", "error")
        return True, dash.no_update, add_app_message(current_messages, error_msg)

# 高亮功能简化：保持永久高亮，无需定时清除

@callback(
    Output("download-graph", "data"),
    Output("app-messages", "data", allow_duplicate=True),
    Input("save-graph-button", "n_clicks"),
    State("app-messages", "data"),
    prevent_initial_call=True
)
def save_calculation_graph(n_clicks, current_messages):
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
        success_msg = create_message("save_graph_success", f"计算图已保存为 {filename}", "success")
        return dict(
            content=json_str,
            filename=filename,
            type="application/json"
        ), add_app_message(current_messages, success_msg)

    except Exception as e:
        error_msg = create_message("save_graph_error", f"保存失败: {str(e)}", "error")
        return dash.no_update, add_app_message(current_messages, error_msg)

# 加载示例计算图
@app.callback(
    Output("canvas-container", "children", allow_duplicate=True),
    Output("app-messages", "data", allow_duplicate=True),
    Input("load-example-graph-button", "n_clicks"),
    State("app-messages", "data"),
    prevent_initial_call=True
)
def load_example_soc_graph_callback(n_clicks, current_messages):
    """加载多核SoC示例计算图的回调函数"""
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    try:
        # 创建示例计算图
        result = create_example_soc_graph()

        # 更新画布显示
        updated_canvas = update_canvas()

        success_message = (
            f"已加载多核SoC示例计算图："
            f"{result['nodes_created']}个节点，"
            f"{result['total_params']}个参数，"
            f"其中{result['calculated_params']}个计算参数"
        )
        
        success_msg = create_message("load_example_success", success_message, "success")
        return updated_canvas, add_app_message(current_messages, success_msg)

    except Exception as e:
        error_msg = create_message("load_example_error", f"加载示例失败: {str(e)}", "error")
        return dash.no_update, add_app_message(current_messages, error_msg)

# 加载计算图
@app.callback(
    Output("canvas-container", "children", allow_duplicate=True),
    Output("app-messages", "data", allow_duplicate=True),
    Input("upload-graph", "contents"),
    State("upload-graph", "filename"),
    State("app-messages", "data"),
    prevent_initial_call=True
)
def load_calculation_graph(contents, filename, current_messages):
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
            error_msg = create_message("upload_graph_error", f"文件格式错误: {str(e)}", "error")
            return dash.no_update, add_app_message(current_messages, error_msg)

        # 验证数据格式
        if "nodes" not in data:
            error_msg = create_message("upload_graph_error", "无效的计算图文件格式", "error")
            return dash.no_update, add_app_message(current_messages, error_msg)

        # 清空现有数据
        # 创建新的布局管理器并重新构建计算图
        new_layout = CanvasLayoutManager(
            initial_cols=AppConstants.MIN_LAYOUT_COLUMNS, 
            initial_rows=AppConstants.DEFAULT_INITIAL_ROWS
        )
        new_graph = CalculationGraph.from_dict(data, new_layout)

        # 写入当前 session
        set_graph(new_graph)
        graph = get_graph()

        # 更新画布显示
        updated_canvas = update_canvas()

        loaded_nodes = len(new_graph.nodes)
        total_params = sum(len(node.parameters) for node in new_graph.nodes.values())

        success_message = f"成功加载计算图 '{filename}'：{loaded_nodes}个节点，{total_params}个参数"
        success_msg = create_message("upload_graph_success", success_message, "success")
        return updated_canvas, add_app_message(current_messages, success_msg)

    except Exception as e:
        error_msg = create_message("upload_graph_error", f"加载失败: {str(e)}", "error")
        return dash.no_update, add_app_message(current_messages, error_msg)

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


# Pin悬停箭头显示系统已移动到 clientside_callbacks.py

# =============== 绘图相关回调函数 ===============


# 初始化空图表
@callback(
    Output("sensitivity-plot", "figure"),
    Input("canvas-container", "id"),  # 使用canvas容器ID作为触发器
    prevent_initial_call=False
)
def initialize_plot(container_id):
    """初始化空图表"""
    return create_empty_plot()

# 生成敏感性分析图表
@callback(
    Output("sensitivity-plot", "figure", allow_duplicate=True),
    Output("app-messages", "data", allow_duplicate=True),
    Output("cumulative-plot-data", "data", allow_duplicate=True),
    Input("generate-plot-btn", "n_clicks"),
    State("selected-x-param", "data"),
    State("selected-y-param", "data"),
    State("x-start-value", "value"),
    State("x-end-value", "value"),
    State("x-step-value", "value"),
    State("cumulative-plot-checkbox", "value"),
    State("cumulative-plot-data", "data"),
    State("series-name-input", "value"),
    State("app-messages", "data"),
    prevent_initial_call=True
)
def generate_sensitivity_plot(n_clicks, x_param, y_param, x_start, x_end, x_step, cumulative_checkbox, cumulative_data, series_name, current_messages):
    """生成参数敏感性分析图表"""
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    if not x_param or not y_param:
        error_msg = create_message("plot_error", "请选择X轴和Y轴参数", "warning")
        return create_empty_plot(), add_app_message(current_messages, error_msg), cumulative_data

    if x_param == y_param:
        error_msg = create_message("plot_error", "X轴和Y轴参数不能相同", "warning")
        return create_empty_plot(), add_app_message(current_messages, error_msg), cumulative_data

    # 验证输入值
    try:
        x_start = float(x_start) if x_start is not None else 0
        x_end = float(x_end) if x_end is not None else 100
        x_step = float(x_step) if x_step is not None else 1

        if x_step <= 0:
            error_msg = create_message("plot_error", "步长必须大于0", "warning")
            return create_empty_plot(), add_app_message(current_messages, error_msg), cumulative_data

        if x_start >= x_end:
            error_msg = create_message("plot_error", "起始值必须小于结束值", "warning")
            return create_empty_plot(), add_app_message(current_messages, error_msg), cumulative_data

    except (ValueError, TypeError):
        error_msg = create_message("plot_error", "请输入有效的数值", "warning")
        return create_empty_plot(), add_app_message(current_messages, error_msg), cumulative_data

    # 从参数值中解析节点ID和参数名
    try:
        x_node_id, x_param_name = x_param.split('|')
        y_node_id, y_param_name = y_param.split('|')
    except ValueError:
        error_msg = create_message("plot_error", "参数格式错误，请重新选择", "warning")
        return create_empty_plot(), add_app_message(current_messages, error_msg), cumulative_data

    # 从graph中获取节点和参数对象
    x_node = graph.nodes.get(x_node_id)
    y_node = graph.nodes.get(y_node_id)

    if not x_node or not y_node:
        error_msg = create_message("plot_error", "参数所属节点不存在，请重新选择", "warning")
        return create_empty_plot(), add_app_message(current_messages, error_msg), cumulative_data

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
        error_msg = create_message("plot_error", result['message'], "error")
        return create_empty_plot(), add_app_message(current_messages, error_msg), cumulative_data

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
        margin=dict(
            l=AppConstants.CHART_MARGIN_LEFT, 
            r=AppConstants.CHART_MARGIN_RIGHT, 
            t=AppConstants.CHART_MARGIN_TOP, 
            b=AppConstants.CHART_MARGIN_BOTTOM
        ),
        height=AppConstants.CHART_DEFAULT_HEIGHT,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        annotations=[
            dict(
                text="powered by ArchDash",
                xref="paper",
                yref="paper",
                x=1.0,
                y=0.02,
                xanchor="right",
                yanchor="bottom",
                showarrow=False,
                font=dict(
                    family="Arial",
                    size=10,
                    color="rgba(150, 150, 150, 0.7)"
                )
            )
        ]
    )

    # 添加网格线和样式优化
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.3)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.3)')

    message = result['message']
    if is_cumulative:
        message += f" (累计: {len(new_cumulative_data)} 条曲线)"
    
    success_msg = create_message("plot_success", message, "success")
    return fig, add_app_message(current_messages, success_msg), new_cumulative_data

# 清除图表
@callback(
    Output("sensitivity-plot", "figure", allow_duplicate=True),
    Output("selected-x-param", "data", allow_duplicate=True),
    Output("selected-y-param", "data", allow_duplicate=True),
    Output("x-param-display", "value", allow_duplicate=True),
    Output("y-param-display", "value", allow_duplicate=True),
    Output("cumulative-plot-data", "data", allow_duplicate=True),
    Input("clear-plot-btn", "n_clicks"),
    prevent_initial_call=True
)
def clear_plot(n_clicks):
    """清除图表、选择器和累计数据"""
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    return create_empty_plot(), None, None, "", "", []

# 导出绘图数据
@callback(
    Output("download-plot-data", "data"),
    Input("export-plot-data-btn", "n_clicks"),
    State("sensitivity-plot", "figure"),
    State("selected-x-param", "data"),
    State("selected-y-param", "data"),
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
    Input("selected-y-param", "data"),
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
    Input("selected-x-param", "data"),
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

        start_value = max(AppConstants.SENSITIVITY_DEFAULT_START, current_value * AppConstants.SENSITIVITY_START_MULTIPLIER)
        end_value = current_value * AppConstants.SENSITIVITY_END_MULTIPLIER

        # 如果当前值为0，设置默认范围
        if current_value == 0:
            start_value = AppConstants.SENSITIVITY_DEFAULT_START
            end_value = AppConstants.SENSITIVITY_DEFAULT_END

        return start_value, end_value

    except (ValueError, TypeError):
        # 如果转换失败，返回默认值
        return AppConstants.SENSITIVITY_DEFAULT_START, AppConstants.SENSITIVITY_DEFAULT_END

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
            confidence_color = "success" if param_info['param_confidence'] >= AppConstants.CONFIDENCE_HIGH_THRESHOLD else "warning" if param_info['param_confidence'] >= AppConstants.CONFIDENCE_MEDIUM_THRESHOLD else "danger"
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
                                   className="code-block")
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
                html.Div(param_card_items, className="border-start border-4 border-primary ps-3 mb-4 param-card-container")
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



# 手动刷新依赖关系显示
@callback(
    Output("dependencies-display", "children", allow_duplicate=True),
    Input("refresh-dependencies-btn", "n_clicks"),
    prevent_initial_call=True
)
def refresh_dependencies_display(n_clicks):
    """手动刷新依赖关系显示面板"""
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    try:
        dependencies_info = get_all_parameter_dependencies()

        # 刷新依赖关系显示
        deps_display = format_dependencies_display(dependencies_info)

        return deps_display

    except Exception as e:
        error_alert = [
            dbc.Alert([
                html.H6("⚠️ 刷新失败", className="mb-2"),
                html.P(f"错误信息: {str(e)}", className="mb-0")
            ], color="danger")
        ]
        return error_alert

# 当节点/参数发生变化时自动更新依赖关系显示
@callback(
    Output("dependencies-display", "children", allow_duplicate=True),
    Input("node-data", "data"),
    prevent_initial_call=True
)
def auto_update_dependencies_display_on_change(node_data):
    """当节点或参数发生变化时自动更新依赖关系显示"""
    try:
        dependencies_info = get_all_parameter_dependencies()

        # 更新依赖关系显示
        deps_display = format_dependencies_display(dependencies_info)

        return deps_display

    except Exception as e:
        error_alert = [
            dbc.Alert([
                html.H6("⚠️ 自动更新失败", className="mb-2"),
                html.P(f"错误信息: {str(e)}", className="mb-0")
            ], color="warning")
        ]
        return error_alert

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

# 下拉菜单z-index管理已移动到 clientside_callbacks.py

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

# 主题切换回调已移动到 clientside_callbacks.py

# 页面加载时恢复主题设置已移动到 clientside_callbacks.py

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

    trigger_value = ctx.triggered[0]["value"]
    if not trigger_value or trigger_value == 0:
        raise dash.exceptions.PreventUpdate

    triggered_id = ctx.triggered_id
    if isinstance(triggered_id, dict) and triggered_id["type"] == "edit-node":
        node_id = triggered_id["node"]

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

@callback(
    Output("node-edit-modal", "is_open", allow_duplicate=True),
    Output("canvas-container", "children", allow_duplicate=True),
    Output("app-messages", "data", allow_duplicate=True),
    Input("node-edit-save", "n_clicks"),
    State("node-edit-name", "value"),
    State("node-edit-description", "value"),
    State("node-edit-data", "data"),
    State("app-messages", "data"),
    prevent_initial_call=True
)
def save_node_changes(save_clicks, node_name, node_description, edit_data, current_messages):
    if not save_clicks:
        raise dash.exceptions.PreventUpdate

    try:
        # 验证输入
        if not node_name or not node_name.strip():
            error_msg = create_message("node_save_error", "节点名称不能为空", "error")
            return True, dash.no_update, add_app_message(current_messages, error_msg)

        node_id = edit_data["node_id"]

        if node_id not in graph.nodes:
            error_msg = create_message("node_save_error", "节点不存在", "error")
            return True, dash.no_update, add_app_message(current_messages, error_msg)

        node = graph.nodes[node_id]
        old_name = node.name

        # 检查节点名称是否与其他节点重复（排除当前节点）
        for other_node_id, other_node in graph.nodes.items():
            if other_node_id != node_id and other_node.name == node_name.strip():
                error_msg = create_message("node_save_error", f"节点名称 '{node_name.strip()}' 已存在，请使用不同的名称", "error")
                return True, dash.no_update, add_app_message(current_messages, error_msg)

        # 更新节点信息
        node.name = node_name.strip()
        node.description = node_description or ""

        # 关闭模态窗口并更新界面
        success_message = f"节点 '{old_name}' 已更新为 '{node.name}'"
        success_msg = create_message("node_save_success", success_message, "success")
        return False, update_canvas(), add_app_message(current_messages, success_msg)

    except Exception as e:
        error_msg = create_message("node_save_error", f"错误: {str(e)}", "error")
        return True, dash.no_update, add_app_message(current_messages, error_msg)

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
    Output("app-messages", "data", allow_duplicate=True),
    Input("node-add-save", "n_clicks"),
    State("node-add-name", "value"),
    State("node-add-description", "value"),
    State("app-messages", "data"),
    prevent_initial_call=True
)
def create_new_node(save_clicks, node_name, node_description, current_messages):
    if not save_clicks:
        raise dash.exceptions.PreventUpdate

    try:
        # 验证输入
        if not node_name or not node_name.strip():
            error_msg = create_message("node_create_error", "节点名称不能为空", "error")
            return True, dash.no_update, add_app_message(current_messages, error_msg)

        node_name = node_name.strip()

        # 检查节点名称是否与其他节点重复
        for existing_node in graph.nodes.values():
            if existing_node.name == node_name:
                error_msg = create_message("node_create_error", f"节点名称 '{node_name}' 已存在，请使用不同的名称", "error")
                return True, dash.no_update, add_app_message(current_messages, error_msg)

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
        success_msg = create_message("node_create_success", success_message, "success")
        return False, update_canvas(), add_app_message(current_messages, success_msg)

    except Exception as e:
        error_msg = create_message("node_create_error", f"错误: {str(e)}", "error")
        return True, dash.no_update, add_app_message(current_messages, error_msg)

# 列管理回调函数
@callback(
    Output("canvas-container", "children", allow_duplicate=True),
    Output("app-messages", "data", allow_duplicate=True),
    Output("remove-column-btn", "disabled"),
    Input("add-column-btn", "n_clicks"),
    Input("remove-column-btn", "n_clicks"),
    State("canvas-container", "children"),  # 添加状态以获取当前列信息
    State("app-messages", "data"),
    prevent_initial_call=True
)
def handle_column_management(add_clicks, remove_clicks, canvas_children, current_messages):
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
            error_msg = create_message("column_add_error", add_msg, "error")
            return dash.no_update, add_app_message(current_messages, error_msg), not can_remove

        graph.layout_manager.add_column()
        success_msg = create_message("column_add_success", f"已添加新列 (当前 {graph.layout_manager.cols} 列)", "success")
        return update_canvas(), add_app_message(current_messages, success_msg), False

    if button_id == "remove-column-btn" and remove_clicks:
        if not can_remove:
            error_msg = create_message("column_remove_error", remove_msg, "error")
            return dash.no_update, add_app_message(current_messages, error_msg), True

        success = graph.layout_manager.remove_column()
        if success:
            msg = f"已删除最后一列 (当前 {graph.layout_manager.cols} 列)"
            msg_obj = create_message("column_remove_success", msg, "success")
        else:
            msg = "无法删除最后一列，可能不为空"
            msg_obj = create_message("column_remove_error", msg, "error")

        # 再次检查是否还能继续删除
        can_remove_after, _ = graph.layout_manager.can_remove_column()
        return update_canvas(), add_app_message(current_messages, msg_obj), not can_remove_after

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
def check_parameter_has_dependents(param_obj, graph_instance, exclude_same_node=False):
    """检查参数是否被其他参数依赖

    Args:
        param_obj: 要检查的参数对象
        graph_instance: 要在其中检查的 CalculationGraph 实例
        exclude_same_node: 是否排除同一节点内的依赖关系

    Returns:
        tuple: (has_dependents: bool, dependent_list: list)
            has_dependents: 是否有其他参数依赖此参数
            dependent_list: 依赖此参数的参数列表，格式为[{"node_name": str, "param_name": str, "param_obj": Parameter}, ...]
    """
    dependent_list = []
    
    # 找到被检查参数所在的节点ID（如果需要排除同节点依赖）
    param_node_id = None
    if exclude_same_node:
        for node_id, node in graph_instance.nodes.items():
            if param_obj in node.parameters:
                param_node_id = node_id
                break

    # 遍历所有节点和参数，查找依赖关系
    for node_id, node in graph_instance.nodes.items():
        node_name = node.name

        for param in node.parameters:
            if param_obj in param.dependencies:
                # 如果需要排除同节点依赖且当前参数与被检查参数在同一节点，则跳过
                if exclude_same_node and node_id == param_node_id:
                    continue
                    
                dependent_list.append({
                    "node_name": node_name,
                    "param_name": param.name,
                    "param_obj": param
                })

    return len(dependent_list) > 0, dependent_list

def check_node_has_dependents(node_id, graph_instance):
    """检查节点的所有参数是否被其他节点的参数依赖

    Args:
        node_id: 要检查的节点ID
        graph_instance: 要在其中检查的 CalculationGraph 实例

    Returns:
        tuple: (has_dependents: bool, dependent_info: dict)
            has_dependents: 是否有其他节点的参数依赖此节点的参数
            dependent_info: 依赖信息字典，格式为 {
                "dependent_params": [{"node_name": str, "param_name": str, "depends_on": str}, ...],
                "affected_node_params": [str, ...]  # 本节点中被其他节点依赖的参数名列表
            }
    """
    if node_id not in graph_instance.nodes:
        return False, {"dependent_params": [], "affected_node_params": []}

    node = graph_instance.nodes[node_id]
    dependent_params = []
    affected_node_params = []

    # 检查该节点的每个参数是否被其他节点的参数依赖（排除同节点内的依赖）
    for param in node.parameters:
        has_deps, dep_list = check_parameter_has_dependents(param, graph_instance, exclude_same_node=True)
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
    Output("app-messages", "data", allow_duplicate=True),
    Input("clear-graph-btn", "n_clicks"),
    State("app-messages", "data"),
    prevent_initial_call=True
)
def clear_calculation_graph(n_clicks, current_messages):
    """清空当前的计算图，重置为空白状态"""
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    try:
        # 清空全局数据模型
        # 重新创建空的计算图和布局管理器
        new_graph = CalculationGraph()
        new_graph.set_layout_manager(CanvasLayoutManager(
            initial_cols=AppConstants.MIN_LAYOUT_COLUMNS, 
            initial_rows=AppConstants.DEFAULT_INITIAL_ROWS
        ))
        set_graph(new_graph)
        graph = get_graph()

        # 清空最近更新的参数集合
        graph.recently_updated_params.clear()

        # 更新画布显示
        updated_canvas = update_canvas()

        success_msg = create_message("clear_graph_success", "计算图已清空，可以重新开始构建", "success")
        return updated_canvas, add_app_message(current_messages, success_msg)

    except Exception as e:
        error_msg = create_message("clear_graph_error", f"清空失败: {str(e)}", "error")
        return dash.no_update, add_app_message(current_messages, error_msg)

# 参数选择弹窗相关回调函数

# 打开参数选择弹窗
@callback(
    Output("param-select-modal", "is_open"),
    Output("current-param-type", "data"),
    Input("x-param-select-btn", "n_clicks"),
    Input("y-param-select-btn", "n_clicks"),
    Input("param-select-cancel", "n_clicks"),
    State("param-select-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_param_select_modal(x_clicks, y_clicks, cancel_clicks, is_open):
    """控制参数选择弹窗的打开和关闭"""
    button_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    if button_id == "x-param-select-btn":
        return True, "x"
    elif button_id == "y-param-select-btn":
        return True, "y"
    elif button_id == "param-select-cancel":
        return False, dash.no_update

    return is_open, dash.no_update

# 更新参数类型显示
@callback(
    Output("param-type-display", "children"),
    Input("current-param-type", "data"),
    prevent_initial_call=False
)
def update_param_type_display(current_type):
    """更新参数类型显示文本"""
    if current_type == "x":
        return "🔸 选择 X 轴参数"
    elif current_type == "y":
        return "🔹 选择 Y 轴参数"
    else:
        return "📊 选择绘图参数"

# 更新参数列表
@callback(
    Output("param-list-container", "children"),
    Input("param-search", "value"),
    Input("canvas-container", "children"),
    State("selected-x-param", "data"),
    State("selected-y-param", "data"),
    State("current-param-type", "data"),
    prevent_initial_call=False
)
def update_param_list(search_value, canvas_children, current_x, current_y, param_type):
    """更新参数列表显示"""
    try:
        params = get_plotting_parameters()

        # 过滤搜索结果
        if search_value:
            search_lower = search_value.lower()
            params = [p for p in params if search_lower in p['label'].lower()]

        if not params:
            return [
                dbc.Alert(
                    "未找到匹配的参数",
                    color="info",
                    className="text-center"
                )
            ]

        # 确定当前应该高亮的参数
        currently_selected = current_x if param_type == "x" else current_y

        # 创建参数选择项
        param_items = []
        for param in params:
            # 判断是否为当前选中的参数
            is_currently_selected = currently_selected == param['value']

            # 设置卡片样式 - 简化，只显示当前选择状态
            if is_currently_selected:
                card_color = "success"
                button_color = "success" 
                button_outline = False
                button_text = "当前选择"
            else:
                card_color = None
                button_color = "primary"
                button_outline = True
                button_text = "选择"

            param_items.append(
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H6(param['label'], className="mb-0 param-card-label"),
                                html.Small(f"值: {param['current_value']} {param['unit']}", className="text-muted")
                            ], width=8, className="d-flex flex-column justify-content-center"),
                            dbc.Col([
                                dbc.Button(
                                    button_text,
                                    id={"type": "param-item-btn", "index": param['value']},
                                    color=button_color,
                                    size="sm",
                                    outline=button_outline,
                                    className="w-100"
                                )
                            ], width=4, className="d-flex align-items-center")
                        ], className="align-items-center")
                    ], className="py-2")
                ], color=card_color, className="mb-2 param-card-clickable")
            )

        return param_items

    except Exception as e:
        return [
            dbc.Alert(
                f"加载参数失败: {str(e)}",
                color="danger"
            )
        ]

# 处理参数选择
@callback(
    Output("selected-x-param", "data"),
    Output("selected-y-param", "data"),
    Output("x-param-display", "value"),
    Output("y-param-display", "value"),
    Output("param-select-modal", "is_open", allow_duplicate=True),
    Input({"type": "param-item-btn", "index": ALL}, "n_clicks"),
    State("current-param-type", "data"),
    State("selected-x-param", "data"),
    State("selected-y-param", "data"),
    prevent_initial_call=True
)
def handle_param_selection(clicks_list, param_type, current_x, current_y):
    """处理参数选择 - 直接选择参数并关闭模态框"""
    if not any(clicks_list):
        raise dash.exceptions.PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id:
        import json
        button_info = json.loads(button_id)
        selected_param_value = button_info['index']
        
        try:
            params = get_plotting_parameters()
            selected_param = next((p for p in params if p['value'] == selected_param_value), None)

            if not selected_param:
                raise dash.exceptions.PreventUpdate

            # 直接更新参数选择并关闭模态框
            if param_type == "x":
                return selected_param_value, current_y, selected_param['label'], dash.no_update, False
            else:
                return current_x, selected_param_value, dash.no_update, selected_param['label'], False

        except Exception:
            raise dash.exceptions.PreventUpdate

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


# 教程模态窗口回调函数
@callback(
    Output("tutorial-modal", "is_open"),
    [Input("help-tutorial-button", "n_clicks"),
     Input("tutorial-close", "n_clicks")],
    State("tutorial-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_tutorial_modal(help_clicks, close_clicks, is_open):
    """切换教程模态窗口的显示状态"""
    if help_clicks or close_clicks:
        return not is_open
    return is_open

@callback(
    Output("tutorial-modal", "is_open", allow_duplicate=True),
    Output("canvas-container", "children", allow_duplicate=True),
    Output("app-messages", "data", allow_duplicate=True),
    Input("tutorial-load-example", "n_clicks"),
    State("app-messages", "data"),
    prevent_initial_call=True
)
def tutorial_load_example(n_clicks, current_messages):
    """教程中的加载示例按钮"""
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    try:
        # 创建示例计算图
        result = create_example_soc_graph()
        
        # 更新画布显示
        updated_canvas = update_canvas()
        
        success_message = (
            f"已从教程加载多核SoC示例计算图："
            f"{result['nodes_created']}个节点，"
            f"{result['total_params']}个参数，"
            f"其中{result['calculated_params']}个计算参数"
        )
        
        success_msg = create_message("tutorial_load_success", success_message, "success")
        return False, updated_canvas, add_app_message(current_messages, success_msg)
        
    except Exception as e:
        error_msg = create_message("tutorial_load_error", f"从教程加载示例失败: {str(e)}", "error")
        return False, dash.no_update, add_app_message(current_messages, error_msg)

# 注册所有客户端回调函数
register_all_clientside_callbacks(app)


def main():
    """Main entry point for the ArchDash application."""
    import argparse

    parser = argparse.ArgumentParser(description='启动计算图应用')
    parser.add_argument('--port', type=int, default=8050, help='服务端口号(默认:8050)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式(会有定时重载检查)')
    args = parser.parse_args()

    app.run(debug=args.debug, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()
