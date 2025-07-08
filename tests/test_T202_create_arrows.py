#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T202 - 箭头创建测试
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

def test_create_arrows():
    """测试创建箭头覆盖层"""
    arrows_div = create_arrows()
    
    assert isinstance(arrows_div, list)
    assert len(arrows_div) == 1
    
    overlay = arrows_div[0]
    assert isinstance(overlay, html.Div)
    assert overlay.id == "arrows-overlay-dynamic"

if __name__ == "__main__":
    test_create_arrows()
    print("✅ T202 箭头创建测试通过")
