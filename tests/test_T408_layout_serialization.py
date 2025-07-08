#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T408 - 测试
从原始测试文件分离出的独立测试
"""

import pytest
from models import CanvasLayoutManager, GridPosition

def test_layout_serialization():
    """测试布局序列化"""
    layout = CanvasLayoutManager(initial_cols=2, initial_rows=3)
    
    # 添加节点
    layout.place_node("node1", GridPosition(0, 0))
    layout.place_node("node2", GridPosition(1, 1))
    
    # 获取布局字典
    layout_dict = layout.get_layout_dict()
    
    # 验证结构
    assert "grid_size" in layout_dict
    assert "node_positions" in layout_dict
    assert "column_layouts" in layout_dict
    
    assert layout_dict["grid_size"]["rows"] == 3
    assert layout_dict["grid_size"]["cols"] == 2
    assert layout_dict["node_positions"]["node1"] == {"row": 0, "col": 0}
    assert layout_dict["node_positions"]["node2"] == {"row": 1, "col": 1}
    
    print("✅ 序列化测试通过")
    print("布局字典:", layout_dict)

if __name__ == "__main__":
    test_layout_serialization()
    print("✅ T408 测试通过")
