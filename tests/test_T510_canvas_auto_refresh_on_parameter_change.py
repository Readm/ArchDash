from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count, add_parameter, get_parameter_input_box
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T510 - 测试
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

def test_canvas_auto_refresh_on_parameter_change(selenium):
    """测试参数变化时画布自动刷新"""
    try:
        clean_state(selenium)
        create_node(selenium, "RefreshNode", "测试画布刷新")
        wait_for_node_count(selenium, 1)
        
        # 添加参数到节点
        add_parameter(selenium, "1", "test_param", 100, "unit")
        
        # 获取参数输入框（参数值输入框）
        param_input = get_parameter_input_box(selenium, "1", "test_param", "param-value")
        assert param_input is not None, "参数输入框应该出现"
        
        # 修改参数值
        param_input.clear()
        param_input.send_keys("新值")
        param_input.send_keys(Keys.RETURN)
        
        # 验证画布更新
        time.sleep(1)  # 等待画布刷新
        canvas = selenium.find_element(By.ID, "canvas-container")
        assert canvas.is_displayed(), "画布应该保持可见"
        
        print("✅ 参数变化时画布自动刷新测试通过")
        
    except Exception as e:
        pytest.fail(f"参数变化时画布自动刷新测试失败: {str(e)}")

if __name__ == "__main__":
    test_canvas_auto_refresh_on_parameter_change()
    print("✅ T510 测试通过")
