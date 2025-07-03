#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T419 - 测试
从原始测试文件分离出的独立测试
"""

import sys
import os
from models import *
import traceback

def test_sensitivity_analysis_auto_unlink_simulation():
    """模拟相关性分析时的自动unlink功能"""
    print("\n🔬 模拟相关性分析自动unlink功能")
    print("=" * 50)
    
    # 创建测试环境，模拟app.py中的perform_sensitivity_analysis逻辑
    graph = CalculationGraph()
    
    input_node = Node("输入")
    x_param = Parameter("X参数", 10.0, "unit")
    input_node.add_parameter(x_param)
    graph.add_node(input_node)
    
    calc_node = Node("计算")
    # 创建一个依赖于x_param的计算参数
    dependent_param = Parameter("依赖参数", 5.0, "unit")
    calc_node.add_parameter(dependent_param)
    
    y_param = Parameter("Y参数", 0.0, "unit",
                       calculation_func="result = dependencies[0].value + dependencies[1].value")
    y_param.add_dependency(x_param)
    y_param.add_dependency(dependent_param)
    calc_node.add_parameter(y_param)
    graph.add_node(calc_node)
    
    # 设置计算图关联
    for node in graph.nodes.values():
        for param in node.parameters:
            param.set_graph(graph)
    
    # 计算初始值
    y_param.calculate()
    
    print("1. 初始状态：")
    print(f"   X参数 = {x_param.value}, unlinked = {x_param.unlinked}")
    print(f"   Y参数 = {y_param.value}, unlinked = {y_param.unlinked}")
    
    print("\n2. 模拟相关性分析开始（X参数有依赖时会被自动unlink）：")
    # 在实际的相关性分析中，如果X参数有计算依赖，会被自动unlink
    # 这里我们给x_param添加一个虚假的计算函数来模拟这种情况
    original_x_calc_func = x_param.calculation_func
    original_x_deps = x_param.dependencies.copy()
    original_x_unlinked = x_param.unlinked
    
    # 模拟X参数有依赖的情况
    x_param.calculation_func = "result = dependencies[0].value"
    x_param.add_dependency(dependent_param)
    
    # 模拟相关性分析中的auto unlink逻辑
    x_was_unlinked = getattr(x_param, 'unlinked', False)
    if x_param.calculation_func and x_param.dependencies and not x_was_unlinked:
        x_param.set_manual_value(x_param.value)  # 保持当前值但断开计算
        print(f"   X参数被自动unlink: unlinked = {x_param.unlinked}")
        assert x_param.unlinked == True, "相关性分析应该自动unlink有依赖的X参数"
    
    print("\n3. 模拟相关性分析结束，恢复状态：")
    # 恢复原始状态
    x_param.calculation_func = original_x_calc_func
    x_param.dependencies.clear()
    for dep in original_x_deps:
        x_param.add_dependency(dep)
    if not original_x_unlinked:
        x_param.unlinked = False
    
    print(f"   X参数恢复后: unlinked = {x_param.unlinked}")
    
    print("✅ 相关性分析自动unlink模拟测试通过！")

if __name__ == "__main__":
    test_sensitivity_analysis_auto_unlink_simulation()
    print("✅ T419 测试通过")
