#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T207 - 绘图参数获取测试
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

def test_get_plotting_parameters(test_graph):
    """测试获取所有可用于绘图的参数"""
    graph = test_graph
    import app
    app.graph = graph
    
    # 创建测试数据 - 添加数值参数
    from models import Node, Parameter
    
    # 创建Node1，包含数值参数
    node1 = Node("Node1")
    param1 = Parameter("param1", 100.0, param_type="float")
    param2 = Parameter("param2", 200, param_type="int")
    node1.add_parameter(param1)
    node1.add_parameter(param2)
    graph.add_node(node1)
    
    # 创建Node2，包含一个数值参数
    node2 = Node("Node2")
    param3 = Parameter("param3", 300.5, param_type="float")
    node2.add_parameter(param3)
    graph.add_node(node2)
    
    # 添加一个非数值参数
    str_node = Node("StringNode")
    str_param = Parameter("str_param", "text", param_type="string")
    str_node.add_parameter(str_param)
    graph.add_node(str_node)
    
    plot_params = get_plotting_parameters()
    
    assert len(plot_params) == 3  # 应该只返回3个数值参数
    param_labels = {p['label'] for p in plot_params}
    assert "Node1.param1" in param_labels
    assert "Node1.param2" in param_labels
    assert "Node2.param3" in param_labels
    assert "StringNode.str_param" not in param_labels

if __name__ == "__main__":
    test_get_plotting_parameters()
    print("✅ T207 绘图参数获取测试通过")
