#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T103 - 参数计算测试
从原始测试文件分离出的独立测试
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from app import app, graph, layout_manager
import pytest
from models import Parameter, Node, CalculationGraph
import json
import math

def test_parameter_calculation():
    """测试参数计算"""
    # 创建参数
    param1 = Parameter("param1", 10.0, "V", description="测试参数1")
    param2 = Parameter("param2", 20.0, "A", description="测试参数2")
    
    # 测试字符串形式的计算函数
    calc_func_str = "result = dependencies[0].value * dependencies[1].value"
    result_param = Parameter("result", 0.0, "W", description="计算结果", calculation_func=calc_func_str)
    result_param.add_dependency(param1)
    result_param.add_dependency(param2)
    
    # 计算并验证结果
    result = result_param.calculate()
    assert result == 200.0  # 10.0 * 20.0
    
    # 测试函数对象形式的计算函数
    def calc_func(param: Parameter) -> float:
        return param.dependencies[0].value * param.dependencies[1].value
    
    result_param2 = Parameter("result2", 0.0, "W", description="计算结果2", calculation_func=calc_func)
    result_param2.add_dependency(param1)
    result_param2.add_dependency(param2)
    
    # 计算并验证结果
    result = result_param2.calculate()
    assert result == 200.0

if __name__ == "__main__":
    test_parameter_calculation()
    print("✅ T103 参数计算测试通过")
