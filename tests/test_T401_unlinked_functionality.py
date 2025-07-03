#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T401 - 测试
从原始测试文件分离出的独立测试
"""

import sys
import os
import pytest
from models import *

def test_unlinked_functionality():
    """测试参数断开连接功能"""
    print("🔬 测试参数断开连接功能")
    print("=" * 50)
    
    # 创建计算图和节点
    graph = CalculationGraph()
    
    # 创建输入节点
    input_node = Node("输入参数", "基础输入参数")
    length = Parameter("长度", 10.0, "m")
    width = Parameter("宽度", 5.0, "m")
    input_node.add_parameter(length)
    input_node.add_parameter(width)
    graph.add_node(input_node)
    
    # 创建计算节点
    calc_node = Node("计算结果", "基于输入参数的计算")
    area = Parameter("面积", 0.0, "m²", 
                    calculation_func="result = dependencies[0].value * dependencies[1].value")
    area.add_dependency(length)
    area.add_dependency(width)
    calc_node.add_parameter(area)
    graph.add_node(calc_node)
    
    # 设置计算图关联
    for node in graph.nodes.values():
        for param in node.parameters:
            param.set_graph(graph)
    
    print(f"1. 初始状态:")
    print(f"   长度 = {length.value} m, unlinked = {length.unlinked}")
    print(f"   宽度 = {width.value} m, unlinked = {width.unlinked}")
    print(f"   面积 = {area.value} m², unlinked = {area.unlinked}")
    
    # 计算初始面积
    area.calculate()
    print(f"   计算后面积 = {area.value} m²")
    
    print(f"\n2. 手动修改有依赖的面积参数值:")
    # 手动设置面积值（应该被标记为unlinked）
    area.set_manual_value(100.0)
    print(f"   面积 = {area.value} m², unlinked = {area.unlinked}")
    
    # 尝试自动计算（应该被跳过）
    old_value = area.value
    area.calculate()
    print(f"   计算后面积 = {area.value} m² (应该保持不变)")
    assert area.value == old_value, "Unlinked参数不应该被重新计算"
    assert area.unlinked == True, "参数应该被标记为unlinked"
    
    print(f"\n3. 重新连接参数:")
    # 重新连接并计算
    new_value = area.relink_and_calculate()
    print(f"   重新连接后面积 = {new_value} m², unlinked = {area.unlinked}")
    assert area.unlinked == False, "参数应该被重新连接"
    assert area.value == 50.0, "重新计算的值应该正确"
    
    print(f"\n4. 测试无依赖参数的手动设置:")
    # 设置无依赖参数的值（不应该被标记为unlinked）
    length.set_manual_value(15.0)
    print(f"   长度 = {length.value} m, unlinked = {length.unlinked}")
    assert length.unlinked == False, "无依赖参数不应该被标记为unlinked"
    
    print(f"\n5. 测试级联更新:")
    # 修改输入参数，检查面积是否自动更新
    print(f"   宽度修改前，面积为: {area.value}")
    print(f"   将宽度修改为 8.0...")
    graph.set_parameter_value(width, 8.0) # 通过图来设置值，以触发传播
    print(f"   宽度修改为 = {width.value} m")
    print(f"   面积自动更新为 = {area.value} m² (应该是 120.0)")
    assert area.value == 120.0, "级联计算应该正确"
    
    print(f"\n✅ 所有测试通过！")

if __name__ == "__main__":
    test_unlinked_functionality()
    print("✅ T401 测试通过")
