#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T204 - 获取所有可用参数测试
从原始测试文件分离出的独立测试
"""

import pytest
from app import (
    get_all_available_parameters,
    generate_code_template,
    create_dependency_checkboxes,
    get_plotting_parameters,
    perform_sensitivity_analysis,
    create_empty_plot
)
from models import CalculationGraph, Node, Parameter
import dash_bootstrap_components as dbc
import numpy as np
import app
import app
import app
import app

def test_get_all_available_parameters(test_graph):
    """测试获取所有可用参数的函数"""
    # 直接使用测试图，不进行解包
    graph = test_graph
    
    # 创建测试节点和参数
    from models import Node, Parameter
    node1 = Node(name="Node1", description="测试节点1")
    node2 = Node(name="Node2", description="测试节点2")
    
    graph.add_node(node1)
    graph.add_node(node2)
    
    param1 = Parameter("param1", 10.0, "V", description="参数1")
    param2 = Parameter("param2", 20.0, "A", description="参数2")
    param3 = Parameter("param3", 30.0, "W", description="参数3")
    
    node1.add_parameter(param1)
    node1.add_parameter(param2)
    node2.add_parameter(param3)
    
    node1_id = node1.id
    
    # 注入全局 `graph` 实例以供测试
    import app
    app.graph = graph
    
    available = get_all_available_parameters(node1_id, "param1")
    
    assert len(available) == 2
    param_names = {p['display_name'] for p in available}
    assert "Node1.param2" in param_names
    assert "Node2.param3" in param_names
    assert "Node1.param1" not in param_names

if __name__ == "__main__":
    test_get_all_available_parameters()
    print("✅ T204 获取所有可用参数测试通过")
