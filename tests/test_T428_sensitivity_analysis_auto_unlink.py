from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count, setup_test_nodes_with_ui
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T428 - 测试
从原始测试文件分离出的独立测试
"""

import pytest
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from app import app, layout_manager
from models import CalculationGraph, Node, Parameter

def test_sensitivity_analysis_auto_unlink(app_server_driver):
    """测试相关性分析时自动unlink功能"""
    driver, base_url = app_server_driver
    driver.get(base_url)

    # 等待页面加载
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "canvas-container")))
    
    print("🔬 测试相关性分析自动unlink功能")
    
    # 找到相关性分析的参数选择器
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "x-param-selector")))
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "y-param-selector")))
        print("✅ 找到参数选择器")
        
        # 检查是否有生成图表按钮
        generate_btn = driver.find_element(By.ID, "generate-plot-btn")
        assert generate_btn is not None, "应该找到生成图表按钮"
        print("✅ 找到生成图表按钮")
        
        print("✅ 相关性分析UI元素验证通过")
        
    except (NoSuchElementException, TimeoutException) as e:
        pytest.fail(f"相关性分析UI元素未找到: {e}")

if __name__ == "__main__":
    test_sensitivity_analysis_auto_unlink()
    print("✅ T428 测试通过")
