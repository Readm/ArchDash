#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T404 - 测试
从原始测试文件分离出的独立测试
"""

import pytest
from models import CanvasLayoutManager, GridPosition

def test_layout_manager_node_movements():
    """测试节点移动功能"""
    layout = CanvasLayoutManager(initial_cols=3, initial_rows=5)
    
    # 创建测试节点
    layout.place_node("nodeA", GridPosition(0, 0))
    layout.place_node("nodeB", GridPosition(1, 0))
    layout.place_node("nodeC", GridPosition(2, 0))
    
    print("初始布局:")
    print(layout.print_layout())
    
    # 测试节点上移
    success = layout.move_node_up("nodeB")
    assert success == True
    assert layout.get_node_position("nodeB") == GridPosition(0, 0)
    assert layout.get_node_position("nodeA") == GridPosition(1, 0)  # 被交换了
    
    print("nodeB上移后:")
    print(layout.print_layout())
    
    # 测试节点右移
    success = layout.move_node_right("nodeB")
    assert success == True
    assert layout.get_node_position("nodeB").col == 1
    
    print("nodeB右移后:")
    print(layout.print_layout())
    
    print("✅ 节点移动测试通过")

if __name__ == "__main__":
    test_layout_manager_node_movements()
    print("✅ T404 测试通过")
