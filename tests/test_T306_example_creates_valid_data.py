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
        test_graph = result["graph"]
        
        # 验证图结构
        assert len(test_graph.nodes) > 0, "应该创建节点"
        
        # 验证节点有参数
        total_params = 0
        calc_params = 0
        for node in test_graph.nodes.values():
            total_params += len(node.parameters)
            for param in node.parameters:
                if param.calculation_func:
                    calc_params += 1
        
        assert total_params > 0, "应该有参数"
        print(f"✅ 验证通过: {len(test_graph.nodes)}个节点, {total_params}个参数, {calc_params}个计算参数")
        
        # 验证返回值与实际创建的一致
        assert result["nodes_created"] == len(test_graph.nodes), "返回的节点数应该与实际一致"
        assert result["total_params"] == total_params, "返回的参数数应该与实际一致"
        assert result["calculated_params"] == calc_params, "返回的计算参数数应该与实际一致"
        
    except Exception as e:
        pytest.fail(f"数据有效性测试失败: {e}")

if __name__ == "__main__":
    test_example_creates_valid_data()
    print("✅ T306 测试通过")
