from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T518 - 测试
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

def test_headless_layout_operations(selenium):
    """测试无头模式下的布局操作"""
    try:
        clean_state(selenium)
        
        # 等待页面加载完成
        wait_for_page_load(selenium)
        
        # 创建测试节点
        for i in range(3):
            create_node(selenium, f"节点{i+1}", f"测试节点{i+1}")
            wait_for_node_count(selenium, i + 1)
        
        # 验证节点创建
        nodes = selenium.find_elements(By.CSS_SELECTOR, ".node")
        visible_nodes = [n for n in nodes if n.is_displayed()]
        assert len(visible_nodes) == 3, "应该有3个可见节点"
        
        # 测试列管理
        add_col_btn = wait_for_clickable(selenium, By.ID, "add-column-btn")
        initial_cols = len(selenium.find_elements(By.CSS_SELECTOR, ".grid-column"))
        
        # 添加列
        add_col_btn.click()
        
        # 等待新列出现
        WebDriverWait(selenium, 10).until(
            lambda driver: len(driver.find_elements(By.CSS_SELECTOR, ".grid-column")) > initial_cols
        )
        
        # 验证列数增加
        new_cols = len(selenium.find_elements(By.CSS_SELECTOR, ".grid-column"))
        assert new_cols == initial_cols + 1, "应该增加了一列"
        
        print("✅ 无头模式布局操作测试通过")
        
    except Exception as e:
        pytest.fail(f"无头模式布局测试失败: {str(e)}")

if __name__ == "__main__":
    test_headless_layout_operations()
    print("✅ T518 测试通过")
