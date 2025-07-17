#!/usr/bin/env python3
"""
测试新Graph系统的参数计算功能
从旧测试 test_T103_parameter_calculation.py 迁移而来
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core import Graph

def test_basic_parameter_calculation():
    """测试基础参数计算"""
    g = Graph("计算测试")
    
    # 设置基础参数
    g["param1"] = 10.0
    g["param2"] = 20.0
    
    # 定义计算函数
    def multiply_params():
        return g["param1"] * g["param2"]
    
    # 添加计算参数
    g.add_computed("result", multiply_params, "乘法计算")
    
    # 验证计算结果
    assert g["result"] == 200.0
    
    # 测试参数更新后的重新计算
    g["param1"] = 15.0
    assert g["result"] == 300.0  # 15.0 * 20.0

def test_complex_parameter_calculation():
    """测试复杂参数计算"""
    g = Graph("复杂计算测试")
    
    # 设置基础参数
    g["voltage"] = 12.0
    g["current"] = 2.0
    g["resistance"] = 5.0
    
    # 定义多个计算函数
    def power_calculation():
        return g["voltage"] * g["current"]
    
    def ohm_law_check():
        return g["voltage"] / g["current"]
    
    def efficiency():
        power = g["power"]
        theoretical_power = g["voltage"] * g["voltage"] / g["resistance"]
        return power / theoretical_power if theoretical_power > 0 else 0
    
    # 添加计算参数
    g.add_computed("power", power_calculation, "功率计算")
    g.add_computed("calculated_resistance", ohm_law_check, "欧姆定律验证")
    g.add_computed("efficiency", efficiency, "效率计算")
    
    # 验证计算结果
    assert g["power"] == 24.0  # 12.0 * 2.0
    assert g["calculated_resistance"] == 6.0  # 12.0 / 2.0
    assert abs(g["efficiency"] - 0.8333333333333334) < 1e-10  # 24.0 / (12.0*12.0/5.0)

def test_nested_parameter_calculation():
    """测试嵌套参数计算"""
    g = Graph("嵌套计算测试")
    
    # 设置基础参数
    g["base_value"] = 5.0
    g["multiplier"] = 2.0
    g["offset"] = 3.0
    
    # 定义分层计算
    def first_level():
        return g["base_value"] * g["multiplier"]
    
    def second_level():
        return g["first_result"] + g["offset"]
    
    def third_level():
        return g["second_result"] * 2
    
    # 添加计算参数
    g.add_computed("first_result", first_level, "第一级计算")
    g.add_computed("second_result", second_level, "第二级计算")
    g.add_computed("third_result", third_level, "第三级计算")
    
    # 验证计算结果
    assert g["first_result"] == 10.0  # 5.0 * 2.0
    assert g["second_result"] == 13.0  # 10.0 + 3.0
    assert g["third_result"] == 26.0  # 13.0 * 2
    
    # 测试基础值变化的级联更新
    g["base_value"] = 10.0
    assert g["first_result"] == 20.0  # 10.0 * 2.0
    assert g["second_result"] == 23.0  # 20.0 + 3.0
    assert g["third_result"] == 46.0  # 23.0 * 2

def test_calculation_with_error_handling():
    """测试计算过程中的错误处理"""
    g = Graph("错误处理测试")
    
    # 设置基础参数
    g["numerator"] = 10.0
    g["denominator"] = 2.0
    
    # 定义可能出错的计算函数
    def division_calculation():
        denominator = g["denominator"]
        if denominator == 0:
            return 0  # 简单的错误处理
        return g["numerator"] / denominator
    
    # 添加计算参数
    g.add_computed("division_result", division_calculation, "除法计算")
    
    # 正常情况验证
    assert g["division_result"] == 5.0  # 10.0 / 2.0
    
    # 测试除零情况
    g["denominator"] = 0.0
    assert g["division_result"] == 0  # 错误处理返回0

def test_calculation_with_math_functions():
    """测试使用数学函数的计算"""
    import math
    
    g = Graph("数学函数测试")
    
    # 设置基础参数
    g["angle_degrees"] = 45.0
    g["radius"] = 10.0
    
    # 定义数学计算函数
    def sin_calculation():
        angle_radians = math.radians(g["angle_degrees"])
        return math.sin(angle_radians)
    
    def circle_area():
        return math.pi * g["radius"] ** 2
    
    def hypotenuse():
        sin_value = g["sin_value"]
        return g["radius"] / sin_value if sin_value != 0 else 0
    
    # 添加计算参数
    g.add_computed("sin_value", sin_calculation, "正弦计算")
    g.add_computed("area", circle_area, "圆面积计算")
    g.add_computed("hypotenuse", hypotenuse, "斜边计算")
    
    # 验证计算结果
    assert abs(g["sin_value"] - math.sin(math.radians(45.0))) < 1e-10
    assert abs(g["area"] - math.pi * 100) < 1e-10
    assert abs(g["hypotenuse"] - (10.0 / math.sin(math.radians(45.0)))) < 1e-10

def test_calculation_performance():
    """测试计算性能"""
    g = Graph("性能测试")
    
    # 设置基础参数
    g["input_value"] = 1.0
    
    # 创建多个计算层级
    for i in range(10):
        def make_calculation(level):
            def calculation():
                if level == 0:
                    return g["input_value"] * 2
                else:
                    return g[f"level_{level-1}"] + 1
            return calculation
        
        g.add_computed(f"level_{i}", make_calculation(i), f"第{i}级计算")
    
    # 验证最终结果
    assert g["level_9"] == 11.0  # ((1.0 * 2) + 1) + 1 + ... (8次+1)
    
    # 测试输入变化的传播性能
    g["input_value"] = 5.0
    assert g["level_9"] == 19.0  # ((5.0 * 2) + 1) + 1 + ... (8次+1)

if __name__ == "__main__":
    test_basic_parameter_calculation()
    test_complex_parameter_calculation()
    test_nested_parameter_calculation()
    test_calculation_with_error_handling()
    test_calculation_with_math_functions()
    test_calculation_performance()
    print("✅ 新Graph系统参数计算测试全部通过")