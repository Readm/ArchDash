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

@pytest.fixture
def test_app_context():
    """提供一个包含graph和layout_manager的测试上下文"""
    graph = CalculationGraph()
    layout_manager = CanvasLayoutManager(initial_cols=4, initial_rows=12)
    graph.set_layout_manager(layout_manager)
    
    # 注入全局实例以供测试
    import app
    app.graph = graph
    app.layout_manager = layout_manager
    
    node1 = Node(name="Node1")
    graph.add_node(node1)
    layout_manager.place_node(node1.id)
    
    node2 = Node(name="Node2")
    graph.add_node(node2)
    layout_manager.place_node(node2.id, GridPosition(row=0, col=1))
    
    return graph, layout_manager

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

def test_create_arrows():
    """测试创建箭头覆盖层"""
    arrows_div = create_arrows()
    
    assert isinstance(arrows_div, list)
    assert len(arrows_div) == 1
    
    overlay = arrows_div[0]
    assert isinstance(overlay, html.Div)
    assert overlay.id == "arrows-overlay-dynamic"

def test_ensure_minimum_columns(test_app_context):
    """测试确保最小列数的功能"""
    _, layout_manager = test_app_context
    
    layout_manager.cols = 2
    ensure_minimum_columns(min_cols=3)
    assert layout_manager.cols == 3
    
    layout_manager.cols = 4
    ensure_minimum_columns(min_cols=3)
    assert layout_manager.cols == 4
