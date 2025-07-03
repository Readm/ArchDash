#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T423 - 测试
从原始测试文件分离出的独立测试
"""

import sys
import os
from app import check_parameter_has_dependents, check_node_has_dependents, graph
from models import Node, Parameter

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

if __name__ == "__main__":
    test_node_deletion_restriction()
    print("✅ T423 测试通过")
