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
    
    # 添加一个非数值参数
    str_node = Node("StringNode")
    str_param = Parameter("str_param", "text", param_type="str")
    str_node.add_parameter(str_param)
    graph.add_node(str_node)
    
    plot_params = get_plotting_parameters()
    
    assert len(plot_params) == 3  # 应该只返回3个数值参数
    param_labels = {p['label'] for p in plot_params}
    assert "Node1.param1" in param_labels
    assert "StringNode.str_param" not in param_labels

if __name__ == "__main__":
    test_get_plotting_parameters()
    print("✅ T207 绘图参数获取测试通过")
