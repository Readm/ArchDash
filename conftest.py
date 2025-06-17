import pytest
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from dash.testing.application_runners import import_app

@pytest.fixture(autouse=True)
def clean_test_state():
    """在每个测试前清理状态"""
    # 在测试开始前清理
    yield
    # 在测试结束后清理
    try:
        from app import graph, id_mapper, layout_manager, recently_updated_params
        graph.nodes.clear()
        id_mapper._node_mapping.clear()
        layout_manager.node_positions.clear()
        layout_manager.position_nodes.clear()
        layout_manager._init_grid()
        recently_updated_params.clear()
    except Exception as e:
        # 忽略清理错误，避免影响测试结果
        pass

def pytest_addoption(parser):
    """为pytest添加自定义命令行选项"""
    # 不再添加自己的--headless选项，因为dash-testing已经提供了
    pass

# dash-testing已经提供了内置的无头模式支持
# 使用 pytest --headless 来启用无头模式
# 这是dash-testing官方推荐的方式 