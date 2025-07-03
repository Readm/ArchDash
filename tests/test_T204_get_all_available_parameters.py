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
    graph, node1_id, _ = test_graph
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
