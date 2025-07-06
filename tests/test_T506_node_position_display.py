from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T506 - 测试
从原始测试文件分离出的独立测试
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
import time
from app import app, graph, layout_manager

def test_node_position_display(selenium):
    """测试节点位置显示"""
    try:
        clean_state(selenium)
        create_node(selenium, "PositionNode", "测试节点位置")
        wait_for_node_count(selenium, 1)
        
        # 使用更健壮的节点查找方法
        node = wait_for_element(selenium, By.CSS_SELECTOR, "[data-dash-id*='node']")
        if not node:
            node = wait_for_element(selenium, By.CSS_SELECTOR, ".node-container")
        assert node.is_displayed(), "节点应该可见"
        assert node.location['x'] >= 0 and node.location['y'] >= 0, "节点应该有有效的位置"
        
        print("✅ 节点位置显示测试通过")
        
    except Exception as e:
        pytest.fail(f"节点位置显示测试失败: {str(e)}")

if __name__ == "__main__":
    test_node_position_display()
    print("✅ T506 测试通过")
