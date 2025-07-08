#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T407 - 测试
从原始测试文件分离出的独立测试
"""

import pytest
from models import CanvasLayoutManager, GridPosition

def test_layout_manager_remove_column_edge_cases():
    """测试删除列的边界情况"""
    # 测试只有一列时不能删除
    layout = CanvasLayoutManager(initial_cols=1, initial_rows=3)
    
    success = layout.remove_column()
    assert success == False
    assert layout.cols == 1
    print("✅ 正确阻止删除最后一列")
    
    # 测试多列情况下删除到只剩一列
    layout = CanvasLayoutManager(initial_cols=3, initial_rows=3)
    initial_cols = layout.cols
    
    # 删除所有空列直到只剩一列
    deleted_count = 0
    while layout.cols > 1:
        success = layout.remove_column()
        if success:
            deleted_count += 1
        else:
            break
    
    assert layout.cols == 1
    assert deleted_count == initial_cols - 1
    print(f"✅ 成功删除了 {deleted_count} 个空列，剩余 {layout.cols} 列")
    
    # 确认现在不能再删除
    success = layout.remove_column()
    assert success == False
    assert layout.cols == 1
    
    print("✅ 删除列边界情况测试通过")

if __name__ == "__main__":
    test_layout_manager_remove_column_edge_cases()
    print("✅ T407 测试通过")
