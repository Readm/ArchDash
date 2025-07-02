#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试无头模式下的基本功能
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time

from app import app, graph, layout_manager

def wait_for_element(selenium, by, value, timeout=10):
    """等待元素出现并返回"""
    return WebDriverWait(selenium, timeout).until(
        EC.visibility_of_element_located((by, value))
    )

def wait_for_clickable(selenium, by, value, timeout=10):
    """等待元素可点击并返回"""
    element = WebDriverWait(selenium, timeout).until(
        EC.element_to_be_clickable((by, value))
    )
    # Ensure element is in view
    selenium.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.5)  # Give time for scroll to complete
    return element

def wait_for_node_count(selenium, count, timeout=10):
    """等待节点数量达到预期值"""
    def check_node_count(driver):
        nodes = driver.find_elements(By.CSS_SELECTOR, ".node")
        visible_nodes = [n for n in nodes if n.is_displayed()]
        return len(visible_nodes) == count
    WebDriverWait(selenium, timeout).until(check_node_count)

def wait_for_text(selenium, by, value, text, timeout=10):
    """等待元素包含指定文本"""
    return WebDriverWait(selenium, timeout).until(
        EC.text_to_be_present_in_element((by, value), text)
    )

def wait_for_page_load(selenium, timeout=10):
    """等待页面完全加载"""
    return WebDriverWait(selenium, timeout).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )

def create_node(selenium, name, description=""):
    """创建一个新节点"""
    add_node_btn = wait_for_clickable(selenium, By.ID, "add-node-from-graph-button")
    add_node_btn.click()
    
    modal = wait_for_element(selenium, By.ID, "node-add-modal")
    name_input = wait_for_element(selenium, By.ID, "node-add-name")
    name_input.clear()
    name_input.send_keys(name)
    
    if description:
        desc_input = wait_for_element(selenium, By.ID, "node-add-description")
        desc_input.clear()
        desc_input.send_keys(description)
    
    save_btn = wait_for_clickable(selenium, By.ID, "node-add-save")
    save_btn.click()

def add_parameter(selenium, node_index=0):
    """为指定索引的节点添加参数"""
    nodes = selenium.find_elements(By.CSS_SELECTOR, ".node")
    node = nodes[node_index]
    
    add_param_btn = wait_for_clickable(selenium, By.CSS_SELECTOR, "button[id*='add-param']")
    add_param_btn.click()
    
    param_input = wait_for_element(selenium, By.CSS_SELECTOR, ".parameter-input")
    return param_input

def clean_state(selenium):
    """清理应用状态"""
    graph.nodes.clear()
    layout_manager.node_positions.clear()
    layout_manager.position_nodes.clear()
    layout_manager._init_grid()
    
    selenium.get("http://localhost:8050")
    wait_for_page_load(selenium)
    wait_for_element(selenium, By.ID, "canvas-container")

def test_headless_basic_operations(selenium):
    """测试无头模式下的基本操作"""
    try:
        clean_state(selenium)
        
        # 等待页面加载完成
        wait_for_page_load(selenium)
        
        # 创建测试节点
        create_node(selenium, "测试节点", "这是一个测试节点")
        wait_for_node_count(selenium, 1)
        
        # 验证节点创建
        node = wait_for_element(selenium, By.CSS_SELECTOR, ".node")
        assert node.is_displayed(), "节点应该可见"
        assert "测试节点" in node.text, "节点名称应该正确显示"
        
        print("✅ 无头模式基本操作测试通过")
        
    except Exception as e:
        pytest.fail(f"无头模式测试失败: {str(e)}")

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

def test_headless_parameter_operations(selenium):
    """测试无头模式下的参数操作"""
    try:
        clean_state(selenium)
        
        # 等待页面加载完成
        wait_for_page_load(selenium)
        
        # 创建测试节点
        create_node(selenium, "参数测试节点", "用于测试参数操作")
        wait_for_node_count(selenium, 1)
        
        # 添加参数
        param_input = add_parameter(selenium)
        assert param_input is not None and param_input.is_displayed(), "参数输入框应该出现且可见"
        
        # 输入参数值
        param_input.clear()
        param_input.send_keys("测试值")
        param_input.send_keys(Keys.RETURN)
        
        # 等待参数值更新
        wait_for_text(selenium, By.CSS_SELECTOR, ".parameter-input", "测试值")
        
        print("✅ 无头模式参数操作测试通过")
        
    except Exception as e:
        pytest.fail(f"无头模式参数测试失败: {str(e)}") 