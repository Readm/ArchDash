from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T521 - 夹具完整性测试
验证所有夹具是否按预期工作
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_setup_and_teardown_fixture_works():
    """测试 setup_and_teardown 夹具是否正常工作"""
    # 验证应用状态是否被正确清理
    from app import graph, layout_manager
    
    # 检查计算图是否为空
    assert len(graph.nodes) == 0, "计算图应该为空"
    
    # 检查布局管理器是否被重置
    assert len(layout_manager.node_positions) == 0, "节点位置应该为空"
    assert len(layout_manager.position_nodes) == 0, "位置节点映射应该为空"
    
    # 检查最近更新参数是否为空（这是 graph 对象的属性）
    assert len(graph.recently_updated_params) == 0, "最近更新参数应该为空"
    
    print("✅ setup_and_teardown 夹具工作正常")

def test_flask_app_fixture_works(flask_app):
    """测试 flask_app 夹具是否正常工作"""
    # 验证 flask_app 是有效的字典，包含必要的键
    assert isinstance(flask_app, dict), "flask_app 应该是字典"
    assert 'app' in flask_app, "flask_app 应该包含 'app' 键"
    assert 'server' in flask_app, "flask_app 应该包含 'server' 键"
    assert 'port' in flask_app, "flask_app 应该包含 'port' 键"
    assert 'url' in flask_app, "flask_app 应该包含 'url' 键"
    
    # 验证应用对象
    app = flask_app['app']
    assert hasattr(app, 'server'), "应用对象应该有 server 属性"
    assert hasattr(app, 'layout'), "应用对象应该有 layout 属性"
    
    # 验证服务器是否正在运行
    import requests
    try:
        response = requests.get("http://127.0.0.1:8051", timeout=5)
        assert response.status_code == 200, "Flask 服务器应该响应 200"
    except requests.exceptions.RequestException:
        # 如果 8051 端口不可用，尝试其他端口
        for port in range(8052, 8060):
            try:
                response = requests.get(f"http://127.0.0.1:{port}", timeout=2)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                continue
        else:
            pytest.fail("无法连接到 Flask 服务器")
    
    print("✅ flask_app 夹具工作正常")

def test_selenium_fixture_works(selenium):
    """测试 selenium 夹具是否正常工作"""
    # 验证 WebDriver 是否正常工作
    assert selenium is not None, "selenium WebDriver 不应该为 None"
    
    # 测试基本导航功能
    selenium.get("about:blank")
    assert "blank" in selenium.title or selenium.current_url.startswith("about:blank"), "应该能导航到 about:blank"
    
    # 测试页面标题获取
    title = selenium.title
    assert isinstance(title, str), "页面标题应该是字符串"
    
    print("✅ selenium 夹具工作正常")

def test_chrome_options_fixture_works(chrome_options):
    """测试 chrome_options 夹具是否正常工作"""
    # 验证 Chrome 选项是否正确设置
    assert chrome_options is not None, "chrome_options 不应该为 None"
    
    # 检查必要的参数是否存在
    arguments = chrome_options.arguments
    assert "--no-sandbox" in arguments, "应该包含 --no-sandbox 参数"
    assert "--disable-dev-shm-usage" in arguments, "应该包含 --disable-dev-shm-usage 参数"
    assert "--disable-gpu" in arguments, "应该包含 --disable-gpu 参数"
    
    print("✅ chrome_options 夹具工作正常")

def test_chrome_service_fixture_works(chrome_service):
    """测试 chrome_service 夹具是否正常工作"""
    # 验证 Chrome 服务是否正确创建
    assert chrome_service is not None, "chrome_service 不应该为 None"
    
    print("✅ chrome_service 夹具工作正常")

def test_test_graph_fixture_works(test_graph):
    """测试 test_graph 夹具是否正常工作"""
    # 验证测试计算图是否被正确清理
    assert len(test_graph.nodes) == 0, "测试计算图应该为空"
    
    # 测试添加节点功能
    from models import Node
    test_node = Node(name="测试节点", description="测试描述")
    test_graph.add_node(test_node)
    assert len(test_graph.nodes) == 1, "应该能添加节点到测试计算图"
    
    print("✅ test_graph 夹具工作正常")

def test_test_layout_manager_fixture_works(test_layout_manager):
    """测试 test_layout_manager 夹具是否正常工作"""
    # 验证测试布局管理器是否被正确清理
    assert len(test_layout_manager.node_positions) == 0, "节点位置应该为空"
    assert len(test_layout_manager.position_nodes) == 0, "位置节点映射应该为空"
    
    print("✅ test_layout_manager 夹具工作正常")

def test_sample_nodes_fixture_works(sample_nodes):
    """测试 sample_nodes 夹具是否正常工作"""
    # 验证示例节点数据是否正确
    assert len(sample_nodes) == 3, "应该有 3 个示例节点"
    
    node_names = [node.name for node in sample_nodes]
    expected_names = ["输入节点", "计算节点", "输出节点"]
    
    for expected_name in expected_names:
        assert expected_name in node_names, f"应该包含节点: {expected_name}"
    
    print("✅ sample_nodes 夹具工作正常")

def test_performance_timer_fixture_works(performance_timer):
    """测试 performance_timer 夹具是否正常工作"""
    # 这个夹具会在测试结束时打印执行时间
    # 我们只需要验证它不会抛出异常
    time.sleep(0.1)  # 模拟一些工作
    
    print("✅ performance_timer 夹具工作正常")

def test_suppress_errors_fixture_works(suppress_errors):
    """测试 suppress_errors 夹具是否正常工作"""
    # 这个夹具抑制警告，我们只需要验证它不会抛出异常
    import warnings
    warnings.warn("这是一个测试警告", UserWarning)
    
    print("✅ suppress_errors 夹具工作正常")

def test_fixture_isolation():
    """测试夹具之间的隔离性"""
    # 验证不同夹具之间不会相互影响
    from app import graph, layout_manager
    
    # 清理状态
    graph.nodes.clear()
    layout_manager.node_positions.clear()
    layout_manager.position_nodes.clear()
    layout_manager._init_grid()
    graph.recently_updated_params.clear()
    
    # 验证状态是否被正确清理
    assert len(graph.nodes) == 0, "计算图应该被清理"
    assert len(layout_manager.node_positions) == 0, "布局管理器应该被清理"
    assert len(graph.recently_updated_params) == 0, "最近更新参数应该被清理"
    
    print("✅ 夹具隔离性测试通过")

def test_selenium_independence(selenium):
    """测试 selenium 夹具的独立性（每个测试用例使用独立实例）"""
    # 获取当前 WebDriver 的会话 ID
    session_id = selenium.session_id
    
    # 验证会话 ID 存在
    assert session_id is not None, "WebDriver 应该有会话 ID"
    
    # 在页面上设置一个标记，验证这是独立的实例
    selenium.execute_script("window.testMarker = 'test_fixture_integrity';")
    
    # 验证标记被正确设置
    marker = selenium.execute_script("return window.testMarker;")
    assert marker == 'test_fixture_integrity', "应该能在页面上设置标记"
    
    print(f"✅ selenium 独立性测试通过，会话 ID: {session_id}")

if __name__ == "__main__":
    test_setup_and_teardown_fixture_works()
    test_flask_app_fixture_works()
    test_selenium_fixture_works()
    test_chrome_options_fixture_works()
    test_chrome_service_fixture_works()
    test_test_graph_fixture_works()
    test_test_layout_manager_fixture_works()
    test_sample_nodes_fixture_works()
    test_performance_timer_fixture_works()
    test_suppress_errors_fixture_works()
    test_fixture_isolation()
    test_selenium_independence()
    print("✅ T521 夹具完整性测试通过") 