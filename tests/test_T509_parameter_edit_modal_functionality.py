from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T509 - 测试
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

def test_parameter_edit_modal_functionality(selenium):
    """测试参数编辑模态框功能"""
    try:
        clean_state(selenium)
        create_node(selenium, "EditModalNode", "测试参数编辑模态框")
        wait_for_node_count(selenium, 1)
        
        param_input = add_parameter(selenium)
        assert param_input is not None, "参数输入框应该出现"
        
        # 打开参数编辑模态框
        edit_btn = wait_for_clickable(selenium, By.CSS_SELECTOR, "button[id*='edit-param']")
        edit_btn.click()
        
        # 验证模态框
        edit_modal = wait_for_element(selenium, By.ID, "parameter-edit-modal")
        assert edit_modal is not None, "参数编辑模态框应该出现"
        
        print("✅ 参数编辑模态框功能测试通过")
        
    except Exception as e:
        pytest.fail(f"参数编辑模态框功能测试失败: {str(e)}")

if __name__ == "__main__":
    test_parameter_edit_modal_functionality()
    print("✅ T509 测试通过")
