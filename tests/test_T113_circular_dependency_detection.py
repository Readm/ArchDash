#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T113 - 循环依赖检测测试
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

def test_circular_dependency_detection():
    """测试循环依赖检测功能"""
    # 创建计算图
    graph = CalculationGraph()
    node = Node("TestNode", "测试节点")
    
    # 创建参数
    param_a = Parameter("param_a", 1.0, "V", calculation_func="result = dependencies[0].value + 1")
    param_b = Parameter("param_b", 2.0, "A", calculation_func="result = dependencies[0].value * 2")
    
    node.add_parameter(param_a)
    node.add_parameter(param_b)
    graph.add_node(node)
    
    # 创建正常依赖关系
    param_a.add_dependency(param_b)
    
    # 尝试创建循环依赖（这应该在应用层被阻止，但我们测试模型层的行为）
    param_b.add_dependency(param_a)
    
    # 测试更新传播时的循环检测
    # 模型层应该能够处理这种情况而不会无限递归
    try:
        update_result = graph.set_parameter_value(param_a, 5.0)
        # 如果没有抛出异常，说明循环检测工作正常
        print("✅ 循环依赖检测正常工作")
    except RecursionError:
        pytest.fail("循环依赖检测失败，发生无限递归")

if __name__ == "__main__":
    test_circular_dependency_detection()
    print("✅ T113 循环依赖检测测试通过")
