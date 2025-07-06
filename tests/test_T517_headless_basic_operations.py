from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T517 - 测试
从原始测试文件分离出的独立测试
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import time
from app import app, graph, layout_manager

def test_headless_basic_operations(selenium):
    """测试无头模式下的基本操作"""
    try:
        clean_state(selenium)
        
        # 等待页面加载完成
        wait_for_page_load(selenium)
        
        # 创建测试节点
        create_node(selenium, "测试节点", "这是一个测试节点")
        wait_for_node_count(selenium, 1)
        
        # 验证节点创建
        node = wait_for_element(selenium, By.CSS_SELECTOR, ".node-container")
        assert node.is_displayed(), "节点应该可见"
        assert "测试节点" in node.text, "节点名称应该正确显示"
        
        print("✅ 无头模式基本操作测试通过")
        
    except Exception as e:
        pytest.fail(f"无头模式测试失败: {str(e)}")

if __name__ == "__main__":
    test_headless_basic_operations()
    print("✅ T517 测试通过")
