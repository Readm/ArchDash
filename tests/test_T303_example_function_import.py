#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T303 - 测试
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

def test_example_function_import():
    """测试能否正确导入示例函数"""
    try:
        from app import create_example_soc_graph
        assert callable(create_example_soc_graph), "create_example_soc_graph应该是可调用的函数"
        print("✅ 示例函数导入成功")
    except ImportError as e:
        pytest.fail(f"无法导入示例函数: {e}")

if __name__ == "__main__":
    test_example_function_import()
    print("✅ T303 测试通过")
