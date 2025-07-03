#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T208 - 敏感性分析测试
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

def test_perform_sensitivity_analysis(test_graph):
    """测试参数敏感性分析函数"""
    graph, node1_id, node2_id = test_graph
    import app
    app.graph = graph
    
    # 设置依赖关系: param3 = param1 * 2
    param3 = graph.nodes[node2_id].get_parameter("param3")
    param1 = graph.nodes[node1_id].get_parameter("param1")
    param3.dependencies = [param1]
    param3.calculation_func = "result = dependencies[0].value * 2"
    param3.calculate()
    
    x_info = {'value': f'{node1_id}|param1', 'label': 'Node1.param1', 'unit': 'm'}
    y_info = {'value': f'{node2_id}|param3', 'label': 'Node2.param3', 'unit': 's'}
    
    result = perform_sensitivity_analysis(x_info, y_info, 10, 20, 2)
    
    assert result['success']
    assert len(result['x_values']) == 6
    assert result['x_values'] == [10.0, 12.0, 14.0, 16.0, 18.0, 20.0]
    assert result['y_values'] == [20.0, 24.0, 28.0, 32.0, 36.0, 40.0]

if __name__ == "__main__":
    test_perform_sensitivity_analysis()
    print("✅ T208 敏感性分析测试通过")
