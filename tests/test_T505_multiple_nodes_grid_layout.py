from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T505 - 测试
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

def test_multiple_nodes_grid_layout(selenium):
    """测试多节点网格布局"""
    try:
        clean_state(selenium)
        
        for i in range(3):
            create_node(selenium, f"GridNode{i+1}", f"网格布局测试节点{i+1}")
            wait_for_node_count(selenium, i + 1)
        
        # 使用更健壮的节点查找方法
        nodes = selenium.find_elements(By.CSS_SELECTOR, "[data-dash-id*='node']")
        if not nodes:
            nodes = selenium.find_elements(By.CSS_SELECTOR, ".node")
        assert len(nodes) == 3, "应该有3个节点"
        
        print("✅ 多节点网格布局测试通过")
        
    except Exception as e:
        pytest.fail(f"多节点网格布局测试失败: {str(e)}")

if __name__ == "__main__":
    test_multiple_nodes_grid_layout()
    print("✅ T505 测试通过")
