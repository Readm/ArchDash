#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T203 - 最小列数确保测试
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

def test_ensure_minimum_columns():
    """测试确保最小列数的功能"""
    from app import layout_manager
    
    layout_manager.cols = 2
    ensure_minimum_columns(min_cols=3)
    assert layout_manager.cols == 3
    
    layout_manager.cols = 4
    ensure_minimum_columns(min_cols=3)
    assert layout_manager.cols == 4

if __name__ == "__main__":
    test_ensure_minimum_columns()
    print("✅ T203 最小列数确保测试通过")
