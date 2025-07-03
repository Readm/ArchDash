#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T306 - 测试
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

def test_example_creates_valid_data():
    """测试示例创建的数据是否有效"""
    try:
        # 执行示例创建
        result = app.create_example_soc_graph()
        
        # 验证返回的统计信息
        assert "nodes_created" in result, "应该返回节点创建数量"
        assert "total_params" in result, "应该返回总参数数量"
        assert "calculated_params" in result, "应该返回计算参数数量"
        
        # 验证数值合理性
        assert result["nodes_created"] > 0, "应该创建节点"
        assert result["total_params"] > 0, "应该有参数"
        assert result["calculated_params"] > 0, "应该有计算参数"
        
        print(f"✅ 验证通过: {result['nodes_created']}个节点, {result['total_params']}个参数, {result['calculated_params']}个计算参数")
        
    except Exception as e:
        pytest.fail(f"数据有效性测试失败: {e}")

if __name__ == "__main__":
    test_example_creates_valid_data()
    print("✅ T306 测试通过")
