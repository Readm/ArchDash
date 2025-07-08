#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T209 - 空图表创建测试
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

def test_create_empty_plot():
    """测试创建空图表对象"""
    fig = create_empty_plot()
    assert fig is not None
    assert 'data' in fig
    assert len(fig['data']) == 0
    assert 'layout' in fig
    assert 'title' in fig['layout']
    assert fig['layout']['title']['text'] == "请选择参数以生成图表"

if __name__ == "__main__":
    test_create_empty_plot()
    print("✅ T209 空图表创建测试通过")
