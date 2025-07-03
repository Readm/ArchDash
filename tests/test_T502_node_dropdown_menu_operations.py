#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T502 - 测试
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

def test_node_dropdown_menu_operations(selenium):
    """测试节点的dropdown菜单操作"""
    try:
        clean_state(selenium)
        
        # 等待页面加载完成
        wait_for_page_load(selenium)
        
        # 等待画布容器可见
        canvas = wait_for_element(selenium, By.ID, "canvas-container")
        assert canvas is not None and canvas.is_displayed(), "画布容器应该存在且可见"
        
        # 等待添加节点按钮可点击
        add_node_btn = wait_for_clickable(selenium, By.ID, "add-node-from-graph-button")
        add_node_btn.click()
        
        # 等待模态框出现并可见
        modal = wait_for_element(selenium, By.ID, "node-add-modal")
        assert modal is not None and modal.is_displayed(), "节点添加模态框应该出现且可见"
        
        # 输入节点信息
        name_input = wait_for_element(selenium, By.ID, "node-add-name")
        name_input.clear()
        name_input.send_keys("DropdownTestNode")
        
        desc_input = wait_for_element(selenium, By.ID, "node-add-description")
        desc_input.clear()
        desc_input.send_keys("测试下拉菜单")
        
        # 等待保存按钮可点击
        save_btn = wait_for_clickable(selenium, By.ID, "node-add-save")
        save_btn.click()
        
        # 等待节点出现在页面上
        wait_for_node_count(selenium, 1)
        
        # 验证节点创建
        assert len(graph.nodes) == 1, "应该创建了一个节点"
        
        # 获取节点ID
        node = list(graph.nodes.values())[0]
        
        # 等待节点元素可见
        node_element = wait_for_element(selenium, By.CSS_SELECTOR, f".node[data-dash-id*='{node.id}']")
        assert node_element.is_displayed(), "节点元素应该可见"
        
        # 等待下拉菜单按钮可点击
        dropdown_btn = wait_for_clickable(selenium, By.CSS_SELECTOR, f"button[data-dash-id*='{node.id}'][id*='dropdown']")
        dropdown_btn.click()
        
        # 等待下拉菜单出现并可见
        menu = wait_for_element(selenium, By.CSS_SELECTOR, ".dropdown-menu.show")
        assert menu.is_displayed(), "下拉菜单应该可见"
        
        # 等待删除按钮可点击
        delete_btn = wait_for_clickable(selenium, By.CSS_SELECTOR, f"button[data-dash-id*='{node.id}'][id*='delete']")
        delete_btn.click()
        
        # 等待节点消失
        WebDriverWait(selenium, 10).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, f".node[data-dash-id*='{node.id}']"))
        )
        
        # 验证节点被删除
        assert len(graph.nodes) == 0, "节点应该被删除"
        assert len(layout_manager.node_positions) == 0, "节点布局信息应该被删除"
        
    except Exception as e:
        pytest.fail(f"下拉菜单操作测试失败: {str(e)}")

if __name__ == "__main__":
    test_node_dropdown_menu_operations()
    print("✅ T502 测试通过")
