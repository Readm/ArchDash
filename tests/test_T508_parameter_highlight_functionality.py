from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count, add_parameter, get_parameter_input_box
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T508 - 测试
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

def test_parameter_highlight_functionality(selenium):
    """测试参数高亮功能"""
    try:
        clean_state(selenium)
        create_node(selenium, "HighlightNode", "测试参数高亮")
        wait_for_node_count(selenium, 1)
        
        # 添加参数到节点
        add_parameter(selenium, "1", "test_param", 100, "unit")
        
        # 获取参数输入框（参数值输入框）
        param_input = get_parameter_input_box(selenium, "1", "test_param", "param-value")
        assert param_input is not None, "参数输入框应该出现"
        
        # 点击参数以触发高亮
        param_input.click()
        
        # 验证高亮效果
        highlighted = selenium.find_elements(By.CSS_SELECTOR, ".parameter-highlight")
        assert len(highlighted) > 0, "应该有参数被高亮"
        
        print("✅ 参数高亮功能测试通过")
        
    except Exception as e:
        pytest.fail(f"参数高亮功能测试失败: {str(e)}")

if __name__ == "__main__":
    test_parameter_highlight_functionality()
    print("✅ T508 测试通过")
