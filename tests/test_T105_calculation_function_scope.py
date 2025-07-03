#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T105 - 计算函数作用域测试
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

def test_calculation_function_scope():
    """测试计算函数的作用域"""
    # 创建基础参数
    param1 = Parameter("param1", 2.0, "V", description="Test parameter 1")
    param2 = Parameter("param2", 3, "A", description="Test parameter 2")
    
    # 测试访问本地变量（未设置result变量，应该报错）
    local_var_calc = "local_var = 10"
    local_var_param = Parameter(
        name="local_var",
        value=0.0,
        unit="V",
        description="Local variable test",
        calculation_func=local_var_calc
    )
    local_var_param.add_dependency(param1)
    
    # 验证未设置result变量被阻止
    with pytest.raises(ValueError, match="计算函数未设置result变量作为输出"):
        local_var_param.calculate()
    
    # 测试访问全局变量
    global_var_calc = "result = global_var + dependencies[0].value"
    global_var_param = Parameter(
        name="global_var",
        value=0.0,
        unit="V",
        description="Global variable test",
        calculation_func=global_var_calc
    )
    global_var_param.add_dependency(param1)
    
    # 验证全局变量访问被阻止
    with pytest.raises(ValueError, match="计算失败: name 'global_var' is not defined"):
        global_var_param.calculate()
    
    # 测试访问提供的环境变量
    env_var_calc = "result = datetime.now().isoformat()"
    env_var_param = Parameter(
        name="env_var",
        value="",
        unit="",
        description="Environment variable test",
        calculation_func=env_var_calc
    )
    env_var_param.add_dependency(param1)
    
    # 验证环境变量访问正常
    result = env_var_param.calculate()
    assert isinstance(result, str)
    assert len(result) > 0

if __name__ == "__main__":
    test_calculation_function_scope()
    print("✅ T105 计算函数作用域测试通过")
