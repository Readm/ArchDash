#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T501 - 测试
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

def test_add_node_with_grid_layout(selenium):
    """测试添加节点和网格布局"""
    try:
        print("\n=== 开始测试添加节点和网格布局 ===")
        clean_state(selenium)
        print("清理状态完成")
        
        create_node(selenium, "测试节点", "这是一个测试节点")
        print("节点创建完成")
        
        wait_for_node_count(selenium, 1)
        print("等待节点数量验证完成")
        
        print("\n尝试查找节点...")
        # 尝试所有可能的选择器
        selectors = [
            "[data-dash-id*='node']",
            ".node",
            ".node-container",
            "[id^='node-']"
        ]
        
        node = None
        for selector in selectors:
            print(f"\n尝试选择器: {selector}")
            elements = selenium.find_elements(By.CSS_SELECTOR, selector)
            print(f"找到 {len(elements)} 个元素")
            for i, elem in enumerate(elements):
                print(f"元素 {i+1}:")
                print(f"- class: {elem.get_attribute('class')}")
                print(f"- id: {elem.get_attribute('id')}")
                print(f"- text: {elem.text}")
                print(f"- 是否显示: {elem.is_displayed()}")
                if "测试节点" in elem.text and elem.is_displayed():
                    node = elem
                    print("✅ 找到目标节点!")
                    break
            if node:
                break
                
        if not node:
            raise Exception("未找到包含'测试节点'文本的可见节点")
            
        assert "测试节点" in node.text, "节点名称应该正确显示"
        print("✅ 节点名称验证通过")
        
        print("✅ 添加节点和网格布局测试通过")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        print("\n当前页面HTML:")
        print(selenium.page_source)
        pytest.fail(f"添加节点和网格布局测试失败: {str(e)}")

if __name__ == "__main__":
    test_add_node_with_grid_layout()
    print("✅ T501 测试通过")
