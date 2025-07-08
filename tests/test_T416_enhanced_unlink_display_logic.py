#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T416 - 测试
从原始测试文件分离出的独立测试
"""

import sys
import os
from models import *
import traceback

def test_enhanced_unlink_display_logic():
    """测试增强的unlink显示逻辑"""
    print("🔬 测试增强的unlink显示逻辑")
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
    
    # 创建无依赖参数
    standalone_param = Parameter("独立参数", 100.0, "unit")
    calc_node.add_parameter(standalone_param)
    
    # 设置计算图关联
    for node in graph.nodes.values():
        for param in node.parameters:
            param.set_graph(graph)
    
    print("1. 测试显示逻辑：")
    print(f"   area有依赖且unlinked=False -> 应该不显示按钮")
    should_show_area = area.calculation_func and area.dependencies and getattr(area, 'unlinked', False)
    print(f"   area显示按钮: {should_show_area}")
    assert not should_show_area, "有依赖但未unlinked不应显示按钮"
    
    print(f"   length无依赖 -> 应该不显示按钮")
    should_show_length = length.calculation_func and length.dependencies and getattr(length, 'unlinked', False)
    print(f"   length显示按钮: {should_show_length}")
    assert not should_show_length, "无依赖参数不应显示按钮"
    
    print(f"   standalone_param无依赖 -> 应该不显示按钮")
    should_show_standalone = standalone_param.calculation_func and standalone_param.dependencies and getattr(standalone_param, 'unlinked', False)
    print(f"   standalone_param显示按钮: {should_show_standalone}")
    assert not should_show_standalone, "无依赖参数不应显示按钮"
    
    print("\n2. 设置area为unlinked后：")
    area.set_manual_value(100.0)
    should_show_area_unlinked = area.calculation_func and area.dependencies and getattr(area, 'unlinked', False)
    print(f"   area显示按钮: {should_show_area_unlinked}")
    assert should_show_area_unlinked, "有依赖且unlinked=True应该显示按钮"
    
    print("✅ 显示逻辑测试通过！")

if __name__ == "__main__":
    test_enhanced_unlink_display_logic()
    print("✅ T416 测试通过")
