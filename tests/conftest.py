import pytest
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from dash.testing.application_runners import import_app

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """每个测试前后的设置和清理"""
    
    # 清理全局状态
    try:
        from app import graph, layout_manager, recently_updated_params
        
        graph.nodes.clear()
        layout_manager.node_positions.clear()
        layout_manager.position_nodes.clear()
        layout_manager._init_grid()
        recently_updated_params.clear()
    except ImportError:
        # 如果导入失败，跳过清理
        pass
    
    yield  # 运行测试
    
    # 测试后清理（如果需要）
    try:
        from app import graph, layout_manager, recently_updated_params
        
        graph.nodes.clear()
        layout_manager.node_positions.clear()
        layout_manager.position_nodes.clear()
        layout_manager._init_grid()
        recently_updated_params.clear()
    except ImportError:
        pass

# 用于测试的辅助函数
def create_test_node(name="测试节点", description="测试描述"):
    """创建测试节点的辅助函数"""
    from models import Node
    return Node(name=name, description=description)

def add_test_node_to_graph(node):
    """将测试节点添加到计算图的辅助函数"""
    from app import graph
    graph.add_node(node)
    return node.id

# 常用的测试配置
@pytest.fixture
def test_graph():
    """提供一个干净的测试计算图"""
    from app import graph
    graph.nodes.clear()
    return graph

@pytest.fixture
def test_layout_manager():
    """提供一个干净的测试布局管理器"""
    from app import layout_manager
    layout_manager.node_positions.clear()
    layout_manager.position_nodes.clear()
    layout_manager._init_grid()
    return layout_manager

# 测试数据
@pytest.fixture
def sample_nodes():
    """提供示例节点数据"""
    from models import Node
    return [
        Node(name="输入节点", description="输入数据节点"),
        Node(name="计算节点", description="执行计算的节点"),
        Node(name="输出节点", description="输出结果节点")
    ]

# 性能测试相关
@pytest.fixture
def performance_timer():
    """性能测试计时器"""
    import time
    start_time = time.time()
    yield
    end_time = time.time()
    print(f"\n⏱️ 测试执行时间: {end_time - start_time:.3f}秒")

# 日志配置
@pytest.fixture(autouse=True)
def configure_logging():
    """配置测试日志"""
    import logging
    logging.basicConfig(
        level=logging.WARNING,  # 只显示警告和错误
        format='%(levelname)s: %(message)s'
    )

# 错误处理
@pytest.fixture
def suppress_errors():
    """抑制某些预期的错误输出"""
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)

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

def pytest_configure(config):
    """
    Called before tests are collected.
    """
    is_ci = os.environ.get('TEST_ENV') == 'CI'
    if is_ci:
        # CI环境特定配置
        os.environ['NO_BROWSER'] = '1'
        os.environ['DASH_TEST_CHROMEPATH'] = ''  # 使用无头Chrome
        os.environ['DASH_TESTING_MODE'] = 'True'

@pytest.fixture(scope='session')
def dash_thread_server():
    """
    启动测试服务器的fixture
    """
    is_ci = os.environ.get('TEST_ENV') == 'CI'
    options = {'headless': True} if is_ci else {}
    
    app = import_app('app')
    
    yield app.server 