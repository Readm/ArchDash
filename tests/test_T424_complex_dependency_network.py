#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T424 - 测试
从原始测试文件分离出的独立测试
"""

import sys
import os
from app import check_parameter_has_dependents, check_node_has_dependents, graph
from models import Node, Parameter

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
    test_complex_dependency_network()
    print("✅ T424 测试通过")
