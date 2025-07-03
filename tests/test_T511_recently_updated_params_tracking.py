from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count, add_parameter
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T511 - 测试
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

def test_recently_updated_params_tracking(selenium):
    """测试最近更新的参数追踪"""
    try:
        clean_state(selenium)
        create_node(selenium, "TrackingNode", "测试参数追踪")
        wait_for_node_count(selenium, 1)
        
        param_input = add_parameter(selenium)
        assert param_input is not None, "参数输入框应该出现"
        
        # 修改参数值
        param_input.clear()
        param_input.send_keys("新值")
        param_input.send_keys(Keys.RETURN)
        
        # 验证最近更新列表
        recent_list = wait_for_element(selenium, By.ID, "recent-params-list")
        assert recent_list is not None, "最近更新列表应该存在"
        assert "新值" in recent_list.text, "最近更新列表应该包含新值"
        
        print("✅ 最近更新的参数追踪测试通过")
        
    except Exception as e:
        pytest.fail(f"最近更新的参数追踪测试失败: {str(e)}")

if __name__ == "__main__":
    test_recently_updated_params_tracking()
    print("✅ T511 测试通过")
