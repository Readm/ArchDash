#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T406 - 测试
从原始测试文件分离出的独立测试
"""

import pytest
from models import CanvasLayoutManager, GridPosition

def test_layout_manager_add_remove_columns():
    """测试添加和删除列功能"""
    layout = CanvasLayoutManager(initial_cols=2, initial_rows=3)
    initial_cols = layout.cols
    
    print(f"初始列数: {initial_cols}")
    print("初始布局:")
    print(layout.print_layout())
    
    # 测试添加列
    layout.add_column()
    assert layout.cols == initial_cols + 1
    print(f"添加列后列数: {layout.cols}")
    
    # 测试删除空列（应该成功）
    success = layout.remove_column()
    assert success == True
    assert layout.cols == initial_cols
    print(f"删除空列后列数: {layout.cols}")
    
    # 在最后一列放置一个节点
    layout.add_column()  # 先添加一列
    layout.place_node("test_node", GridPosition(0, layout.cols - 1))  # 放在最后一列
    
    print("在最后一列放置节点后:")
    print(layout.print_layout())
    
    # 尝试删除非空的最后一列（应该失败）
    success = layout.remove_column()
    assert success == False
    print(f"尝试删除非空列后列数: {layout.cols} (应该没有变化)")
    
    # 移除节点后再尝试删除列
    layout.remove_node("test_node")
    success = layout.remove_column()
    assert success == True
    print(f"删除节点后再删除列，当前列数: {layout.cols}")
    
    print("✅ 添加和删除列测试通过")

if __name__ == "__main__":
    test_layout_manager_add_remove_columns()
    print("✅ T406 测试通过")
