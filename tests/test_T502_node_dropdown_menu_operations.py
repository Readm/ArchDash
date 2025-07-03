#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T502 - 测试节点下拉菜单操作
使用会话隔离的graph实例
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count

def test_node_dropdown_menu_operations(selenium, flask_app):
    """测试节点下拉菜单操作"""
    try:
        print("\n========== 开始节点下拉菜单操作测试 ==========")
        
        # 清理状态
        clean_state(selenium)
        time.sleep(2)
        
        # 创建测试节点
        print("\n第1步：创建测试节点")
        assert create_node(selenium, "测试节点", "用于测试下拉菜单的节点"), "节点创建失败"
        wait_for_node_count(selenium, 1)
        
        # 查找节点下拉菜单按钮
        print("\n第2步：查找节点下拉菜单")
        dropdown_btn = wait_for_clickable(selenium, By.CSS_SELECTOR, '[data-testid="node-dropdown-btn"]')
        assert dropdown_btn, "未找到节点下拉菜单按钮"
        
        # 点击下拉菜单
        print("\n第3步：点击下拉菜单")
        dropdown_btn.click()
        time.sleep(1)
        
        # 验证下拉菜单项
        print("\n第4步：验证下拉菜单项")
        menu_items = selenium.find_elements(By.CSS_SELECTOR, '.dropdown-menu .dropdown-item')
        assert len(menu_items) > 0, "下拉菜单应该包含菜单项"
        
        # 查找添加参数菜单项
        add_param_item = None
        for item in menu_items:
            if "添加参数" in item.text:
                add_param_item = item
                break
        
        assert add_param_item, "下拉菜单应该包含'添加参数'选项"
        
        # 点击添加参数
        print("\n第5步：点击添加参数")
        add_param_item.click()
        time.sleep(1)
        
        # 验证参数添加模态框出现
        print("\n第6步：验证参数添加模态框")
        modal = wait_for_element(selenium, By.ID, "parameter-add-modal")
        assert modal and modal.is_displayed(), "参数添加模态框应该出现"
        
        print("✅ 节点下拉菜单操作测试通过")
        
    except Exception as e:
        print(f"❌ 节点下拉菜单操作测试失败: {e}")
        raise

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
