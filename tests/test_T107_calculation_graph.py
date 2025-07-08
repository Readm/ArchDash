#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T107 - 计算图测试
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

def test_calculation_graph():
    """测试计算图"""
    # 创建计算图
    graph = CalculationGraph()
    
    # 创建节点和参数
    node1 = Node("node1", "测试节点1")
    node2 = Node("node2", "测试节点2")
    
    global_param = Parameter("global_param", 100.0, "V", description="全局参数")
    param1 = Parameter("param1", 10.0, "V", description="测试参数1")
    param2 = Parameter("param2", 20.0, "A", description="测试参数2", 
                      calculation_func="result = dependencies[0].value * 2")
    
    # 设置依赖关系
    param2.add_dependency(param1)
    
    # 添加参数到节点
    node1.add_parameter(global_param)
    node1.add_parameter(param1)
    node2.add_parameter(param2)
    
    # 添加节点到图
    graph.add_node(node1)
    graph.add_node(node2)
    
    # 测试计算
    param2.calculate()
    assert param2.value == 20.0  # 10.0 * 2
    
    # 测试依赖链
    chain = graph.get_dependency_chain(param2)
    assert len(chain) > 0

if __name__ == "__main__":
    test_calculation_graph()
    print("✅ T107 计算图测试通过")
