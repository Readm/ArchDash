#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T514 - 测试
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

def test_column_management(selenium):
    """测试列管理"""
    try:
        clean_state(selenium)
        
        # 获取初始列数
        initial_cols = len(selenium.find_elements(By.CSS_SELECTOR, ".grid-column"))
        
        # 添加列
        add_col_btn = wait_for_clickable(selenium, By.ID, "add-column-btn")
        add_col_btn.click()
        
        # 验证列数增加
        time.sleep(1)  # 等待列添加完成
        new_cols = len(selenium.find_elements(By.CSS_SELECTOR, ".grid-column"))
        assert new_cols == initial_cols + 1, "应该增加了一列"
        
        print("✅ 列管理测试通过")
        
    except Exception as e:
        pytest.fail(f"列管理测试失败: {str(e)}")

if __name__ == "__main__":
    test_column_management()
    print("✅ T514 测试通过")
