from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T516 - 测试
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

def test_single_node_creation(selenium):
    """测试创建单个节点"""
    try:
        print("\n========== 开始单节点创建测试 ==========")
        
        print("\n第1步：清理应用状态")
        clean_state(selenium)
        time.sleep(2)  # 等待清理完成
        
        print("\n第2步：创建测试节点")
        create_node(selenium, "TestNode", "测试节点")
        time.sleep(2)  # 等待节点创建完成
        
        print("\n第3步：分析页面内容")
        page_source = selenium.page_source
        print("\n当前页面HTML:")
        print(page_source)
        
        print("\n尝试查找所有可能的节点相关元素:")
        # 尝试各种选择器
        selectors = [
            "[data-dash-id*='node']",  # Dash节点标识
            ".node-container",         # 节点容器类
            ".node-entrance",          # 节点入场动画类
            "[id^='node-']",          # 以node-开头的ID
            "[data-row]",             # 具有data-row属性的元素
            "[data-col]"              # 具有data-col属性的元素
        ]
        
        for selector in selectors:
            elements = selenium.find_elements(By.CSS_SELECTOR, selector)
            print(f"\n使用选择器 '{selector}' 找到 {len(elements)} 个元素:")
            for i, elem in enumerate(elements):
                try:
                    print(f"元素 {i+1}:")
                    print(f"- class: {elem.get_attribute('class')}")
                    print(f"- id: {elem.get_attribute('id')}")
                    print(f"- data-dash-id: {elem.get_attribute('data-dash-id')}")
                    print(f"- data-row: {elem.get_attribute('data-row')}")
                    print(f"- data-col: {elem.get_attribute('data-col')}")
                    print(f"- text: {elem.text}")
                    print(f"- HTML: {elem.get_attribute('outerHTML')}")
                    print(f"- 是否显示: {elem.is_displayed()}")
                except:
                    print(f"- 无法获取元素 {i+1} 的详细信息")
        
        print("\n第4步：等待并验证节点")
        wait_for_node_count(selenium, 1)
        time.sleep(2)  # 等待节点完全渲染
        
        print("\n✅ 单节点创建测试通过")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        raise

if __name__ == "__main__":
    test_single_node_creation()
    print("✅ T516 测试通过")
