#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T308 - 测试
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

def test_example_performance():
    """测试示例创建的性能"""
    try:
        import time
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行示例创建
        result = app.create_example_soc_graph()
        
        # 计算执行时间
        execution_time = time.time() - start_time
        
        # 验证性能
        assert execution_time < 2.0, f"示例创建应该在2秒内完成，实际用时{execution_time:.2f}秒"
        print(f"✅ 性能测试通过: 创建用时{execution_time:.2f}秒")
        
    except Exception as e:
        pytest.fail(f"性能测试失败: {e}")

if __name__ == "__main__":
    test_example_performance()
    print("✅ T308 测试通过")
