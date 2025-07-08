#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T305 - 测试
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

def test_example_function_consistency():
    """测试示例函数的一致性（多次调用应该产生相同结果）"""
    try:
        from app import create_example_soc_graph
        
        # 第一次调用
        result1 = create_example_soc_graph()
        
        # 第二次调用
        result2 = create_example_soc_graph()
        
        # 验证结果一致性
        assert result1["nodes_created"] == result2["nodes_created"], "节点数量应该一致"
        assert result1["total_params"] == result2["total_params"], "参数数量应该一致"
        assert result1["calculated_params"] == result2["calculated_params"], "计算参数数量应该一致"
        
        print("✅ 示例函数多次调用结果一致")
        
    except Exception as e:
        pytest.fail(f"一致性测试失败: {e}")

if __name__ == "__main__":
    test_example_function_consistency()
    print("✅ T305 测试通过")
