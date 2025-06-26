#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试依赖删除限制功能
验证当参数或节点被其他参数依赖时，无法删除
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import CalculationGraph, Node, Parameter
from app import check_parameter_has_dependents, check_node_has_dependents, graph, id_mapper

def test_parameter_dependency_deletion_restriction():
    """测试参数依赖删除限制功能"""
    print("🔬 测试参数依赖删除限制功能")
    print("=" * 50)
    
    # 清理全局状态
    graph.nodes.clear()
    id_mapper._node_mapping.clear()
    
    # 创建测试节点和参数
    input_node = Node("输入参数", "基础输入参数")
    length = Parameter("长度", 10.0, "m")
    width = Parameter("宽度", 5.0, "m")
    input_node.add_parameter(length)
    input_node.add_parameter(width)
    graph.add_node(input_node)
    id_mapper.register_node(input_node.id, input_node.name)
    
    # 创建计算节点
    calc_node = Node("计算结果", "基于输入参数的计算")
    area = Parameter("面积", 0.0, "m²", 
                    calculation_func="result = dependencies[0].value * dependencies[1].value")
    area.add_dependency(length)
    area.add_dependency(width)
    calc_node.add_parameter(area)
    graph.add_node(calc_node)
    id_mapper.register_node(calc_node.id, calc_node.name)
    
    # 创建更复杂的依赖
    advanced_node = Node("高级计算", "基于面积的计算")
    price_per_sqm = Parameter("单价", 1000.0, "元/m²")
    total_cost = Parameter("总成本", 0.0, "元",
                          calculation_func="result = dependencies[0].value * dependencies[1].value")
    total_cost.add_dependency(area)
    total_cost.add_dependency(price_per_sqm)
    advanced_node.add_parameter(price_per_sqm)
    advanced_node.add_parameter(total_cost)
    graph.add_node(advanced_node)
    id_mapper.register_node(advanced_node.id, advanced_node.name)
    
    print("1. 测试参数依赖检查：")
    
    # 测试长度参数（被面积依赖）
    has_deps, dep_list = check_parameter_has_dependents(length)
    print(f"   长度参数是否被依赖: {has_deps}")
    if has_deps:
        for dep in dep_list:
            print(f"   └── 被 {dep['node_name']}.{dep['param_name']} 依赖")
    assert has_deps, "长度参数应该被面积参数依赖"
    
    # 测试面积参数（被总成本依赖）
    has_deps, dep_list = check_parameter_has_dependents(area)
    print(f"   面积参数是否被依赖: {has_deps}")
    if has_deps:
        for dep in dep_list:
            print(f"   └── 被 {dep['node_name']}.{dep['param_name']} 依赖")
    assert has_deps, "面积参数应该被总成本参数依赖"
    
    # 测试单价参数（被总成本依赖）
    has_deps, dep_list = check_parameter_has_dependents(price_per_sqm)
    print(f"   单价参数是否被依赖: {has_deps}")
    if has_deps:
        for dep in dep_list:
            print(f"   └── 被 {dep['node_name']}.{dep['param_name']} 依赖")
    assert has_deps, "单价参数应该被总成本参数依赖"
    
    # 测试总成本参数（不被任何参数依赖）
    has_deps, dep_list = check_parameter_has_dependents(total_cost)
    print(f"   总成本参数是否被依赖: {has_deps}")
    assert not has_deps, "总成本参数不应该被任何参数依赖"
    
    print("\n2. 测试节点依赖检查：")
    
    # 测试输入节点（其参数被依赖）
    has_deps, dep_info = check_node_has_dependents(input_node.id)
    print(f"   输入节点是否有参数被依赖: {has_deps}")
    if has_deps:
        print(f"   被依赖的参数: {dep_info['affected_node_params']}")
        for dep in dep_info['dependent_params']:
            print(f"   └── {dep['depends_on']} 被 {dep['node_name']}.{dep['param_name']} 依赖")
    assert has_deps, "输入节点的参数应该被依赖"
    
    # 测试计算节点（其面积参数被依赖）
    has_deps, dep_info = check_node_has_dependents(calc_node.id)
    print(f"   计算节点是否有参数被依赖: {has_deps}")
    if has_deps:
        print(f"   被依赖的参数: {dep_info['affected_node_params']}")
        for dep in dep_info['dependent_params']:
            print(f"   └── {dep['depends_on']} 被 {dep['node_name']}.{dep['param_name']} 依赖")
    assert has_deps, "计算节点的面积参数应该被依赖"
    
    # 测试高级计算节点（其参数不被依赖）
    has_deps, dep_info = check_node_has_dependents(advanced_node.id)
    print(f"   高级计算节点是否有参数被依赖: {has_deps}")
    if has_deps:
        print(f"   被依赖的参数: {dep_info['affected_node_params']}")
        for dep in dep_info['dependent_params']:
            print(f"   └── {dep['depends_on']} 被 {dep['node_name']}.{dep['param_name']} 依赖")
    # 注意：单价参数被总成本依赖，所以高级计算节点应该有被依赖的参数
    
    print("\n✅ 所有依赖检查测试通过！")
    
    return {
        'input_node': input_node,
        'calc_node': calc_node,
        'advanced_node': advanced_node,
        'length': length,
        'width': width,
        'area': area,
        'price_per_sqm': price_per_sqm,
        'total_cost': total_cost
    }

def test_dependency_chain():
    """测试复杂依赖链的检查"""
    print("\n🔬 测试复杂依赖链检查")
    print("=" * 50)
    
    # 清理全局状态
    graph.nodes.clear()
    id_mapper._node_mapping.clear()
    
    # 创建更复杂的依赖链: A -> B -> C -> D
    chain_node = Node("依赖链", "复杂依赖链测试")
    
    param_a = Parameter("A", 1.0, "unit")  # 基础参数
    param_b = Parameter("B", 0.0, "unit", calculation_func="result = dependencies[0].value * 2")
    param_c = Parameter("C", 0.0, "unit", calculation_func="result = dependencies[0].value + 5")
    param_d = Parameter("D", 0.0, "unit", calculation_func="result = dependencies[0].value * 3")
    
    # 建立依赖关系
    param_b.add_dependency(param_a)  # B 依赖 A
    param_c.add_dependency(param_b)  # C 依赖 B
    param_d.add_dependency(param_c)  # D 依赖 C
    
    chain_node.add_parameter(param_a)
    chain_node.add_parameter(param_b)
    chain_node.add_parameter(param_c)
    chain_node.add_parameter(param_d)
    
    graph.add_node(chain_node)
    id_mapper.register_node(chain_node.id, chain_node.name)
    
    print("依赖链结构: A -> B -> C -> D")
    
    # 测试每个参数的依赖情况
    params = [param_a, param_b, param_c, param_d]
    param_names = ['A', 'B', 'C', 'D']
    
    for param, name in zip(params, param_names):
        has_deps, dep_list = check_parameter_has_dependents(param)
        print(f"{name} 是否被依赖: {has_deps}")
        if has_deps:
            for dep in dep_list:
                print(f"   └── 被 {dep['param_name']} 依赖")
    
    # 验证依赖关系
    assert check_parameter_has_dependents(param_a)[0], "A应该被B依赖"
    assert check_parameter_has_dependents(param_b)[0], "B应该被C依赖"
    assert check_parameter_has_dependents(param_c)[0], "C应该被D依赖"
    assert not check_parameter_has_dependents(param_d)[0], "D不应该被任何参数依赖"
    
    print("✅ 依赖链检查测试通过！")

if __name__ == "__main__":
    try:
        test_data = test_parameter_dependency_deletion_restriction()
        test_dependency_chain()
        print("\n🎉 所有测试通过！依赖删除限制功能正常工作。")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc() 