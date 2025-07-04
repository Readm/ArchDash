from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T513 - 测试
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

def test_empty_node_name_validation(selenium):
    """测试空节点名称验证"""
    try:
        clean_state(selenium)
        
        # 尝试创建空名称节点
        add_node_btn = wait_for_clickable(selenium, By.ID, "add-node-from-graph-button")
        add_node_btn.click()
        
        time.sleep(1)  # 等待模态框加载
        modal = wait_for_element(selenium, By.ID, "node-add-modal")
        save_btn = wait_for_clickable(selenium, By.ID, "node-add-save")
        save_btn.click()
        
        # 验证错误提示
        error_msg = wait_for_element(selenium, By.CSS_SELECTOR, '[data-testid="error-message"]')
        assert error_msg is not None, "错误消息元素应该存在"
        error_text = error_msg.text or ""
        assert "不能为空" in error_text, f"应该显示名称为空错误，实际显示: {error_text}"
        
        print("✅ 空节点名称验证测试通过")
        
    except Exception as e:
        pytest.fail(f"空节点名称验证测试失败: {str(e)}")

if __name__ == "__main__":
    test_empty_node_name_validation()
    print("✅ T513 测试通过")
