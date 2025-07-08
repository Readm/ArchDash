#!/usr/bin/env python3
"""
数据流系统演示
展示参数值改变时的自动传播更新功能
"""

from models import CalculationGraph, Node, Parameter


def demo_dataflow_system():
    """演示数据流系统的核心功能"""
    print("🌊 ArchDash 数据流系统演示")
    print("=" * 50)
    
    # 创建电路分析场景
    graph = CalculationGraph()
    power_node = Node(name="电源模块", description="电源参数")
    calc_node = Node(name="计算模块", description="计算参数")
    
    graph.add_node(power_node)
    graph.add_node(calc_node)
    
    # 创建基础参数
    voltage = Parameter(name="电压", value=12.0, unit="V", description="输入电压")
    current = Parameter(name="电流", value=2.0, unit="A", description="输入电流")
    
    # 创建计算参数
    power = Parameter(name="功率", value=0.0, unit="W", description="计算功率")
    resistance = Parameter(name="电阻", value=0.0, unit="Ω", description="计算电阻")
    energy = Parameter(name="能量", value=0.0, unit="J", description="单位时间能量")
    
    # 添加参数到节点（这会自动设置graph引用）
    graph.add_parameter_to_node(power_node.id, voltage)
    graph.add_parameter_to_node(power_node.id, current)
    graph.add_parameter_to_node(calc_node.id, power)
    graph.add_parameter_to_node(calc_node.id, resistance)
    graph.add_parameter_to_node(calc_node.id, energy)
    
    print("✅ 步骤1：创建参数结构")
    print(f"   - 基础参数: {voltage.name}({voltage.value}{voltage.unit}), {current.name}({current.value}{current.unit})")
    print(f"   - 计算参数: {power.name}, {resistance.name}, {energy.name}")
    print()
    
    # 建立依赖关系
    print("✅ 步骤2：建立参数依赖关系")
    
    # 功率 = 电压 * 电流
    power.add_dependency(voltage)
    power.add_dependency(current)
    power.calculation_func = """
voltage = dependencies[0].value
current = dependencies[1].value
result = voltage * current
"""
    print(f"   - {power.name} = {voltage.name} × {current.name}")
    
    # 电阻 = 电压 / 电流
    resistance.add_dependency(voltage)
    resistance.add_dependency(current)
    resistance.calculation_func = """
voltage = dependencies[0].value
current = dependencies[1].value
result = voltage / current if current != 0 else 0
"""
    print(f"   - {resistance.name} = {voltage.name} ÷ {current.name}")
    
    # 能量 = 功率 * 1秒
    energy.add_dependency(power)
    energy.calculation_func = """
power = dependencies[0].value
time = 1  # 1秒
result = power * time
"""
    print(f"   - {energy.name} = {power.name} × 1秒")
    
    # 更新依赖关系到计算图
    graph.update_parameter_dependencies(power)
    graph.update_parameter_dependencies(resistance)
    graph.update_parameter_dependencies(energy)
    print()
    
    # 初始计算
    print("✅ 步骤3：初始计算")
    power.calculate()
    resistance.calculate()
    energy.calculate()
    
    def show_current_state():
        print(f"   📊 当前状态:")
        print(f"      {voltage.name}: {voltage.value} {voltage.unit}")
        print(f"      {current.name}: {current.value} {current.unit}")
        print(f"      {power.name}: {power.value} {power.unit}")
        print(f"      {resistance.name}: {resistance.value} {resistance.unit}")
        print(f"      {energy.name}: {energy.value} {energy.unit}")
    
    show_current_state()
    print()
    
    # 演示数据流传播
    print("✅ 步骤4：数据流传播演示")
    print("🔄 改变电压从 12V 到 24V（观察自动传播）")
    
    # 使用数据流更新机制
    update_result = graph.set_parameter_value(voltage, 24.0)
    
    print(f"   📈 更新结果:")
    print(f"      主要变化: {update_result['primary_change']['param'].name} -> {update_result['primary_change']['new_value']}")
    print(f"      级联更新: {update_result['total_updated_params']} 个参数")
    for update in update_result['cascaded_updates']:
        print(f"         └── {update['param'].name}: {update['old_value']} → {update['new_value']}")
    
    show_current_state()
    print()
    
    # 再次演示
    print("🔄 改变电流从 2A 到 3A（观察级联传播）")
    update_result = graph.set_parameter_value(current, 3.0)
    
    print(f"   📈 更新结果:")
    print(f"      主要变化: {update_result['primary_change']['param'].name} -> {update_result['primary_change']['new_value']}")
    print(f"      级联更新: {update_result['total_updated_params']} 个参数")
    for update in update_result['cascaded_updates']:
        print(f"         └── {update['param'].name}: {update['old_value']} → {update['new_value']}")
    
    show_current_state()
    print()
    
    # 依赖链可视化
    print("✅ 步骤5：依赖链可视化")
    voltage_chain = graph.get_dependency_chain(voltage)
    current_chain = graph.get_dependency_chain(current)
    
    def show_dependency_chain(chain, param_name):
        print(f"   🔗 {param_name} 的依赖链:")
        
        def print_dependents(dependents, indent=1):
            for dep in dependents:
                print("     " * indent + f"└── {dep['param'].name}")
                if dep['children']:
                    print_dependents(dep['children'], indent + 1)
        
        if chain['dependents']:
            print_dependents(chain['dependents'])
        else:
            print("       (无下级依赖)")
    
    show_dependency_chain(voltage_chain, voltage.name)
    show_dependency_chain(current_chain, current.name)
    print()
    
    print("🎉 数据流系统演示完成！")
    print("=" * 50)
    print("💡 关键特性:")
    print("   ✅ 自动传播更新：参数值改变时自动触发相关计算")
    print("   ✅ 级联传播：更新会沿着依赖链传播到所有相关参数") 
    print("   ✅ 智能检测：避免不必要的重复计算")
    print("   ✅ 依赖可视化：清晰展示参数间的依赖关系")
    print()
    print("🚀 在Web应用中使用:")
    print("   - 编辑任何参数值时，所有相关参数会自动更新")
    print("   - 在参数编辑窗口中可以看到更新传播的信息")
    print("   - 画布会实时显示所有参数的最新值")
    print()
    print("📝 运行Web应用:")
    print("   python app.py")
    print("   然后访问 http://localhost:8050")


if __name__ == "__main__":
    demo_dataflow_system() 