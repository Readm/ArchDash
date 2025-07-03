#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T304 - 测试
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

def test_example_function_execution():
    """测试示例函数是否能正常执行"""
    try:
        from app import create_example_soc_graph
        
        # 执行示例创建函数
        result = create_example_soc_graph()
        
        # 验证返回结果
        assert isinstance(result, dict), "函数应该返回字典"
        assert "nodes_created" in result, "结果应该包含nodes_created"
        assert "total_params" in result, "结果应该包含total_params"
        assert "calculated_params" in result, "结果应该包含calculated_params"
        
        print(f"✅ 示例函数执行成功: {result}")
        
        # 验证创建的数量是否合理
        assert result["nodes_created"] > 0, "应该创建至少1个节点"
        assert result["total_params"] > 0, "应该创建至少1个参数"
        assert result["calculated_params"] >= 0, "计算参数数量应该非负"
        
        print(f"✅ 创建了{result['nodes_created']}个节点，{result['total_params']}个参数，其中{result['calculated_params']}个是计算参数")
        
    except Exception as e:
        pytest.fail(f"示例函数执行失败: {e}")

if __name__ == "__main__":
    test_example_function_execution()
    print("✅ T304 测试通过")
