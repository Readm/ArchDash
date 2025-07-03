#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T515 - 测试
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

def test_remove_column_functionality(selenium):
    """测试删除列功能"""
    try:
        clean_state(selenium)
        
        # 获取初始列数
        initial_cols = len(selenium.find_elements(By.CSS_SELECTOR, ".grid-column"))
        
        # 添加列
        add_col_btn = wait_for_clickable(selenium, By.ID, "add-column-btn")
        add_col_btn.click()
        
        # 等待列添加完成
        time.sleep(1)
        
        # 删除列
        remove_col_btn = wait_for_clickable(selenium, By.ID, "remove-column-btn")
        remove_col_btn.click()
        
        # 验证列数恢复
        time.sleep(1)  # 等待列删除完成
        final_cols = len(selenium.find_elements(By.CSS_SELECTOR, ".grid-column"))
        assert final_cols == initial_cols, "列数应该恢复到初始值"
        
        print("✅ 删除列功能测试通过")
        
    except Exception as e:
        pytest.fail(f"删除列功能测试失败: {str(e)}")

if __name__ == "__main__":
    test_remove_column_functionality()
    print("✅ T515 测试通过")
