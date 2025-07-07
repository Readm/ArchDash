#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T201 - 画布更新测试
从原始测试文件分离出的独立测试
"""

import pytest
from app import (
    update_canvas,
    create_arrows,
    auto_remove_empty_last_column,
    ensure_minimum_columns
)
from models import CalculationGraph, Node, Parameter, CanvasLayoutManager, GridPosition
from dash import html
import dash_bootstrap_components as dbc
import app

def test_update_canvas():
    """测试画布更新函数 - 支持空状态和有节点状态"""
    canvas_content = update_canvas()
    
    assert isinstance(canvas_content, html.Div)
    
    # 转换为字符串查找是否包含空状态标识
    canvas_str = str(canvas_content)
    
    # 检查是否是空状态
    if 'empty-state' in canvas_str:
        print("✅ 检测到空状态画布")
        # 验证空状态结构（支持单引号和双引号）
        assert ("data-ready='true'" in canvas_str or 
                'data-ready="true"' in canvas_str or 
                'data-ready=True' in canvas_str)
        return
    
    # 如果不是空状态，检查是否有节点状态
    if 'canvas-with-arrows' in canvas_str:
        print("✅ 检测到有节点状态画布")
        # 验证有节点状态结构
        assert hasattr(canvas_content, 'children') and len(canvas_content.children) > 0
        # 第一个子元素应该是Row（包含节点）
        first_child = canvas_content.children[0]
        if isinstance(first_child, dbc.Row):
            print("✅ 找到节点Row结构")
        return
    
    # 未知状态，输出调试信息
    print(f"🔍 画布内容（前500字符）: {canvas_str[:500]}...")
    assert False, "画布既不是空状态也不是有节点状态"

if __name__ == "__main__":
    test_update_canvas()
    print("✅ T201 画布更新测试通过")
