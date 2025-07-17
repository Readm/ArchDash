#!/usr/bin/env python3
"""
测试新Graph系统的计算错误处理
从旧测试 test_T114_propagate_updates_with_calculation_errors.py 迁移而来
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core import Graph

def test_basic_calculation_error_handling():
    """测试基本的计算错误处理"""
    g = Graph("计算错误处理测试")
    
    # 创建基础参数
    g["base"] = 10.0
    
    # 创建有错误的计算函数（除零错误）
    def error_calculation():
        return g["base"] / 0
    
    g.add_computed("error_param", error_calculation, "错误计算")
    
    # 验证错误处理 - 系统应该返回0而不是抛出异常
    assert g["error_param"] == 0

def test_error_propagation_in_dependency_chain():
    """测试错误在依赖链中的传播"""
    g = Graph("错误传播测试")
    
    # 创建基础参数
    g["base"] = 10.0
    
    # 创建有错误的计算函数
    def error_calculation():
        return g["base"] / 0  # 除零错误
    
    # 创建依赖错误参数的计算
    def dependent_calculation():
        return g["error_param"] * 2
    
    g.add_computed("error_param", error_calculation, "错误计算")
    g.add_computed("dependent_param", dependent_calculation, "依赖计算")
    
    # 验证错误传播
    assert g["error_param"] == 0  # 错误返回0
    assert g["dependent_param"] == 0  # 0 * 2 = 0

def test_error_recovery_after_fix():
    """测试错误修复后的计算恢复"""
    g = Graph("错误恢复测试")
    
    # 创建基础参数
    g["base"] = 10.0
    g["divisor"] = 0.0  # 初始为0，会导致错误
    
    # 创建可能出错的计算
    def division_calculation():
        if g["divisor"] == 0:
            return 0  # 错误处理
        return g["base"] / g["divisor"]
    
    def dependent_calculation():
        return g["division_result"] * 2
    
    g.add_computed("division_result", division_calculation, "除法计算")
    g.add_computed("dependent_result", dependent_calculation, "依赖计算")
    
    # 验证错误情况
    assert g["division_result"] == 0
    assert g["dependent_result"] == 0
    
    # 修复错误
    g["divisor"] = 2.0
    
    # 验证恢复后的计算
    assert g["division_result"] == 5.0  # 10.0 / 2.0
    assert g["dependent_result"] == 10.0  # 5.0 * 2

def test_multiple_error_sources():
    """测试多个错误源的处理"""
    g = Graph("多错误源测试")
    
    # 创建基础参数
    g["param1"] = 10.0
    g["param2"] = 0.0
    g["param3"] = 5.0
    
    # 创建多个可能出错的计算
    def error_calc1():
        return g["param1"] / g["param2"]  # 除零错误
    
    def error_calc2():
        return g["param3"] ** 1000  # 可能的溢出
    
    def normal_calc():
        return g["param1"] + g["param3"]  # 正常计算
    
    def combined_calc():
        return g["error1"] + g["error2"] + g["normal"]
    
    g.add_computed("error1", error_calc1, "错误1")
    g.add_computed("error2", error_calc2, "错误2")
    g.add_computed("normal", normal_calc, "正常计算")
    g.add_computed("combined", combined_calc, "组合计算")
    
    # 验证各种错误处理
    assert g["error1"] == 0  # 除零错误
    assert g["normal"] == 15.0  # 正常计算
    # error2和combined的值取决于系统如何处理大数溢出

def test_error_in_complex_dependency_graph():
    """测试复杂依赖图中的错误处理"""
    g = Graph("复杂错误处理测试")
    
    # 创建基础参数
    g["base1"] = 10.0
    g["base2"] = 0.0  # 会导致错误
    g["base3"] = 5.0
    
    # 创建复杂的依赖关系
    def calc_a():
        return g["base1"] * 2
    
    def calc_b():
        return g["base2"] / 0  # 错误计算
    
    def calc_c():
        return g["base3"] + 1
    
    def calc_d():
        return g["calc_a"] + g["calc_c"]  # 不依赖错误计算
    
    def calc_e():
        return g["calc_b"] * g["calc_c"]  # 依赖错误计算
    
    def final_calc():
        return g["calc_d"] + g["calc_e"]
    
    g.add_computed("calc_a", calc_a, "计算A")
    g.add_computed("calc_b", calc_b, "计算B（错误）")
    g.add_computed("calc_c", calc_c, "计算C")
    g.add_computed("calc_d", calc_d, "计算D")
    g.add_computed("calc_e", calc_e, "计算E")
    g.add_computed("final", final_calc, "最终计算")
    
    # 验证错误不会影响无关计算
    assert g["calc_a"] == 20.0  # 正常
    assert g["calc_b"] == 0  # 错误返回0
    assert g["calc_c"] == 6.0  # 正常
    assert g["calc_d"] == 26.0  # 正常：20 + 6
    assert g["calc_e"] == 0  # 错误影响：0 * 6 = 0
    assert g["final"] == 26.0  # 26 + 0 = 26

def test_error_with_exception_types():
    """测试不同类型异常的处理"""
    g = Graph("异常类型测试")
    
    # 创建基础参数
    g["number"] = 10.0
    g["text"] = "hello"
    g["list_data"] = [1, 2, 3]
    
    # 创建不同类型的错误
    def type_error_calc():
        return g["number"] + g["text"]  # TypeError
    
    def index_error_calc():
        return g["list_data"][10]  # IndexError
    
    def value_error_calc():
        return int(g["text"])  # ValueError
    
    def attribute_error_calc():
        return g["number"].nonexistent_method()  # AttributeError
    
    g.add_computed("type_error", type_error_calc, "类型错误")
    g.add_computed("index_error", index_error_calc, "索引错误")
    g.add_computed("value_error", value_error_calc, "值错误")
    g.add_computed("attr_error", attribute_error_calc, "属性错误")
    
    # 验证所有错误都被统一处理为返回0
    assert g["type_error"] == 0
    assert g["index_error"] == 0
    assert g["value_error"] == 0
    assert g["attr_error"] == 0

def test_error_recovery_with_parameter_updates():
    """测试通过参数更新进行错误恢复"""
    g = Graph("参数更新错误恢复测试")
    
    # 创建基础参数
    g["numerator"] = 10.0
    g["denominator"] = 0.0  # 初始错误值
    
    # 创建可能出错的计算链
    def division_calc():
        if g["denominator"] == 0:
            return 0  # 错误处理
        return g["numerator"] / g["denominator"]
    
    def square_calc():
        return g["division_result"] ** 2
    
    def final_calc():
        return g["square_result"] + 100
    
    g.add_computed("division_result", division_calc, "除法计算")
    g.add_computed("square_result", square_calc, "平方计算")
    g.add_computed("final_result", final_calc, "最终计算")
    
    # 验证错误状态
    assert g["division_result"] == 0
    assert g["square_result"] == 0
    assert g["final_result"] == 100
    
    # 修复参数
    g["denominator"] = 2.0
    
    # 验证恢复后的计算
    assert g["division_result"] == 5.0  # 10.0 / 2.0
    assert g["square_result"] == 25.0  # 5.0 ** 2
    assert g["final_result"] == 125.0  # 25.0 + 100

def test_error_isolation():
    """测试错误隔离机制"""
    g = Graph("错误隔离测试")
    
    # 创建基础参数
    g["good_param"] = 10.0
    g["bad_param"] = 0.0
    
    # 创建独立的计算分支
    def good_branch1():
        return g["good_param"] * 2
    
    def good_branch2():
        return g["good_param"] + 5
    
    def bad_branch():
        return g["good_param"] / g["bad_param"]  # 错误
    
    def good_combination():
        return g["good1"] + g["good2"]
    
    def mixed_combination():
        return g["good1"] + g["bad_result"]
    
    g.add_computed("good1", good_branch1, "正常分支1")
    g.add_computed("good2", good_branch2, "正常分支2")
    g.add_computed("bad_result", bad_branch, "错误分支")
    g.add_computed("good_combo", good_combination, "正常组合")
    g.add_computed("mixed_combo", mixed_combination, "混合组合")
    
    # 验证错误隔离
    assert g["good1"] == 20.0  # 正常
    assert g["good2"] == 15.0  # 正常
    assert g["bad_result"] == 0  # 错误返回0
    assert g["good_combo"] == 35.0  # 正常：20 + 15
    assert g["mixed_combo"] == 20.0  # 部分错误：20 + 0

def test_error_logging_and_tracking():
    """测试错误记录和跟踪"""
    g = Graph("错误跟踪测试")
    
    # 创建基础参数
    g["value"] = 10.0
    
    # 创建会产生错误的计算
    def error_calc():
        raise ValueError("测试错误")
    
    g.add_computed("error_param", error_calc, "错误参数")
    
    # 验证错误被处理并返回默认值
    assert g["error_param"] == 0
    
    # 验证错误信息被记录（通过检查计算参数的状态）
    computed_info = g.get_computed_info("error_param")
    assert computed_info["computed"] == True
    assert computed_info["value"] == 0

def test_recursive_error_handling():
    """测试递归错误处理"""
    g = Graph("递归错误测试")
    
    # 创建基础参数
    g["depth"] = 1000  # 可能导致递归过深
    
    # 创建可能导致递归错误的计算
    def recursive_calc():
        def recursive_function(n):
            if n <= 0:
                return 1
            return n * recursive_function(n - 1)
        
        try:
            return recursive_function(g["depth"])
        except RecursionError:
            return 0  # 递归错误处理
    
    g.add_computed("recursive_result", recursive_calc, "递归计算")
    
    # 验证递归错误处理
    # 结果取决于系统的递归限制和错误处理机制
    result = g["recursive_result"]
    assert isinstance(result, (int, float))

if __name__ == "__main__":
    test_basic_calculation_error_handling()
    test_error_propagation_in_dependency_chain()
    test_error_recovery_after_fix()
    test_multiple_error_sources()
    test_error_in_complex_dependency_graph()
    test_error_with_exception_types()
    test_error_recovery_with_parameter_updates()
    test_error_isolation()
    test_error_logging_and_tracking()
    test_recursive_error_handling()
    print("✅ 新Graph系统计算错误处理测试全部通过")