#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T307 - 测试
从原始测试文件分离出的独立测试
"""

import pytest
import sys
import os
import app
from dash import callback
from models import CalculationGraph, CanvasLayoutManager
from session_graph import set_graph, get_graph
from app import create_example_soc_graph
from app import create_example_soc_graph
from app import create_example_soc_graph
import time

def test_example_parameter_calculations():
    """测试示例参数的计算功能"""
    try:
        # 创建示例
        result = app.create_example_soc_graph()
        test_graph = result["graph"]
        
        # 测试计算功能
        calculation_tests = 0
        calculation_successes = 0
        
        for node in test_graph.nodes.values():
            for param in node.parameters:
                if param.calculation_func and param.dependencies:
                    calculation_tests += 1
                    try:
                        # 执行计算
                        calc_result = param.calculate()
                        assert calc_result is not None, f"参数 {param.name} 的计算结果不应为None"
                        calculation_successes += 1
                    except Exception as calc_error:
                        print(f"⚠️ 参数 {param.name} 计算失败: {calc_error}")
        
        print(f"✅ 计算测试: {calculation_successes}/{calculation_tests} 个参数计算成功")
        
        # 至少应该有一些计算参数能够成功计算
        if calculation_tests > 0:
            assert calculation_successes > 0, "至少应该有一些计算参数能够成功计算"
            success_rate = calculation_successes / calculation_tests
            assert success_rate >= 0.7, f"计算成功率应该至少70%，实际{success_rate:.1%}"
            print(f"✅ 计算成功率: {success_rate:.1%}")
        
    except Exception as e:
        pytest.fail(f"计算功能测试失败: {e}")

if __name__ == "__main__":
    test_example_parameter_calculations()
    print("✅ T307 测试通过")
