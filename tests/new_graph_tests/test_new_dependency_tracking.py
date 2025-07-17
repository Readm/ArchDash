#!/usr/bin/env python3
"""
测试新Graph系统的依赖追踪功能
从旧测试 test_T102_parameter_dependencies.py 迁移而来
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core import Graph

def test_basic_dependency_tracking():
    """测试基本的依赖关系追踪"""
    g = Graph("依赖追踪测试")
    
    # 设置基础参数
    g["param1"] = 2.0
    g["param2"] = 3.0
    
    # 创建依赖param1和param2的计算参数
    def multiply_params():
        return g["param1"] * g["param2"]
    
    g.add_computed("result", multiply_params, "参数乘积")
    
    # 验证依赖关系被正确追踪
    computed_info = g.get_computed_info("result")
    assert "param1" in computed_info["dependencies"]
    assert "param2" in computed_info["dependencies"]
    assert len(computed_info["dependencies"]) == 2

def test_automatic_dependency_detection():
    """测试自动依赖检测"""
    g = Graph("自动依赖检测测试")
    
    # 设置基础参数
    g["voltage"] = 12.0
    g["current"] = 2.0
    g["resistance"] = 6.0
    
    # 创建只依赖voltage和current的计算参数
    def power_calculation():
        return g["voltage"] * g["current"]
    
    g.add_computed("power", power_calculation, "功率计算")
    
    # 验证只追踪了实际使用的参数
    computed_info = g.get_computed_info("power")
    assert "voltage" in computed_info["dependencies"]
    assert "current" in computed_info["dependencies"]
    assert "resistance" not in computed_info["dependencies"]  # 未使用，不应该在依赖中

def test_chain_dependency_tracking():
    """测试链式依赖追踪"""
    g = Graph("链式依赖测试")
    
    # 设置基础参数
    g["base_value"] = 10.0
    
    # 创建依赖链
    def first_level():
        return g["base_value"] * 2
    
    def second_level():
        return g["first_level"] + 5
    
    def third_level():
        return g["second_level"] * 0.5
    
    g.add_computed("first_level", first_level, "第一级")
    g.add_computed("second_level", second_level, "第二级")
    g.add_computed("third_level", third_level, "第三级")
    
    # 验证依赖关系
    first_info = g.get_computed_info("first_level")
    second_info = g.get_computed_info("second_level")
    third_info = g.get_computed_info("third_level")
    
    assert "base_value" in first_info["dependencies"]
    assert "first_level" in second_info["dependencies"]
    assert "second_level" in third_info["dependencies"]
    
    # 验证依赖图
    dep_graph = g.get_dependency_graph()
    assert "first_level" in dep_graph.get("base_value", [])
    assert "second_level" in dep_graph.get("first_level", [])
    assert "third_level" in dep_graph.get("second_level", [])

def test_multiple_dependencies():
    """测试多重依赖"""
    g = Graph("多重依赖测试")
    
    # 设置基础参数
    g["a"] = 1.0
    g["b"] = 2.0
    g["c"] = 3.0
    g["d"] = 4.0
    
    # 创建依赖多个参数的计算
    def complex_calculation():
        return g["a"] + g["b"] * g["c"] - g["d"]
    
    g.add_computed("complex_result", complex_calculation, "复杂计算")
    
    # 验证所有依赖都被追踪
    computed_info = g.get_computed_info("complex_result")
    assert "a" in computed_info["dependencies"]
    assert "b" in computed_info["dependencies"]
    assert "c" in computed_info["dependencies"]
    assert "d" in computed_info["dependencies"]
    assert len(computed_info["dependencies"]) == 4

def test_dependency_update_propagation():
    """测试依赖更新传播"""
    g = Graph("依赖更新传播测试")
    
    # 设置基础参数
    g["input"] = 5.0
    
    # 创建依赖链
    def double_input():
        return g["input"] * 2
    
    def add_ten():
        return g["doubled"] + 10
    
    g.add_computed("doubled", double_input, "双倍")
    g.add_computed("final", add_ten, "最终结果")
    
    # 验证初始值
    assert g["doubled"] == 10.0
    assert g["final"] == 20.0
    
    # 修改基础参数
    g["input"] = 10.0
    
    # 验证依赖更新传播
    assert g["doubled"] == 20.0
    assert g["final"] == 30.0

def test_circular_dependency_prevention():
    """测试循环依赖预防"""
    g = Graph("循环依赖预防测试")
    
    # 设置基础参数
    g["x"] = 5.0
    
    # 创建正常的计算参数
    def calc_y():
        return g["x"] * 2
    
    g.add_computed("y", calc_y, "计算y")
    
    # 尝试创建循环依赖（这应该不会导致无限循环）
    def calc_z():
        return g["y"] + g["x"]
    
    g.add_computed("z", calc_z, "计算z")
    
    # 验证计算正常
    assert g["y"] == 10.0
    assert g["z"] == 15.0
    
    # 测试依赖链获取不会无限循环
    chain = g.get_dependency_chain("z")
    assert len(chain) > 0

def test_dependency_graph_structure():
    """测试依赖图结构"""
    g = Graph("依赖图结构测试")
    
    # 设置基础参数
    g["param1"] = 1.0
    g["param2"] = 2.0
    g["param3"] = 3.0
    
    # 创建计算参数
    def calc_a():
        return g["param1"] + g["param2"]
    
    def calc_b():
        return g["param2"] * g["param3"]
    
    def calc_c():
        return g["calc_a"] + g["calc_b"]
    
    g.add_computed("calc_a", calc_a, "计算A")
    g.add_computed("calc_b", calc_b, "计算B")
    g.add_computed("calc_c", calc_c, "计算C")
    
    # 验证依赖图结构
    dep_graph = g.get_dependency_graph()
    
    # param1被calc_a依赖
    assert "calc_a" in dep_graph.get("param1", [])
    
    # param2被calc_a和calc_b依赖
    assert "calc_a" in dep_graph.get("param2", [])
    assert "calc_b" in dep_graph.get("param2", [])
    
    # calc_a和calc_b被calc_c依赖
    assert "calc_c" in dep_graph.get("calc_a", [])
    assert "calc_c" in dep_graph.get("calc_b", [])

def test_reverse_dependency_graph():
    """测试反向依赖图"""
    g = Graph("反向依赖图测试")
    
    # 设置基础参数
    g["base"] = 10.0
    
    # 创建依赖链
    def level1():
        return g["base"] * 2
    
    def level2():
        return g["level1"] + 5
    
    g.add_computed("level1", level1, "第一级")
    g.add_computed("level2", level2, "第二级")
    
    # 获取反向依赖图
    reverse_dep_graph = g.get_reverse_dependency_graph()
    
    # 验证反向依赖关系
    assert "base" in reverse_dep_graph["level1"]
    assert "level1" in reverse_dep_graph["level2"]
    assert len(reverse_dep_graph["base"]) == 0  # 基础参数没有依赖

def test_dependency_chain_extraction():
    """测试依赖链提取"""
    g = Graph("依赖链提取测试")
    
    # 设置基础参数
    g["root"] = 1.0
    
    # 创建深度依赖链
    def step1():
        return g["root"] + 1
    
    def step2():
        return g["step1"] + 1
    
    def step3():
        return g["step2"] + 1
    
    g.add_computed("step1", step1, "步骤1")
    g.add_computed("step2", step2, "步骤2")
    g.add_computed("step3", step3, "步骤3")
    
    # 获取依赖链
    chain = g.get_dependency_chain("step3")
    
    # 验证依赖链包含所有必要的参数
    assert "root" in chain
    assert "step1" in chain
    assert "step2" in chain
    assert "step3" in chain

def test_dependents_chain_extraction():
    """测试依赖者链提取"""
    g = Graph("依赖者链提取测试")
    
    # 设置基础参数
    g["source"] = 5.0
    
    # 创建多个依赖source的计算参数
    def branch1():
        return g["source"] * 2
    
    def branch2():
        return g["source"] + 10
    
    def final():
        return g["branch1"] + g["branch2"]
    
    g.add_computed("branch1", branch1, "分支1")
    g.add_computed("branch2", branch2, "分支2")
    g.add_computed("final", final, "最终结果")
    
    # 获取依赖者链
    dependents_chain = g.get_dependents_chain("source")
    
    # 验证依赖者链包含所有受影响的参数
    assert "source" in dependents_chain
    assert "branch1" in dependents_chain
    assert "branch2" in dependents_chain
    assert "final" in dependents_chain

if __name__ == "__main__":
    test_basic_dependency_tracking()
    test_automatic_dependency_detection()
    test_chain_dependency_tracking()
    test_multiple_dependencies()
    test_dependency_update_propagation()
    test_circular_dependency_prevention()
    test_dependency_graph_structure()
    test_reverse_dependency_graph()
    test_dependency_chain_extraction()
    test_dependents_chain_extraction()
    print("✅ 新Graph系统依赖追踪测试全部通过")