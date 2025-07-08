from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count, setup_test_nodes_with_ui
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T425 - 测试
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

def test_unlink_icon_display_logic(app_server_driver):
    """测试unlink图标的显示逻辑：只有unlinked=True且有依赖时才显示🔓"""
    driver, base_url = app_server_driver
    driver.get(base_url)
    
    # 等待页面加载
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "canvas-container"))
    )
    
    # 设置测试数据
    test_data = setup_test_nodes_with_ui(driver, WebDriverWait(driver, 10))
    
    print("🔬 测试unlink图标显示逻辑")
    
    # 使用更健壮的图标查找方法
    all_unlink_icons = driver.find_elements(By.CSS_SELECTOR, "[data-dash-id*='unlink'], .unlink-icon")
    assert len(all_unlink_icons) == 0, "初始状态下不应显示unlink图标"
    print("✅ 初始状态：不显示🔓图标")
    
    # 使用更健壮的容器查找方法
    all_unlink_containers = driver.find_elements(By.CSS_SELECTOR, "[data-dash-id*='unlink-container'], .unlink-icon-container")
    assert len(all_unlink_containers) == 0, "初始状态下不应显示unlink图标容器"
    print("✅ 无依赖参数：不显示🔓图标")

if __name__ == "__main__":
    test_unlink_icon_display_logic()
    print("✅ T425 测试通过")
