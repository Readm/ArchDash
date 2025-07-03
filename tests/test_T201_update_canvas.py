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
    """测试画布更新函数"""
    canvas_content = update_canvas()
    
    assert isinstance(canvas_content, html.Div)
    
    # 检查是否有节点
    from app import graph
    if len(graph.nodes) == 0:
        # 空状态：应该返回空状态内容
        assert "开始构建计算图" in str(canvas_content)
    else:
        # 有节点状态：确认生成了包含节点的Row
        row = canvas_content.children[0]
        assert isinstance(row, dbc.Row)
        # 应该有包含内容的列
        non_empty_cols = [col for col in row.children if col.children]
        assert len(non_empty_cols) > 0

if __name__ == "__main__":
    test_update_canvas()
    print("✅ T201 画布更新测试通过")
