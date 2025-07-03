#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T402 - 测试
从原始测试文件分离出的独立测试
"""

import sys
import os
import pytest
from models import *

def test_serialization():
    """测试序列化和反序列化"""
    print("\n🔬 测试序列化功能")
    print("=" * 50)
    
    # 创建带有unlinked参数的计算图
    graph = CalculationGraph()
    node = Node("测试节点")
    
    param1 = Parameter("参数1", 10.0, "unit", calculation_func="result = value * 2")
    param1.add_dependency(Parameter("依赖", 5.0, "unit"))
    param1.unlinked = True
    
    param2 = Parameter("参数2", 20.0, "unit")
    
    node.add_parameter(param1)
    node.add_parameter(param2)
    graph.add_node(node)
    
    # 序列化
    data = graph.to_dict()
    print(f"原始参数1 unlinked状态: {param1.unlinked}")
    print(f"序列化数据中的unlinked: {data['nodes'][node.id]['parameters'][0]['unlinked']}")
    
    # 反序列化
    new_graph = CalculationGraph.from_dict(data)
    new_node = list(new_graph.nodes.values())[0]
    new_param1 = new_node.parameters[0]
    
    print(f"反序列化后参数1 unlinked状态: {new_param1.unlinked}")
    assert new_param1.unlinked == True, "Unlinked状态应该被正确恢复"
    
    print("✅ 序列化测试通过！")

if __name__ == "__main__":
    test_serialization()
    print("✅ T402 测试通过")
