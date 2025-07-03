#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置文件
提供所有测试文件共用的夹具和配置
"""

import pytest
import os
import sys
import time
import threading
import subprocess
import signal
from pathlib import Path
from urllib.parse import urlparse
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver import Chrome as WebDriver

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入应用模块
from app import app

# 测试配置
TEST_TIMEOUT = 60  # 测试超时时间（秒）
SERVER_START_TIMEOUT = 30  # 服务器启动超时时间（秒）
PAGE_LOAD_TIMEOUT = 10  # 页面加载超时时间（秒）

# 端口分配配置
BASE_PORT = 8051
PORTS_PER_WORKER = 10

def get_worker_port_range():
    """获取当前worker的端口范围"""
    worker_id = os.environ.get('PYTEST_XDIST_WORKER', '0')
    try:
        worker_num = int(worker_id.replace('gw', ''))
    except ValueError:
        worker_num = 0
    
    start_port = BASE_PORT + (worker_num * PORTS_PER_WORKER)
    end_port = start_port + PORTS_PER_WORKER - 1
    
    return start_port, end_port

def find_available_port(start_port, end_port):
    """在指定范围内查找可用端口"""
    import socket
    
    for port in range(start_port, end_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    
    raise RuntimeError(f"在端口范围 {start_port}-{end_port} 内没有找到可用端口")

def wait_for_server(url, timeout=SERVER_START_TIMEOUT):
    """等待服务器启动"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        
        time.sleep(0.5)
    
    return False

class FlaskThread(threading.Thread):
    """Flask应用服务器线程"""
    
    def __init__(self, app, port=None):
        super().__init__()
        self.app = app
        self.port = port or find_available_port(*get_worker_port_range())
        self.server = None
        self._shutdown_event = threading.Event()
    
    def run(self):
        """运行Flask服务器"""
        try:
            self.server = self.app.run(
                host='127.0.0.1',
                port=self.port,
                debug=False,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            print(f"Flask服务器启动失败: {e}")
    
    def shutdown(self):
        """关闭服务器"""
        self._shutdown_event.set()
        if self.server:
            try:
                # 发送SIGTERM信号
                os.kill(os.getpid(), signal.SIGTERM)
            except:
                pass

@pytest.fixture(scope="session")
def chrome_options():
    """Chrome浏览器选项配置"""
    options = Options()
    
    # 基本配置
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-images')
    options.add_argument('--disable-javascript')
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-features=VizDisplayCompositor')
    
    # 窗口配置
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    
    # 性能优化
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-features=TranslateUI')
    options.add_argument('--disable-ipc-flooding-protection')
    
    # 日志配置
    options.add_argument('--log-level=3')
    options.add_argument('--silent')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # 无头模式（可通过环境变量控制）
    if os.environ.get('HEADLESS', 'true').lower() == 'true':
        options.add_argument('--headless')
    
    return options

@pytest.fixture(scope="session")
def chrome_service():
    """Chrome服务配置"""
    # 查找Chrome可执行文件
    chrome_paths = [
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium',
        '/snap/bin/chromium',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',  # Windows
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',  # Windows
    ]
    
    chrome_path = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_path = path
            break
    
    if not chrome_path:
        # 尝试使用系统PATH中的Chrome
        try:
            result = subprocess.run(['which', 'google-chrome'], capture_output=True, text=True)
            if result.returncode == 0:
                chrome_path = result.stdout.strip()
        except:
            pass
    
    if not chrome_path:
        # 最后尝试使用默认路径
        chrome_path = 'google-chrome'
    
    print(f"使用Chrome路径: {chrome_path}")
    
    service = Service(executable_path=chrome_path)
    return service

@pytest.fixture(scope="function")
def selenium(chrome_options, chrome_service, flask_app):
    """创建Selenium WebDriver实例 - 每个测试用例使用独立的浏览器实例"""
    driver = WebDriver(service=chrome_service, options=chrome_options)
    
    # 为每个测试生成唯一的会话ID
    import uuid
    session_id = str(uuid.uuid4())
    
    # 导航到应用页面，添加会话ID参数
    server_url = flask_app['url']
    test_url = f"{server_url}?_sid={session_id}"
    driver.get(test_url)
    
    print(f"🔗 测试会话ID: {session_id}")
    
    yield driver
    driver.quit()

@pytest.fixture(scope="session")
def flask_app():
    """启动Flask应用服务器 - 每个worker使用独立的应用实例"""
    from app import app as original_app
    
    # 为每个worker创建独立的应用实例
    worker_id = os.environ.get('PYTEST_XDIST_WORKER', '0')
    
    # 确保每个worker有独立的会话管理
    original_app.server.secret_key = f"test_secret_key_{worker_id}"
    
    server = FlaskThread(original_app.server)
    server.daemon = True
    server.start()
    
    # Wait for server to be ready using the actual port
    server_url = f"http://127.0.0.1:{server.port}"
    assert wait_for_server(server_url), f"Server failed to start within timeout on port {server.port}"
    
    print(f"🌐 Worker {worker_id} 测试服务器启动成功: {server_url}")
    print(f"🔄 使用会话隔离，每个测试有独立的graph实例")
    
    # 返回包含应用和服务器信息的字典
    yield {
        'app': original_app,
        'server': server,
        'port': server.port,
        'url': server_url,
        'worker_id': worker_id
    }
    
    # 清理
    server.shutdown()
    server.join(timeout=5)

@pytest.fixture(scope="function")
def wait():
    """WebDriverWait实例"""
    def _wait(driver, timeout=PAGE_LOAD_TIMEOUT):
        return WebDriverWait(driver, timeout)
    return _wait

@pytest.fixture(scope="function")
def clean_test_environment(selenium):
    """清理测试环境"""
    try:
        # 清理浏览器状态
        selenium.delete_all_cookies()
        selenium.execute_script("window.localStorage.clear();")
        selenium.execute_script("window.sessionStorage.clear();")
        
        # 刷新页面
        selenium.refresh()
        time.sleep(1)
        
        yield
        
    except Exception as e:
        print(f"清理测试环境时出错: {e}")
        yield

@pytest.fixture(scope="session")
def test_data():
    """测试数据"""
    return {
        'nodes': [
            {'name': '输入节点', 'description': '输入数据节点'},
            {'name': '计算节点', 'description': '执行计算的节点'},
            {'name': '输出节点', 'description': '输出结果节点'}
        ],
        'parameters': [
            {'name': '参数1', 'value': 10, 'unit': 'mm'},
            {'name': '参数2', 'value': 20, 'unit': 'kg'},
            {'name': '参数3', 'value': 30, 'unit': 's'}
        ]
    }

@pytest.fixture(scope="function")
def setup_test_nodes(selenium, test_data):
    """设置测试节点"""
    try:
        from utils import clean_state, create_node, wait_for_node_count
        
        # 清理状态
        clean_state(selenium)
        
        # 创建测试节点
        created_nodes = []
        for node_data in test_data['nodes']:
            if create_node(selenium, node_data['name'], node_data['description']):
                created_nodes.append(node_data['name'])
                wait_for_node_count(selenium, len(created_nodes))
        
        yield created_nodes
        
    except Exception as e:
        print(f"设置测试节点失败: {e}")
        yield []

@pytest.fixture(scope="function")
def setup_test_parameters(selenium, setup_test_nodes):
    """设置测试参数"""
    try:
        from utils import add_parameter
        
        # 为第一个节点添加参数
        if setup_test_nodes:
            node_id = "1"  # 假设第一个节点的ID是1
            for param_data in [
                {'name': '参数1', 'value': 10, 'unit': 'mm'},
                {'name': '参数2', 'value': 20, 'unit': 'kg'}
            ]:
                add_parameter(selenium, node_id, param_data['name'], param_data['value'], param_data['unit'])
        
        yield
        
    except Exception as e:
        print(f"设置测试参数失败: {e}")
        yield

# 性能测试夹具
@pytest.fixture(scope="function")
def performance_timer():
    """性能计时器"""
    start_time = time.time()
    
    def get_elapsed():
        return time.time() - start_time
    
    return get_elapsed

# 错误处理夹具
@pytest.fixture(scope="function")
def error_handler():
    """错误处理器"""
    errors = []
    
    def add_error(error):
        errors.append(error)
    
    def get_errors():
        return errors
    
    return add_error, get_errors

# 调试夹具
@pytest.fixture(scope="function")
def debug_info(selenium):
    """调试信息收集器"""
    def collect_info():
        info = {
            'url': selenium.current_url,
            'title': selenium.title,
            'page_source_length': len(selenium.page_source),
            'cookies': len(selenium.get_cookies()),
            'window_size': selenium.get_window_size(),
            'screenshot': None
        }
        
        try:
            screenshot_path = f"debug_screenshot_{int(time.time())}.png"
            selenium.save_screenshot(screenshot_path)
            info['screenshot'] = screenshot_path
        except:
            pass
        
        return info
    
    return collect_info

# 并行测试支持
def pytest_configure(config):
    """pytest配置"""
    # 添加自定义标记
    config.addinivalue_line("markers", "slow: 标记为慢速测试")
    config.addinivalue_line("markers", "integration: 标记为集成测试")
    config.addinivalue_line("markers", "ui: 标记为UI测试")
    config.addinivalue_line("markers", "headless: 标记为无头模式测试")

def pytest_collection_modifyitems(config, items):
    """修改测试项"""
    for item in items:
        # 为UI测试添加超时
        if "ui" in item.keywords or "selenium" in str(item.fspath):
            item.add_marker(pytest.mark.timeout(60))
        
        # 为集成测试添加标记
        if "integration" in item.keywords:
            item.add_marker(pytest.mark.integration)

# 测试报告配置
def pytest_html_report_title(report):
    """HTML报告标题"""
    report.title = "ArchDash 测试报告"

def pytest_html_results_table_header(cells):
    """HTML结果表头"""
    cells.insert(2, html.th('描述'))
    cells.pop()

def pytest_html_results_table_row(report, cells):
    """HTML结果表行"""
    cells.insert(2, html.td(report.description))
    cells.pop()

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """生成测试报告"""
    outcome = yield
    report = outcome.get_result()
    
    # 添加描述
    report.description = str(item.function.__doc__)
    
    # 添加截图（如果测试失败）
    if report.when == "call" and report.failed:
        try:
            # 获取selenium实例
            selenium = item.funcargs.get('selenium')
            if selenium:
                screenshot_path = f"failure_{item.name}_{int(time.time())}.png"
                selenium.save_screenshot(screenshot_path)
                report.extra = [pytest_html.extras.image(screenshot_path)]
        except:
            pass 