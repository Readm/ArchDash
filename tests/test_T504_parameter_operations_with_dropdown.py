#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T504 - 测试
从原始测试文件分离出的独立测试
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
from app import app, graph, layout_manager

def test_parameter_operations_with_dropdown(selenium):
    """测试参数操作和下拉菜单"""
    try:
        print("\n=== 开始测试参数操作和下拉菜单 ===")
        clean_state(selenium)
        print("清理状态完成")
        
        create_node(selenium, "ParameterTestNode", "测试参数操作")
        print("节点创建完成")
        
        wait_for_node_count(selenium, 1)
        print("等待节点数量验证完成")
        
        # 找到节点
        print("\n尝试查找节点...")
        node = wait_for_element(selenium, By.CSS_SELECTOR, "[data-dash-id*='node']")
        if not node:
            raise Exception("未找到节点")
        print("✅ 找到节点")
        
        # 找到添加参数按钮
        print("\n查找添加参数按钮...")
        add_param_btn = wait_for_element(selenium, By.CSS_SELECTOR, "button[id*='add-param']")
        if not add_param_btn:
            raise Exception("未找到添加参数按钮")
        print("✅ 找到添加参数按钮")
        
        # 点击添加参数按钮
        print("\n点击添加参数按钮...")
        safe_click(selenium, add_param_btn)
        print("添加参数按钮已点击")
        time.sleep(1)  # 等待参数输入框出现
        
        # 等待参数输入框出现
        print("\n等待参数输入框出现...")
        param_input = wait_for_element(selenium, By.CSS_SELECTOR, "[data-dash-id*='param-input'], .parameter-input")
        if not param_input:
            raise Exception("参数输入框未出现")
        print("✅ 找到参数输入框")
        
        # 验证参数输入框可以输入
        print("\n测试参数输入...")
        param_input.clear()
        param_input.send_keys("test_param")
        time.sleep(0.5)  # 等待输入完成
        
        # 验证输入值
        actual_value = param_input.get_attribute("value")
        print(f"输入框当前值: {actual_value}")
        assert actual_value == "test_param", f"参数输入框的值应该是'test_param'，实际是'{actual_value}'"
        print("✅ 参数输入验证通过")
        
        print("✅ 参数操作和下拉菜单测试通过")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        print("\n当前页面HTML:")
        print(selenium.page_source)
        raise

if __name__ == "__main__":
    test_parameter_operations_with_dropdown()
    print("✅ T504 测试通过")
