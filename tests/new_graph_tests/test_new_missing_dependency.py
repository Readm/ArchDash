#!/usr/bin/env python3
"""
测试新Graph系统的缺失依赖处理
从旧测试 test_T108_missing_dependency.py 迁移而来
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core import Graph

def test_missing_parameter_dependency():
    """测试缺失参数依赖的情况"""
    g = Graph("缺失依赖测试")
    
    # 设置一个基础参数为None（缺失值）
    g["param1"] = None
    
    # 创建依赖param1的计算参数
    def calculation_with_missing_dep():
        return g["param1"] * 2  # 这应该处理None值
    
    g.add_computed("param2", calculation_with_missing_dep, "依赖缺失值的计算")
    
    # 测试访问依赖缺失值的计算参数时，系统返回0（错误处理）
    assert g["param2"] == 0

def test_nonexistent_parameter_dependency():
    """测试不存在参数依赖的情况"""
    g = Graph("不存在参数测试")
    
    # 创建依赖不存在参数的计算函数
    def calculation_with_nonexistent_dep():
        return g["nonexistent_param"] * 2
    
    g.add_computed("dependent_param", calculation_with_nonexistent_dep, "依赖不存在参数")
    
    # 测试访问依赖不存在参数的计算参数时，系统返回0（错误处理）
    assert g["dependent_param"] == 0

def test_missing_dependency_in_chain():
    """测试依赖链中缺失依赖的情况"""
    g = Graph("依赖链缺失测试")
    
    # 设置基础参数，其中一个缺失
    g["param1"] = 10.0
    g["param2"] = None  # 缺失值
    
    # 创建依赖链
    def first_calculation():
        return g["param1"] + g["param2"]  # param2缺失
    
    def second_calculation():
        return g["first_result"] * 2
    
    g.add_computed("first_result", first_calculation, "第一级计算")
    g.add_computed("second_result", second_calculation, "第二级计算")
    
    # 测试依赖链中的缺失依赖，系统返回0（错误处理）
    assert g["first_result"] == 0
    assert g["second_result"] == 0

def test_missing_dependency_with_error_handling():
    """测试带错误处理的缺失依赖"""
    g = Graph("错误处理缺失依赖测试")
    
    # 设置缺失参数
    g["param1"] = None
    
    # 创建带错误处理的计算函数
    def safe_calculation():
        try:
            value = g["param1"]
            if value is None:
                return 0.0  # 默认值
            return value * 2
        except (TypeError, ValueError):
            return 0.0  # 错误时返回默认值
    
    g.add_computed("safe_result", safe_calculation, "安全计算")
    
    # 验证错误处理正常工作
    assert g["safe_result"] == 0.0

def test_missing_dependency_detection():
    """测试缺失依赖检测机制"""
    g = Graph("依赖检测测试")
    
    # 设置一些参数，包括缺失的
    g["valid_param"] = 10.0
    g["missing_param"] = None
    
    # 创建依赖多个参数的计算，其中一个缺失
    def multi_dependency_calculation():
        valid_val = g["valid_param"]
        missing_val = g["missing_param"]
        
        if valid_val is None or missing_val is None:
            raise ValueError("存在缺失的依赖参数")
        
        return valid_val + missing_val
    
    g.add_computed("multi_result", multi_dependency_calculation, "多依赖计算")
    
    # 测试缺失依赖检测，系统返回0（错误处理）
    assert g["multi_result"] == 0

def test_missing_dependency_update_propagation():
    """测试缺失依赖的更新传播"""
    g = Graph("缺失依赖更新测试")
    
    # 设置初始参数
    g["param1"] = 5.0
    
    # 创建依赖链
    def first_calculation():
        return g["param1"] * 2
    
    def second_calculation():
        return g["first_result"] + 10
    
    g.add_computed("first_result", first_calculation, "第一级")
    g.add_computed("second_result", second_calculation, "第二级")
    
    # 验证初始状态正常
    assert g["first_result"] == 10.0
    assert g["second_result"] == 20.0
    
    # 将基础参数设为None（缺失）
    g["param1"] = None
    
    # 测试更新传播时的错误处理，系统返回0
    assert g["first_result"] == 0
    assert g["second_result"] == 10  # 0 + 10

def test_partial_missing_dependencies():
    """测试部分缺失依赖的情况"""
    g = Graph("部分缺失依赖测试")
    
    # 设置参数，部分缺失
    g["param1"] = 10.0
    g["param2"] = None
    g["param3"] = 30.0
    
    # 创建依赖所有参数的计算
    def calculation_with_partial_missing():
        p1 = g["param1"]
        p2 = g["param2"]
        p3 = g["param3"]
        
        # 检查缺失依赖
        missing_params = []
        if p1 is None:
            missing_params.append("param1")
        if p2 is None:
            missing_params.append("param2")
        if p3 is None:
            missing_params.append("param3")
        
        if missing_params:
            raise ValueError(f"依赖参数缺失: {', '.join(missing_params)}")
        
        return p1 + p2 + p3
    
    g.add_computed("partial_result", calculation_with_partial_missing, "部分缺失计算")
    
    # 测试部分缺失依赖，系统返回0（错误处理）
    assert g["partial_result"] == 0

def test_missing_dependency_recovery():
    """测试缺失依赖的恢复"""
    g = Graph("依赖恢复测试")
    
    # 设置缺失参数
    g["param1"] = None
    
    # 创建带恢复机制的计算
    def recovery_calculation():
        value = g["param1"]
        if value is None:
            return 0.0
        return value * 2
    
    g.add_computed("recovery_result", recovery_calculation, "恢复计算")
    
    # 验证缺失时的默认值
    assert g["recovery_result"] == 0.0
    
    # 恢复参数值
    g["param1"] = 15.0
    
    # 验证恢复后的计算
    assert g["recovery_result"] == 30.0

def test_missing_dependency_in_complex_graph():
    """测试复杂图中的缺失依赖"""
    g = Graph("复杂图缺失依赖测试")
    
    # 创建复杂的依赖图
    g["base1"] = 10.0
    g["base2"] = None  # 缺失
    g["base3"] = 30.0
    
    # 第一级计算
    def calc1():
        return g["base1"] * 2
    
    def calc2():
        return g["base2"] + 5  # 会因为None而失败
    
    def calc3():
        return g["base3"] / 2
    
    # 第二级计算
    def final_calc():
        return g["calc1"] + g["calc2"] + g["calc3"]
    
    g.add_computed("calc1", calc1, "计算1")
    g.add_computed("calc2", calc2, "计算2")
    g.add_computed("calc3", calc3, "计算3")
    g.add_computed("final", final_calc, "最终计算")
    
    # 验证独立计算的结果
    assert g["calc1"] == 20.0  # 正常
    assert g["calc3"] == 15.0  # 正常
    
    # 验证依赖缺失参数的计算失败，系统返回0
    assert g["calc2"] == 0  # None + 5 会出错，返回0
    
    # final依赖calc2，而calc2返回0，所以final = 20 + 0 + 15 = 35
    assert g["final"] == 35

if __name__ == "__main__":
    test_missing_parameter_dependency()
    test_nonexistent_parameter_dependency()
    test_missing_dependency_in_chain()
    test_missing_dependency_with_error_handling()
    test_missing_dependency_detection()
    test_missing_dependency_update_propagation()
    test_partial_missing_dependencies()
    test_missing_dependency_recovery()
    test_missing_dependency_in_complex_graph()
    print("✅ 新Graph系统缺失依赖处理测试全部通过")