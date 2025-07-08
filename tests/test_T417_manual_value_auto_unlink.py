#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T417 - 测试
从原始测试文件分离出的独立测试
"""

import sys
import os
from models import *
import traceback

def test_manual_value_auto_unlink():
    """测试手动修改值时自动unlink功能"""
    print("\n🔬 测试手动修改值自动unlink功能")
    print("=" * 50)
    
    # 创建测试环境
    graph = CalculationGraph()
    
    input_node = Node("输入")
    base_value = Parameter("基值", 10.0, "unit")
    input_node.add_parameter(base_value)
    graph.add_node(input_node)
    
    calc_node = Node("计算")
    
    # 有依赖的计算参数
    computed_param = Parameter("计算参数", 0.0, "unit",
                             calculation_func="result = dependencies[0].value * 2")
    computed_param.add_dependency(base_value)
    calc_node.add_parameter(computed_param)
    
    # 无依赖的普通参数
    simple_param = Parameter("普通参数", 5.0, "unit")
    calc_node.add_parameter(simple_param)
    
    graph.add_node(calc_node)
    
    # 设置计算图关联
    for node in graph.nodes.values():
        for param in node.parameters:
            param.set_graph(graph)
    
    # 计算初始值
    computed_param.calculate()
    
    print("1. 初始状态：")
    print(f"   computed_param = {computed_param.value}, unlinked = {computed_param.unlinked}")
    print(f"   simple_param = {simple_param.value}, unlinked = {simple_param.unlinked}")
    
    print("\n2. 手动修改有依赖的计算参数：")
    computed_param.set_manual_value(50.0)
    print(f"   computed_param = {computed_param.value}, unlinked = {computed_param.unlinked}")
    assert computed_param.unlinked == True, "有依赖的参数手动设置应该auto unlink"
    
    print("\n3. 手动修改无依赖的普通参数：")
    simple_param.set_manual_value(25.0)
    print(f"   simple_param = {simple_param.value}, unlinked = {simple_param.unlinked}")
    assert simple_param.unlinked == False, "无依赖的参数手动设置不应该unlink"
    
    print("\n4. 手动修改输入参数（无计算函数）：")
    base_value.set_manual_value(15.0)
    print(f"   base_value = {base_value.value}, unlinked = {base_value.unlinked}")
    assert base_value.unlinked == False, "无计算函数的参数不应该unlink"
    
    print("✅ 手动修改值自动unlink测试通过！")

if __name__ == "__main__":
    test_manual_value_auto_unlink()
    print("✅ T417 测试通过")
