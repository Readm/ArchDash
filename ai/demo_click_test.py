#!/usr/bin/env python3
"""
测试点击禁用输入框功能的演示

这个演示创建一个简单的计算图，包含有依赖关系的参数，
用于测试点击禁用输入框时的提示功能。
"""

from models import Parameter, Node, CalculationGraph
from app import graph, id_mapper

def create_test_graph():
    """创建测试用的计算图"""
    print("🔧 创建测试计算图...")
    
    # 清空现有数据
    graph.nodes.clear()
    id_mapper._node_mapping.clear()
    
    # 创建输入节点
    input_node = Node("输入参数", "基础输入参数")
    
    # 添加输入参数
    voltage = Parameter("电压", 12.0, "V", description="输入电压")
    current = Parameter("电流", 2.5, "A", description="输入电流")
    
    input_node.add_parameter(voltage)
    input_node.add_parameter(current)
    
    # 创建计算节点
    calc_node = Node("计算结果", "计算得出的参数")
    
    # 添加计算参数（有依赖关系）
    power = Parameter("功率", 0.0, "W", 
                     description="由电压和电流计算得出的功率",
                     calculation_func="result = dependencies[0].value * dependencies[1].value")
    power.add_dependency(voltage)
    power.add_dependency(current)
    
    energy = Parameter("能量", 0.0, "J",
                      description="假设1秒时间内的能量",
                      calculation_func="result = dependencies[0].value * 1.0  # 功率 × 时间")
    energy.add_dependency(power)
    
    calc_node.add_parameter(power)
    calc_node.add_parameter(energy)
    
    # 添加节点到图
    graph.add_node(input_node)
    graph.add_node(calc_node)
    
    # 注册节点名称
    input_node_id = list(graph.nodes.keys())[0]
    calc_node_id = list(graph.nodes.keys())[1]
    
    id_mapper.register_node(input_node_id, input_node.name)
    id_mapper.register_node(calc_node_id, calc_node.name)
    
    # 执行计算
    print("⚙️ 执行级联计算...")
    graph.recalculate_all()
    
    print("✅ 测试计算图创建完成!")
    print(f"📊 总节点数: {len(graph.nodes)}")
    print(f"📈 总参数数: {sum(len(node.parameters) for node in graph.nodes.values())}")
    
    # 显示参数状态
    print("\n📝 参数状态:")
    for node_id, node in graph.nodes.items():
        node_name = id_mapper.get_node_name(node_id)
        print(f"  📦 {node_name}:")
        for i, param in enumerate(node.parameters):
            dep_count = len(param.dependencies)
            status = "🔒 禁用" if dep_count > 0 else "✏️ 可编辑"
            print(f"    {status} {param.name}: {param.value} {param.unit} (依赖: {dep_count})")
    
    return input_node_id, calc_node_id

if __name__ == "__main__":
    print("🎨 点击禁用输入框功能测试演示")
    print("=" * 50)
    
    try:
        input_node_id, calc_node_id = create_test_graph()
        
        print("\n" + "=" * 50)
        print("✅ 演示图创建完成!")
        print("\n📝 测试说明:")
        print("1. 🖱️ 点击「电压」或「电流」输入框 - 应该可以正常编辑")
        print("2. 🖱️ 点击「功率」或「能量」输入框 - 应该显示禁用提示")
        print("3. 💡 在操作提示区域查看详细的禁用原因和解决方案")
        
        print(f"\n🌐 访问 http://localhost:8051 测试功能")
        print("📌 重点测试：点击灰色的禁用输入框，查看操作提示区域")
        
    except Exception as e:
        print(f"❌ 演示创建失败: {e}")
        import traceback
        traceback.print_exc() 