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
    
    params = get_all_available_parameters("some_node", "some_param")
    checkboxes = create_dependency_checkboxes(params)
    
    # 检查复选框列表
    assert isinstance(checkboxes, list)
    
    if len(params) > 0:
        # 有依赖参数时，应该有复选框
        assert len(checkboxes) > 0
        assert isinstance(checkboxes[0], dbc.Checkbox)
    else:
        # 没有依赖参数时，应该显示提示信息
        assert len(checkboxes) == 1
        assert "暂无可用的依赖参数" in str(checkboxes[0])

if __name__ == "__main__":
    test_create_dependency_checkboxes()
    print("✅ T206 依赖复选框创建测试通过")
