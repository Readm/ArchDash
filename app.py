import dash
from dash import html, dcc, callback, Output, Input, State, ctx, MATCH, ALL
import dash_bootstrap_components as dbc
from models import CalculationGraph, Node, Parameter, CanvasLayoutManager, GridPosition
from typing import Dict, Optional, List, Any
import json
from datetime import datetime
import uuid
import plotly.graph_objects as go
import numpy as np

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
    
    def update_node_name(self, node_id: str, new_name: str) -> None:
        """更新节点名称"""
        if node_id in self._node_mapping:
            self._node_mapping[node_id]["name"] = new_name

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# 全局数据模型
graph = CalculationGraph()
id_mapper = IDMapper()
layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=10)  # 新增：布局管理器
recently_updated_params = set()  # 新增：存储最近更新的参数ID，用于高亮显示

# 将布局管理器与计算图关联
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

def get_plotting_parameters():
    """获取所有可用于绘图的参数"""
    all_params = []
    for node_id, node in graph.nodes.items():
        for param in node.parameters:
            # 只允许数值类型的参数用于绘图
            if isinstance(param.value, (int, float)):
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
                
                # 如果Y参数有计算函数，触发重新计算
                if y_param.calculation_func:
                    y_param.calculate()
                
                x_values.append(float(x_val))
                y_values.append(float(y_param.value))
                
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
    fig.add_annotation(
        text="请选择参数并点击'生成图表'开始分析",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color="gray")
    )
    fig.update_layout(
        template="plotly_white",
        showlegend=True,
        xaxis=dict(showgrid=False, showticklabels=False, title=""),
        yaxis=dict(showgrid=False, showticklabels=False, title=""),
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
    """检查并自动删除空的最后一列
    
    Returns:
        str: 删除结果的描述，如果没有删除则返回None
    """
    removed_count = 0
    
    # 持续检查并删除空的最后一列，直到最后一列不为空或只剩一列
    while layout_manager.cols > 1:
        # 检查最后一列是否为空
        last_col = layout_manager.cols - 1
        is_empty = True
        
        for row in range(layout_manager.rows):
            if layout_manager.grid[row][last_col] is not None:
                is_empty = False
                break
        
        if is_empty:
            # 删除空的最后一列
            if layout_manager.remove_column():
                removed_count += 1
            else:
                break
        else:
            break
    
    if removed_count > 0:
        if removed_count == 1:
            return f"自动删除了1个空列"
        else:
            return f"自动删除了{removed_count}个空列"
    
    return None

def create_example_soc_graph():
    """创建多核SoC示例计算图"""
    global graph, layout_manager, id_mapper
    
    # 清空现有数据
    graph = CalculationGraph()
    layout_manager = CanvasLayoutManager(initial_cols=4, initial_rows=12)  # 增加列数以容纳更多节点
    id_mapper = IDMapper()
    graph.set_layout_manager(layout_manager)
    
    from models import Node, Parameter
    
    # 1. 工艺节点 - 基础参数
    process_node = Node(name="工艺技术", description="半导体工艺技术参数", node_type="input")
    process_node.add_parameter(Parameter("工艺节点", 7, "nm", description="制程工艺节点大小", confidence=0.95))
    process_node.add_parameter(Parameter("电压", 0.8, "V", description="工作电压", confidence=0.9))
    process_node.add_parameter(Parameter("温度", 85, "°C", description="工作温度", confidence=0.8))
    graph.add_node(process_node)
    id_mapper.register_node(process_node.id, process_node.name)
    from models import GridPosition
    layout_manager.place_node(process_node.id, GridPosition(0, 0))
    
    # 2. CPU核心节点
    cpu_core_node = Node(name="CPU核心", description="处理器核心参数", node_type="calculation")
    cpu_core_node.add_parameter(Parameter("基础频率", 2.5, "GHz", description="基础运行频率", confidence=0.9))
    cpu_core_node.add_parameter(Parameter("核心数量", 8, "个", description="CPU核心数量", confidence=1.0))
    
    # 最大频率 - 依赖基础频率和工艺
    max_freq_param = Parameter("最大频率", 3.2, "GHz", description="最大加速频率", confidence=0.8)
    max_freq_param.add_dependency(cpu_core_node.parameters[0])  # 基础频率
    max_freq_param.add_dependency(process_node.parameters[1])   # 电压
    max_freq_param.calculation_func = """
# 最大频率计算：基于基础频率和电压
base_freq = dependencies[0].value  # 基础频率
voltage = dependencies[1].value    # 电压

# 频率随电压线性增长，电压越高频率越高
voltage_factor = voltage / 0.8  # 归一化到标准电压
result = base_freq * voltage_factor * 1.28  # 最大频率比基础频率高28%
"""
    cpu_core_node.add_parameter(max_freq_param)
    
    graph.add_node(cpu_core_node)
    id_mapper.register_node(cpu_core_node.id, cpu_core_node.name)
    layout_manager.place_node(cpu_core_node.id, GridPosition(1, 0))
    
    # 3. 缓存系统节点
    cache_node = Node(name="缓存系统", description="多级缓存参数", node_type="calculation")
    cache_node.add_parameter(Parameter("L1缓存", 32, "KB", description="一级缓存大小", confidence=0.95))
    cache_node.add_parameter(Parameter("L2缓存", 256, "KB", description="二级缓存大小", confidence=0.9))
    cache_node.add_parameter(Parameter("L3缓存", 16, "MB", description="三级缓存大小", confidence=0.85))
    
    # 总缓存大小 - 依赖各级缓存
    total_cache_param = Parameter("总缓存", 24.3, "MB", description="总缓存容量", confidence=0.8)
    total_cache_param.add_dependency(cache_node.parameters[0])  # L1
    total_cache_param.add_dependency(cache_node.parameters[1])  # L2
    total_cache_param.add_dependency(cache_node.parameters[2])  # L3
    total_cache_param.add_dependency(cpu_core_node.parameters[1])  # 核心数量
    total_cache_param.calculation_func = """
# 总缓存计算
l1_per_core = dependencies[0].value  # L1缓存每核心
l2_per_core = dependencies[1].value  # L2缓存每核心  
l3_shared = dependencies[2].value    # L3共享缓存
core_count = dependencies[3].value   # 核心数量

# 每个核心有独立的L1和L2，L3是共享的
total_l1 = l1_per_core * core_count / 1024  # 转换为MB
total_l2 = l2_per_core * core_count / 1024  # 转换为MB
result = total_l1 + total_l2 + l3_shared
"""
    cache_node.add_parameter(total_cache_param)
    
    graph.add_node(cache_node)
    id_mapper.register_node(cache_node.id, cache_node.name)
    layout_manager.place_node(cache_node.id, GridPosition(2, 0))
    
    # 4. 内存控制器节点
    memory_node = Node(name="内存系统", description="内存控制器和带宽", node_type="calculation")
    memory_node.add_parameter(Parameter("内存频率", 3200, "MHz", description="DDR4内存频率", confidence=0.9))
    memory_node.add_parameter(Parameter("内存通道", 2, "个", description="内存通道数量", confidence=1.0))
    memory_node.add_parameter(Parameter("总线宽度", 64, "bit", description="单通道总线宽度", confidence=1.0))
    
    # 内存带宽 - 依赖频率、通道数和总线宽度
    bandwidth_param = Parameter("内存带宽", 51.2, "GB/s", description="理论内存带宽", confidence=0.7)
    bandwidth_param.add_dependency(memory_node.parameters[0])  # 频率
    bandwidth_param.add_dependency(memory_node.parameters[1])  # 通道数
    bandwidth_param.add_dependency(memory_node.parameters[2])  # 总线宽度
    bandwidth_param.calculation_func = """
# 内存带宽计算
freq_mhz = dependencies[0].value     # 内存频率
channels = dependencies[1].value     # 通道数量
bus_width = dependencies[2].value    # 总线宽度

# 带宽 = 频率 × 通道数 × 总线宽度 × 2 (DDR) / 8 (转换为字节)
result = freq_mhz * channels * bus_width * 2 / 8 / 1000  # GB/s
"""
    memory_node.add_parameter(bandwidth_param)
    
    graph.add_node(memory_node)
    id_mapper.register_node(memory_node.id, memory_node.name)
    layout_manager.place_node(memory_node.id, GridPosition(3, 0))
    
    # 5. 功耗分析节点
    power_node = Node(name="功耗分析", description="芯片功耗计算", node_type="calculation")
    
    # CPU功耗 - 依赖频率、电压、核心数
    cpu_power_param = Parameter("CPU功耗", 65, "W", description="CPU总功耗", confidence=0.75)
    cpu_power_param.add_dependency(cpu_core_node.parameters[2])  # 最大频率
    cpu_power_param.add_dependency(process_node.parameters[1])   # 电压
    cpu_power_param.add_dependency(cpu_core_node.parameters[1])  # 核心数量
    cpu_power_param.calculation_func = """
# CPU功耗计算 (P = C × V² × f × N)
frequency = dependencies[0].value    # 频率 GHz
voltage = dependencies[1].value      # 电压 V
core_count = dependencies[2].value   # 核心数量

# 简化的功耗模型：功耗与电压平方和频率成正比
capacitance = 2.5  # 等效电容常数
result = capacitance * voltage * voltage * frequency * core_count
"""
    power_node.add_parameter(cpu_power_param)
    
    # 缓存功耗 - 依赖总缓存大小
    cache_power_param = Parameter("缓存功耗", 8, "W", description="缓存系统功耗", confidence=0.8)
    cache_power_param.add_dependency(cache_node.parameters[3])  # 总缓存
    cache_power_param.calculation_func = """
# 缓存功耗计算
total_cache_mb = dependencies[0].value  # 总缓存 MB

# 缓存功耗大约每MB消耗0.3W
result = total_cache_mb * 0.33
"""
    power_node.add_parameter(cache_power_param)
    
    # 内存控制器功耗 - 依赖内存带宽
    memory_power_param = Parameter("内存控制器功耗", 6, "W", description="内存控制器功耗", confidence=0.8)
    memory_power_param.add_dependency(memory_node.parameters[3])  # 内存带宽
    memory_power_param.calculation_func = """
# 内存控制器功耗
bandwidth = dependencies[0].value  # 内存带宽 GB/s

# 功耗与带宽成正比，大约每10GB/s消耗1W
result = bandwidth * 0.12
"""
    power_node.add_parameter(memory_power_param)
    
    # 总功耗 - 依赖各个子系统功耗
    total_power_param = Parameter("总功耗", 85, "W", description="芯片总功耗(TDP)", confidence=0.7)
    total_power_param.add_dependency(power_node.parameters[0])  # CPU功耗
    total_power_param.add_dependency(power_node.parameters[1])  # 缓存功耗
    total_power_param.add_dependency(power_node.parameters[2])  # 内存控制器功耗
    total_power_param.calculation_func = """
# 总功耗计算
cpu_power = dependencies[0].value       # CPU功耗
cache_power = dependencies[1].value     # 缓存功耗
memory_power = dependencies[2].value    # 内存控制器功耗

# 其他功耗（GPU、IO等）约占15%
other_power = 10
result = cpu_power + cache_power + memory_power + other_power
"""
    power_node.add_parameter(total_power_param)
    
    graph.add_node(power_node)
    id_mapper.register_node(power_node.id, power_node.name)
    layout_manager.place_node(power_node.id, GridPosition(0, 1))
    
    # 6. 性能分析节点
    performance_node = Node(name="性能分析", description="系统性能指标", node_type="calculation")
    
    # 单核性能 - 依赖频率和缓存
    single_core_param = Parameter("单核性能", 2500, "分", description="单核心性能评分", confidence=0.8)
    single_core_param.add_dependency(cpu_core_node.parameters[2])  # 最大频率
    single_core_param.add_dependency(cache_node.parameters[2])     # L3缓存
    single_core_param.calculation_func = """
# 单核性能计算
frequency = dependencies[0].value  # 最大频率 GHz
l3_cache = dependencies[1].value   # L3缓存 MB

# 性能基准：3GHz + 16MB L3 = 2500分
base_score = 2500
freq_factor = frequency / 3.0      # 频率因子
cache_factor = l3_cache / 16.0     # 缓存因子

result = base_score * freq_factor * (0.7 + 0.3 * cache_factor)
"""
    performance_node.add_parameter(single_core_param)
    
    # 多核性能 - 依赖单核性能、核心数、缓存
    multi_core_param = Parameter("多核性能", 18000, "分", description="多核心性能评分", confidence=0.75)
    multi_core_param.add_dependency(performance_node.parameters[0])  # 单核性能
    multi_core_param.add_dependency(cpu_core_node.parameters[1])     # 核心数量
    multi_core_param.add_dependency(memory_node.parameters[3])       # 内存带宽
    multi_core_param.calculation_func = """
# 多核性能计算
single_score = dependencies[0].value    # 单核性能
core_count = dependencies[1].value      # 核心数量
bandwidth = dependencies[2].value       # 内存带宽

# 多核扩展效率受内存带宽限制
bandwidth_factor = min(1.0, bandwidth / 30.0)  # 30GB/s为理想带宽
scaling_efficiency = 0.8 + 0.2 * bandwidth_factor

result = single_score * core_count * scaling_efficiency
"""
    performance_node.add_parameter(multi_core_param)
    
    graph.add_node(performance_node)
    id_mapper.register_node(performance_node.id, performance_node.name)
    layout_manager.place_node(performance_node.id, GridPosition(1, 1))
    
    # 7. 热设计功耗节点
    thermal_node = Node(name="热设计", description="散热和温度管理", node_type="calculation")
    
    # 热阻 - 依赖工艺和功耗
    thermal_resistance_param = Parameter("热阻", 0.8, "°C/W", description="芯片热阻", confidence=0.7)
    thermal_resistance_param.add_dependency(process_node.parameters[0])  # 工艺节点
    thermal_resistance_param.add_dependency(power_node.parameters[3])    # 总功耗
    thermal_resistance_param.calculation_func = """
# 热阻计算
process_nm = dependencies[0].value    # 工艺节点
total_power = dependencies[1].value   # 总功耗

# 先进工艺热阻更低，功耗越高热阻相对增加
base_thermal_resistance = 1.2 - (28 - process_nm) * 0.015
power_factor = 1 + (total_power - 65) * 0.002
result = base_thermal_resistance * power_factor
"""
    thermal_node.add_parameter(thermal_resistance_param)
    
    # 结温 - 依赖环境温度、功耗、热阻
    junction_temp_param = Parameter("结温", 70, "°C", description="芯片结点温度", confidence=0.75)
    junction_temp_param.add_dependency(process_node.parameters[2])       # 环境温度
    junction_temp_param.add_dependency(power_node.parameters[3])         # 总功耗
    junction_temp_param.add_dependency(thermal_node.parameters[0])       # 热阻
    junction_temp_param.calculation_func = """
# 结温计算
ambient_temp = dependencies[0].value      # 环境温度
total_power = dependencies[1].value       # 总功耗
thermal_resistance = dependencies[2].value # 热阻

# 结温 = 环境温度 + 功耗 × 热阻
result = ambient_temp + total_power * thermal_resistance
"""
    thermal_node.add_parameter(junction_temp_param)
    
    graph.add_node(thermal_node)
    id_mapper.register_node(thermal_node.id, thermal_node.name)
    layout_manager.place_node(thermal_node.id, GridPosition(2, 1))
    
    # 8. 成本分析节点
    cost_node = Node(name="成本分析", description="芯片成本估算", node_type="calculation")
    
    # 芯片面积 - 依赖工艺、核心数、缓存
    die_area_param = Parameter("芯片面积", 180, "mm²", description="芯片裸片面积", confidence=0.6)
    die_area_param.add_dependency(process_node.parameters[0])    # 工艺节点
    die_area_param.add_dependency(cpu_core_node.parameters[1])  # 核心数量
    die_area_param.add_dependency(cache_node.parameters[3])     # 总缓存
    die_area_param.calculation_func = """
# 芯片面积计算
process_nm = dependencies[0].value    # 工艺节点
core_count = dependencies[1].value    # 核心数量
total_cache = dependencies[2].value   # 总缓存

# 基础面积模型（7nm基准）
process_factor = (process_nm / 7.0) ** 2  # 面积与工艺平方成反比
core_area = core_count * 15  # 每核心约15mm²
cache_area = total_cache * 2.5  # 每MB缓存约2.5mm²
other_area = 50  # 其他逻辑面积

result = (core_area + cache_area + other_area) * process_factor
"""
    cost_node.add_parameter(die_area_param)
    
    # 制造成本 - 依赖面积和工艺
    manufacturing_cost_param = Parameter("制造成本", 45, "$", description="芯片制造成本", confidence=0.6)
    manufacturing_cost_param.add_dependency(cost_node.parameters[0])     # 芯片面积
    manufacturing_cost_param.add_dependency(process_node.parameters[0])  # 工艺节点
    manufacturing_cost_param.calculation_func = """
# 制造成本计算
die_area = dependencies[0].value      # 芯片面积
process_nm = dependencies[1].value    # 工艺节点

# 先进工艺成本更高，面积越大成本越高
process_cost_factor = (7.0 / process_nm) ** 1.5  # 先进工艺成本指数增长
area_cost = die_area * 0.2 * process_cost_factor  # 每mm²基础成本
result = area_cost + 5  # 固定成本
"""
    cost_node.add_parameter(manufacturing_cost_param)
    
    graph.add_node(cost_node)
    id_mapper.register_node(cost_node.id, cost_node.name)
    layout_manager.place_node(cost_node.id, GridPosition(3, 1))
    
    # 9. 能效分析节点
    efficiency_node = Node(name="能效分析", description="性能功耗比分析", node_type="calculation")
    
    # 性能功耗比 - 依赖多核性能和总功耗
    perf_watt_param = Parameter("性能功耗比", 212, "分/W", description="每瓦性能", confidence=0.8)
    perf_watt_param.add_dependency(performance_node.parameters[1])  # 多核性能
    perf_watt_param.add_dependency(power_node.parameters[3])        # 总功耗
    perf_watt_param.calculation_func = """
# 性能功耗比计算
multi_core_score = dependencies[0].value  # 多核性能
total_power = dependencies[1].value        # 总功耗

# 每瓦性能 = 总性能 / 总功耗
result = multi_core_score / total_power
"""
    efficiency_node.add_parameter(perf_watt_param)
    
    # 性价比 - 依赖多核性能和制造成本
    value_ratio_param = Parameter("性价比", 400, "分/$", description="每美元性能", confidence=0.7)
    value_ratio_param.add_dependency(performance_node.parameters[1])  # 多核性能
    value_ratio_param.add_dependency(cost_node.parameters[1])         # 制造成本
    value_ratio_param.calculation_func = """
# 性价比计算
multi_core_score = dependencies[0].value  # 多核性能
manufacturing_cost = dependencies[1].value # 制造成本

# 每美元性能 = 总性能 / 制造成本
result = multi_core_score / manufacturing_cost
"""
    efficiency_node.add_parameter(value_ratio_param)
    
    graph.add_node(efficiency_node)
    id_mapper.register_node(efficiency_node.id, efficiency_node.name)
    layout_manager.place_node(efficiency_node.id, GridPosition(0, 2))
    
    # 触发所有参数的计算以建立完整的依赖关系
    for node in graph.nodes.values():
        for param in node.parameters:
            if param.calculation_func and param.dependencies:
                try:
                    param.calculate()
                except Exception as e:
                    print(f"计算参数 {param.name} 时出错: {e}")
    
    return {
        "nodes_created": len(graph.nodes),
        "total_params": sum(len(node.parameters) for node in graph.nodes.values()),
        "calculated_params": sum(1 for node in graph.nodes.values() 
                               for param in node.parameters 
                               if param.calculation_func and param.dependencies)
    }

# 画布更新函数 - 使用新的布局管理器
def update_canvas(node_data=None):
    """使用布局管理器渲染画布"""
    canvas_content = []
    
    # 检查是否有节点，如果没有则显示空状态提示
    print(f"🔍 update_canvas调用: graph.nodes = {graph.nodes}")
    print(f"🔍 graph.nodes是否为空: {not graph.nodes}")
    print(f"🔍 graph.nodes长度: {len(graph.nodes)}")
    
    if not graph.nodes:
        print("✅ 触发空状态显示 - 计算图为空，显示引导提示")
        empty_state_content = html.Div([
            html.Div([
                html.Div([
                    html.I(className="fas fa-project-diagram", style={"fontSize": "4rem", "color": "#dee2e6", "marginBottom": "1rem"}),
                    html.H4("计算图为空", className="text-muted mb-3"),
                    html.P([
                        "开始构建您的计算图：",
                    ], className="text-muted mb-4"),
                    html.Div([
                        html.Div([
                            html.Span("🎯", style={"fontSize": "1.5rem", "marginRight": "0.5rem"}),
                            "点击右上角 ",
                            html.Strong("🎯", className="text-warning"),
                            " 按钮载入SoC示例计算图"
                        ], className="mb-3 p-3 border rounded bg-light"),
                        html.Div([
                            html.Span("➕", style={"fontSize": "1.5rem", "marginRight": "0.5rem"}),
                            "点击左上角 ",
                            html.Strong("➕", className="text-primary"),
                            " 按钮添加新节点"
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
    for col in range(layout_manager.cols):
        col_content = []
        col_nodes = layout_manager.get_column_nodes(col)
        
        # 按行排序节点
        for node_id, row in sorted(col_nodes, key=lambda x: x[1]):
            node_name = id_mapper.get_node_name(node_id)
            node = graph.nodes.get(node_id)
            
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
                                            "marginRight": "8px",
                                            "marginTop": "6px",
                                            "flex": "none"
                                        },
                                        className="param-pin",
                                        id=f"pin-{node_id}-{param_idx}"
                                    ),
                                    # 参数名输入框
                                    dcc.Input(
                                        id={"type": "param-name", "node": node_id, "index": param_idx},
                                        value=param.name,
                                        style={"flex": "1", "border": "1px solid transparent", "background": "transparent", "fontWeight": "bold", "borderRadius": "3px", "padding": "2px 4px"},
                                        className="param-input"
                                    )
                                ], style={"display": "flex", "alignItems": "center", "width": "100%"}),
                                style={"paddingRight": "8px", "width": "40%"}
                            ),
                            html.Td(
                                html.Div([
                                    dcc.Input(
                                        id={"type": "param-value", "node": node_id, "index": param_idx},
                                        value=str(param.value),
                                        style={
                                            "width": "calc(100% - 30px)" if (param.calculation_func and param.dependencies and getattr(param, 'unlinked', False)) else "100%", 
                                            "border": "1px solid transparent", 
                                            "background": "lightgreen" if f"{node_id}-{param_idx}" in recently_updated_params else "transparent",
                                            "borderRadius": "3px", 
                                            "padding": "2px 4px",
                                            "transition": "background-color 2s ease-out"
                                        },
                                        className="param-input"
                                    ),
                                    # Unlink图标 - 只有有依赖计算且unlinked=True时显示
                                    html.Div(
                                        "🔓",
                                        id={"type": "unlink-icon", "node": node_id, "index": param_idx},
                                        className="unlink-icon",
                                        style={
                                            "cursor": "pointer",
                                            "fontSize": "14px",
                                            "opacity": "1",
                                            "marginLeft": "4px",
                                            "padding": "2px",
                                            "borderRadius": "3px",
                                            "display": "inline-block",
                                            "minWidth": "20px",
                                            "textAlign": "center",
                                            "userSelect": "none"
                                        },
                                        title="重新连接 (点击恢复自动计算)"
                                    ) if (param.calculation_func and param.dependencies and getattr(param, 'unlinked', False)) else None
                                ], style={"display": "flex", "alignItems": "center", "width": "100%"}),
                                style={"width": "40%"}
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
                                    label="⋮",
                                    size="sm",
                                    direction="left"
                                ),
                                style={"width": "20%", "textAlign": "right", "paddingLeft": "4px"}
                            )
                        ])
                    )
            
            param_table = html.Table(param_rows, style={"width": "100%", "fontSize": "0.95em", "marginTop": "4px"}) if param_rows else None
            
            # 获取节点在网格中的位置信息
            position = layout_manager.get_node_position(node_id)
            position_info = f"({position.row},{position.col})" if position else ""
            
            node_div = html.Div(
                [
                    html.Div([
                        html.Div([
                            html.Span(f"节点: {node_name}", className="node-name"),
                            html.Small(f" {position_info}", className="text-muted", style={"fontSize": "0.7em"})
                        ]),
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
                            label="⋮",
                            size="sm",
                            direction="left"
                        )
                    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}),
                    param_table,
                    html.Div(id=f"node-content-{node_id}", className="node-content")
                ],
                className="p-3 node-container node-entrance fade-in",
                id=id_mapper.get_html_id(node_id),
                **{"data-row": row, "data-col": col, "data-dash-id": json.dumps(id_mapper.get_dash_id(node_id))}
            )
            col_content.append(node_div)
        
        # 计算列宽
        col_width = max(1, 12 // layout_manager.cols)
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
    """创建箭头连接 - 使用客户端JavaScript获取真实pin位置"""
    # 总是返回箭头容器，让客户端JavaScript处理具体的箭头绘制
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

app.layout = dbc.Container([
    html.H1([
        "🎨 ArchDash"
    ], className="text-center my-2 fade-in"),

    dbc.Row([
        dbc.Col([
            # 计算图卡片
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.H5([ 
                            html.Span("计算图", className="fw-bold")
                        ], className="mb-0"),
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
                                "color": "#6c757d"
                            },
                            title="添加新节点"
                        )
                    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "width": "100%"})
                ]),
                dbc.CardBody([
                    html.Div(
                        id="canvas-container", 
                        className="position-relative",
                        style={"minHeight": "500px"},
                        children=update_canvas()  # 直接在布局中调用，确保初始渲染
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
                                title="加载文件"
                            ),
                            accept=".json",
                            multiple=False
                        ),
                        html.Button(
                            "💾", 
                            id="save-graph-button", 
                            className="btn btn-success btn-sm",
                            title="保存文件"
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
                            title="加载示例计算图"
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
                            style={"minWidth": "32px"}
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
                                    dcc.Dropdown(
                                        id="x-param-selector", 
                                        placeholder="选择X轴参数",
                                        clearable=True,
                                        className="mb-1",
                                        style={"zIndex": "9999"}
                                    )
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Y轴参数:", className="mb-1"),
                                    dcc.Dropdown(
                                        id="y-param-selector", 
                                        placeholder="选择Y轴参数",
                                        clearable=True,
                                        className="mb-1",
                                        style={"zIndex": "9999"}
                                    )
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
                                        className="form-control"
                                    )
                                ], width=4),
                            ], className="mb-2"),
                            
                            # 系列名称和累计绘图选项
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        dbc.InputGroup([
                                            dbc.InputGroupText("系列名称:", style={"fontSize": "0.9rem", "minWidth": "85px"}),
                                            dbc.Input(
                                                id="series-name-input",
                                                placeholder="自定义系列名称",
                                                size="sm",
                                                style={"fontSize": "0.9rem"}
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
                                            style={"fontSize": "0.9rem"}
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
                                            [html.Span("导出")], 
                                            id="export-plot-data-btn", 
                                            color="info", 
                                            size="sm"
                                        )
                                    ], className="w-100")
                                ])
                            ])
                        ], className="p-2 dropdown-container")
                    ], className="glass-card dropdown-safe-card")
                ], className="p-1", style={"minHeight": "450px"})
            ], className="glass-card"),
        ], width=4),
    ]),
    

    
    # 参数依赖关系模块 - 可折叠，独立一行
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.H5([ 
                            html.Span("参数依赖关系", className="fw-bold"),
                        ], className="mb-0 d-inline-flex align-items-center"),
                        html.Div([
                            dbc.Button(
                                "🔄", 
                                id="refresh-dependencies-btn", 
                                color="outline-primary", 
                                size="sm", 
                                className="me-2",
                                title="刷新依赖关系"
                            ),
                            dbc.Button(
                                ["🔽 ", html.Span("展开")], 
                                id="collapse-dependencies-btn", 
                                color="outline-secondary", 
                                size="sm",
                                className="collapse-btn",
                                title="展开/折叠依赖关系面板"
                            ),
                        ], className="d-flex")
                    ], className="d-flex justify-content-between align-items-center w-100")
                ], className="dependencies-header py-2"),
                dbc.Collapse([
                    dbc.CardBody([
                        # 使用标签页显示不同的视图
                        dbc.Tabs([
                            dbc.Tab([
                                html.Div(
                                    id="dependencies-display",
                                    style={"height": "350px", "overflowY": "auto"},
                                    children=[html.P("📊 加载依赖关系中...", className="text-muted text-center")]
                                )
                            ], label="🔗 依赖关系", tab_id="dependencies-tab"),
                            dbc.Tab([
                                html.Div(
                                    id="calculation-flow-display",
                                    style={"height": "350px", "overflowY": "auto"},
                                    children=[html.P("🔄 加载计算流程中...", className="text-muted text-center")]
                                )
                            ], label="⚙️ 计算流程", tab_id="flow-tab"),
                            dbc.Tab([
                                html.Div([
                                    html.H6("📊 实时计算分析", className="mb-3"),
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Label("选择参数进行分析:"),
                                            dbc.Select(id="analysis-param-selector", placeholder="选择要分析的参数", style={"zIndex": "9999"})
                                        ], width=8),
                                        dbc.Col([
                                            dbc.Button("开始分析", id="start-analysis-btn", color="primary", size="sm")
                                        ], width=4)
                                    ], className="mb-3"),
                                    html.Div(
                                        id="realtime-analysis-display",
                                        style={"height": "280px", "overflowY": "auto"},
                                        children=[html.P("选择参数后点击'开始分析'查看实时计算过程", className="text-muted text-center")]
                                    )
                                ], style={"padding": "15px"})
                            ], label="📈 实时分析", tab_id="analysis-tab")
                        ], id="dependencies-tabs", active_tab="dependencies-tab")
                    ], className="p-2 dropdown-container")
                ], id="dependencies-collapse", is_open=False)
            ], className="glass-card dependencies-panel dropdown-safe-card"),
        ], width=12),
    ], className="mt-2"),

    dcc.Store(id="node-data", data={}),  # 简化为空字典，布局由layout_manager管理
    dcc.Store(id="arrow-connections-data", data=[]),  # 存储箭头连接数据
    dcc.Store(id="dependencies-collapse-state", data={"is_open": False}),  # 存储依赖关系面板折叠状态
    dcc.Store(id="cumulative-plot-data", data=[]),  # 存储累计绘图数据
    dcc.Interval(id="clear-highlight-timer", interval=3000, n_intervals=0, disabled=True),  # 3秒后清除高亮
    dcc.Download(id="download-graph"),  # 用于下载计算图文件
    dcc.Download(id="download-plot-data"),  # 新增：用于下载绘图数据
# 移除旧的context menu，使用新的dropdown menu
    
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
    
    # 节点编辑模态窗口
    dbc.Modal([
        dbc.ModalHeader([
            html.H4("编辑节点", id="node-edit-title")
        ]),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("节点名称:"),
                    dbc.Input(id="node-edit-name", placeholder="节点名称")
                ], width=8),
                dbc.Col([
                    dbc.Label("节点类型:"),
                    dbc.Select(
                        id="node-edit-type",
                        options=[
                            {"label": "默认", "value": "default"},
                            {"label": "输入", "value": "input"},
                            {"label": "计算", "value": "calculation"},
                            {"label": "输出", "value": "output"}
                        ],
                        value="default"
                    )
                ], width=4),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("节点描述:"),
                    dbc.Textarea(id="node-edit-description", placeholder="节点描述", rows=3)
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
                    dbc.Input(id="node-add-name", placeholder="输入节点名称")
                ], width=8),
                dbc.Col([
                    dbc.Label("节点类型:"),
                    dbc.Select(
                        id="node-add-type",
                        options=[
                            {"label": "默认", "value": "default"},
                            {"label": "输入", "value": "input"},
                            {"label": "计算", "value": "calculation"},
                            {"label": "输出", "value": "output"}
                        ],
                        value="default"
                    )
                ], width=4),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("节点描述:"),
                    dbc.Textarea(id="node-add-description", placeholder="节点描述（可选）", rows=3)
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
], fluid=True)

# 添加自定义CSS样式 - 使用外部样式文件
app.index_string = '''
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
            
            /* 箭头样式保持 */
            #arrows-overlay {
                pointer-events: none;
                z-index: 10;
            }
            
            .dependency-arrow {
                transition: all 0.2s ease;
                cursor: pointer;
                pointer-events: auto;
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
            }
            
            .dependency-arrow:hover {
                transform: scaleY(1.5);
                filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
            }
            
            .dependency-arrow-head {
                transition: all 0.2s ease;
                cursor: pointer;
                pointer-events: auto;
                filter: drop-shadow(0 1px 2px rgba(0,0,0,0.1));
            }
            
            .dependency-arrow-head:hover {
                transform: scale(1.2);
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
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
    Input({"type": "delete-node", "node": ALL}, "n_clicks"),
    State("node-data", "data"),
    prevent_initial_call=True
)
def handle_node_operations(move_up_clicks, move_down_clicks, 
                          move_left_clicks, move_right_clicks, 
                          add_param_clicks, delete_node_clicks,
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
        
        node_name = id_mapper.get_node_name(node_id)
        
        if operation_type == "move-node-up":
            success = layout_manager.move_node_up(node_id)
            result_message = f"节点 {node_name} 已上移" if success else f"节点 {node_name} 无法上移"
            # 节点移动后检查并自动删除空的最后一列
            if success:
                auto_remove_result = auto_remove_empty_last_column()
                if auto_remove_result:
                    result_message += f"，{auto_remove_result}"
            return result_message, node_data, update_canvas()
        
        elif operation_type == "move-node-down":
            success = layout_manager.move_node_down(node_id)
            result_message = f"节点 {node_name} 已下移" if success else f"节点 {node_name} 无法下移"
            # 节点移动后检查并自动删除空的最后一列
            if success:
                auto_remove_result = auto_remove_empty_last_column()
                if auto_remove_result:
                    result_message += f"，{auto_remove_result}"
            return result_message, node_data, update_canvas()
        
        elif operation_type == "move-node-left":
            success = layout_manager.move_node_left(node_id)
            result_message = f"节点 {node_name} 已左移" if success else f"节点 {node_name} 无法左移"
            # 节点移动后检查并自动删除空的最后一列
            if success:
                auto_remove_result = auto_remove_empty_last_column()
                if auto_remove_result:
                    result_message += f"，{auto_remove_result}"
            return result_message, node_data, update_canvas()
        
        elif operation_type == "move-node-right":
            success = layout_manager.move_node_right(node_id)
            result_message = f"节点 {node_name} 已右移" if success else f"节点 {node_name} 无法右移"
            # 节点移动后检查并自动删除空的最后一列
            if success:
                auto_remove_result = auto_remove_empty_last_column()
                if auto_remove_result:
                    result_message += f"，{auto_remove_result}"
            return result_message, node_data, update_canvas()
        
        elif operation_type == "add-param":
            param = Parameter(name="new_param", value=0.0, unit="", description=f"新参数")
            
            # 添加参数到节点
            graph.add_parameter_to_node(node_id, param)
            
            return f"参数已添加到节点 {node_name}", node_data, update_canvas()
        
        elif operation_type == "delete-node":
            # 从布局管理器移除节点
            layout_manager.remove_node(node_id)
            # 从计算图移除节点
            if node_id in graph.nodes:
                del graph.nodes[node_id]
            # 从ID映射器移除
            if hasattr(id_mapper, '_node_mapping') and node_id in id_mapper._node_mapping:
                del id_mapper._node_mapping[node_id]
            
            result_message = f"节点 {node_name} 已删除"
            # 删除节点后检查并自动删除空的最后一列
            auto_remove_result = auto_remove_empty_last_column()
            if auto_remove_result:
                result_message += f"，{auto_remove_result}"
            
            return result_message, node_data, update_canvas()
    
    return dash.no_update, dash.no_update, dash.no_update

# 移除旧的show_context_menu回调，现在使用直接的dropdown menu

# 添加参数更新回调 - 修改为失去焦点或按Enter时更新
@callback(
    Output("node-data", "data", allow_duplicate=True),
    Output("canvas-container", "children", allow_duplicate=True),
    Output("output-result", "children", allow_duplicate=True),
    Output("clear-highlight-timer", "disabled", allow_duplicate=True),
    Input({"type": "param-name", "node": ALL, "index": ALL}, "n_blur"),
    Input({"type": "param-name", "node": ALL, "index": ALL}, "n_submit"),
    Input({"type": "param-value", "node": ALL, "index": ALL}, "n_blur"),
    Input({"type": "param-value", "node": ALL, "index": ALL}, "n_submit"),
    State({"type": "param-name", "node": ALL, "index": ALL}, "value"),
    State({"type": "param-value", "node": ALL, "index": ALL}, "value"),
    State("node-data", "data"),
    prevent_initial_call=True
)
def update_parameter(name_n_blur, name_n_submit, value_n_blur, value_n_submit, param_names, param_values, node_data):
    if not ctx.triggered_id:
        return node_data, dash.no_update, dash.no_update, dash.no_update
    
    triggered_id = ctx.triggered_id
    if isinstance(triggered_id, dict):
        node_id = triggered_id["node"]
        param_index = triggered_id["index"]
        param_type = triggered_id["type"]
        
        # 检查触发类型，只处理有效的触发
        trigger_prop = ctx.triggered[0]["prop_id"].split(".")[-1]
        if trigger_prop not in ["n_blur", "n_submit"]:
            return node_data, dash.no_update, dash.no_update, dash.no_update
        
        # 检查触发值是否有效（避免初始化误触发）
        trigger_value = ctx.triggered[0]["value"]
        if not trigger_value or trigger_value == 0:
            return node_data, dash.no_update, dash.no_update, dash.no_update
        
        # 🔧 重要修复：使用ctx.triggered获取准确的新值
        new_value = None
        
        # 方法1：直接从ctx.triggered获取当前触发值（最可靠）
        try:
            # ctx.triggered[0]["value"] 包含实际触发的新值
            new_value = ctx.triggered[0]["value"]
            
            # 对于n_blur和n_submit事件，我们需要从states中获取实际的输入值
            if new_value in [1, True]:  # 这些是事件计数，不是实际值
                # 构建精确的状态键来获取输入值
                state_key = f'{{"index":{param_index},"node":"{node_id}","type":"{param_type}"}}.value'
                
                # 从ctx.states中查找匹配的状态
                for state_id, state_value in ctx.states.items():
                    if state_key == state_id or (isinstance(state_id, str) and state_key in state_id):
                        new_value = state_value
                        break
                
                # 如果还是没找到，尝试不同的键格式
                if new_value in [1, True]:
                    alt_key = f'{{"type":"{param_type}","node":"{node_id}","index":{param_index}}}.value'
                    for state_id, state_value in ctx.states.items():
                        if alt_key == state_id or (isinstance(state_id, str) and alt_key in state_id):
                            new_value = state_value
                            break
        except Exception as e:
            print(f"🔧 方法1失败: {e}")
            new_value = None
        
        # 方法2：如果方法1失败，使用有序索引匹配（回退方案）
        if new_value is None or new_value in [1, True]:
            try:
                # 创建与callback参数顺序一致的参数ID列表
                ordered_param_ids = []
                for n_id in sorted(graph.nodes.keys()):
                    node = graph.nodes[n_id]
                    for p_idx in range(len(node.parameters)):
                        ordered_param_ids.append({"type": param_type, "node": n_id, "index": p_idx})
                
                # 找到目标参数在有序列表中的位置
                target_param_id = {"type": param_type, "node": node_id, "index": param_index}
                target_index = ordered_param_ids.index(target_param_id)
                
                # 获取对应的值
                if param_type == "param-name" and target_index < len(param_names):
                    new_value = param_names[target_index]
                elif param_type == "param-value" and target_index < len(param_values):
                    new_value = param_values[target_index]
                    
            except (ValueError, IndexError) as e:
                print(f"🔧 方法2失败: {e}")
                new_value = None
        
        # 方法3：最后的回退方案 - 保持当前值不变
        if new_value is None or new_value in [1, True]:
            node = graph.nodes.get(node_id)
            if node and param_index < len(node.parameters):
                current_param = node.parameters[param_index]
                if param_type == "param-name":
                    new_value = current_param.name
                elif param_type == "param-value":
                    new_value = current_param.value
                print(f"🔧 使用回退方案，保持当前值: {new_value}")
        
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
            # 更新参数值
            try:
                if new_value is not None and new_value != "":
                    if isinstance(new_value, str) and '.' in new_value:
                        new_value = float(new_value)
                    elif isinstance(new_value, str):
                        new_value = int(new_value)
                else:
                    new_value = 0
            except (ValueError, TypeError):
                new_value = str(new_value) if new_value is not None else ""
            
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
                recently_updated_params.add(f"{node_id}-{param_index}")
            else:
                # 无计算依赖的参数，正常更新
                # 清空之前的高亮标记
                recently_updated_params.clear()
                
                # 使用新的数据流更新机制
                update_result = graph.set_parameter_value(current_param, new_value)
                should_update_canvas = True
                
                # 标记主参数为已更新
                recently_updated_params.add(f"{node_id}-{param_index}")
                
                # 标记所有被级联更新的参数
                for update_info in update_result.get('cascaded_updates', []):
                    updated_param = update_info['param']
                    # 找到该参数所在的节点和索引
                    for check_node_id, check_node in graph.nodes.items():
                        for check_idx, check_param in enumerate(check_node.parameters):
                            if check_param is updated_param:
                                recently_updated_params.add(f"{check_node_id}-{check_idx}")
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
    Input({"type": "delete-param", "node": ALL, "index": ALL}, "n_clicks"),
    Input({"type": "move-param-up", "node": ALL, "index": ALL}, "n_clicks"),
    Input({"type": "move-param-down", "node": ALL, "index": ALL}, "n_clicks"),
    State("node-data", "data"),
    prevent_initial_call=True
)
def handle_parameter_operations(delete_clicks, move_up_clicks, move_down_clicks, node_data):
    if not ctx.triggered_id:
        return node_data, update_canvas()
    
    triggered_id = ctx.triggered_id
    if not isinstance(triggered_id, dict):
        return node_data, update_canvas()
    
    node_id = triggered_id.get("node")
    param_index = triggered_id.get("index")
    operation_type = triggered_id.get("type")
    
    # 检查点击数值，避免初始化时的误触发
    trigger_value = ctx.triggered[0]["value"]
    if not trigger_value or trigger_value == 0:
        return node_data, update_canvas()
    
    if not node_id or param_index is None:
        return node_data, update_canvas()
    
    # 获取节点
    node = graph.nodes.get(node_id)
    if not node:
        return node_data, update_canvas()
        
    if param_index >= len(node.parameters):
        return node_data, update_canvas()
    
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
    return node_data, update_canvas()

# 处理unlink图标点击的回调函数
@callback(
    Output("node-data", "data", allow_duplicate=True),
    Output("canvas-container", "children", allow_duplicate=True),
    Output("output-result", "children", allow_duplicate=True),
    Input({"type": "unlink-icon", "node": ALL, "index": ALL}, "n_clicks"),
    State("node-data", "data"),
    prevent_initial_call=True
)
def handle_unlink_toggle(unlink_clicks, node_data):
    """处理unlink图标点击，重新连接参数并计算"""
    if not ctx.triggered_id:
        return node_data, dash.no_update, dash.no_update
    
    triggered_id = ctx.triggered_id
    if not isinstance(triggered_id, dict):
        return node_data, dash.no_update, dash.no_update
    
    node_id = triggered_id.get("node")
    param_index = triggered_id.get("index")
    
    # 检查点击数值，避免初始化时的误触发
    trigger_value = ctx.triggered[0]["value"]
    if not trigger_value or trigger_value == 0:
        return node_data, dash.no_update, dash.no_update
    
    if not node_id or param_index is None:
        return node_data, dash.no_update, dash.no_update
    
    # 获取节点和参数
    node = graph.nodes.get(node_id)
    if not node or param_index >= len(node.parameters):
        return node_data, dash.no_update, dash.no_update
    
    param = node.parameters[param_index]
    node_name = id_mapper.get_node_name(node_id)
    
    # 检查参数是否可以重新连接
    if not param.calculation_func or not param.dependencies:
        return node_data, dash.no_update, f"⚠️ 参数 {node_name}.{param.name} 无计算依赖"
    
    try:
        # 重新连接参数（设置unlinked=False并重新计算）
        new_value = param.relink_and_calculate()
        result_message = f"🔗 参数 {node_name}.{param.name} 已重新连接，新值: {new_value}"
        
        return node_data, update_canvas(), result_message
        
    except Exception as e:
        return node_data, dash.no_update, f"❌ 重新连接失败: {str(e)}"

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
        update_result = graph.set_parameter_value(param, new_value)
        cascaded_info = ""
        if update_result['cascaded_updates']:
            affected_params = [update['param'].name for update in update_result['cascaded_updates']]
            cascaded_info = f"，同时更新了 {len(affected_params)} 个关联参数: {', '.join(affected_params)}"
        
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
        
        return False, updated_canvas, success_msg
        
    except Exception as e:
        return True, dash.no_update, f"保存失败: {str(e)}"

# 添加定时清理高亮的回调
@callback(
    Output("canvas-container", "children", allow_duplicate=True),
    Output("clear-highlight-timer", "disabled", allow_duplicate=True),
    Input("clear-highlight-timer", "n_intervals"),
    prevent_initial_call=True
)
def clear_parameter_highlights(n_intervals):
    """定时清除参数高亮"""
    if recently_updated_params:
        recently_updated_params.clear()
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
@callback(
    Output("canvas-container", "children", allow_duplicate=True),
    Output("output-result", "children", allow_duplicate=True),
    Input("load-example-graph-button", "n_clicks"),
    prevent_initial_call=True
)
def load_example_soc_graph(n_clicks):
    """加载多核SoC示例计算图"""
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
@callback(
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
        global graph, layout_manager, id_mapper
        
        # 重新创建布局管理器
        layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=10)
        
        # 从数据重建计算图
        graph = CalculationGraph.from_dict(data, layout_manager)
        
        # 重新注册所有节点到ID映射器
        id_mapper = IDMapper()
        for node_id, node in graph.nodes.items():
            id_mapper.register_node(node_id, node.name)
        
        # 更新画布显示
        updated_canvas = update_canvas()
        
        loaded_nodes = len(graph.nodes)
        total_params = sum(len(node.parameters) for node in graph.nodes.values())
        
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
                
                // 绘制箭头的函数
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
                            var angle = Math.atan2(dy, dx) * 180 / Math.PI;
                            
                            if (length > 5) {
                                // 确定箭头颜色（当前pin相关的用特殊颜色）
                                var isActiveConnection = (connection.source_pin_id === activePinId || connection.target_pin_id === activePinId);
                                var arrowColor = isActiveConnection ? '#e74c3c' : '#007bff';
                                var arrowOpacity = isActiveConnection ? '1' : '0.6';
                                
                                // 创建连接线
                                var line = document.createElement('div');
                                line.style.position = 'absolute';
                                line.style.left = x1 + 'px';
                                line.style.top = (y1 - 1) + 'px';
                                line.style.width = length + 'px';
                                line.style.height = isActiveConnection ? '3px' : '2px';
                                line.style.backgroundColor = arrowColor;
                                line.style.opacity = arrowOpacity;
                                line.style.transformOrigin = '0 50%';
                                line.style.transform = 'rotate(' + angle + 'deg)';
                                line.style.zIndex = isActiveConnection ? '1002' : '1000';
                                line.className = 'dependency-arrow';
                                line.title = connection.source_node_name + '.' + connection.source_param_name + 
                                            ' → ' + connection.target_node_name + '.' + connection.target_param_name;
                                
                                window.arrowContainer.appendChild(line);
                                
                                // 创建箭头头部
                                var arrowHead = document.createElement('div');
                                arrowHead.style.position = 'absolute';
                                arrowHead.style.left = (x2 - 6) + 'px';
                                arrowHead.style.top = (y2 - 3) + 'px';
                                arrowHead.style.width = '0';
                                arrowHead.style.height = '0';
                                arrowHead.style.borderLeft = '6px solid ' + arrowColor;
                                arrowHead.style.borderTop = '3px solid transparent';
                                arrowHead.style.borderBottom = '3px solid transparent';
                                arrowHead.style.opacity = arrowOpacity;
                                arrowHead.style.zIndex = isActiveConnection ? '1003' : '1001';
                                arrowHead.className = 'dependency-arrow-head';
                                
                                window.arrowContainer.appendChild(arrowHead);
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
        node_name = id_mapper.get_node_name(node_id)
        
        for param_idx, param in enumerate(node.parameters):

            
            # 分析计算复杂度和执行状态
            calculation_status = "无计算"
            if param.calculation_func:
                try:
                    # 尝试解析计算函数的复杂度
                    func_lines = param.calculation_func.split('\n')
                    non_comment_lines = [line.strip() for line in func_lines if line.strip() and not line.strip().startswith('#')]
                    complexity = len(non_comment_lines)
                    
                    if complexity <= 3:
                        calculation_status = "简单计算"
                    elif complexity <= 10:
                        calculation_status = "中等复杂度"
                    else:
                        calculation_status = "复杂计算"
                except:
                    calculation_status = "计算函数"
            
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
                'calculation_status': calculation_status,
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
                        dep_node_name = id_mapper.get_node_name(search_node_id)
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
                        search_node_name = id_mapper.get_node_name(search_node_id)
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
    
    # 按计算状态分类统计
    simple_calcs = sum(1 for p in dependencies_info if p['calculation_status'] == '简单计算')
    medium_calcs = sum(1 for p in dependencies_info if p['calculation_status'] == '中等复杂度')
    complex_calcs = sum(1 for p in dependencies_info if p['calculation_status'] == '复杂计算')
    
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
                    html.P(f"🎯 总体健康度: {((total_params - calculation_errors) / max(total_params, 1) * 100):.1f}%", className="mb-0"),
                ], width=6),
            ]),
            html.Hr(),
            html.H6("🔧 计算复杂度分布", className="mb-2"),
            html.P([
                dbc.Badge(f"简单 {simple_calcs}", color="success", className="me-2"),
                dbc.Badge(f"中等 {medium_calcs}", color="warning", className="me-2"),
                dbc.Badge(f"复杂 {complex_calcs}", color="danger", className="me-2"),
            ], className="mb-0")
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
                        dbc.Badge(f"{param_info['calculation_status']}", 
                                color="success" if param_info['has_calculation'] else "secondary", 
                                className="me-2"),
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

def simulate_parameter_change_and_show_process(param_id, new_value):
    """模拟参数变化并展示完整的计算传播过程"""
    try:
        # 找到对应的参数对象
        target_param = None
        target_node_id = None
        target_param_idx = None
        
        for node_id, node in graph.nodes.items():
            for param_idx, param in enumerate(node.parameters):
                if id(param) == param_id:
                    target_param = param
                    target_node_id = node_id
                    target_param_idx = param_idx
                    break
            if target_param:
                break
        
        if not target_param:
            return {"success": False, "message": "参数未找到"}
        
        # 记录原始值
        original_value = target_param.value
        
        # 执行变化并收集传播过程
        propagation_log = []
        propagation_log.append({
            "step": 0,
            "action": "初始变化",
            "param_name": target_param.name,
            "old_value": original_value,
            "new_value": new_value,
            "node_name": id_mapper.get_node_name(target_node_id)
        })
        
        # 设置新值
        update_result = graph.set_parameter_value(target_param, new_value)
        
        # 记录级联更新过程
        if update_result and 'cascaded_updates' in update_result:
            for i, cascade_info in enumerate(update_result['cascaded_updates']):
                param = cascade_info['param']
                
                # 找到参数所在的节点
                cascade_node_name = "未知节点"
                for node_id, node in graph.nodes.items():
                    if param in node.parameters:
                        cascade_node_name = id_mapper.get_node_name(node_id)
                        break
                
                propagation_log.append({
                    "step": i + 1,
                    "action": "级联计算",
                    "param_name": param.name,
                    "old_value": cascade_info['old_value'],
                    "new_value": cascade_info['new_value'],
                    "node_name": cascade_node_name,
                    "calculation_func": getattr(param, 'calculation_func', None)
                })
            
        return {
            "success": True,
            "propagation_log": propagation_log,
            "total_affected": len(propagation_log),
            "original_value": original_value,
            "final_value": new_value
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"模拟失败: {str(e)}"
        }

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
            html.P(f"计算复杂度: {param_info['calculation_status']}", className="mt-2")
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

# 初始化实时分析参数选择器
@callback(
    Output("analysis-param-selector", "options"),
    Input("canvas-container", "children"),
    prevent_initial_call=False
)
def update_analysis_param_selector(canvas_children):
    """更新实时分析的参数选择器"""
    try:
        options = []
        for node_id, node in graph.nodes.items():
            node_name = id_mapper.get_node_name(node_id)
            for param_idx, param in enumerate(node.parameters):
                option_value = f"{node_id}|{param_idx}"
                option_label = f"{node_name}.{param.name} ({param.value} {param.unit})"
                options.append({"label": option_label, "value": option_value})
        
        return options
    except Exception as e:
        return []

# 手动刷新依赖关系和计算流程
@callback(
    Output("dependencies-display", "children", allow_duplicate=True),
    Output("calculation-flow-display", "children", allow_duplicate=True),
    Output("analysis-param-selector", "options", allow_duplicate=True),
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
        
        # 刷新参数选择器
        options = []
        for node_id, node in graph.nodes.items():
            node_name = id_mapper.get_node_name(node_id)
            for param_idx, param in enumerate(node.parameters):
                option_value = f"{node_id}|{param_idx}"
                option_label = f"{node_name}.{param.name} ({param.value} {param.unit})"
                options.append({"label": option_label, "value": option_value})
        
        return deps_display, flow_display, options
        
    except Exception as e:
        error_alert = [
            dbc.Alert([
                html.H6("⚠️ 刷新失败", className="mb-2"),
                html.P(f"错误信息: {str(e)}", className="mb-0")
            ], color="danger")
        ]
        return error_alert, error_alert, []

# 当节点/参数发生变化时自动更新所有显示
@callback(
    Output("dependencies-display", "children", allow_duplicate=True),
    Output("calculation-flow-display", "children", allow_duplicate=True),
    Output("analysis-param-selector", "options", allow_duplicate=True),
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
        
        # 更新参数选择器
        options = []
        for node_id, node in graph.nodes.items():
            node_name = id_mapper.get_node_name(node_id)
            for param_idx, param in enumerate(node.parameters):
                option_value = f"{node_id}|{param_idx}"
                option_label = f"{node_name}.{param.name} ({param.value} {param.unit})"
                options.append({"label": option_label, "value": option_value})
        
        return deps_display, flow_display, options
        
    except Exception as e:
        error_alert = [
            dbc.Alert([
                html.H6("⚠️ 自动更新失败", className="mb-2"),
                html.P(f"错误信息: {str(e)}", className="mb-0")
            ], color="warning")
        ]
        return error_alert, error_alert, []

# 实时分析功能
@callback(
    Output("realtime-analysis-display", "children"),
    Input("start-analysis-btn", "n_clicks"),
    State("analysis-param-selector", "value"),
    prevent_initial_call=True
)
def perform_realtime_analysis(n_clicks, selected_param):
    """执行实时计算分析"""
    if not n_clicks or not selected_param:
        raise dash.exceptions.PreventUpdate
    
    try:
        # 解析选择的参数
        node_id, param_idx = selected_param.split('|')
        param_idx = int(param_idx)
        
        # 获取参数对象
        target_node = graph.nodes.get(node_id)
        if not target_node or param_idx >= len(target_node.parameters):
            return dbc.Alert("参数未找到", color="danger")
        
        target_param = target_node.parameters[param_idx]
        node_name = id_mapper.get_node_name(node_id)
        
        # 创建分析结果
        analysis_components = []
        
        # 参数信息卡片
        analysis_components.append(
            dbc.Card([
                dbc.CardHeader([
                    html.H6(f"🎯 分析目标: {node_name}.{target_param.name}")
                ]),
                dbc.CardBody([
                    html.P(f"当前值: {target_param.value} {target_param.unit}"),
                    html.P(f"描述: {target_param.description}"),
                    html.P(f"置信度: {getattr(target_param, 'confidence', 1.0):.1%}")
                ])
            ], className="mb-3")
        )
        
        # 计算链分析
        if hasattr(target_param, 'calculation_func') and target_param.calculation_func:
            dependencies_info = get_all_parameter_dependencies()
            param_info = None
            
            for info in dependencies_info:
                if info['node_id'] == node_id and info['param_name'] == target_param.name:
                    param_info = info
                    break
            
            if param_info and param_info['calculation_chain']:
                analysis_components.append(
                    dbc.Card([
                        dbc.CardHeader([
                            html.H6("🔄 计算链条分析")
                        ]),
                        dbc.CardBody([
                            html.P("执行步骤:", className="fw-bold"),
                            html.Ol([
                                html.Li(step, className={
                                    "text-info": "dependencies[" in step,
                                    "text-warning": "执行计算函数" in step,
                                    "text-success": "result =" in step
                                }.get(True, ""))
                                for step in param_info['calculation_chain']
                            ])
                        ])
                    ], className="mb-3")
                )
        
        # 影响分析
        dependent_params = []
        for search_node_id, search_node in graph.nodes.items():
            for search_param in search_node.parameters:
                if target_param in search_param.dependencies:
                    search_node_name = id_mapper.get_node_name(search_node_id)
                    dependent_params.append({
                        'node_name': search_node_name,
                        'param_name': search_param.name,
                        'value': search_param.value,
                        'unit': search_param.unit
                    })
        
        if dependent_params:
            analysis_components.append(
                dbc.Card([
                    dbc.CardHeader([
                        html.H6("📊 影响分析")
                    ]),
                    dbc.CardBody([
                        html.P("修改此参数将影响以下计算:", className="fw-bold"),
                        html.Ul([
                            html.Li(f"{dep['node_name']}.{dep['param_name']} = {dep['value']} {dep['unit']}")
                            for dep in dependent_params
                        ])
                    ])
                ], className="mb-3")
            )
        
        # 敏感性指标
        sensitivity_score = len(dependent_params) * 10 + (50 if target_param.calculation_func else 0)
        sensitivity_level = "高" if sensitivity_score > 80 else "中" if sensitivity_score > 40 else "低"
        sensitivity_color = "danger" if sensitivity_level == "高" else "warning" if sensitivity_level == "中" else "success"
        
        analysis_components.append(
            dbc.Alert([
                html.H6("🎯 敏感性评估", className="mb-2"),
                html.P(f"敏感性等级: {sensitivity_level} (评分: {sensitivity_score})", className="mb-1"),
                html.P(f"影响参数数量: {len(dependent_params)}", className="mb-1"),
                html.P(f"计算复杂度: {'高' if target_param.calculation_func else '无'}", className="mb-0")
            ], color=sensitivity_color)
        )
        
        return analysis_components
        
    except Exception as e:
        return dbc.Alert([
            html.H6("⚠️ 分析失败"),
            html.P(f"错误信息: {str(e)}")
        ], color="danger")

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
                        'source_node_name': id_mapper.get_node_name(source_node_id),
                        'target_node_name': id_mapper.get_node_name(node_id)
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
    Output("node-edit-type", "value"),
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
        node_name = id_mapper.get_node_name(node_id)
        
        return (
            True,  # 打开模态窗口
            f"编辑节点: {node_name}",
            node.name,
            getattr(node, 'node_type', 'default'),
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
    State("node-edit-type", "value"),
    State("node-edit-description", "value"),
    State("node-edit-data", "data"),
    prevent_initial_call=True
)
def save_node_changes(save_clicks, node_name, node_type, node_description, edit_data):
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
        node.node_type = node_type
        node.description = node_description or ""
        
        # 更新ID映射器中的节点名称
        id_mapper.update_node_name(node_id, node.name)
        
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
    Output("node-add-type", "value"),
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
        return True, "", "default", ""
    elif ctx.triggered_id == "node-add-cancel":
        # 关闭模态窗口
        return False, "", "default", ""
    
    raise dash.exceptions.PreventUpdate

# 创建新节点
@callback(
    Output("node-add-modal", "is_open", allow_duplicate=True),
    Output("canvas-container", "children", allow_duplicate=True),
    Output("output-result", "children", allow_duplicate=True),
    Input("node-add-save", "n_clicks"),
    State("node-add-name", "value"),
    State("node-add-type", "value"),
    State("node-add-description", "value"),
    prevent_initial_call=True
)
def create_new_node(save_clicks, node_name, node_type, node_description):
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
        node = Node(
            name=node_name,
            description=node_description or f"节点 {node_name}",
            node_type=node_type
        )
        
        # 添加到计算图
        graph.add_node(node)
        id_mapper.register_node(node.id, node_name)
        
        # 使用布局管理器放置节点
        position = layout_manager.place_node(node.id)
        
        # 关闭模态窗口并更新界面
        success_message = f"节点 '{node_name}' 已创建并添加到位置 ({position.row}, {position.col})"
        return False, update_canvas(), success_message
        
    except Exception as e:
        return True, dash.no_update, f"错误: {str(e)}"

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='启动计算图应用')
    parser.add_argument('--port', type=int, default=8050, help='服务端口号(默认:8050)')
    args = parser.parse_args()
    
    app.run(debug=True, host="0.0.0.0", port=args.port)