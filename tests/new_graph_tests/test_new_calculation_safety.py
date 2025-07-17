#!/usr/bin/env python3
"""
测试新Graph系统的计算函数安全性
从旧测试 test_T104_calculation_function_safety.py 迁移而来
"""

import pytest
import sys
import os
import math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core import Graph

def test_basic_calculation_safety():
    """测试基本计算函数的安全性"""
    g = Graph("安全性测试")
    
    # 设置基础参数
    g["param1"] = 2.0
    g["param2"] = 3.0
    
    # 测试正常的计算函数
    def safe_calculation():
        return g["param1"] + g["param2"]
    
    g.add_computed("safe_result", safe_calculation, "安全计算")
    
    # 验证计算正常工作
    assert g["safe_result"] == 5.0

def test_math_function_usage():
    """测试数学函数的使用"""
    g = Graph("数学函数测试")
    
    # 设置基础参数
    g["value"] = 4.0
    g["angle"] = 45.0
    
    # 测试平方根计算
    def sqrt_calculation():
        return math.sqrt(g["value"])
    
    # 测试三角函数计算
    def sin_calculation():
        return math.sin(math.radians(g["angle"]))
    
    g.add_computed("sqrt_result", sqrt_calculation, "平方根")
    g.add_computed("sin_result", sin_calculation, "正弦值")
    
    # 验证计算结果
    assert g["sqrt_result"] == 2.0
    assert abs(g["sin_result"] - 0.7071067811865476) < 1e-10

def test_error_handling_in_calculations():
    """测试计算中的错误处理"""
    g = Graph("错误处理测试")
    
    # 设置基础参数
    g["numerator"] = 10.0
    g["denominator"] = 0.0
    
    # 测试除零错误处理
    def division_with_error_handling():
        try:
            if g["denominator"] == 0:
                return 0.0  # 自定义错误处理
            return g["numerator"] / g["denominator"]
        except ZeroDivisionError:
            return 0.0
    
    g.add_computed("division_result", division_with_error_handling, "除法计算")
    
    # 验证错误处理生效
    assert g["division_result"] == 0.0

def test_complex_calculation_patterns():
    """测试复杂计算模式"""
    g = Graph("复杂计算测试")
    
    # 设置基础参数
    g["list_size"] = 5
    g["multiplier"] = 2.0
    
    # 测试使用内置函数的复杂计算
    def complex_calculation():
        size = int(g["list_size"])
        mult = g["multiplier"]
        
        # 创建列表并计算
        values = [i * mult for i in range(size)]
        return sum(values)
    
    g.add_computed("complex_result", complex_calculation, "复杂计算")
    
    # 验证计算结果 (0*2 + 1*2 + 2*2 + 3*2 + 4*2 = 20)
    assert g["complex_result"] == 20.0

def test_calculation_with_conditionals():
    """测试带条件判断的计算"""
    g = Graph("条件判断测试")
    
    # 设置基础参数
    g["temperature"] = 25.0
    g["pressure"] = 1.0
    
    # 测试条件计算
    def conditional_calculation():
        temp = g["temperature"]
        press = g["pressure"]
        
        if temp > 30:
            return press * 1.2
        elif temp > 20:
            return press * 1.1
        else:
            return press * 1.0
    
    g.add_computed("adjusted_pressure", conditional_calculation, "调整压力")
    
    # 验证条件计算
    assert g["adjusted_pressure"] == 1.1  # 25 > 20, 所以 1.0 * 1.1 = 1.1

def test_calculation_with_loops():
    """测试带循环的计算"""
    g = Graph("循环计算测试")
    
    # 设置基础参数
    g["iterations"] = 3
    g["base_value"] = 2.0
    
    # 测试循环计算
    def loop_calculation():
        iterations = int(g["iterations"])
        base = g["base_value"]
        
        result = 1.0
        for i in range(iterations):
            result *= base
        
        return result
    
    g.add_computed("power_result", loop_calculation, "幂次计算")
    
    # 验证循环计算 (2^3 = 8)
    assert g["power_result"] == 8.0

def test_calculation_with_exception_handling():
    """测试异常处理机制"""
    g = Graph("异常处理测试")
    
    # 设置基础参数
    g["data"] = [1, 2, 3]
    g["index"] = 5  # 超出范围的索引
    
    # 测试异常处理
    def safe_indexing():
        try:
            data = g["data"]
            index = g["index"]
            return data[index]
        except IndexError:
            return -1  # 返回默认值
    
    g.add_computed("safe_value", safe_indexing, "安全索引")
    
    # 验证异常处理
    assert g["safe_value"] == -1

def test_calculation_function_error_recovery():
    """测试计算函数错误恢复"""
    g = Graph("错误恢复测试")
    
    # 设置基础参数
    g["input_value"] = "not_a_number"
    
    # 测试错误恢复
    def error_recovery_calculation():
        try:
            # 尝试将字符串转换为数字
            return float(g["input_value"]) * 2
        except ValueError:
            # 如果转换失败，返回默认值
            return 0.0
    
    g.add_computed("recovered_value", error_recovery_calculation, "错误恢复")
    
    # 验证错误恢复
    assert g["recovered_value"] == 0.0
    
    # 修改为有效值
    g["input_value"] = "10.5"
    assert g["recovered_value"] == 21.0

def test_calculation_with_nested_function_calls():
    """测试嵌套函数调用"""
    g = Graph("嵌套函数测试")
    
    # 设置基础参数
    g["radius"] = 5.0
    
    # 测试嵌套的数学函数调用
    def nested_calculation():
        r = g["radius"]
        # 计算圆的面积和周长的比值
        area = math.pi * math.pow(r, 2)
        circumference = 2 * math.pi * r
        return area / circumference if circumference > 0 else 0
    
    g.add_computed("ratio", nested_calculation, "面积周长比")
    
    # 验证嵌套计算 (π*r²)/(2*π*r) = r/2
    assert abs(g["ratio"] - 2.5) < 1e-10

def test_calculation_with_string_operations():
    """测试字符串操作"""
    g = Graph("字符串操作测试")
    
    # 设置基础参数
    g["first_name"] = "John"
    g["last_name"] = "Doe"
    g["separator"] = " "
    
    # 测试字符串拼接
    def string_calculation():
        return g["first_name"] + g["separator"] + g["last_name"]
    
    g.add_computed("full_name", string_calculation, "全名")
    
    # 验证字符串操作
    assert g["full_name"] == "John Doe"

def test_calculation_with_data_structures():
    """测试数据结构操作"""
    g = Graph("数据结构测试")
    
    # 设置基础参数
    g["numbers"] = [1, 2, 3, 4, 5]
    g["threshold"] = 3
    
    # 测试列表操作
    def list_calculation():
        numbers = g["numbers"]
        threshold = g["threshold"]
        
        # 过滤并求和
        filtered = [x for x in numbers if x > threshold]
        return sum(filtered)
    
    g.add_computed("filtered_sum", list_calculation, "过滤求和")
    
    # 验证列表操作 (4 + 5 = 9)
    assert g["filtered_sum"] == 9

if __name__ == "__main__":
    test_basic_calculation_safety()
    test_math_function_usage()
    test_error_handling_in_calculations()
    test_complex_calculation_patterns()
    test_calculation_with_conditionals()
    test_calculation_with_loops()
    test_calculation_with_exception_handling()
    test_calculation_function_error_recovery()
    test_calculation_with_nested_function_calls()
    test_calculation_with_string_operations()
    test_calculation_with_data_structures()
    print("✅ 新Graph系统计算函数安全性测试全部通过")