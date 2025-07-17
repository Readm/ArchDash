#!/usr/bin/env python3
"""
测试新Graph系统的计算函数作用域
从旧测试 test_T105_calculation_function_scope.py 迁移而来
"""

import pytest
import sys
import os
import datetime
import math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core import Graph

def test_local_variable_scope():
    """测试局部变量作用域"""
    g = Graph("局部变量作用域测试")
    
    # 设置基础参数
    g["param1"] = 2.0
    g["param2"] = 3.0
    
    # 测试在函数内部使用局部变量
    def local_var_calculation():
        local_var = 10
        return g["param1"] + local_var
    
    g.add_computed("local_result", local_var_calculation, "局部变量计算")
    
    # 验证局部变量正常工作
    assert g["local_result"] == 12.0

def test_function_parameter_scope():
    """测试函数参数作用域"""
    g = Graph("函数参数作用域测试")
    
    # 设置基础参数
    g["base_value"] = 5.0
    
    # 测试使用函数参数
    def parameterized_calculation():
        def inner_function(x, y):
            return x * y + 1
        
        return inner_function(g["base_value"], 2.0)
    
    g.add_computed("param_result", parameterized_calculation, "参数化计算")
    
    # 验证函数参数正常工作
    assert g["param_result"] == 11.0  # 5.0 * 2.0 + 1

def test_closure_scope():
    """测试闭包作用域"""
    g = Graph("闭包作用域测试")
    
    # 设置基础参数
    g["multiplier"] = 3.0
    
    # 测试闭包
    def closure_calculation():
        def create_multiplier(factor):
            def multiply(value):
                return value * factor
            return multiply
        
        multiplier_func = create_multiplier(g["multiplier"])
        return multiplier_func(10.0)
    
    g.add_computed("closure_result", closure_calculation, "闭包计算")
    
    # 验证闭包正常工作
    assert g["closure_result"] == 30.0

def test_global_function_access():
    """测试全局函数访问"""
    g = Graph("全局函数访问测试")
    
    # 设置基础参数
    g["numbers"] = [1, 2, 3, 4, 5]
    
    # 测试访问全局函数
    def global_function_calculation():
        numbers = g["numbers"]
        return sum(numbers)  # sum是全局函数
    
    g.add_computed("global_func_result", global_function_calculation, "全局函数计算")
    
    # 验证全局函数访问正常
    assert g["global_func_result"] == 15

def test_module_import_scope():
    """测试模块导入作用域"""
    g = Graph("模块导入作用域测试")
    
    # 设置基础参数
    g["angle"] = 90.0
    
    # 测试在函数内导入模块
    def module_import_calculation():
        import math
        return math.sin(math.radians(g["angle"]))
    
    g.add_computed("module_result", module_import_calculation, "模块导入计算")
    
    # 验证模块导入正常工作
    assert abs(g["module_result"] - 1.0) < 1e-10

def test_datetime_access():
    """测试datetime访问"""
    g = Graph("datetime访问测试")
    
    # 设置基础参数
    g["trigger"] = True
    
    # 测试访问datetime
    def datetime_calculation():
        if g["trigger"]:
            return datetime.datetime.now().year
        return 2023
    
    g.add_computed("datetime_result", datetime_calculation, "datetime计算")
    
    # 验证datetime访问正常
    result = g["datetime_result"]
    assert isinstance(result, int)
    assert result >= 2023

def test_nested_function_scope():
    """测试嵌套函数作用域"""
    g = Graph("嵌套函数作用域测试")
    
    # 设置基础参数
    g["x"] = 2.0
    g["y"] = 3.0
    
    # 测试嵌套函数
    def nested_function_calculation():
        def outer_function(a):
            def inner_function(b):
                return a + b + 1
            return inner_function
        
        inner_func = outer_function(g["x"])
        return inner_func(g["y"])
    
    g.add_computed("nested_result", nested_function_calculation, "嵌套函数计算")
    
    # 验证嵌套函数正常工作
    assert g["nested_result"] == 6.0  # 2.0 + 3.0 + 1

def test_variable_shadowing():
    """测试变量遮蔽"""
    g = Graph("变量遮蔽测试")
    
    # 设置基础参数
    g["value"] = 10.0
    
    # 测试变量遮蔽
    def shadowing_calculation():
        value = 5.0  # 遮蔽graph中的value
        return value + g["value"]  # 使用局部变量和graph变量
    
    g.add_computed("shadow_result", shadowing_calculation, "遮蔽计算")
    
    # 验证变量遮蔽正常工作
    assert g["shadow_result"] == 15.0  # 5.0 + 10.0

def test_lambda_scope():
    """测试lambda函数作用域"""
    g = Graph("lambda作用域测试")
    
    # 设置基础参数
    g["data"] = [1, 2, 3, 4, 5]
    
    # 测试lambda函数
    def lambda_calculation():
        data = g["data"]
        squared = list(map(lambda x: x ** 2, data))
        return sum(squared)
    
    g.add_computed("lambda_result", lambda_calculation, "lambda计算")
    
    # 验证lambda函数正常工作
    assert g["lambda_result"] == 55  # 1 + 4 + 9 + 16 + 25

def test_list_comprehension_scope():
    """测试列表推导式作用域"""
    g = Graph("列表推导式作用域测试")
    
    # 设置基础参数
    g["limit"] = 3
    g["multiplier"] = 2
    
    # 测试列表推导式
    def comprehension_calculation():
        limit = g["limit"]
        multiplier = g["multiplier"]
        
        # 列表推导式中的变量作用域
        result = [x * multiplier for x in range(limit)]
        return sum(result)
    
    g.add_computed("comprehension_result", comprehension_calculation, "推导式计算")
    
    # 验证列表推导式正常工作
    assert g["comprehension_result"] == 6  # (0*2) + (1*2) + (2*2) = 6

def test_exception_handling_scope():
    """测试异常处理作用域"""
    g = Graph("异常处理作用域测试")
    
    # 设置基础参数
    g["risky_operation"] = True
    
    # 测试异常处理中的变量作用域
    def exception_scope_calculation():
        try:
            if g["risky_operation"]:
                error_message = "This is a test error"
                raise ValueError(error_message)
            return 1.0
        except ValueError as e:
            # 在异常处理中访问局部变量
            return len(str(e))
    
    g.add_computed("exception_result", exception_scope_calculation, "异常处理计算")
    
    # 验证异常处理作用域正常工作
    assert g["exception_result"] == 20  # len("This is a test error")

def test_generator_scope():
    """测试生成器作用域"""
    g = Graph("生成器作用域测试")
    
    # 设置基础参数
    g["count"] = 5
    
    # 测试生成器
    def generator_calculation():
        def fibonacci_gen(n):
            a, b = 0, 1
            for _ in range(n):
                yield a
                a, b = b, a + b
        
        count = g["count"]
        fib_gen = fibonacci_gen(count)
        return sum(fib_gen)
    
    g.add_computed("generator_result", generator_calculation, "生成器计算")
    
    # 验证生成器正常工作
    assert g["generator_result"] == 7  # 0 + 1 + 1 + 2 + 3 = 7

def test_decorator_scope():
    """测试装饰器作用域"""
    g = Graph("装饰器作用域测试")
    
    # 设置基础参数
    g["input_value"] = 10.0
    
    # 测试装饰器
    def decorator_calculation():
        def double_result(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs) * 2
            return wrapper
        
        @double_result
        def calculate_value():
            return g["input_value"] + 5
        
        return calculate_value()
    
    g.add_computed("decorator_result", decorator_calculation, "装饰器计算")
    
    # 验证装饰器正常工作
    assert g["decorator_result"] == 30.0  # (10.0 + 5) * 2

if __name__ == "__main__":
    test_local_variable_scope()
    test_function_parameter_scope()
    test_closure_scope()
    test_global_function_access()
    test_module_import_scope()
    test_datetime_access()
    test_nested_function_scope()
    test_variable_shadowing()
    test_lambda_scope()
    test_list_comprehension_scope()
    test_exception_handling_scope()
    test_generator_scope()
    test_decorator_scope()
    print("✅ 新Graph系统计算函数作用域测试全部通过")