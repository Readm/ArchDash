import pytest
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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

@pytest.fixture(scope="session")
def chrome_options():
    """为WSL2环境配置Chrome选项"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--window-size=1920,1080")
    
    # 设置Chromium二进制路径
    if os.path.exists("/usr/bin/chromium-browser"):
        options.binary_location = "/usr/bin/chromium-browser"
    elif os.path.exists("/usr/bin/google-chrome"):
        options.binary_location = "/usr/bin/google-chrome"
    elif os.path.exists("/usr/bin/google-chrome-stable"):
        options.binary_location = "/usr/bin/google-chrome-stable"
    
    return options

def pytest_setup_options():
    """为dash-testing设置Chrome选项"""
    # 返回默认的Chrome选项用于headless测试
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--window-size=1920,1080")
    
    # 设置Chromium二进制路径
    if os.path.exists("/usr/bin/chromium-browser"):
        options.binary_location = "/usr/bin/chromium-browser"
    elif os.path.exists("/usr/bin/google-chrome"):
        options.binary_location = "/usr/bin/google-chrome"
    elif os.path.exists("/usr/bin/google-chrome-stable"):
        options.binary_location = "/usr/bin/google-chrome-stable"
    
    return options

# dash-testing已经提供了内置的无头模式支持
# 使用 pytest --headless 来启用无头模式
# 这是dash-testing官方推荐的方式 