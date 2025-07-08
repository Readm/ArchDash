#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T114 - 计算错误时的更新传播测试
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

def test_propagate_updates_with_calculation_errors():
    """测试在计算错误情况下的更新传播"""
    # 创建计算图
    graph = CalculationGraph()
    node = Node("ErrorTestNode", "错误测试节点")
    
    # 创建基础参数
    base_param = Parameter("base", 10.0, "V")
    
    # 创建有错误计算函数的参数
    error_param = Parameter("error_param", 0.0, "A", 
                           calculation_func="result = dependencies[0].value / 0")  # 除零错误
    error_param.add_dependency(base_param)
    
    # 创建依赖于错误参数的参数
    dependent_param = Parameter("dependent", 0.0, "W",
                               calculation_func="result = dependencies[0].value * 2")
    dependent_param.add_dependency(error_param)
    
    node.add_parameter(base_param)
    node.add_parameter(error_param)
    node.add_parameter(dependent_param)
    graph.add_node(node)
    
    # 初始值
    with pytest.raises(ValueError, match="计算失败: float division by zero"):
        error_param.calculate()
    
    # 验证错误参数的值未改变
    assert error_param.value == 0.0
    
    # 验证依赖参数的值也未改变
    assert dependent_param.value == 0.0
    
    # 修复错误并重新计算
    base_param.value = 20.0
    error_param.calculation_func = "result = dependencies[0].value * 2"  # 修复函数
    
    # 重新计算并验证
    error_param.value = error_param.calculate()
    assert error_param.value == 40.0
    
    dependent_param.value = dependent_param.calculate()
    assert dependent_param.value == 80.0

if __name__ == "__main__":
    test_propagate_updates_with_calculation_errors()
    print("✅ T114 计算错误时的更新传播测试通过")
