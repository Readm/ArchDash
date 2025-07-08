#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T403 - 测试
从原始测试文件分离出的独立测试
"""

import pytest
from models import CanvasLayoutManager, GridPosition

def test_layout_manager_basic_operations():
    """测试布局管理器的基本操作"""
    layout = CanvasLayoutManager(initial_cols=3, initial_rows=5)
    
    # 测试添加节点
    pos1 = layout.place_node("node1")
    assert pos1.row == 0 and pos1.col == 0
    
    pos2 = layout.place_node("node2")
    assert pos2.row == 1 and pos2.col == 0  # 在第一列的下一行
    
    # 测试指定位置放置节点
    specific_pos = GridPosition(0, 2)
    pos3 = layout.place_node("node3", specific_pos)
    assert pos3 == specific_pos
    
    print("✅ 基本操作测试通过")
    print(layout.print_layout())

if __name__ == "__main__":
    test_layout_manager_basic_operations()
    print("✅ T403 测试通过")
