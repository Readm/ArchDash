from models import CalculationGraph, Node, Parameter, CanvasLayoutManager, GridPosition

def create_example_soc_graph(graph=None):
    """创建多核SoC示例计算图"""
    from session_graph import set_graph, get_graph
    
    if graph is None:
        # 新建独立 CalculationGraph 并初始化布局
        graph = CalculationGraph()  # 每个实例有自己的ID计数器
        layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=12)  # 设置为3列布局
        # 确保布局管理器是干净的
        layout_manager.reset()
        graph.set_layout_manager(layout_manager)
        
        # 更新当前会话的图
        set_graph(graph)
    else:
        # 如果传入了图，就使用它
        if graph.layout_manager is None:
            layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=12)
            graph.set_layout_manager(layout_manager)
        graph.layout_manager.reset()

    from models import Node, Parameter, GridPosition
    
    # 1. 工艺节点 - 基础参数
    process_node = Node(name="工艺技术", description="半导体工艺技术参数")
    process_node.add_parameter(Parameter("工艺节点", 7, "nm", description="制程工艺节点大小", confidence=0.95, param_type="int"))
    process_node.add_parameter(Parameter("电压", 0.8, "V", description="工作电压", confidence=0.9, param_type="float"))
    process_node.add_parameter(Parameter("温度", 85, "°C", description="工作温度", confidence=0.8, param_type="int"))
    process_node.add_parameter(Parameter("工艺厂商", "TSMC", "", description="芯片代工厂商", confidence=1.0, param_type="string"))
    graph.add_node(process_node, auto_place=False)
    graph.layout_manager.place_node(process_node.id, GridPosition(0, 0))
    
    # 2. CPU核心节点
    cpu_core_node = Node(name="CPU核心", description="处理器核心参数")
    cpu_core_node.add_parameter(Parameter("基础频率", 2.5, "GHz", description="基础运行频率", confidence=0.9, param_type="float"))
    cpu_core_node.add_parameter(Parameter("核心数量", 8, "个", description="CPU核心数量", confidence=1.0, param_type="int"))
    
    # 最大频率 - 依赖基础频率和工艺
    max_freq_param = Parameter("最大频率", 3.2, "GHz", description="最大加速频率", confidence=0.8, param_type="float")
    max_freq_param.add_dependency(cpu_core_node.parameters[0])  # 基础频率
    max_freq_param.add_dependency(process_node.parameters[1])   # 电压
    max_freq_param.calculation_func = """
# 最大频率计算：基于基础频率和电压
base_freq = dependencies[0].value  # 基础频率
voltage = dependencies[1].value    # 电压

# 频率随电压线性增长，电压越高频率越高
voltage_factor = voltage / 0.8  # 归一化到标准电压
result = base_freq * voltage_factor * 1.28  # 最大频率比基础频率高28%

# 置信度处理：基于依赖参数的置信度
base_confidence = dependencies[0].confidence  # 基础频率置信度
voltage_confidence = dependencies[1].confidence  # 电压置信度
# 计算结果的置信度取决于最不确定的输入参数
self.confidence = min(base_confidence, voltage_confidence) * 0.95
"""
    cpu_core_node.add_parameter(max_freq_param)
    
    graph.add_node(cpu_core_node, auto_place=False)
    graph.layout_manager.place_node(cpu_core_node.id, GridPosition(1, 0))
    
    # 3. 缓存系统节点
    cache_node = Node(name="缓存系统", description="多级缓存参数")
    cache_node.add_parameter(Parameter("L1缓存", 32, "KB", description="一级缓存大小", confidence=0.95, param_type="int"))
    cache_node.add_parameter(Parameter("L2缓存", 256, "KB", description="二级缓存大小", confidence=0.9, param_type="int"))
    cache_node.add_parameter(Parameter("L3缓存", 16, "MB", description="三级缓存大小", confidence=0.85, param_type="int"))
    
    # 总缓存大小 - 依赖各级缓存
    total_cache_param = Parameter("总缓存", 24.3, "MB", description="总缓存容量", confidence=0.8, param_type="float")
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

# 置信度处理：多个依赖参数的置信度合成
dep_confidences = [dep.confidence for dep in dependencies]
# 使用几何平均数来合成置信度
import math
self.confidence = math.pow(math.prod(dep_confidences), 1/len(dep_confidences)) * 0.9
"""
    cache_node.add_parameter(total_cache_param)
    
    graph.add_node(cache_node, auto_place=False)
    graph.layout_manager.place_node(cache_node.id, GridPosition(2, 0))
    
    # 4. 内存控制器节点
    memory_node = Node(name="内存系统", description="内存控制器和带宽")
    memory_node.add_parameter(Parameter("内存频率", 3200, "MHz", description="DDR4内存频率", confidence=0.9, param_type="int"))
    memory_node.add_parameter(Parameter("内存通道", 2, "个", description="内存通道数量", confidence=1.0, param_type="int"))
    memory_node.add_parameter(Parameter("总线宽度", 64, "bit", description="单通道总线宽度", confidence=1.0, param_type="int"))
    
    # 内存带宽 - 依赖频率、通道数和总线宽度
    bandwidth_param = Parameter("内存带宽", 51.2, "GB/s", description="理论内存带宽", confidence=0.7, param_type="float")
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

# 置信度处理：理论计算结果，但实际性能可能有差异
# 设置相对较低的置信度，因为理论带宽与实际带宽通常有差距
self.confidence = 0.7  # 固定70%置信度
"""
    memory_node.add_parameter(bandwidth_param)
    
    graph.add_node(memory_node, auto_place=False)
    graph.layout_manager.place_node(memory_node.id, GridPosition(0, 1))
    
    # 5. 功耗分析节点
    power_node = Node(name="功耗分析", description="芯片功耗计算")
    
    # CPU功耗 - 依赖频率、电压、核心数
    cpu_power_param = Parameter("CPU功耗", 65, "W", description="CPU总功耗", confidence=0.75, param_type="float")
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

# 置信度处理：基于依赖参数的置信度
dep_confidences = [dep.confidence for dep in dependencies]
self.confidence = min(dep_confidences) * 0.95  # 取最低置信度并略微降低
"""
    power_node.add_parameter(cpu_power_param)
    
    # 缓存功耗 - 依赖总缓存大小
    cache_power_param = Parameter("缓存功耗", 8, "W", description="缓存系统功耗", confidence=0.8, param_type="float")
    cache_power_param.add_dependency(cache_node.parameters[3])  # 总缓存
    cache_power_param.calculation_func = """
# 缓存功耗计算
total_cache_mb = dependencies[0].value  # 总缓存 MB

# 缓存功耗大约每MB消耗0.3W
result = total_cache_mb * 0.33

# 置信度处理：基于依赖参数的置信度
self.confidence = dependencies[0].confidence * 0.9  # 略微降低置信度
"""
    power_node.add_parameter(cache_power_param)
    
    # 内存控制器功耗 - 依赖内存带宽
    memory_power_param = Parameter("内存控制器功耗", 6, "W", description="内存控制器功耗", confidence=0.8, param_type="float")
    memory_power_param.add_dependency(memory_node.parameters[3])  # 内存带宽
    memory_power_param.calculation_func = """
# 内存控制器功耗
bandwidth = dependencies[0].value  # 内存带宽 GB/s

# 功耗与带宽成正比，大约每10GB/s消耗1W
result = bandwidth * 0.12

# 置信度处理：基于依赖参数的置信度
self.confidence = dependencies[0].confidence * 0.9  # 略微降低置信度
"""
    power_node.add_parameter(memory_power_param)
    
    # 总功耗 - 依赖各个子系统功耗
    total_power_param = Parameter("总功耗", 85, "W", description="芯片总功耗(TDP)", confidence=0.7, param_type="float")
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

# 置信度处理：基于依赖参数的置信度
dep_confidences = [dep.confidence for dep in dependencies]
self.confidence = min(dep_confidences) * 0.9  # 取最低置信度并略微降低
"""
    power_node.add_parameter(total_power_param)
    
    graph.add_node(power_node, auto_place=False)
    graph.layout_manager.place_node(power_node.id, GridPosition(1, 1))
    
    # 6. 性能分析节点
    performance_node = Node(name="性能分析", description="系统性能指标")
    
    # 单核性能 - 依赖频率和缓存
    single_core_param = Parameter("单核性能", 2500, "分", description="单核心性能评分", confidence=0.8, param_type="int")
    single_core_param.add_dependency(cpu_core_node.parameters[2])  # 最大频率
    single_core_param.add_dependency(cache_node.parameters[2])     # L3缓存
    single_core_param.calculation_func = """
# 单核性能计算
freq = dependencies[0].value  # 最大频率 GHz
l3_cache = dependencies[1].value  # L3缓存 MB

# 性能评分计算：频率和缓存大小都会影响性能
base_score = freq * 1000  # 基础分数
cache_bonus = l3_cache * 20  # 缓存带来的性能提升
result = int(base_score + cache_bonus)

# 置信度处理：基于依赖参数的置信度
dep_confidences = [dep.confidence for dep in dependencies]
self.confidence = min(dep_confidences) * 0.9  # 取最低置信度并略微降低
"""
    performance_node.add_parameter(single_core_param)
    
    # 多核性能 - 依赖单核性能和核心数
    multi_core_param = Parameter("多核性能", 18000, "分", description="多核心性能评分", confidence=0.75, param_type="int")
    multi_core_param.add_dependency(performance_node.parameters[0])  # 单核性能
    multi_core_param.add_dependency(cpu_core_node.parameters[1])     # 核心数量
    multi_core_param.calculation_func = """
# 多核性能计算
single_core = dependencies[0].value  # 单核性能分数
core_count = dependencies[1].value   # 核心数量

# 多核性能不是简单的线性关系，有一定的效率损失
scaling_factor = 0.9  # 90%的并行效率
result = int(single_core * core_count * scaling_factor)

# 置信度处理：基于依赖参数的置信度
dep_confidences = [dep.confidence for dep in dependencies]
self.confidence = min(dep_confidences) * 0.95  # 取最低置信度并略微降低
"""
    performance_node.add_parameter(multi_core_param)
    
    graph.add_node(performance_node, auto_place=False)
    graph.layout_manager.place_node(performance_node.id, GridPosition(2, 1))
    
    # 7. 热设计节点
    thermal_node = Node(name="热设计", description="芯片散热分析")
    
    # 结温 - 依赖总功耗和工艺温度
    junction_temp_param = Parameter("结温", 95, "°C", description="芯片结温", confidence=0.7, param_type="float")
    junction_temp_param.add_dependency(power_node.parameters[3])    # 总功耗
    junction_temp_param.add_dependency(process_node.parameters[2])  # 工作温度
    junction_temp_param.calculation_func = """
# 结温计算
total_power = dependencies[0].value  # 总功耗
ambient_temp = dependencies[1].value  # 环境温度

# 热阻约为0.3°C/W
thermal_resistance = 0.3
temp_rise = total_power * thermal_resistance
result = ambient_temp + temp_rise

# 置信度处理：基于依赖参数的置信度
dep_confidences = [dep.confidence for dep in dependencies]
self.confidence = min(dep_confidences) * 0.9  # 取最低置信度并略微降低
"""
    thermal_node.add_parameter(junction_temp_param)
    
    # 散热功率 - 依赖结温和环境温度
    cooling_power_param = Parameter("散热功率", 95, "W", description="散热器功率", confidence=0.75, param_type="float")
    cooling_power_param.add_dependency(thermal_node.parameters[0])  # 结温
    cooling_power_param.add_dependency(process_node.parameters[2])  # 环境温度
    cooling_power_param.calculation_func = """
# 散热功率计算
junction_temp = dependencies[0].value  # 结温
ambient_temp = dependencies[1].value   # 环境温度

# 散热功率 = 温差 / 热阻
thermal_resistance = 0.3
result = (junction_temp - ambient_temp) / thermal_resistance

# 置信度处理：基于依赖参数的置信度
dep_confidences = [dep.confidence for dep in dependencies]
self.confidence = min(dep_confidences) * 0.9  # 取最低置信度并略微降低
"""
    thermal_node.add_parameter(cooling_power_param)
    
    graph.add_node(thermal_node, auto_place=False)
    graph.layout_manager.place_node(thermal_node.id, GridPosition(0, 2))
    
    # 8. 成本分析节点
    cost_node = Node(name="成本分析", description="芯片成本估算")
    
    # 硅片成本 - 依赖工艺节点
    die_cost_param = Parameter("硅片成本", 120, "美元", description="单颗芯片硅片成本", confidence=0.6, param_type="float")
    die_cost_param.add_dependency(process_node.parameters[0])  # 工艺节点
    die_cost_param.calculation_func = """
# 硅片成本计算
process_node = dependencies[0].value  # 工艺节点

# 成本与工艺节点成反比关系
base_cost = 40  # 基础成本
node_factor = 7 / process_node  # 工艺系数
result = base_cost * node_factor * node_factor  # 成本与工艺节点平方成反比

# 置信度处理：成本预估的不确定性较大
self.confidence = dependencies[0].confidence * 0.8  # 较低的置信度
"""
    cost_node.add_parameter(die_cost_param)
    
    # 封装成本 - 依赖核心数和缓存
    package_cost_param = Parameter("封装成本", 25, "美元", description="芯片封装成本", confidence=0.7, param_type="float")
    package_cost_param.add_dependency(cpu_core_node.parameters[1])  # 核心数量
    package_cost_param.add_dependency(cache_node.parameters[3])     # 总缓存
    package_cost_param.calculation_func = """
# 封装成本计算
core_count = dependencies[0].value  # 核心数量
total_cache = dependencies[1].value  # 总缓存大小

# 基础封装成本加上核心和缓存带来的额外成本
base_cost = 15
core_cost = core_count * 1.2
cache_cost = total_cache * 0.1
result = base_cost + core_cost + cache_cost

# 置信度处理：基于依赖参数的置信度
dep_confidences = [dep.confidence for dep in dependencies]
self.confidence = min(dep_confidences) * 0.9  # 取最低置信度并略微降低
"""
    cost_node.add_parameter(package_cost_param)
    
    graph.add_node(cost_node, auto_place=False)
    graph.layout_manager.place_node(cost_node.id, GridPosition(1, 2))
    
    # 9. 能效分析节点
    efficiency_node = Node(name="能效分析", description="性能功耗比分析")
    
    # 性能功耗比 - 依赖多核性能和总功耗
    perf_per_watt_param = Parameter("性能功耗比", 200, "分/瓦", description="每瓦性能得分", confidence=0.7, param_type="float")
    perf_per_watt_param.add_dependency(performance_node.parameters[1])  # 多核性能
    perf_per_watt_param.add_dependency(power_node.parameters[3])       # 总功耗
    perf_per_watt_param.calculation_func = """
# 性能功耗比计算
performance = dependencies[0].value  # 多核性能分数
power = dependencies[1].value       # 总功耗

# 简单的性能功耗比
result = performance / power

# 置信度处理：基于依赖参数的置信度
dep_confidences = [dep.confidence for dep in dependencies]
self.confidence = min(dep_confidences) * 0.9  # 取最低置信度并略微降低
"""
    efficiency_node.add_parameter(perf_per_watt_param)
    
    # 能效等级 - 依赖性能功耗比
    efficiency_class_param = Parameter("能效等级", "A", "", description="能效等级评定", confidence=0.8, param_type="string")
    efficiency_class_param.add_dependency(efficiency_node.parameters[0])  # 性能功耗比
    efficiency_class_param.calculation_func = """
# 能效等级计算
perf_per_watt = dependencies[0].value  # 性能功耗比

# 根据性能功耗比确定等级
if perf_per_watt >= 250:
    result = "A+"
elif perf_per_watt >= 200:
    result = "A"
elif perf_per_watt >= 150:
    result = "B"
else:
    result = "C"

# 置信度处理：基于依赖参数的置信度，但因为是离散等级，所以置信度稍高
self.confidence = dependencies[0].confidence * 0.95
"""
    efficiency_node.add_parameter(efficiency_class_param)
    
    graph.add_node(efficiency_node, auto_place=False)
    graph.layout_manager.place_node(efficiency_node.id, GridPosition(2, 2))
    
    # 返回创建结果统计
    nodes_created = len(graph.nodes)
    total_params = sum(len(node.parameters) for node in graph.nodes.values())
    calculated_params = sum(
        sum(1 for param in node.parameters if param.calculation_func)
        for node in graph.nodes.values()
    )
    
    return {
        "graph": graph,
        "nodes_created": nodes_created,
        "total_params": total_params,
        "calculated_params": calculated_params
    }
