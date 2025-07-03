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

# ==================== 辅助函数 ====================

def clean_state(selenium):
    """清理测试状态"""
    try:
        # 清理应用状态
        from app import graph, layout_manager
        graph.nodes.clear()
        layout_manager.node_positions.clear()
        layout_manager.position_nodes.clear()
        layout_manager._init_grid()
        graph.recently_updated_params.clear()
        
        # 刷新页面
        selenium.refresh()
        time.sleep(1)
        
        # 等待页面加载完成
        wait_for_page_load(selenium)
        
    except Exception as e:
        print(f"清理状态时出错: {e}")

def wait_for_page_load(selenium, timeout=5):
    """等待页面加载完成"""
    try:
        WebDriverWait(selenium, timeout).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        time.sleep(0.2)  # 减少额外等待时间
    except TimeoutException:
        print("页面加载超时")

def wait_for_element(selenium, by, value, timeout=5):
    """等待元素出现并返回"""
    try:
        element = WebDriverWait(selenium, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        print(f"等待元素超时: {by}={value}")
        return None

def wait_for_clickable(selenium, by, value, timeout=5):
    """等待元素可点击并返回"""
    try:
        element = WebDriverWait(selenium, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        return element
    except TimeoutException:
        print(f"wait_for_clickable超时: {by}={value}")
        return None

def wait_for_visible(selenium, by, value, timeout=10):
    """等待元素可见并返回"""
    try:
        element = WebDriverWait(selenium, timeout).until(
            EC.visibility_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        print(f"等待元素可见超时: {by}={value}")
        return None

def create_node(selenium, name, description):
    """创建节点"""
    try:
        # 等待添加节点按钮可点击
        add_node_btn = wait_for_clickable(selenium, By.ID, "add-node-from-graph-button")
        add_node_btn.click()
        
        # 等待模态框出现
        modal = wait_for_element(selenium, By.ID, "node-add-modal")
        assert modal is not None and modal.is_displayed(), "节点添加模态框应该出现"
        
        # 输入节点信息
        name_input = wait_for_element(selenium, By.ID, "node-add-name")
        name_input.clear()
        name_input.send_keys(name)
        
        desc_input = wait_for_element(selenium, By.ID, "node-add-description")
        desc_input.clear()
        desc_input.send_keys(description)
        
        # 保存节点
        save_btn = wait_for_clickable(selenium, By.ID, "node-add-save")
        save_btn.click()
        
        # 等待模态框消失
        WebDriverWait(selenium, 10).until_not(
            EC.visibility_of_element_located((By.ID, "node-add-modal"))
        )
        
        return True
    except Exception as e:
        print(f"创建节点失败: {e}")
        return False

def wait_for_node_count(selenium, expected_count, timeout=10):
    """等待节点数量达到预期值"""
    try:
        WebDriverWait(selenium, timeout).until(
            lambda driver: len(driver.find_elements(By.CSS_SELECTOR, ".node")) == expected_count
        )
        return True
    except TimeoutException:
        print(f"等待节点数量超时，期望: {expected_count}")
        return False

def delete_node(selenium, node_id):
    """删除指定节点"""
    try:
        # 点击节点的下拉菜单
        dropdown_btn = wait_for_clickable(selenium, By.CSS_SELECTOR, f"button[data-dash-id*='{node_id}'][id*='dropdown']")
        dropdown_btn.click()
        
        # 点击删除按钮
        delete_btn = wait_for_clickable(selenium, By.CSS_SELECTOR, f"button[data-dash-id*='{node_id}'][id*='delete']")
        delete_btn.click()
        
        # 等待节点消失
        WebDriverWait(selenium, 10).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, f".node[data-dash-id*='{node_id}']"))
        )
        
        return True
    except Exception as e:
        print(f"删除节点失败: {e}")
        return False

def add_parameter(selenium, node_id, param_name, param_value, param_unit):
    """为节点添加参数"""
    try:
        # 点击节点的参数添加按钮
        add_param_btn = wait_for_clickable(selenium, By.CSS_SELECTOR, f"button[data-dash-id*='{node_id}'][id*='add-param']")
        add_param_btn.click()
        
        # 等待参数添加模态框
        modal = wait_for_element(selenium, By.ID, "parameter-add-modal")
        assert modal.is_displayed(), "参数添加模态框应该出现"
        
        # 输入参数信息
        name_input = wait_for_element(selenium, By.ID, "parameter-add-name")
        name_input.clear()
        name_input.send_keys(param_name)
        
        value_input = wait_for_element(selenium, By.ID, "parameter-add-value")
        value_input.clear()
        value_input.send_keys(str(param_value))
        
        unit_input = wait_for_element(selenium, By.ID, "parameter-add-unit")
        unit_input.clear()
        unit_input.send_keys(param_unit)
        
        # 保存参数
        save_btn = wait_for_clickable(selenium, By.ID, "parameter-add-save")
        save_btn.click()
        
        # 等待模态框消失
        WebDriverWait(selenium, 10).until_not(
            EC.visibility_of_element_located((By.ID, "parameter-add-modal"))
        )
        
        return True
    except Exception as e:
        print(f"添加参数失败: {e}")
        return False

def edit_parameter(selenium, node_id, param_name, new_value):
    """编辑参数值"""
    try:
        # 找到参数输入框
        param_input = wait_for_element(selenium, By.CSS_SELECTOR, f"input[data-dash-id*='{node_id}'][data-param='{param_name}']")
        param_input.clear()
        param_input.send_keys(str(new_value))
        
        # 触发值变化事件
        param_input.send_keys(Keys.TAB)
        time.sleep(0.5)
        
        return True
    except Exception as e:
        print(f"编辑参数失败: {e}")
        return False

def get_node_element(selenium, node_name):
    """获取指定名称的节点元素"""
    try:
        nodes = selenium.find_elements(By.CSS_SELECTOR, ".node")
        for node in nodes:
            if node_name in node.text:
                return node
        return None
    except Exception as e:
        print(f"获取节点元素失败: {e}")
        return None



# ==================== 测试夹具 ====================

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """每个测试前后的设置和清理"""
    
    # 清理全局状态
    try:
        from app import graph, layout_manager
        
        graph.nodes.clear()
        layout_manager.node_positions.clear()
        layout_manager.position_nodes.clear()
        layout_manager._init_grid()
        graph.recently_updated_params.clear()
    except ImportError:
        # 如果导入失败，跳过清理
        pass
    
    yield  # 运行测试
    
    # 测试后清理（如果需要）
    try:
        from app import graph, layout_manager
        
        graph.nodes.clear()
        layout_manager.node_positions.clear()
        layout_manager.position_nodes.clear()
        layout_manager._init_grid()
        graph.recently_updated_params.clear()
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
        self.ctx = app.app_context()
        self.ctx.push()
        self.is_ready = threading.Event()

    def run(self):
        self.is_ready.set()
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()

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
    """启动Flask应用服务器 - 支持并发访问"""
    server = FlaskThread(app.server)
    server.daemon = True
    server.start()
    
    # Wait for server to be ready using the actual port
    server_url = f"http://127.0.0.1:{server.port}"
    assert wait_for_server(server_url), f"Server failed to start within timeout on port {server.port}"
    
    print(f"🌐 测试服务器启动成功: {server_url}")
    print(f"🔄 支持并发访问，每个测试用例使用独立浏览器会话")
    
    # 返回包含应用和服务器信息的字典
    yield {
        'app': app,
        'server': server,
        'port': server.port,
        'url': server_url
    }
    server.shutdown()

@pytest.fixture(scope="function")
def selenium(chrome_options, chrome_service, flask_app):
    """创建Selenium WebDriver实例 - 每个测试用例使用独立的浏览器实例"""
    driver = WebDriver(service=chrome_service, options=chrome_options)
    
    # 导航到应用页面
    server_url = flask_app['url']
    driver.get(server_url)
    
    yield driver
    driver.quit()

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

@pytest.fixture
def test_app_context():
    """提供测试应用上下文"""
    from app import app
    with app.test_request_context():
        yield app

@pytest.fixture
def app_server_driver(selenium, flask_app):
    """提供应用服务器和驱动器的组合"""
    return selenium, flask_app['url'] 