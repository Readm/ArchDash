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
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys


# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ==================== 测试辅助函数已移至utils.py ====================
# 所有测试辅助函数都已迁移到utils.py中，conftest.py只保留pytest fixtures

# ==================== 测试夹具 ====================

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """全局测试设置和清理"""
    # 测试前设置
    try:
        from app import graph, layout_manager
        # 清理状态但不影响其他并发测试
        graph.nodes.clear()
        layout_manager.node_positions.clear()
        layout_manager.position_nodes.clear()
        layout_manager._init_grid()
        graph.recently_updated_params.clear()
        
        # 清理任何残留的回调或状态
        if hasattr(graph, '_callbacks'):
            graph._callbacks.clear()
        if hasattr(graph, '_dependency_cache'):
            graph._dependency_cache.clear()
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
    except ImportError:
        pass
    except Exception as e:
        print(f"⚠️ 测试前状态清理异常: {e}")
    
    yield
    
    # 测试后清理
    try:
        from app import graph, layout_manager
        
        # 完全清理状态
        graph.nodes.clear()
        layout_manager.node_positions.clear()
        layout_manager.position_nodes.clear()
        layout_manager._init_grid()
        graph.recently_updated_params.clear()
        
        # 清理任何残留的回调或状态
        if hasattr(graph, '_callbacks'):
            graph._callbacks.clear()
        if hasattr(graph, '_dependency_cache'):
            graph._dependency_cache.clear()
        
        # 重置应用状态到初始状态
        try:
            if hasattr(graph, 'reset'):
                graph.reset()
            if hasattr(layout_manager, 'reset'):
                layout_manager.reset()
        except Exception as e:
            print(f"⚠️ 应用状态重置异常: {e}")
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
    except ImportError:
        pass
    except Exception as e:
        print(f"⚠️ 测试后状态清理异常: {e}")
        # 如果清理失败，记录但不中断测试

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
    def __init__(self, app, port=None):  # 使用不同的端口避免冲突
        threading.Thread.__init__(self)
        
        # 获取worker ID，用于端口分配
        worker_id = os.environ.get('PYTEST_XDIST_WORKER', '0')
        
        # 解析worker ID：格式可能是 'gw0', 'gw1', 'gw2' 等
        if worker_id.startswith('gw'):
            try:
                worker_num = int(worker_id[2:])  # 提取数字部分
            except ValueError:
                worker_num = 0
        else:
            try:
                worker_num = int(worker_id)
            except ValueError:
                worker_num = 0
        
        if worker_num > 0:
            # 并行模式：每个worker使用不同端口范围
            base_port = 8051 + (worker_num * 10)  # 每个worker间隔10个端口
        else:
            # 串行模式：使用默认端口
            base_port = 8051
        
        # 尝试绑定端口
        for port_offset in range(10):  # 每个worker最多尝试10个端口
            try_port = base_port + port_offset
            try:
                self.srv = make_server('127.0.0.1', try_port, app)
                port = try_port
                break
            except OSError:
                continue
        else:
            raise OSError(f"Worker {worker_id} 无法找到可用端口 (范围: {base_port}-{base_port+9})")
        
        self.port = port
        self.app = app
        self.ctx = app.app_context()
        self.ctx.push()
        self.is_ready = threading.Event()
        self.is_shutdown = threading.Event()
        self.exception = None  # 记录异常

    def run(self):
        try:
            self.is_ready.set()
            self.srv.serve_forever()
        except Exception as e:
            self.exception = e
            print(f"❌ Flask服务器异常: {e}")
        finally:
            self.is_shutdown.set()

    def shutdown(self):
        try:
            self.srv.shutdown()
            self.is_shutdown.wait(timeout=10)  # 等待关闭完成
        except Exception as e:
            print(f"⚠️ 关闭Flask服务器时出错: {e}")
    
    def health_check(self):
        """检查服务器健康状态"""
        if self.exception:
            return False, f"服务器异常: {self.exception}"
        if not self.is_ready.is_set():
            return False, "服务器未就绪"
        if self.is_shutdown.is_set():
            return False, "服务器已关闭"
        return True, "服务器正常"

def wait_for_server(url, timeout=30):
    """Wait for server to be ready"""
    import requests
    from requests.exceptions import RequestException
    import time
    import os
    
    # 临时禁用所有代理环境变量
    original_proxies = {}
    for proxy_var in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
        if proxy_var in os.environ:
            original_proxies[proxy_var] = os.environ[proxy_var]
            del os.environ[proxy_var]
    
    try:
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5, proxies={'http': None, 'https': None})
                if response.status_code == 200:
                    return True
            except RequestException:
                time.sleep(0.5)
        return False
    finally:
        # 恢复原始代理设置
        for proxy_var, value in original_proxies.items():
            os.environ[proxy_var] = value

def check_flask_health(flask_app):
    """检查Flask应用健康状态"""
    try:
        server = flask_app['server']
        is_healthy, message = server.health_check()
        if not is_healthy:
            print(f"⚠️ Flask应用健康检查失败: {message}")
            return False
        
        # 尝试访问服务器
        import requests
        import os
        
        # 临时禁用所有代理环境变量
        original_proxies = {}
        for proxy_var in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
            if proxy_var in os.environ:
                original_proxies[proxy_var] = os.environ[proxy_var]
                del os.environ[proxy_var]
        
        try:
            response = requests.get(
                flask_app['url'], 
                timeout=5, 
                proxies={'http': None, 'https': None}
            )
            if response.status_code != 200:
                print(f"⚠️ Flask应用响应异常: {response.status_code}")
                return False
        except Exception as e:
            print(f"⚠️ Flask应用连接失败: {e}")
            return False
        finally:
            # 恢复原始代理设置
            for proxy_var, value in original_proxies.items():
                os.environ[proxy_var] = value
        
        return True
    except Exception as e:
        print(f"⚠️ Flask应用健康检查异常: {e}")
        return False

@pytest.fixture(scope="session")
def chrome_options():
    """配置Chrome选项"""
    options = Options()
    # 启用headless模式以支持WSL2环境
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=800,600")  # 设置更小的窗口尺寸
    # 添加更多稳定性选项
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    # 设置页面加载策略
    options.page_load_strategy = 'eager'
    
    # Try system Chrome first, fallback to downloaded Chrome
    import os
    system_chrome_paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable", 
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/snap/bin/chromium",
        "/home/readm/chrome_install/opt/google/chrome/chrome"
    ]
    
    for chrome_path in system_chrome_paths:
        if os.path.exists(chrome_path):
            options.binary_location = chrome_path
            break
    return options

@pytest.fixture(scope="session")
def chrome_service():
    """配置Chrome服务"""
    # 使用本地安装的Chrome
    chrome_binary = "/home/readm/chrome_install/opt/google/chrome/chrome"
    service = Service()
    return service

@pytest.fixture(scope="session")
def flask_app():
    """启动Flask应用服务器 - 支持并发访问"""
    server = FlaskThread(app.server)
    server.daemon = True
    server.start()
    
    # Wait for server to be ready using the actual port
    server_url = f"http://127.0.0.1:{server.port}"
    
    # 增加健康检查
    if not wait_for_server(server_url):
        # 如果服务器启动失败，尝试获取异常信息
        if server.exception:
            raise Exception(f"Flask服务器启动失败: {server.exception}")
        else:
            raise Exception(f"Flask服务器在端口{server.port}上启动超时")
    
    print(f"🌐 测试服务器启动成功: {server_url}")
    print(f"🔄 支持并发访问，每个测试用例使用独立浏览器会话")
    
    # 返回包含应用和服务器信息的字典
    flask_app_data = {
        'app': app,
        'server': server,
        'port': server.port,
        'url': server_url
    }
    
    try:
        yield flask_app_data
    finally:
        # 确保服务器被正确关闭
        try:
            print(f"🔄 正在关闭Flask服务器 (端口: {server.port})...")
            server.shutdown()
            print("✅ Flask服务器已关闭")
        except Exception as e:
            print(f"❌ 关闭Flask服务器时出错: {e}")
        
        # 最后检查服务器状态
        if server.exception:
            print(f"⚠️ 服务器运行期间发生异常: {server.exception}")

# 添加专门的健康检查fixture
@pytest.fixture(scope="function")
def flask_health_check(flask_app):
    """在每个测试前后检查Flask应用健康状态"""
    # 测试前检查
    if not check_flask_health(flask_app):
        pytest.fail("测试前Flask应用健康检查失败")
    
    yield flask_app
    
    # 测试后检查
    if not check_flask_health(flask_app):
        print("⚠️ 测试后Flask应用健康检查失败，可能影响后续测试")
        # 不失败，但记录警告

@pytest.fixture(scope="function")
def selenium(chrome_options, chrome_service, flask_app):
    """为每个测试提供独立的浏览器实例"""
    # 创建WebDriver前先检查Flask应用健康状态
    if not check_flask_health(flask_app):
        pytest.fail("Flask应用健康检查失败，无法创建WebDriver")
    
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    
    try:
        # 生成唯一的会话ID
        import uuid
        session_id = str(uuid.uuid4())
        server_url = flask_app['url']
        url = f"{server_url}?_sid={session_id}"
        
        # 访问URL前再次检查Flask应用状态
        if not check_flask_health(flask_app):
            raise Exception("Flask应用在WebDriver创建后变为不健康状态")
        
        driver.get(url)
        time.sleep(1)  # 等待页面初始化
        
        # 验证页面加载成功
        try:
            driver.find_element(By.TAG_NAME, "body")
        except Exception as e:
            raise Exception(f"页面加载失败: {e}")
        
        yield driver
        
    except Exception as e:
        print(f"❌ Selenium初始化失败: {e}")
        driver.quit()
        raise
    finally:
        # 清理
        try:
            driver.quit()
        except Exception as e:
            print(f"⚠️ 关闭WebDriver时出错: {e}")

def pytest_configure(config):
    """全局pytest配置"""
    # 设置测试环境变量
    os.environ['TESTING'] = 'True'
    
    # 配置日志级别
    import logging
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

@pytest.fixture(scope='session')
def dash_thread_server():
    """为Dash应用提供线程化服务器"""
    port = 8052  # 不同的端口避免冲突
    server = make_server('127.0.0.1', port, app.server)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(2)  # 等待服务器启动
    yield f"http://127.0.0.1:{port}"
    server.shutdown()

@pytest.fixture
def test_app_context():
    """提供应用上下文"""
    with app.app_context():
        yield

@pytest.fixture
def app_server_driver(selenium, flask_app):
    """提供应用服务器和驱动器的组合"""
    # 为了保持向后兼容，返回两个值：driver 和 url
    return selenium, flask_app['url'] 