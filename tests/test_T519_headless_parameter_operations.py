from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count, add_parameter
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T519 - 测试
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

def test_headless_parameter_operations(selenium):
    """测试无头模式下的参数操作"""
    try:
        clean_state(selenium)
        
        # 等待页面加载完成
        wait_for_page_load(selenium)
        
        # 创建测试节点
        create_node(selenium, "参数测试节点", "用于测试参数操作")
        wait_for_node_count(selenium, 1)
        
        # 添加参数
        param_input = add_parameter(selenium)
        assert param_input is not None and param_input.is_displayed(), "参数输入框应该出现且可见"
        
        # 输入参数值
        param_input.clear()
        param_input.send_keys("测试值")
        param_input.send_keys(Keys.RETURN)
        
        # 等待参数值更新
        wait_for_text(selenium, By.CSS_SELECTOR, ".parameter-input", "测试值")
        
        print("✅ 无头模式参数操作测试通过")
        
    except Exception as e:
        pytest.fail(f"无头模式参数测试失败: {str(e)}")

if __name__ == "__main__":
    test_headless_parameter_operations()
    print("✅ T519 测试通过")
