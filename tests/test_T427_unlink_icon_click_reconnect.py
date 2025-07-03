from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count, setup_test_nodes_with_ui
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T427 - 测试
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

def test_unlink_icon_click_reconnect(app_server_driver):
    """点击unlink图标应该重新链接参数，重新计算其值，并使图标消失。"""
    driver, base_url = app_server_driver
    driver.get(base_url)
    wait = WebDriverWait(driver, 10)

    # 等待画布加载
    wait.until(EC.presence_of_element_located((By.ID, "canvas-container")))

    # 设置并手动更改参数以显示图标
    test_data = setup_test_nodes_with_ui(driver, wait)
    calc_node_id = test_data['calc_node_params'][0]
    calc_param_name = test_data['calc_node_params'][1]
    
    # 修复: 使用正确的CSS选择器
    calc_input_selector = f"div[data-dash-id*='{calc_node_id}'] .param-input"
    calc_inputs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, calc_input_selector)))
    
    if len(calc_inputs) < 2:
        raise Exception(f"计算节点输入框数量不足: {len(calc_inputs)}")
    
    calc_input = calc_inputs[1]  # 参数值输入框
    calc_input.clear()
    calc_input.send_keys("150")
    calc_input.send_keys(Keys.ENTER)

    # 等待并点击unlink图标以重新连接
    unlink_icon_container_selector = f"div[data-dash-id*='{calc_node_id}'] .unlink-icon-container"
    unlink_icon_container = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, unlink_icon_container_selector)))
    unlink_icon_container.click()

    # 等待值被重新计算和更新
    recalculated_value = f"{test_data['calc_node_params'][1]:.2f}"
    # 重新获取输入框来验证值
    calc_inputs = driver.find_elements(By.CSS_SELECTOR, f"div[data-dash-id*='{calc_node_id}'] .param-input")
    calc_input = calc_inputs[1]  # 参数值输入框
    wait.until(
        lambda driver: calc_input.get_attribute("value") == recalculated_value
    )

    # 验证unlink图标消失
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, unlink_icon_container_selector)))

if __name__ == "__main__":
    test_unlink_icon_click_reconnect()
    print("✅ T427 测试通过")
