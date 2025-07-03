import pytest
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from dash.testing.application_runners import import_app
import threading
import time
import multiprocessing
from werkzeug.serving import make_server
from app import app

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

class FlaskThread(threading.Thread):
    def __init__(self, app, port=8050):
        threading.Thread.__init__(self)
        self.srv = make_server('127.0.0.1', port, app)
        self.ctx = app.app_context()
        self.ctx.push()
        self.is_ready = threading.Event()

    def run(self):
        self.is_ready.set()
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()

def wait_for_server(url, timeout=10):
    """Wait for server to be ready"""
    import requests
    from requests.exceptions import RequestException
    import time
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except RequestException:
            time.sleep(0.1)
    return False

@pytest.fixture(scope="session")
def chrome_options():
    """配置Chrome选项"""
    options = Options()
    # 移除headless模式
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=800,600")  # 设置更小的窗口尺寸
    return options

@pytest.fixture(scope="session")
def chrome_service():
    """配置Chrome服务"""
    service = Service()
    return service

@pytest.fixture(scope="session")
def flask_app():
    """启动Flask应用服务器"""
    server = FlaskThread(app.server)
    server.daemon = True
    server.start()
    
    # Wait for server to be ready
    assert wait_for_server("http://127.0.0.1:8050"), "Server failed to start within timeout"
    
    yield app
    server.shutdown()

@pytest.fixture(scope="session")
def selenium(chrome_options, chrome_service, flask_app):
    """创建Selenium WebDriver实例"""
    driver = WebDriver(service=chrome_service, options=chrome_options)
    yield driver
    driver.quit()

@pytest.fixture(autouse=True)
def clean_app_state():
    """每个测试前清理应用状态"""
    from app import graph, layout_manager
    graph.nodes.clear()
    layout_manager.node_positions.clear()
    layout_manager.position_nodes.clear()
    layout_manager._init_grid()
    yield

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
        os.environ['NO_BROWSER'] = '0'  # 允许使用浏览器
        os.environ['DASH_TEST_CHROMEPATH'] = ''
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