#!/usr/bin/env python3
"""
计算图文件操作演示脚本
展示如何使用新实现的保存和加载功能
"""

from models import CalculationGraph, Node, Parameter, CanvasLayoutManager, GridPosition
import json

def create_sample_graph():
    """创建一个示例计算图"""
    print("📝 创建示例计算图...")
    
    # 创建计算图和布局管理器
    graph = CalculationGraph()
    layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=5)
    graph.set_layout_manager(layout_manager)
    
    # 创建电路分析节点
    circuit_node = Node("电路分析", "基本电路参数计算")
    
    # 添加基础参数
    voltage = Parameter("电压", 12.0, "V", description="输入电压")
    resistance = Parameter("电阻", 100.0, "Ω", description="负载电阻")
    
    # 添加计算参数
    current = Parameter("电流", 0.0, "A", description="通过电路的电流",
                       calculation_func="result = dependencies[0].value / dependencies[1].value")
    current.add_dependency(voltage)
    current.add_dependency(resistance)
    
    power = Parameter("功率", 0.0, "W", description="电路消耗的功率",
                     calculation_func="result = dependencies[0].value * dependencies[1].value")
    power.add_dependency(voltage)
    power.add_dependency(current)
    
    # 添加参数到节点
    circuit_node.add_parameter(voltage)
    circuit_node.add_parameter(resistance)
    circuit_node.add_parameter(current)
    circuit_node.add_parameter(power)
    
    # 创建效率分析节点
    efficiency_node = Node("效率分析", "电路效率计算")
    
    input_power = Parameter("输入功率", 15.0, "W", description="总输入功率")
    efficiency = Parameter("效率", 0.0, "%", description="电路效率",
                          calculation_func="result = (dependencies[0].value / dependencies[1].value) * 100")
    efficiency.add_dependency(power)
    efficiency.add_dependency(input_power)
    
    efficiency_node.add_parameter(input_power)
    efficiency_node.add_parameter(efficiency)
    
    # 添加节点到图
    graph.add_node(circuit_node)
    graph.add_node(efficiency_node)
    
    # 设置布局位置
    layout_manager.place_node(circuit_node.id, GridPosition(0, 0))
    layout_manager.place_node(efficiency_node.id, GridPosition(0, 1))
    
    return graph

def demo_save_and_load():
    """演示保存和加载功能"""
    print("🎯 开始演示计算图文件操作功能\n")
    
    # 1. 创建示例图
    graph = create_sample_graph()
    
    # 2. 执行计算
    print("🔄 执行计算...")
    for node in graph.nodes.values():
        for param in node.parameters:
            if param.calculation_func:
                try:
                    result = param.calculate()
                    print(f"   {param.name}: {result} {param.unit}")
                except Exception as e:
                    print(f"   ❌ {param.name} 计算失败: {e}")
    
    print()
    
    # 3. 保存到文件
    filename = "demo_circuit_graph.json"
    print(f"💾 保存计算图到文件: {filename}")
    success = graph.save_to_file(filename, include_layout=True)
    
    if not success:
        print("❌ 保存失败！")
        return
    
    # 4. 显示保存的文件内容概览
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📄 文件内容预览:")
    print(f"   - 版本: {data.get('version')}")
    print(f"   - 时间戳: {data.get('timestamp')}")
    print(f"   - 节点数: {len(data.get('nodes', {}))}")
    print(f"   - 包含布局: {'layout' in data}")
    print()
    
    # 5. 导出摘要
    summary_filename = "demo_summary.json"
    print(f"📋 导出摘要到文件: {summary_filename}")
    summary = graph.export_summary()
    
    with open(summary_filename, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"📊 摘要内容:")
    print(f"   - 总节点数: {summary['总节点数']}")
    print(f"   - 总参数数: {summary['总参数数']}")
    for node_info in summary['节点信息']:
        print(f"   - {node_info['节点名称']}: {node_info['参数数量']}个参数")
    print()
    
    # 6. 从文件加载
    print(f"🔼 从文件加载计算图: {filename}")
    new_layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=5)
    loaded_graph = CalculationGraph.load_from_file(filename, new_layout_manager)
    
    if loaded_graph is None:
        print("❌ 加载失败！")
        return
    
    # 7. 验证加载的数据
    print("✅ 验证加载的计算图:")
    print(f"   - 节点数: {len(loaded_graph.nodes)}")
    total_params = sum(len(node.parameters) for node in loaded_graph.nodes.values())
    print(f"   - 参数数: {total_params}")
    print(f"   - 布局节点数: {len(loaded_graph.layout_manager.node_positions)}")
    
    # 8. 重新计算以验证功能完整性
    print("\n🔄 验证加载的计算图功能:")
    for node in loaded_graph.nodes.values():
        print(f"   节点: {node.name}")
        for param in node.parameters:
            if param.calculation_func:
                try:
                    result = param.calculate()
                    print(f"     - {param.name}: {result} {param.unit}")
                except Exception as e:
                    print(f"     - ❌ {param.name} 计算失败: {e}")
            else:
                print(f"     - {param.name}: {param.value} {param.unit} (输入值)")
    
    print(f"\n✅ 演示完成！")
    print(f"📁 生成的文件:")
    print(f"   - 计算图文件: {filename}")
    print(f"   - 摘要文件: {summary_filename}")

if __name__ == "__main__":
    demo_save_and_load() 