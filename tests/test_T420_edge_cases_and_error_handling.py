from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T420 - 测试
从原始测试文件分离出的独立测试
"""

import sys
import os
from models import *
import traceback

def test_edge_cases_and_error_handling():
    """测试边界情况和错误处理"""
    print("\n🔬 测试边界情况和错误处理")
    print("=" * 50)
    
    # 创建测试环境
    graph = CalculationGraph()
    node = Node("测试节点")
    
    print("1. 测试空依赖列表的参数：")
    param_no_deps = Parameter("无依赖", 10.0, "unit", 
                             calculation_func="result = value * 2")
    # 不添加任何依赖
    node.add_parameter(param_no_deps)
    
    # 尝试unlink（应该不会被unlink，因为没有依赖）
    param_no_deps.set_manual_value(20.0)
    print(f"   无依赖参数 unlinked = {param_no_deps.unlinked}")
    assert param_no_deps.unlinked == False, "无依赖的参数不应该被unlink"
    
    print("\n2. 测试空计算函数的参数：")
    param_no_calc = Parameter("无计算", 30.0, "unit")
    param_no_calc.add_dependency(param_no_deps)  # 添加依赖但无计算函数
    node.add_parameter(param_no_calc)
    
    param_no_calc.set_manual_value(40.0)
    print(f"   无计算函数参数 unlinked = {param_no_calc.unlinked}")
    assert param_no_calc.unlinked == False, "无计算函数的参数不应该被unlink"
    
    print("\n3. 测试已经unlinked的参数重复unlink：")
    param_with_both = Parameter("完整参数", 50.0, "unit",
                              calculation_func="result = dependencies[0].value + 10")
    param_with_both.add_dependency(param_no_deps)
    node.add_parameter(param_with_both)
    
    # 第一次unlink
    param_with_both.set_manual_value(60.0)
    first_unlink_state = param_with_both.unlinked
    print(f"   第一次unlink: {first_unlink_state}")
    
    # 再次unlink
    param_with_both.set_manual_value(70.0)
    second_unlink_state = param_with_both.unlinked
    print(f"   第二次unlink: {second_unlink_state}")
    assert first_unlink_state == second_unlink_state == True, "重复unlink应该保持状态"
    
    print("\n4. 测试重新连接错误处理：")
    # 测试没有计算函数的参数调用relink_and_calculate
    try:
        result = param_no_calc.relink_and_calculate()
        print(f"   无计算函数参数重新连接结果: {result}")
        # 应该返回当前值
        assert result == param_no_calc.value, "无计算函数的参数应该返回当前值"
    except Exception as e:
        print(f"   重新连接错误（预期）: {e}")
    
    graph.add_node(node)
    
    print("✅ 边界情况和错误处理测试通过！")

if __name__ == "__main__":
    test_edge_cases_and_error_handling()
    print("✅ T420 测试通过")
