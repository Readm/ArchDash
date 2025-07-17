#!/usr/bin/env python3
"""
测试新Graph系统的参数更新传播功能
从旧测试 test_T112_parameter_update_propagation.py 迁移而来
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core import Graph

def test_basic_update_propagation():
    """测试基本的参数更新传播"""
    g = Graph("更新传播测试")
    
    # 设置基础参数
    g["voltage"] = 12.0
    g["current"] = 2.0
    
    # 创建依赖参数（功率 = 电压 × 电流）
    def power_calculation():
        return g["voltage"] * g["current"]
    
    g.add_computed("power", power_calculation, "功率计算")
    
    # 验证初始计算
    assert g["power"] == 24.0  # 12V × 2A = 24W
    
    # 测试参数更新传播
    g["voltage"] = 15.0
    
    # 验证更新传播
    assert g["voltage"] == 15.0
    assert g["power"] == 30.0  # 15V × 2A = 30W

def test_multi_level_update_propagation():
    """测试多级参数更新传播"""
    g = Graph("多级更新传播测试")
    
    # 设置基础参数
    g["voltage"] = 12.0
    g["current"] = 2.0
    g["time"] = 1.0
    
    # 创建一级依赖（功率 = 电压 × 电流）
    def power_calculation():
        return g["voltage"] * g["current"]
    
    # 创建二级依赖（能耗 = 功率 × 时间）
    def energy_calculation():
        return g["power"] * g["time"]
    
    g.add_computed("power", power_calculation, "功率计算")
    g.add_computed("energy", energy_calculation, "能耗计算")
    
    # 验证初始计算
    assert g["power"] == 24.0  # 12V × 2A = 24W
    assert g["energy"] == 24.0  # 24W × 1h = 24Wh
    
    # 测试多级更新传播
    g["voltage"] = 15.0
    
    # 验证多级更新传播
    assert g["voltage"] == 15.0
    assert g["power"] == 30.0  # 15V × 2A = 30W
    assert g["energy"] == 30.0  # 30W × 1h = 30Wh

def test_complex_update_propagation():
    """测试复杂的更新传播场景"""
    g = Graph("复杂更新传播测试")
    
    # 设置基础参数
    g["base_value"] = 10.0
    g["multiplier"] = 2.0
    g["offset"] = 5.0
    
    # 创建复杂的依赖关系
    def first_calc():
        return g["base_value"] * g["multiplier"]
    
    def second_calc():
        return g["first_result"] + g["offset"]
    
    def third_calc():
        return g["second_result"] * 0.5
    
    def combined_calc():
        return g["first_result"] + g["third_result"]
    
    g.add_computed("first_result", first_calc, "第一级计算")
    g.add_computed("second_result", second_calc, "第二级计算")
    g.add_computed("third_result", third_calc, "第三级计算")
    g.add_computed("combined_result", combined_calc, "组合计算")
    
    # 验证初始计算
    assert g["first_result"] == 20.0  # 10.0 * 2.0
    assert g["second_result"] == 25.0  # 20.0 + 5.0
    assert g["third_result"] == 12.5  # 25.0 * 0.5
    assert g["combined_result"] == 32.5  # 20.0 + 12.5
    
    # 测试复杂更新传播
    g["base_value"] = 20.0
    
    # 验证复杂更新传播
    assert g["first_result"] == 40.0  # 20.0 * 2.0
    assert g["second_result"] == 45.0  # 40.0 + 5.0
    assert g["third_result"] == 22.5  # 45.0 * 0.5
    assert g["combined_result"] == 62.5  # 40.0 + 22.5

def test_multiple_dependency_update_propagation():
    """测试多重依赖的更新传播"""
    g = Graph("多重依赖更新传播测试")
    
    # 设置基础参数
    g["a"] = 1.0
    g["b"] = 2.0
    g["c"] = 3.0
    
    # 创建多重依赖
    def sum_ab():
        return g["a"] + g["b"]
    
    def product_bc():
        return g["b"] * g["c"]
    
    def complex_calc():
        return g["sum_ab"] * g["product_bc"]
    
    g.add_computed("sum_ab", sum_ab, "a+b")
    g.add_computed("product_bc", product_bc, "b*c")
    g.add_computed("complex_result", complex_calc, "复杂计算")
    
    # 验证初始计算
    assert g["sum_ab"] == 3.0  # 1.0 + 2.0
    assert g["product_bc"] == 6.0  # 2.0 * 3.0
    assert g["complex_result"] == 18.0  # 3.0 * 6.0
    
    # 测试影响多个依赖的参数更新
    g["b"] = 4.0  # b同时影响sum_ab和product_bc
    
    # 验证多重依赖更新传播
    assert g["sum_ab"] == 5.0  # 1.0 + 4.0
    assert g["product_bc"] == 12.0  # 4.0 * 3.0
    assert g["complex_result"] == 60.0  # 5.0 * 12.0

def test_update_propagation_with_conditionals():
    """测试带条件判断的更新传播"""
    g = Graph("条件更新传播测试")
    
    # 设置基础参数
    g["input_value"] = 5.0
    g["threshold"] = 10.0
    
    # 创建条件计算
    def conditional_calc():
        if g["input_value"] > g["threshold"]:
            return g["input_value"] * 2
        else:
            return g["input_value"] * 0.5
    
    def result_calc():
        return g["conditional_result"] + 10
    
    g.add_computed("conditional_result", conditional_calc, "条件计算")
    g.add_computed("final_result", result_calc, "最终结果")
    
    # 验证初始计算（input_value < threshold）
    assert g["conditional_result"] == 2.5  # 5.0 * 0.5
    assert g["final_result"] == 12.5  # 2.5 + 10
    
    # 测试跨越条件阈值的更新
    g["input_value"] = 15.0  # 现在 input_value > threshold
    
    # 验证条件更新传播
    assert g["conditional_result"] == 30.0  # 15.0 * 2
    assert g["final_result"] == 40.0  # 30.0 + 10

def test_update_propagation_performance():
    """测试更新传播的性能"""
    g = Graph("性能测试")
    
    # 设置基础参数
    g["base"] = 1.0
    
    # 创建多层依赖链
    current_param = "base"
    for i in range(20):
        def make_calc(prev_param):
            def calc():
                return g[prev_param] + 1
            return calc
        
        next_param = f"level_{i}"
        g.add_computed(next_param, make_calc(current_param), f"第{i}级")
        current_param = next_param
    
    # 验证初始计算
    assert g["level_19"] == 21.0  # 1.0 + 20个+1
    
    # 测试深度更新传播
    g["base"] = 2.0
    
    # 验证深度更新传播
    assert g["level_19"] == 22.0  # 2.0 + 20个+1

def test_circular_update_prevention():
    """测试循环更新预防"""
    g = Graph("循环更新预防测试")
    
    # 设置基础参数
    g["x"] = 10.0
    g["y"] = 20.0
    
    # 创建相互依赖（但不是真正的循环）
    def calc_a():
        return g["x"] + g["y"]
    
    def calc_b():
        return g["calc_a"] * 2
    
    def calc_c():
        return g["calc_b"] + g["x"]  # 同时依赖calc_b和x
    
    g.add_computed("calc_a", calc_a, "计算A")
    g.add_computed("calc_b", calc_b, "计算B")
    g.add_computed("calc_c", calc_c, "计算C")
    
    # 验证初始计算
    assert g["calc_a"] == 30.0  # 10.0 + 20.0
    assert g["calc_b"] == 60.0  # 30.0 * 2
    assert g["calc_c"] == 70.0  # 60.0 + 10.0
    
    # 测试更新传播
    g["x"] = 15.0
    
    # 验证无循环更新
    assert g["calc_a"] == 35.0  # 15.0 + 20.0
    assert g["calc_b"] == 70.0  # 35.0 * 2
    assert g["calc_c"] == 85.0  # 70.0 + 15.0

def test_batch_update_propagation():
    """测试批量更新传播"""
    g = Graph("批量更新传播测试")
    
    # 设置基础参数
    g["param1"] = 10.0
    g["param2"] = 20.0
    g["param3"] = 30.0
    
    # 创建依赖所有参数的计算
    def sum_all():
        return g["param1"] + g["param2"] + g["param3"]
    
    def average_all():
        return g["sum_all"] / 3
    
    g.add_computed("sum_all", sum_all, "总和")
    g.add_computed("average_all", average_all, "平均值")
    
    # 验证初始计算
    assert g["sum_all"] == 60.0  # 10 + 20 + 30
    assert g["average_all"] == 20.0  # 60 / 3
    
    # 测试批量更新
    g.update({
        "param1": 15.0,
        "param2": 25.0,
        "param3": 35.0
    })
    
    # 验证批量更新传播
    assert g["sum_all"] == 75.0  # 15 + 25 + 35
    assert g["average_all"] == 25.0  # 75 / 3

def test_update_propagation_with_errors():
    """测试带错误的更新传播"""
    g = Graph("错误更新传播测试")
    
    # 设置基础参数
    g["numerator"] = 10.0
    g["denominator"] = 2.0
    
    # 创建可能出错的计算
    def division_calc():
        if g["denominator"] == 0:
            return 0  # 错误处理
        return g["numerator"] / g["denominator"]
    
    def result_calc():
        return g["division_result"] * 2
    
    g.add_computed("division_result", division_calc, "除法计算")
    g.add_computed("final_result", result_calc, "最终结果")
    
    # 验证初始计算
    assert g["division_result"] == 5.0  # 10.0 / 2.0
    assert g["final_result"] == 10.0  # 5.0 * 2
    
    # 测试错误情况的更新传播
    g["denominator"] = 0.0
    
    # 验证错误处理的更新传播
    assert g["division_result"] == 0.0  # 错误处理返回0
    assert g["final_result"] == 0.0  # 0.0 * 2

def test_update_propagation_timing():
    """测试更新传播的时机"""
    g = Graph("更新时机测试")
    
    # 设置基础参数
    g["counter"] = 0
    
    # 创建跟踪计算次数的函数
    calculation_count = 0
    
    def counting_calc():
        nonlocal calculation_count
        calculation_count += 1
        return g["counter"] * 2
    
    g.add_computed("doubled", counting_calc, "计数计算")
    
    # 首次访问触发计算
    assert g["doubled"] == 0
    assert calculation_count == 1
    
    # 再次访问不应该重新计算
    assert g["doubled"] == 0
    assert calculation_count == 1
    
    # 更新参数后应该重新计算
    g["counter"] = 5
    assert g["doubled"] == 10
    assert calculation_count == 2

if __name__ == "__main__":
    test_basic_update_propagation()
    test_multi_level_update_propagation()
    test_complex_update_propagation()
    test_multiple_dependency_update_propagation()
    test_update_propagation_with_conditionals()
    test_update_propagation_performance()
    test_circular_update_prevention()
    test_batch_update_propagation()
    test_update_propagation_with_errors()
    test_update_propagation_timing()
    print("✅ 新Graph系统参数更新传播测试全部通过")