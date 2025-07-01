#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试参数和节点删除时的依赖关系限制功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import check_parameter_has_dependents, check_node_has_dependents, graph
from models import Node, Parameter

def test_parameter_deletion_restriction():
    """测试参数删除的依赖关系限制"""
    print("🧪 测试参数删除依赖关系限制")
    
    # 清理状态
    graph.nodes.clear()
    
    # 创建输入节点
    input_node = Node(name="输入节点", description="提供基础数据")
    voltage_param = Parameter(name="电压", value=12.0, unit="V", description="输入电压")
    current_param = Parameter(name="电流", value=2.0, unit="A", description="输入电流")
    
    input_node.add_parameter(voltage_param)
    input_node.add_parameter(current_param)
    graph.add_node(input_node)
    
    # 创建计算节点
    calc_node = Node(name="计算节点", description="执行功率计算")
    power_param = Parameter(
        name="功率", 
        value=0.0, 
        unit="W", 
        description="计算的功率值",
        calculation_func="result = dependencies[0].value * dependencies[1].value"
    )
    power_param.add_dependency(voltage_param)
    power_param.add_dependency(current_param)
    
    calc_node.add_parameter(power_param)
    graph.add_node(calc_node)
    
    # 创建高级计算节点
    advanced_node = Node(name="高级计算", description="基于功率的进一步计算")
    efficiency_param = Parameter(
        name="效率",
        value=0.0,
        unit="%",
        description="系统效率",
        calculation_func="result = dependencies[0].value / 30.0 * 100"  # 假设最大功率为30W
    )
    efficiency_param.add_dependency(power_param)
    
    advanced_node.add_parameter(efficiency_param)
    graph.add_node(advanced_node)
    
    print(f"✅ 创建了依赖链: 电压,电流 → 功率 → 效率")
    
    # 测试1: 尝试删除有依赖的电压参数（应该被阻止）
    print("\n📝 测试1: 删除有依赖的电压参数")
    result = check_parameter_has_dependents(voltage_param, graph)
    has_dependents = result[0] if isinstance(result, tuple) else result
    print(f"电压参数是否有依赖者: {has_dependents}")
    assert has_dependents == True, "电压参数应该有依赖者（功率参数依赖它）"
    
    # 测试2: 尝试删除有依赖的功率参数（应该被阻止）
    print("\n📝 测试2: 删除有依赖的功率参数")
    result = check_parameter_has_dependents(power_param, graph)
    has_dependents = result[0] if isinstance(result, tuple) else result
    print(f"功率参数是否有依赖者: {has_dependents}")
    assert has_dependents == True, "功率参数应该有依赖者（效率参数依赖它）"
    
    # 测试3: 删除末端的效率参数（应该被允许）
    print("\n📝 测试3: 删除末端的效率参数")
    result = check_parameter_has_dependents(efficiency_param, graph)
    has_dependents = result[0] if isinstance(result, tuple) else result
    print(f"效率参数是否有依赖者: {has_dependents}")
    assert has_dependents == False, "效率参数应该没有依赖者（可以安全删除）"
    
    print("✅ 参数删除依赖关系限制测试通过")

def test_node_deletion_restriction():
    """测试节点删除的依赖关系限制"""
    print("\n🧪 测试节点删除依赖关系限制")
    
    # 清理状态
    graph.nodes.clear()
    
    # 创建节点链：A → B → C → D
    node_a = Node(name="节点A", description="起始节点")
    param_a = Parameter(name="参数A", value=10.0, unit="unit")
    node_a.add_parameter(param_a)
    graph.add_node(node_a)
    
    node_b = Node(name="节点B", description="中间节点1")
    param_b = Parameter(
        name="参数B", 
        value=0.0, 
        unit="unit",
        calculation_func="result = dependencies[0].value * 2"
    )
    param_b.add_dependency(param_a)
    node_b.add_parameter(param_b)
    graph.add_node(node_b)
    
    node_c = Node(name="节点C", description="中间节点2")
    param_c = Parameter(
        name="参数C",
        value=0.0,
        unit="unit", 
        calculation_func="result = dependencies[0].value + 5"
    )
    param_c.add_dependency(param_b)
    node_c.add_parameter(param_c)
    graph.add_node(node_c)
    
    node_d = Node(name="节点D", description="终端节点")
    param_d = Parameter(
        name="参数D",
        value=0.0,
        unit="unit",
        calculation_func="result = dependencies[0].value / 2"
    )
    param_d.add_dependency(param_c)
    node_d.add_parameter(param_d)
    graph.add_node(node_d)
    
    print("✅ 创建了节点依赖链: A → B → C → D")
    
    # 测试节点删除限制
    test_cases = [
        (node_a.id, "节点A", True, "节点A有依赖者（节点B依赖它）"),
        (node_b.id, "节点B", True, "节点B有依赖者（节点C依赖它）"),
        (node_c.id, "节点C", True, "节点C有依赖者（节点D依赖它）"),
        (node_d.id, "节点D", False, "节点D没有依赖者（可以安全删除）")
    ]
    
    for node_id, node_name, expected_has_dependents, description in test_cases:
        print(f"\n📝 测试删除{node_name}")
        result = check_node_has_dependents(node_id, graph)
        has_dependents = result[0] if isinstance(result, tuple) else result
        print(f"{node_name}是否有依赖者: {has_dependents}")
        assert has_dependents == expected_has_dependents, description
    
    print("✅ 节点删除依赖关系限制测试通过")

def test_complex_dependency_network():
    """测试复杂依赖网络的删除限制"""
    print("\n🧪 测试复杂依赖网络")
    
    # 清理状态
    graph.nodes.clear()
    
    # 创建复杂的依赖网络
    # 基础输入节点
    input_node = Node(name="输入节点")
    base_param = Parameter(name="基础参数", value=100.0, unit="unit")
    input_node.add_parameter(base_param)
    graph.add_node(input_node)
    
    # 分支节点1
    branch1_node = Node(name="分支1")
    branch1_param = Parameter(
        name="分支1参数",
        value=0.0,
        unit="unit",
        calculation_func="result = dependencies[0].value * 0.5"
    )
    branch1_param.add_dependency(base_param)
    branch1_node.add_parameter(branch1_param)
    graph.add_node(branch1_node)
    
    # 分支节点2
    branch2_node = Node(name="分支2")
    branch2_param = Parameter(
        name="分支2参数",
        value=0.0,
        unit="unit",
        calculation_func="result = dependencies[0].value * 0.3"
    )
    branch2_param.add_dependency(base_param)
    branch2_node.add_parameter(branch2_param)
    graph.add_node(branch2_node)
    
    # 汇聚节点（依赖两个分支）
    merge_node = Node(name="汇聚节点")
    merge_param = Parameter(
        name="汇聚参数",
        value=0.0,
        unit="unit",
        calculation_func="result = dependencies[0].value + dependencies[1].value"
    )
    merge_param.add_dependency(branch1_param)
    merge_param.add_dependency(branch2_param)
    merge_node.add_parameter(merge_param)
    graph.add_node(merge_node)
    
    print("✅ 创建了复杂依赖网络:")
    print("   基础参数 → 分支1参数")
    print("   基础参数 → 分支2参数")
    print("   分支1参数 + 分支2参数 → 汇聚参数")
    
    # 测试删除限制
    test_results = []
    
    # 基础参数：有两个依赖者
    result = check_parameter_has_dependents(base_param, graph)
    has_dep = result[0] if isinstance(result, tuple) else result
    test_results.append(("基础参数", has_dep, True))
    
    # 分支参数：各有一个依赖者
    result1 = check_parameter_has_dependents(branch1_param, graph)
    has_dep1 = result1[0] if isinstance(result1, tuple) else result1
    result2 = check_parameter_has_dependents(branch2_param, graph)
    has_dep2 = result2[0] if isinstance(result2, tuple) else result2
    test_results.append(("分支1参数", has_dep1, True))
    test_results.append(("分支2参数", has_dep2, True))
    
    # 汇聚参数：没有依赖者
    result_merge = check_parameter_has_dependents(merge_param, graph)
    has_dep_merge = result_merge[0] if isinstance(result_merge, tuple) else result_merge
    test_results.append(("汇聚参数", has_dep_merge, False))
    
    # 验证结果
    for param_name, actual, expected in test_results:
        print(f"📝 {param_name}: 有依赖者={actual}, 预期={expected}")
        assert actual == expected, f"{param_name}的依赖检查结果不符合预期"
    
    print("✅ 复杂依赖网络测试通过")

if __name__ == "__main__":
    test_parameter_deletion_restriction()
    test_node_deletion_restriction()
    test_complex_dependency_network()
    print("\n🎉 所有依赖删除限制测试通过！") 