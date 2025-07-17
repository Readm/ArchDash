#!/usr/bin/env python3
"""
测试新Graph系统的依赖链分析功能
从旧测试 test_T115_dependency_chain_analysis.py 迁移而来
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core import Graph

def test_basic_dependency_chain_analysis():
    """测试基本的依赖链分析功能"""
    g = Graph("依赖链分析测试")
    
    # 创建三级依赖链：A -> B -> C
    g["param_a"] = 1.0
    
    def calc_b():
        return g["param_a"] * 2
    
    def calc_c():
        return g["param_b"] + 5
    
    g.add_computed("param_b", calc_b, "B依赖A")
    g.add_computed("param_c", calc_c, "C依赖B")
    
    # 测试依赖链分析
    chain_a = g.get_dependency_chain("param_a")
    chain_b = g.get_dependency_chain("param_b")
    chain_c = g.get_dependency_chain("param_c")
    
    # 验证param_a的依赖链（作为根参数）
    assert "param_a" in chain_a
    assert len(chain_a) == 1  # 只有自己
    
    # 验证param_b的依赖链
    assert "param_a" in chain_b
    assert "param_b" in chain_b
    assert len(chain_b) == 2
    
    # 验证param_c的依赖链
    assert "param_a" in chain_c
    assert "param_b" in chain_c
    assert "param_c" in chain_c
    assert len(chain_c) == 3

def test_dependency_chain_with_multiple_roots():
    """测试多个根参数的依赖链分析"""
    g = Graph("多根依赖链测试")
    
    # 创建多个根参数
    g["root1"] = 10.0
    g["root2"] = 20.0
    g["root3"] = 30.0
    
    # 创建依赖多个根的计算
    def calc_combined():
        return g["root1"] + g["root2"] + g["root3"]
    
    def calc_derived():
        return g["combined"] * 2
    
    g.add_computed("combined", calc_combined, "组合计算")
    g.add_computed("derived", calc_derived, "派生计算")
    
    # 测试各个参数的依赖链
    chain_root1 = g.get_dependency_chain("root1")
    chain_combined = g.get_dependency_chain("combined")
    chain_derived = g.get_dependency_chain("derived")
    
    # 验证根参数的依赖链
    assert len(chain_root1) == 1
    assert "root1" in chain_root1
    
    # 验证组合参数的依赖链
    assert "root1" in chain_combined
    assert "root2" in chain_combined
    assert "root3" in chain_combined
    assert "combined" in chain_combined
    assert len(chain_combined) == 4
    
    # 验证派生参数的依赖链
    assert "root1" in chain_derived
    assert "root2" in chain_derived
    assert "root3" in chain_derived
    assert "combined" in chain_derived
    assert "derived" in chain_derived
    assert len(chain_derived) == 5

def test_dependents_chain_analysis():
    """测试依赖者链分析功能"""
    g = Graph("依赖者链分析测试")
    
    # 创建依赖关系
    g["source"] = 5.0
    
    def calc_level1():
        return g["source"] * 2
    
    def calc_level2():
        return g["level1"] + 10
    
    def calc_level3():
        return g["level2"] / 2
    
    g.add_computed("level1", calc_level1, "第一级")
    g.add_computed("level2", calc_level2, "第二级")
    g.add_computed("level3", calc_level3, "第三级")
    
    # 测试依赖者链分析
    dependents_source = g.get_dependents_chain("source")
    dependents_level1 = g.get_dependents_chain("level1")
    dependents_level2 = g.get_dependents_chain("level2")
    
    # 验证源参数的依赖者链
    assert "source" in dependents_source
    assert "level1" in dependents_source
    assert "level2" in dependents_source
    assert "level3" in dependents_source
    assert len(dependents_source) == 4
    
    # 验证中间参数的依赖者链
    assert "level1" in dependents_level1
    assert "level2" in dependents_level1
    assert "level3" in dependents_level1
    assert len(dependents_level1) == 3
    
    # 验证末端参数的依赖者链
    assert "level2" in dependents_level2
    assert "level3" in dependents_level2
    assert len(dependents_level2) == 2

def test_dependency_graph_analysis():
    """测试依赖图分析功能"""
    g = Graph("依赖图分析测试")
    
    # 创建复杂的依赖关系
    g["base1"] = 1.0
    g["base2"] = 2.0
    g["base3"] = 3.0
    
    def calc_a():
        return g["base1"] + g["base2"]
    
    def calc_b():
        return g["base2"] * g["base3"]
    
    def calc_c():
        return g["calc_a"] + g["calc_b"]
    
    g.add_computed("calc_a", calc_a, "A计算")
    g.add_computed("calc_b", calc_b, "B计算")
    g.add_computed("calc_c", calc_c, "C计算")
    
    # 获取依赖图
    dep_graph = g.get_dependency_graph()
    
    # 验证依赖图结构
    assert "calc_a" in dep_graph.get("base1", [])
    assert "calc_a" in dep_graph.get("base2", [])
    assert "calc_b" in dep_graph.get("base2", [])
    assert "calc_b" in dep_graph.get("base3", [])
    assert "calc_c" in dep_graph.get("calc_a", [])
    assert "calc_c" in dep_graph.get("calc_b", [])

def test_reverse_dependency_graph_analysis():
    """测试反向依赖图分析功能"""
    g = Graph("反向依赖图分析测试")
    
    # 创建依赖关系
    g["root"] = 10.0
    
    def calc_step1():
        return g["root"] * 2
    
    def calc_step2():
        return g["step1"] + 5
    
    def calc_step3():
        return g["step2"] / 2
    
    g.add_computed("step1", calc_step1, "步骤1")
    g.add_computed("step2", calc_step2, "步骤2")
    g.add_computed("step3", calc_step3, "步骤3")
    
    # 获取反向依赖图
    reverse_dep_graph = g.get_reverse_dependency_graph()
    
    # 验证反向依赖图结构
    assert "root" in reverse_dep_graph["step1"]
    assert "step1" in reverse_dep_graph["step2"]
    assert "step2" in reverse_dep_graph["step3"]
    assert len(reverse_dep_graph["root"]) == 0  # 根参数没有依赖

def test_complex_dependency_chain_analysis():
    """测试复杂依赖链分析"""
    g = Graph("复杂依赖链分析测试")
    
    # 创建复杂的依赖网络
    g["input1"] = 10.0
    g["input2"] = 20.0
    g["input3"] = 30.0
    
    # 第一层计算
    def calc_layer1_a():
        return g["input1"] + g["input2"]
    
    def calc_layer1_b():
        return g["input2"] * g["input3"]
    
    # 第二层计算
    def calc_layer2_a():
        return g["layer1_a"] / 2
    
    def calc_layer2_b():
        return g["layer1_b"] - g["input1"]
    
    # 第三层计算
    def calc_final():
        return g["layer2_a"] + g["layer2_b"]
    
    g.add_computed("layer1_a", calc_layer1_a, "第一层A")
    g.add_computed("layer1_b", calc_layer1_b, "第一层B")
    g.add_computed("layer2_a", calc_layer2_a, "第二层A")
    g.add_computed("layer2_b", calc_layer2_b, "第二层B")
    g.add_computed("final", calc_final, "最终计算")
    
    # 分析最终计算的依赖链
    final_chain = g.get_dependency_chain("final")
    
    # 验证最终计算的完整依赖链
    assert "input1" in final_chain
    assert "input2" in final_chain
    assert "input3" in final_chain
    assert "layer1_a" in final_chain
    assert "layer1_b" in final_chain
    assert "layer2_a" in final_chain
    assert "layer2_b" in final_chain
    assert "final" in final_chain
    # 依赖链可能包含重复项，所以检查唯一参数数量
    unique_params = set(final_chain)
    assert len(unique_params) == 8

def test_dependency_chain_with_branching():
    """测试分支依赖链分析"""
    g = Graph("分支依赖链测试")
    
    # 创建分支依赖结构
    g["source"] = 100.0
    
    # 创建多个分支
    def branch_a():
        return g["source"] * 0.1
    
    def branch_b():
        return g["source"] * 0.2
    
    def branch_c():
        return g["source"] * 0.3
    
    # 创建分支的子节点
    def sub_a1():
        return g["branch_a"] + 10
    
    def sub_a2():
        return g["branch_a"] - 5
    
    def sub_b1():
        return g["branch_b"] * 2
    
    g.add_computed("branch_a", branch_a, "分支A")
    g.add_computed("branch_b", branch_b, "分支B")
    g.add_computed("branch_c", branch_c, "分支C")
    g.add_computed("sub_a1", sub_a1, "子A1")
    g.add_computed("sub_a2", sub_a2, "子A2")
    g.add_computed("sub_b1", sub_b1, "子B1")
    
    # 分析源参数的依赖者链
    source_dependents = g.get_dependents_chain("source")
    
    # 验证所有分支都在依赖者链中
    assert "source" in source_dependents
    assert "branch_a" in source_dependents
    assert "branch_b" in source_dependents
    assert "branch_c" in source_dependents
    assert "sub_a1" in source_dependents
    assert "sub_a2" in source_dependents
    assert "sub_b1" in source_dependents
    assert len(source_dependents) == 7

def test_circular_dependency_detection():
    """测试循环依赖检测"""
    g = Graph("循环依赖检测测试")
    
    # 创建可能的循环依赖结构
    g["base"] = 10.0
    
    def calc_a():
        return g["base"] * 2
    
    def calc_b():
        return g["calc_a"] + 5
    
    def calc_c():
        return g["calc_b"] - 3
    
    g.add_computed("calc_a", calc_a, "计算A")
    g.add_computed("calc_b", calc_b, "计算B")
    g.add_computed("calc_c", calc_c, "计算C")
    
    # 获取依赖链应该不会无限循环
    chain_a = g.get_dependency_chain("calc_a")
    chain_b = g.get_dependency_chain("calc_b")
    chain_c = g.get_dependency_chain("calc_c")
    
    # 验证没有循环依赖
    assert len(chain_a) == 2  # base, calc_a
    assert len(chain_b) == 3  # base, calc_a, calc_b
    assert len(chain_c) == 4  # base, calc_a, calc_b, calc_c

def test_dependency_chain_performance():
    """测试依赖链分析性能"""
    g = Graph("依赖链性能测试")
    
    # 创建深度依赖链
    g["root"] = 1.0
    
    current_param = "root"
    for i in range(50):
        def make_calc(prev_param):
            def calc():
                return g[prev_param] + 1
            return calc
        
        next_param = f"level_{i}"
        g.add_computed(next_param, make_calc(current_param), f"第{i}级")
        current_param = next_param
    
    # 测试深度依赖链分析
    final_chain = g.get_dependency_chain("level_49")
    
    # 验证深度依赖链的完整性
    assert len(final_chain) == 51  # root + 50 levels
    assert "root" in final_chain
    assert "level_49" in final_chain

def test_dependency_info_extraction():
    """测试依赖信息提取"""
    g = Graph("依赖信息提取测试")
    
    # 创建带描述的计算参数
    g["voltage"] = 12.0
    g["current"] = 2.0
    
    def power_calc():
        return g["voltage"] * g["current"]
    
    def energy_calc():
        return g["power"] * 1.0  # 假设1小时
    
    g.add_computed("power", power_calc, "功率计算", "电气参数")
    g.add_computed("energy", energy_calc, "能耗计算", "电气参数")
    
    # 测试计算参数信息提取
    power_info = g.get_computed_info("power")
    energy_info = g.get_computed_info("energy")
    
    # 验证信息完整性
    assert power_info["name"] == "power"
    assert power_info["description"] == "功率计算"
    assert power_info["group"] == "电气参数"
    assert "voltage" in power_info["dependencies"]
    assert "current" in power_info["dependencies"]
    assert power_info["computed"] == True
    
    assert energy_info["name"] == "energy"
    assert "power" in energy_info["dependencies"]

if __name__ == "__main__":
    test_basic_dependency_chain_analysis()
    test_dependency_chain_with_multiple_roots()
    test_dependents_chain_analysis()
    test_dependency_graph_analysis()
    test_reverse_dependency_graph_analysis()
    test_complex_dependency_chain_analysis()
    test_dependency_chain_with_branching()
    test_circular_dependency_detection()
    test_dependency_chain_performance()
    test_dependency_info_extraction()
    print("✅ 新Graph系统依赖链分析测试全部通过")