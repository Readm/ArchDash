from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count, setup_test_nodes_with_ui
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T429 - 测试
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

def test_unlink_ui_integration(app_server_driver):
    """测试unlink功能的完整UI集成"""
    driver, base_url = app_server_driver
    driver.get(base_url)
    wait = WebDriverWait(driver, 10)

    # 设置测试数据
    test_data = setup_test_nodes_with_ui(driver, wait)
    assert test_data is not None, "测试数据设置失败"
    
    # 获取节点（假设第一个是输入节点，第二个是计算节点）
    nodes = driver.find_elements(By.CSS_SELECTOR, ".node")
    assert len(nodes) >= 2, "应该有至少2个节点"
    
    # 获取节点ID
    input_node = nodes[0]  # 输入节点
    area_node = nodes[1]   # 计算节点
    input_node_id = input_node.get_attribute("data-dash-id")
    area_node_id = area_node.get_attribute("data-dash-id")
    
    # 假设的参数名和值
    area_param_name = "计算参数"
    length_param_name = "输入参数"

    # 等待画布容器加载
    wait.until(EC.presence_of_element_located((By.ID, "canvas-container")))

    print("🔬 测试unlink功能完整UI集成")

    # 1. 验证初始状态：无unlink图标
    initial_icon_count = len(driver.find_elements(By.CSS_SELECTOR, ".unlink-icon-container"))
    assert initial_icon_count == 0, "初始状态不应有unlink图标"
    print(f"初始状态unlink图标数量: {initial_icon_count}")

    # 2. 修改有依赖的参数值，应该显示🔓图标
    # 修复: 使用正确的CSS选择器
    area_input_selector = f"div[data-dash-id*='{area_node_id}'] .param-input"
    area_inputs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, area_input_selector)))
    
    if len(area_inputs) < 2:
        raise Exception(f"计算节点输入框数量不足: {len(area_inputs)}")
    
    area_input = area_inputs[1]  # 参数值输入框
    area_input.clear()
    area_input.send_keys("150")
    area_input.send_keys(Keys.ENTER)

    unlink_icon_container_selector = f"div[data-dash-id*='{area_node_id}'] .unlink-icon-container"
    unlink_icon_container = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, unlink_icon_container_selector)))
    print("🔓 Unlink图标已显示")

    # 3. 验证其父参数的值未改变
    length_input_selector = f"div[data-dash-id*='{input_node_id}'] .param-input"
    length_inputs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, length_input_selector)))
    
    if len(length_inputs) < 2:
        raise Exception(f"输入节点输入框数量不足: {len(length_inputs)}")
    
    length_input = length_inputs[1]  # 参数值输入框
    assert length_input.get_attribute("value") == f"{test_data['input_node_params'][1]:.2f}"
    print("父参数值未变")

    # 4. 点击图标，重新计算，图标消失
    clickable_icon = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, unlink_icon_container_selector)))
    clickable_icon.click()
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, unlink_icon_container_selector)))
    print("🔄 图标已点击，等待重新计算和图标消失")

    # 5. 验证值已重新计算
    recalculated_value = f"{test_data['calc_node_params'][1]:.2f}"
    wait.until(lambda driver: area_input.get_attribute("value") == recalculated_value)
    print(f"值已重新计算为 {recalculated_value}")

    # 6. 再次修改父参数，不应显示图标
    length_input.clear()
    length_input.send_keys("12")
    length_input.send_keys(Keys.ENTER)

    # 值应该根据新父级值更新 12 * 5 = 60
    final_recalculated_value = f"{12.0 * test_data['input_node_params'][1]:.2f}"
    wait.until(lambda driver: area_input.get_attribute("value") == final_recalculated_value)
    # 确认图标没有再次出现
    assert len(driver.find_elements(By.CSS_SELECTOR, unlink_icon_container_selector)) == 0, "修改父参数后不应出现unlink图标"
    print("✅ UI集成测试通过")

if __name__ == "__main__":
    test_unlink_ui_integration()
    print("✅ T429 测试通过")
