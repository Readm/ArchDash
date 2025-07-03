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

def test_update_canvas(test_app_context):
    """测试画布更新函数"""
    canvas_content = update_canvas()
    
    assert isinstance(canvas_content, html.Div)
    # 确认生成了包含节点的Row
    row = canvas_content.children[0]
    assert isinstance(row, dbc.Row)
    # 应该有2个包含内容的列
    non_empty_cols = [col for col in row.children if col.children]
    assert len(non_empty_cols) == 2

if __name__ == "__main__":
    test_update_canvas()
    print("✅ T201 画布更新测试通过")
