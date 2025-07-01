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
frequency = dependencies[0].value  # 最大频率 GHz
l3_cache = dependencies[1].value   # L3缓存 MB

# 性能评分 = 基础分 × 频率因子 × 缓存因子
base_score = 1000
freq_factor = frequency / 2.5  # 相对于2.5GHz的提升
cache_factor = (l3_cache + 8) / 24  # 相对于16MB缓存的提升

result = int(base_score * freq_factor * cache_factor)
"""
    performance_node.add_parameter(single_core_param)
    
    # 多核性能 - 依赖单核性能和核心数
    multi_core_param = Parameter("多核性能", 18000, "分", description="多核心性能评分", confidence=0.75, param_type="float")
    multi_core_param.add_dependency(performance_node.parameters[0])  # 单核性能
    multi_core_param.add_dependency(cpu_core_node.parameters[1])     # 核心数量
    multi_core_param.calculation_func = """
# 多核性能计算
single_core = dependencies[0].value  # 单核性能
core_count = dependencies[1].value   # 核心数量

# 多核性能 = 单核性能 × 核心数 × 并行效率
parallel_efficiency = 0.9  # 90%的并行效率
result = single_core * core_count * parallel_efficiency
"""
    performance_node.add_parameter(multi_core_param)
    
    graph.add_node(performance_node, auto_place=False)
    graph.layout_manager.place_node(performance_node.id, GridPosition(2, 1))
    
    # 7. 热设计节点
    thermal_node = Node(name="热设计", description="散热和温度分析")
    
    # 热阻 - 依赖工艺和功耗
    thermal_resistance_param = Parameter("热阻", 0.8, "°C/W", description="散热器热阻", confidence=0.85, param_type="float")
    thermal_resistance_param.add_dependency(process_node.parameters[0])  # 工艺节点
    thermal_resistance_param.add_dependency(power_node.parameters[3])    # 总功耗
    thermal_resistance_param.calculation_func = """
# 热阻计算
process_node = dependencies[0].value  # 工艺节点 nm
total_power = dependencies[1].value   # 总功耗 W

# 热阻基值
base_resistance = 0.8

# 工艺越小，热密度越大，需要更好的散热（更低的热阻）
process_factor = (7 / process_node) ** 0.5

# 功耗越大，需要更好的散热
power_factor = (85 / total_power) ** 0.3

result = base_resistance * process_factor * power_factor
"""
    thermal_node.add_parameter(thermal_resistance_param)
    
    # 结温 - 依赖热阻和总功耗
    junction_temp_param = Parameter("结温", 70, "°C", description="芯片结温", confidence=0.8, param_type="float")
    junction_temp_param.add_dependency(thermal_node.parameters[0])  # 热阻
    junction_temp_param.add_dependency(power_node.parameters[3])    # 总功耗
    junction_temp_param.calculation_func = """
# 结温计算
thermal_resistance = dependencies[0].value  # 热阻 °C/W
total_power = dependencies[1].value         # 总功耗 W

# 结温 = 环境温度 + 热阻 × 功耗
ambient_temp = 25  # 环境温度25°C
result = ambient_temp + thermal_resistance * total_power
"""
    thermal_node.add_parameter(junction_temp_param)
    
    graph.add_node(thermal_node)
    graph.layout_manager.place_node(thermal_node.id, GridPosition(0, 2))
    
    # 8. 成本分析节点
    cost_node = Node(name="成本分析", description="芯片成本分析")
    
    # 芯片面积 - 依赖工艺和总缓存
    die_area_param = Parameter("芯片面积", 180, "mm²", description="芯片核心面积", confidence=0.85, param_type="float")
    die_area_param.add_dependency(process_node.parameters[0])  # 工艺节点
    die_area_param.add_dependency(cache_node.parameters[3])    # 总缓存
    die_area_param.calculation_func = """
# 芯片面积计算
process_node = dependencies[0].value  # 工艺节点 nm
total_cache = dependencies[1].value   # 总缓存 MB

# 基础面积
base_area = 100  # mm²

# 工艺缩放
process_factor = (7 / process_node) ** 2

# 缓存面积（每MB约12mm²@7nm）
cache_area = total_cache * 12 * process_factor

result = (base_area + cache_area) * 1.2  # 20%余量
"""
    cost_node.add_parameter(die_area_param)
    
    # 制造成本 - 依赖面积
    manufacturing_cost_param = Parameter("制造成本", 45, "美元", description="芯片制造成本", confidence=0.8, param_type="float")
    manufacturing_cost_param.add_dependency(cost_node.parameters[0])  # 芯片面积
    manufacturing_cost_param.calculation_func = """
# 制造成本计算
die_area = dependencies[0].value  # 芯片面积 mm²

# 每平方毫米成本（考虑良率等因素）
cost_per_mm2 = 0.25  # 美元/mm²

# 考虑封装和测试成本
packaging_cost = 5  # 美元

result = die_area * cost_per_mm2 + packaging_cost
"""
    cost_node.add_parameter(manufacturing_cost_param)
    
    graph.add_node(cost_node)
    graph.layout_manager.place_node(cost_node.id, GridPosition(1, 2))
    
    # 9. 能效分析节点
    efficiency_node = Node(name="能效分析", description="性能功耗比分析")
    
    # 性能功耗比
    perf_power_ratio_param = Parameter("性能功耗比", 212, "分/W", description="每瓦性能", confidence=0.75, param_type="float")
    perf_power_ratio_param.add_dependency(performance_node.parameters[1])  # 多核性能
    perf_power_ratio_param.add_dependency(power_node.parameters[3])        # 总功耗
    perf_power_ratio_param.calculation_func = """
# 性能功耗比计算
performance = dependencies[0].value  # 多核性能分
total_power = dependencies[1].value  # 总功耗 W

result = performance / total_power
"""
    efficiency_node.add_parameter(perf_power_ratio_param)
    
    # 性价比
    cost_performance_ratio_param = Parameter("性价比", 400, "分/美元", description="每美元性能", confidence=0.7, param_type="float")
    cost_performance_ratio_param.add_dependency(performance_node.parameters[1])  # 多核性能
    cost_performance_ratio_param.add_dependency(cost_node.parameters[1])         # 制造成本
    cost_performance_ratio_param.calculation_func = """
# 性价比计算
performance = dependencies[0].value  # 多核性能分
cost = dependencies[1].value        # 制造成本 美元

result = performance / cost
"""
    efficiency_node.add_parameter(cost_performance_ratio_param)
    
    graph.add_node(efficiency_node)
    graph.layout_manager.place_node(efficiency_node.id, GridPosition(2, 2))
    
    # 为所有参数设置计算图引用
    for node in graph.nodes.values():
        for param in node.parameters:
            param.set_graph(graph)
    
    # 返回创建结果和图对象
    return {
        "nodes_created": len(graph.nodes),
        "total_params": sum(len(node.parameters) for node in graph.nodes.values()),
        "calculated_params": sum(1 for node in graph.nodes.values() for param in node.parameters if param.calculation_func),
        "graph": graph
    }
