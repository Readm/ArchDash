#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T205 - 代码模板生成测试
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

def test_generate_code_template():
    """测试生成代码模板的函数"""
    # 无依赖
    template = generate_code_template([])
    assert "无依赖参数" in template
    
    # 有依赖
    deps = [{'param_name': 'dep1'}, {'param_name': 'dep2'}]
    template = generate_code_template(deps)
    assert "# dep1 = dependencies[0].value" in template
    assert "# dep2 = dependencies[1].value" in template

if __name__ == "__main__":
    test_generate_code_template()
    print("✅ T205 代码模板生成测试通过")
