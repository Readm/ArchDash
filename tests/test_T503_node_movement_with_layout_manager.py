from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T503 - 测试
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

def test_node_movement_with_layout_manager(selenium):
    """测试节点移动和布局管理器"""
    try:
        print("\n=== 开始测试节点移动和布局管理器 ===")
        clean_state(selenium)
        print("清理状态完成")
        
        create_node(selenium, "MovementTestNode", "测试节点移动")
        print("节点创建完成")
        
        wait_for_node_count(selenium, 1)
        print("等待节点数量验证完成")
        
        print("\n尝试查找节点...")
        node = wait_for_element(selenium, By.CSS_SELECTOR, "[data-dash-id*='node']")
        if not node:
            raise Exception("未找到节点")
        print("✅ 找到节点")
        
        # 记录初始位置
        initial_location = node.location
        print(f"初始位置: {initial_location}")
        
        # 在节点内部查找下拉按钮
        print("\n在节点内部查找下拉按钮...")
        dropdown_btn = wait_for_element(selenium, By.CSS_SELECTOR, ".node-menu-btn")
        if not dropdown_btn:
            raise Exception("未在节点内找到下拉按钮")
        print("✅ 找到下拉按钮")
        
        # 点击下拉按钮
        print("\n点击下拉按钮...")
        safe_click(selenium, dropdown_btn)
        print("下拉按钮已点击")
        time.sleep(1)  # 等待菜单展开
        
        # 等待下拉菜单出现
        print("\n等待下拉菜单出现...")
        menu = wait_for_element(selenium, By.CSS_SELECTOR, ".dropdown-menu.show")
        assert menu.is_displayed(), "下拉菜单应该可见"
        print("下拉菜单已显示")
        
        # 查找并点击右移按钮
        print("\n查找右移按钮...")
        move_right_btn = wait_for_element(selenium, By.CSS_SELECTOR, "[id*='move-node-right']")
        if not move_right_btn:
            raise Exception("未找到右移按钮")
        print("✅ 找到右移按钮")
        
        print("\n点击右移按钮...")
        safe_click(selenium, move_right_btn)
        print("右移按钮已点击")
        
        time.sleep(2)  # 等待移动完成
        
        # 重新获取节点位置（因为节点可能已经重新渲染）
        node = wait_for_element(selenium, By.CSS_SELECTOR, "[data-dash-id*='node']")
        new_location = node.location
        print(f"新位置: {new_location}")
        
        # 检查位置变化
        print("\n检查位置变化...")
        print(f"初始X坐标: {initial_location['x']}")
        print(f"新X坐标: {new_location['x']}")
        
        if new_location['x'] <= initial_location['x']:
            raise Exception(f"节点没有向右移动。初始X: {initial_location['x']}, 新X: {new_location['x']}")
            
        print("✅ 位置变化验证通过")
        print("✅ 节点移动和布局管理器测试通过")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        print("\n当前页面HTML:")
        print(selenium.page_source)
        raise

if __name__ == "__main__":
    test_node_movement_with_layout_manager()
    print("✅ T503 测试通过")
