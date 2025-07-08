#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T405 - 测试
从原始测试文件分离出的独立测试
"""

import pytest
from models import CanvasLayoutManager, GridPosition

def test_layout_manager_column_operations():
    """测试列操作"""
    layout = CanvasLayoutManager(initial_cols=2, initial_rows=3)
    
    # 填充一些节点
    layout.place_node("n1", GridPosition(0, 0))
    layout.place_node("n2", GridPosition(1, 0))
    layout.place_node("n3", GridPosition(0, 1))
    
    # 测试获取列节点
    col0_nodes = layout.get_column_nodes(0)
    assert len(col0_nodes) == 2
    assert ("n1", 0) in col0_nodes
    assert ("n2", 1) in col0_nodes
    
    col1_nodes = layout.get_column_nodes(1)
    assert len(col1_nodes) == 1
    assert ("n3", 0) in col1_nodes
    
    print("✅ 列操作测试通过")

if __name__ == "__main__":
    test_layout_manager_column_operations()
    print("✅ T405 测试通过")
