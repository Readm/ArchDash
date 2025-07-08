from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T522 - Selenium 夹具独立性测试
验证每个测试用例是否使用独立的浏览器实例
"""

import pytest

def test_selenium_instance_1(selenium):
    """第一个测试用例 - 验证浏览器实例独立性"""
    # 获取当前 WebDriver 的会话 ID
    session_id_1 = selenium.session_id
    
    # 验证会话 ID 存在
    assert session_id_1 is not None, "WebDriver 应该有会话 ID"
    
    # 在页面上设置一个标记
    selenium.execute_script("window.testMarker = 'test_1';")
    
    # 验证标记被正确设置
    marker = selenium.execute_script("return window.testMarker;")
    assert marker == 'test_1', "应该能在页面上设置标记"
    
    print(f"✅ 测试 1 使用会话 ID: {session_id_1}")
    
    # 将会话 ID 存储到全局变量中，供其他测试比较
    test_selenium_instance_1.session_id = session_id_1

def test_selenium_instance_2(selenium):
    """第二个测试用例 - 验证浏览器实例独立性"""
    # 获取当前 WebDriver 的会话 ID
    session_id_2 = selenium.session_id
    
    # 验证会话 ID 存在
    assert session_id_2 is not None, "WebDriver 应该有会话 ID"
    
    # 在页面上设置一个标记
    selenium.execute_script("window.testMarker = 'test_2';")
    
    # 验证标记被正确设置
    marker = selenium.execute_script("return window.testMarker;")
    assert marker == 'test_2', "应该能在页面上设置标记"
    
    print(f"✅ 测试 2 使用会话 ID: {session_id_2}")
    
    # 将会话 ID 存储到全局变量中，供其他测试比较
    test_selenium_instance_2.session_id = session_id_2

def test_selenium_instance_3(selenium):
    """第三个测试用例 - 验证浏览器实例独立性"""
    # 获取当前 WebDriver 的会话 ID
    session_id_3 = selenium.session_id
    
    # 验证会话 ID 存在
    assert session_id_3 is not None, "WebDriver 应该有会话 ID"
    
    # 在页面上设置一个标记
    selenium.execute_script("window.testMarker = 'test_3';")
    
    # 验证标记被正确设置
    marker = selenium.execute_script("return window.testMarker;")
    assert marker == 'test_3', "应该能在页面上设置标记"
    
    print(f"✅ 测试 3 使用会话 ID: {session_id_3}")
    
    # 将会话 ID 存储到全局变量中，供其他测试比较
    test_selenium_instance_3.session_id = session_id_3

def test_session_ids_are_different():
    """验证不同测试用例使用了不同的会话 ID"""
    # 获取前三个测试的会话 ID
    session_id_1 = getattr(test_selenium_instance_1, 'session_id', None)
    session_id_2 = getattr(test_selenium_instance_2, 'session_id', None)
    session_id_3 = getattr(test_selenium_instance_3, 'session_id', None)
    
    # 验证所有会话 ID 都存在
    assert session_id_1 is not None, "测试 1 的会话 ID 应该存在"
    assert session_id_2 is not None, "测试 2 的会话 ID 应该存在"
    assert session_id_3 is not None, "测试 3 的会话 ID 应该存在"
    
    # 验证会话 ID 都是不同的
    session_ids = [session_id_1, session_id_2, session_id_3]
    unique_session_ids = set(session_ids)
    
    assert len(unique_session_ids) == 3, f"应该有 3 个不同的会话 ID，实际有 {len(unique_session_ids)} 个"
    assert session_id_1 != session_id_2, "测试 1 和测试 2 应该使用不同的会话 ID"
    assert session_id_1 != session_id_3, "测试 1 和测试 3 应该使用不同的会话 ID"
    assert session_id_2 != session_id_3, "测试 2 和测试 3 应该使用不同的会话 ID"
    
    print(f"✅ 所有测试用例使用了不同的会话 ID:")
    print(f"   测试 1: {session_id_1}")
    print(f"   测试 2: {session_id_2}")
    print(f"   测试 3: {session_id_3}")

if __name__ == "__main__":
    test_selenium_instance_1()
    test_selenium_instance_2()
    test_selenium_instance_3()
    test_session_ids_are_different()
    print("✅ T522 Selenium 独立性测试通过") 