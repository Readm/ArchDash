from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T512 - 测试
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

def test_duplicate_node_name_prevention(selenium):
    """测试重复节点名称预防"""
    try:
        clean_state(selenium)
        create_node(selenium, "DuplicateNode", "测试重复名称")
        wait_for_node_count(selenium, 1)
        
        # 尝试创建同名节点
        add_node_btn = wait_for_clickable(selenium, By.ID, "add-node-from-graph-button")
        add_node_btn.click()
        
        modal = wait_for_element(selenium, By.ID, "node-add-modal")
        name_input = wait_for_element(selenium, By.ID, "node-add-name")
        name_input.clear()
        name_input.send_keys("DuplicateNode")
        
        desc_input = wait_for_element(selenium, By.ID, "node-add-description")
        desc_input.clear()
        desc_input.send_keys("测试重复名称2")
        
        save_btn = wait_for_clickable(selenium, By.ID, "node-add-save")
        save_btn.click()
        
        # 验证错误提示
        error_msg = wait_for_element(selenium, By.CSS_SELECTOR, ".alert-danger")
        assert "已存在" in error_msg.text, "应该显示重复名称错误"
        
        print("✅ 重复节点名称预防测试通过")
        
    except Exception as e:
        pytest.fail(f"重复节点名称预防测试失败: {str(e)}")

if __name__ == "__main__":
    test_duplicate_node_name_prevention()
    print("✅ T512 测试通过")
