#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T106 - 节点操作测试
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

def test_node_operations():
    """测试节点操作"""
    # 创建节点
    node = Node("test_node", "测试节点")
    
    # 创建参数
    param1 = Parameter("param1", 10.0, "V", description="测试参数1")
    param2 = Parameter("param2", 20.0, "A", description="测试参数2")
    
    # 测试添加参数
    node.add_parameter(param1)
    node.add_parameter(param2)
    assert len(node.parameters) == 2
    
    # 测试移除参数
    node.remove_parameter("param1")
    assert len(node.parameters) == 1
    assert node.parameters[0].name == "param2"

if __name__ == "__main__":
    test_node_operations()
    print("✅ T106 节点操作测试通过")
