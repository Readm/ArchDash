#!/usr/bin/env python3
"""
测试新Graph系统的循环依赖检测功能
从旧测试 test_T113_circular_dependency_detection.py 迁移而来
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core import Graph

def test_simple_circular_dependency_detection():
    """测试简单的循环依赖检测"""
    g = Graph("简单循环依赖测试")
    
    # 创建基础参数
    g["base"] = 10.0
    
    # 首先创建两个不循环的计算参数
    def calc_a():
        return g["base"] + 1
    
    def calc_b():
        return g["base"] * 2
    
    g.add_computed("calc_a", calc_a, "A计算")
    g.add_computed("calc_b", calc_b, "B计算")
    
    # 验证正常工作
    assert g["calc_a"] == 11.0
    assert g["calc_b"] == 20.0
    
    # 现在修改calc_a来创建循环依赖：calc_a 依赖 calc_b，然后修改calc_b依赖calc_a
    def calc_a_circular():
        return g["calc_b"] + 1
    
    def calc_b_circular():
        return g["calc_a"] * 2
    
    # 修改计算函数来创建循环
    g._computed_parameters["calc_a"].func = calc_a_circular
    g._computed_parameters["calc_b"].func = calc_b_circular
    
    # 使两个参数失效
    g._computed_parameters["calc_a"].invalidate()
    g._computed_parameters["calc_b"].invalidate()
    
    # 尝试访问会导致循环的参数，应该检测到循环并抛出异常
    with pytest.raises(ValueError, match="检测到循环依赖"):
        _ = g["calc_a"]

def test_indirect_circular_dependency():
    """测试间接循环依赖检测"""
    g = Graph("间接循环依赖测试")
    
    # 创建基础参数
    g["base"] = 10.0
    
    # 创建计算链：base -> calc_a -> calc_b -> calc_c
    def calc_a():
        return g["base"] * 2
    
    def calc_b():
        return g["calc_a"] + 5
    
    def calc_c():
        return g["calc_b"] / 2
    
    g.add_computed("calc_a", calc_a, "A计算")
    g.add_computed("calc_b", calc_b, "B计算")
    g.add_computed("calc_c", calc_c, "C计算")
    
    # 验证正常计算链工作
    assert g["calc_a"] == 20.0
    assert g["calc_b"] == 25.0
    assert g["calc_c"] == 12.5
    
    # 现在尝试创建间接循环：calc_a 依赖 calc_c，同时保持原有的依赖链
    def calc_a_circular():
        return g["calc_c"] + g["base"]  # 这会创建循环：calc_a -> calc_c -> calc_b -> calc_a
    
    # 重新定义calc_a来创建循环
    g._computed_parameters["calc_a"].func = calc_a_circular
    g._computed_parameters["calc_a"].invalidate()
    g._computed_parameters["calc_b"].invalidate()
    g._computed_parameters["calc_c"].invalidate()
    
    # 尝试访问会导致循环的参数
    with pytest.raises(ValueError, match="检测到循环依赖"):
        _ = g["calc_a"]

def test_self_dependency():
    """测试自依赖检测"""
    g = Graph("自依赖测试")
    
    # 创建基础参数
    g["base"] = 5.0
    
    # 尝试创建自依赖，应该在add_computed时就检测到
    def self_calc():
        return g["self_param"] + 1  # 自己依赖自己
    
    # 应该在添加时就检测到循环依赖
    with pytest.raises(ValueError, match="检测到循环依赖"):
        g.add_computed("self_param", self_calc, "自依赖")

def test_complex_circular_dependency():
    """测试复杂的循环依赖检测"""
    g = Graph("复杂循环依赖测试")
    
    # 创建基础参数
    g["input1"] = 10.0
    g["input2"] = 20.0
    
    # 创建复杂的依赖网络
    def calc_a():
        return g["input1"] + g["input2"]
    
    def calc_b():
        return g["calc_a"] * 2
    
    def calc_c():
        return g["calc_b"] + g["input1"]
    
    def calc_d():
        return g["calc_c"] - 5
    
    g.add_computed("calc_a", calc_a, "A计算")
    g.add_computed("calc_b", calc_b, "B计算")
    g.add_computed("calc_c", calc_c, "C计算")
    g.add_computed("calc_d", calc_d, "D计算")
    
    # 验证正常计算
    assert g["calc_a"] == 30.0
    assert g["calc_b"] == 60.0
    assert g["calc_c"] == 70.0
    assert g["calc_d"] == 65.0
    
    # 现在创建循环：calc_a 依赖 calc_d
    def calc_a_circular():
        return g["calc_d"] + g["input2"]  # 创建循环
    
    g._computed_parameters["calc_a"].func = calc_a_circular
    g._computed_parameters["calc_a"].invalidate()
    
    # 应该检测到循环依赖
    with pytest.raises(ValueError, match="检测到循环依赖"):
        _ = g["calc_a"]

def test_parameter_update_with_circular_dependency():
    """测试参数更新时的循环依赖检测"""
    g = Graph("参数更新循环依赖测试")
    
    # 创建基础参数
    g["base"] = 10.0
    
    # 创建计算参数
    def calc_x():
        return g["base"] * 2
    
    g.add_computed("calc_x", calc_x, "X计算")
    
    # 验证正常工作
    assert g["calc_x"] == 20.0
    
    # 现在创建循环依赖
    def calc_y():
        return g["calc_x"] + 5
    
    def calc_x_circular():
        return g["calc_y"] + g["base"]  # 创建循环
    
    g.add_computed("calc_y", calc_y, "Y计算")
    g._computed_parameters["calc_x"].func = calc_x_circular
    g._computed_parameters["calc_x"].invalidate()
    
    # 更新基础参数，应该检测到循环依赖
    with pytest.raises(ValueError, match="检测到循环依赖"):
        g["base"] = 15.0

def test_circular_dependency_detection_method():
    """测试循环依赖检测方法"""
    g = Graph("循环依赖检测方法测试")
    
    # 创建无循环的依赖图
    g["input"] = 10.0
    
    def calc_a():
        return g["input"] * 2
    
    def calc_b():
        return g["calc_a"] + 5
    
    g.add_computed("calc_a", calc_a, "A计算")
    g.add_computed("calc_b", calc_b, "B计算")
    
    # 应该没有循环依赖
    cycles = g.detect_circular_dependencies()
    assert len(cycles) == 0
    
    # 现在创建循环依赖
    def calc_a_circular():
        return g["calc_b"] + g["input"]  # 创建循环
    
    g._computed_parameters["calc_a"].func = calc_a_circular
    
    # 重新构建依赖图
    g._computed_parameters["calc_a"].dependencies = set()
    g._computed_parameters["calc_a"].compute()
    g._update_dependency_graph("calc_a", g._computed_parameters["calc_a"].dependencies)
    
    # 现在应该检测到循环依赖
    cycles = g.detect_circular_dependencies()
    assert len(cycles) > 0

def test_multiple_circular_dependencies():
    """测试多个循环依赖"""
    g = Graph("多循环依赖测试")
    
    # 创建基础参数
    g["base1"] = 10.0
    g["base2"] = 20.0
    
    # 创建第一个循环：calc_a <-> calc_b
    def calc_a():
        return g["calc_b"] + g["base1"]
    
    def calc_b():
        return g["calc_a"] * 2
    
    g.add_computed("calc_a", calc_a, "A计算")
    g.add_computed("calc_b", calc_b, "B计算")
    
    # 应该检测到循环依赖
    with pytest.raises(ValueError, match="检测到循环依赖"):
        _ = g["calc_a"]

def test_circular_dependency_with_error_handling():
    """测试循环依赖检测的错误处理"""
    g = Graph("循环依赖错误处理测试")
    
    # 创建基础参数
    g["base"] = 10.0
    
    # 创建会产生循环的计算
    def calc_circular():
        return g["calc_circular"] + 1  # 自依赖
    
    # 测试错误信息
    try:
        g.add_computed("calc_circular", calc_circular, "循环计算")
        assert False, "应该抛出循环依赖异常"
    except ValueError as e:
        assert "检测到循环依赖" in str(e)
        assert "calc_circular" in str(e)

def test_dependency_graph_integrity_after_circular_detection():
    """测试循环依赖检测后依赖图的完整性"""
    g = Graph("依赖图完整性测试")
    
    # 创建基础参数
    g["base"] = 10.0
    
    # 创建正常的计算
    def calc_normal():
        return g["base"] * 2
    
    g.add_computed("calc_normal", calc_normal, "正常计算")
    
    # 验证正常工作
    assert g["calc_normal"] == 20.0
    
    # 尝试创建循环依赖，应该在add_computed时就被检测到
    def calc_circular():
        return g["calc_circular"] + 1
    
    # 循环依赖应该被检测到
    with pytest.raises(ValueError, match="检测到循环依赖"):
        g.add_computed("calc_circular", calc_circular, "循环计算")
    
    # 正常计算应该仍然工作
    assert g["calc_normal"] == 20.0
    
    # 更新基础参数应该仍然工作
    g["base"] = 15.0
    assert g["calc_normal"] == 30.0

def test_circular_dependency_prevention_in_add_computed():
    """测试在添加计算参数时的循环依赖预防"""
    g = Graph("添加计算参数循环预防测试")
    
    # 创建基础参数
    g["base"] = 10.0
    
    # 创建第一个计算参数
    def calc_a():
        return g["base"] * 2
    
    g.add_computed("calc_a", calc_a, "A计算")
    
    # 尝试添加会创建循环的计算参数
    def calc_b():
        return g["calc_a"] + 5
    
    g.add_computed("calc_b", calc_b, "B计算")
    
    # 现在尝试修改calc_a来创建循环
    def calc_a_circular():
        return g["calc_b"] + g["base"]
    
    # 这应该在访问时检测到循环
    g._computed_parameters["calc_a"].func = calc_a_circular
    g._computed_parameters["calc_a"].invalidate()
    
    with pytest.raises(ValueError, match="检测到循环依赖"):
        _ = g["calc_a"]

if __name__ == "__main__":
    test_simple_circular_dependency_detection()
    test_indirect_circular_dependency()
    test_self_dependency()
    test_circular_dependency_with_error_handling()
    test_dependency_graph_integrity_after_circular_detection()
    print("✅ 新Graph系统循环依赖检测测试全部通过")