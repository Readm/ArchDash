#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T206 - 依赖复选框创建测试
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

def test_create_dependency_checkboxes(test_graph):
    """测试创建依赖复选框列表的函数"""
    graph = test_graph
    import app
    app.graph = graph
    
    # 创建测试数据 - 添加一些节点和参数
    from models import Node, Parameter
    
    # 创建第一个节点，包含两个参数
    node1 = Node(name="节点1", description="测试节点1")
    node1.add_parameter(Parameter(name="参数1", value=100, unit="", description="测试参数1", param_type="float"))
    node1.add_parameter(Parameter(name="参数2", value=200, unit="mm", description="测试参数2", param_type="int"))
    graph.add_node(node1)
    
    # 创建第二个节点，包含一个参数
    node2 = Node(name="节点2", description="测试节点2")
    node2.add_parameter(Parameter(name="参数3", value=300, unit="kg", description="测试参数3", param_type="float"))
    graph.add_node(node2)
    
    # 现在测试 get_all_available_parameters - 排除当前节点的当前参数
    # 应该返回 3 个参数，但排除当前节点的当前参数
    params = get_all_available_parameters(node1.id, "参数1")
    checkboxes = create_dependency_checkboxes(params)
    
    # 应该返回 2 个复选框（节点1的参数2 + 节点2的参数3）
    assert len(checkboxes) == 2
    assert isinstance(checkboxes[0], dbc.Checkbox)
    assert isinstance(checkboxes[1], dbc.Checkbox)

if __name__ == "__main__":
    test_create_dependency_checkboxes()
    print("✅ T206 依赖复选框创建测试通过")
