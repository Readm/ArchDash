#!/usr/bin/env python3
"""
测试新Graph系统的核心功能
从旧测试 test_T107_calculation_graph.py 迁移而来
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core import Graph

def test_graph_creation():
    """测试图的创建和基本功能"""
    g = Graph("测试图")
    
    # 验证图创建
    assert g.name == "测试图"
    assert len(g.keys()) == 0
    
    # 测试基础参数添加
    g["param1"] = 10.0
    g["param2"] = 20.0
    g["global_param"] = 100.0
    
    # 验证参数添加
    assert len(g.keys()) == 3
    assert "param1" in g
    assert "param2" in g
    assert "global_param" in g
    
    # 验证参数值
    assert g["param1"] == 10.0
    assert g["param2"] == 20.0
    assert g["global_param"] == 100.0

def test_graph_computed_parameters():
    """测试图的计算参数功能"""
    g = Graph("计算参数测试")
    
    # 添加基础参数
    g["param1"] = 10.0
    
    # 添加计算参数
    def multiply_by_two():
        return g["param1"] * 2
    
    g.add_computed("param2", multiply_by_two, "乘以2的计算")
    
    # 验证计算参数
    assert g["param2"] == 20.0
    
    # 验证参数信息
    info = g.get_computed_info("param2")
    assert info["name"] == "param2"
    assert info["description"] == "乘以2的计算"
    assert "param1" in info["dependencies"]
    assert info["computed"] == True

def test_graph_dependency_management():
    """测试图的依赖关系管理"""
    g = Graph("依赖管理测试")
    
    # 设置基础参数
    g["base_value"] = 5.0
    g["multiplier"] = 3.0
    
    # 创建依赖链
    def first_calc():
        return g["base_value"] * g["multiplier"]
    
    def second_calc():
        return g["first_result"] + 10
    
    def third_calc():
        return g["second_result"] * 0.5
    
    g.add_computed("first_result", first_calc, "第一级计算")
    g.add_computed("second_result", second_calc, "第二级计算")
    g.add_computed("third_result", third_calc, "第三级计算")
    
    # 验证计算结果
    assert g["first_result"] == 15.0  # 5.0 * 3.0
    assert g["second_result"] == 25.0  # 15.0 + 10
    assert g["third_result"] == 12.5  # 25.0 * 0.5
    
    # 验证依赖关系
    dep_graph = g.get_dependency_graph()
    assert "first_result" in dep_graph.get("base_value", [])
    assert "first_result" in dep_graph.get("multiplier", [])
    assert "second_result" in dep_graph.get("first_result", [])
    assert "third_result" in dep_graph.get("second_result", [])

def test_graph_parameter_updates():
    """测试图中参数更新的传播"""
    g = Graph("参数更新测试")
    
    # 设置基础参数
    g["input"] = 10.0
    
    # 创建计算链
    def double_input():
        return g["input"] * 2
    
    def add_five():
        return g["doubled"] + 5
    
    def square_result():
        return g["added"] ** 2
    
    g.add_computed("doubled", double_input, "双倍输入")
    g.add_computed("added", add_five, "加5")
    g.add_computed("squared", square_result, "平方结果")
    
    # 验证初始结果
    assert g["doubled"] == 20.0
    assert g["added"] == 25.0
    assert g["squared"] == 625.0
    
    # 修改基础参数
    g["input"] = 5.0
    
    # 验证更新传播
    assert g["doubled"] == 10.0
    assert g["added"] == 15.0
    assert g["squared"] == 225.0

def test_graph_multiple_dependencies():
    """测试图中多重依赖关系"""
    g = Graph("多重依赖测试")
    
    # 设置基础参数
    g["a"] = 2.0
    g["b"] = 3.0
    g["c"] = 4.0
    
    # 创建多重依赖的计算
    def sum_ab():
        return g["a"] + g["b"]
    
    def product_bc():
        return g["b"] * g["c"]
    
    def complex_calc():
        return g["sum_ab"] * g["product_bc"] + g["a"]
    
    g.add_computed("sum_ab", sum_ab, "a+b")
    g.add_computed("product_bc", product_bc, "b*c")
    g.add_computed("complex_result", complex_calc, "复杂计算")
    
    # 验证计算结果
    assert g["sum_ab"] == 5.0  # 2.0 + 3.0
    assert g["product_bc"] == 12.0  # 3.0 * 4.0
    assert g["complex_result"] == 62.0  # 5.0 * 12.0 + 2.0
    
    # 测试单个参数变化的影响
    g["b"] = 5.0
    assert g["sum_ab"] == 7.0  # 2.0 + 5.0
    assert g["product_bc"] == 20.0  # 5.0 * 4.0
    assert g["complex_result"] == 142.0  # 7.0 * 20.0 + 2.0

def test_graph_parameter_grouping():
    """测试图中参数分组功能"""
    g = Graph("参数分组测试")
    
    # 设置基础参数并分组
    g["voltage"] = 12.0
    g["current"] = 2.0
    g["resistance"] = 6.0
    
    g.set_group("voltage", "电气参数")
    g.set_group("current", "电气参数")
    g.set_group("resistance", "电气参数")
    
    # 添加计算参数
    def power_calc():
        return g["voltage"] * g["current"]
    
    def ohm_check():
        return g["voltage"] / g["current"]
    
    g.add_computed("power", power_calc, "功率计算", "计算结果")
    g.add_computed("calculated_resistance", ohm_check, "欧姆定律验证", "计算结果")
    
    # 验证分组
    assert g.get_group("voltage") == "电气参数"
    assert g.get_group("power") == "计算结果"
    
    # 验证按组获取参数
    electrical_params = g.get_parameters_by_group("电气参数")
    assert "voltage" in electrical_params
    assert "current" in electrical_params
    assert "resistance" in electrical_params
    
    result_params = g.get_parameters_by_group("计算结果")
    assert "power" in result_params
    assert "calculated_resistance" in result_params

def test_graph_complex_scenario():
    """测试图的复杂应用场景"""
    g = Graph("复杂场景测试")
    
    # 模拟一个电路设计场景
    # 基础参数
    g["supply_voltage"] = 12.0
    g["load_resistance"] = 10.0
    g["transistor_gain"] = 100.0
    g["base_resistance"] = 1000.0
    
    # 计算参数
    def load_current():
        return g["supply_voltage"] / g["load_resistance"]
    
    def base_current():
        return g["load_current"] / g["transistor_gain"]
    
    def base_voltage():
        return g["base_current"] * g["base_resistance"]
    
    def power_dissipation():
        return g["supply_voltage"] * g["load_current"]
    
    def efficiency():
        useful_power = g["load_current"] ** 2 * g["load_resistance"]
        total_power = g["power_dissipation"]
        return useful_power / total_power if total_power > 0 else 0
    
    # 添加计算参数
    g.add_computed("load_current", load_current, "负载电流")
    g.add_computed("base_current", base_current, "基极电流")
    g.add_computed("base_voltage", base_voltage, "基极电压")
    g.add_computed("power_dissipation", power_dissipation, "功率耗散")
    g.add_computed("efficiency", efficiency, "效率")
    
    # 验证复杂计算
    assert g["load_current"] == 1.2  # 12.0 / 10.0
    assert g["base_current"] == 0.012  # 1.2 / 100.0
    assert g["base_voltage"] == 12.0  # 0.012 * 1000.0
    assert abs(g["power_dissipation"] - 14.4) < 1e-10  # 12.0 * 1.2
    assert g["efficiency"] == 1.0  # (1.2^2 * 10.0) / 14.4
    
    # 测试设计优化
    g["transistor_gain"] = 200.0  # 提高晶体管增益
    assert g["base_current"] == 0.006  # 1.2 / 200.0
    assert g["base_voltage"] == 6.0  # 0.006 * 1000.0
    assert g["efficiency"] == 1.0  # 效率保持不变

def test_graph_keys_values_items():
    """测试图的字典式接口"""
    g = Graph("字典接口测试")
    
    # 添加各种类型的参数
    g["int_param"] = 42
    g["float_param"] = 3.14
    g["string_param"] = "hello"
    g["bool_param"] = True
    
    def computed_param():
        return g["int_param"] * 2
    
    g.add_computed("computed_param", computed_param, "计算参数")
    
    # 测试keys()
    keys = g.keys()
    assert len(keys) == 5
    assert "int_param" in keys
    assert "computed_param" in keys
    
    # 测试values()
    values = g.values()
    assert len(values) == 5
    assert 42 in values
    assert 84 in values  # computed_param的值
    
    # 测试items()
    items = g.items()
    assert len(items) == 5
    items_dict = dict(items)
    assert items_dict["int_param"] == 42
    assert items_dict["computed_param"] == 84

if __name__ == "__main__":
    test_graph_creation()
    test_graph_computed_parameters()
    test_graph_dependency_management()
    test_graph_parameter_updates()
    test_graph_multiple_dependencies()
    test_graph_parameter_grouping()
    test_graph_complex_scenario()
    test_graph_keys_values_items()
    print("✅ 新Graph系统核心功能测试全部通过")