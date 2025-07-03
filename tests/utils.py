#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试辅助函数工具模块
提供所有测试文件共用的辅助函数
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys


def clean_state(selenium):
    """清理测试状态"""
    try:
        # 清理应用状态
        from app import graph, layout_manager
        graph.nodes.clear()
        layout_manager.node_positions.clear()
        layout_manager.position_nodes.clear()
        layout_manager._init_grid()
        graph.recently_updated_params.clear()
        
        # 刷新页面
        selenium.refresh()
        time.sleep(0.5)
        
        # 等待页面加载完成
        wait_for_page_load(selenium)
        
    except Exception as e:
        print(f"清理状态时出错: {e}")

def wait_for_page_load(selenium, timeout=5):
    """等待页面加载完成"""
    try:
        WebDriverWait(selenium, timeout).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        time.sleep(0.2)  # 减少额外等待时间
    except TimeoutException:
        print("页面加载超时")

def wait_for_element(selenium, by, value, timeout=5):
    """等待元素出现并返回"""
    try:
        element = WebDriverWait(selenium, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        print(f"等待元素超时: {by}={value}")
        return None

def wait_for_clickable(selenium, by, value, timeout=5):
    """等待元素可点击并返回"""
    try:
        element = WebDriverWait(selenium, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        return element
    except TimeoutException:
        print(f"等待元素可点击超时: {by}={value}")
        return None

def wait_for_visible(selenium, by, value, timeout=5):
    """等待元素可见并返回"""
    try:
        element = WebDriverWait(selenium, timeout).until(
            EC.visibility_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        print(f"等待元素可见超时: {by}={value}")
        return None

def create_node(selenium, name, description):
    """创建节点"""
    try:
        # 等待添加节点按钮可点击
        add_node_btn = wait_for_clickable(selenium, By.ID, "add-node-from-graph-button")
        add_node_btn.click()
        
        # 等待模态框出现
        modal = wait_for_element(selenium, By.ID, "node-add-modal")
        assert modal is not None and modal.is_displayed(), "节点添加模态框应该出现"
        
        # 输入节点信息
        name_input = wait_for_element(selenium, By.ID, "node-add-name")
        name_input.clear()
        name_input.send_keys(name)
        
        desc_input = wait_for_element(selenium, By.ID, "node-add-description")
        desc_input.clear()
        desc_input.send_keys(description)
        
        # 保存节点
        save_btn = wait_for_clickable(selenium, By.ID, "node-add-save")
        save_btn.click()
        
        # 等待模态框消失
        WebDriverWait(selenium, 10).until_not(
            EC.visibility_of_element_located((By.ID, "node-add-modal"))
        )
        
        return True
    except Exception as e:
        print(f"创建节点失败: {e}")
        return False

def wait_for_node_count(selenium, expected_count, timeout=5):
    """等待节点数量达到预期值"""
    try:
        WebDriverWait(selenium, timeout).until(
            lambda driver: len(driver.find_elements(By.CSS_SELECTOR, ".node")) == expected_count
        )
        return True
    except TimeoutException:
        print(f"等待节点数量超时，期望: {expected_count}")
        return False

def delete_node(selenium, node_id):
    """删除指定节点"""
    try:
        # 点击节点的下拉菜单
        dropdown_btn = wait_for_clickable(selenium, By.CSS_SELECTOR, f"button[data-dash-id*='{node_id}'][id*='dropdown']")
        dropdown_btn.click()
        
        # 点击删除按钮
        delete_btn = wait_for_clickable(selenium, By.CSS_SELECTOR, f"button[data-dash-id*='{node_id}'][id*='delete']")
        delete_btn.click()
        
        # 等待节点消失
        WebDriverWait(selenium, 10).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, f".node[data-dash-id*='{node_id}']"))
        )
        
        return True
    except Exception as e:
        print(f"删除节点失败: {e}")
        return False

def add_parameter(selenium, node_id, param_name, param_value, param_unit):
    """为节点添加参数"""
    try:
        # 点击节点的参数添加按钮
        add_param_btn = wait_for_clickable(selenium, By.CSS_SELECTOR, f"button[data-dash-id*='{node_id}'][id*='add-param']")
        add_param_btn.click()
        
        # 等待参数添加模态框
        modal = wait_for_element(selenium, By.ID, "parameter-add-modal")
        assert modal.is_displayed(), "参数添加模态框应该出现"
        
        # 输入参数信息
        name_input = wait_for_element(selenium, By.ID, "parameter-add-name")
        name_input.clear()
        name_input.send_keys(param_name)
        
        value_input = wait_for_element(selenium, By.ID, "parameter-add-value")
        value_input.clear()
        value_input.send_keys(str(param_value))
        
        unit_input = wait_for_element(selenium, By.ID, "parameter-add-unit")
        unit_input.clear()
        unit_input.send_keys(param_unit)
        
        # 保存参数
        save_btn = wait_for_clickable(selenium, By.ID, "parameter-add-save")
        save_btn.click()
        
        # 等待模态框消失
        WebDriverWait(selenium, 10).until_not(
            EC.visibility_of_element_located((By.ID, "parameter-add-modal"))
        )
        
        return True
    except Exception as e:
        print(f"添加参数失败: {e}")
        return False

def edit_parameter(selenium, node_id, param_name, new_value):
    """编辑参数值"""
    try:
        # 找到参数输入框
        param_input = wait_for_element(selenium, By.CSS_SELECTOR, f"input[data-dash-id*='{node_id}'][data-param='{param_name}']")
        param_input.clear()
        param_input.send_keys(str(new_value))
        
        # 触发值变化事件
        param_input.send_keys(Keys.TAB)
        time.sleep(0.2)
        
        return True
    except Exception as e:
        print(f"编辑参数失败: {e}")
        return False

def get_node_element(selenium, node_name):
    """获取指定名称的节点元素"""
    try:
        nodes = selenium.find_elements(By.CSS_SELECTOR, ".node")
        for node in nodes:
            if node_name in node.text:
                return node
        return None
    except Exception as e:
        print(f"获取节点元素失败: {e}")
        return None

def setup_test_nodes_with_ui(driver, wait):
    """设置测试节点和UI环境"""
    try:
        # 清理状态
        clean_state(driver)
        
        # 创建测试节点
        test_nodes = [
            ("输入节点", "输入数据节点"),
            ("计算节点", "执行计算的节点"),
            ("输出节点", "输出结果节点")
        ]
        
        created_nodes = []
        for name, description in test_nodes:
            if create_node(driver, name, description):
                created_nodes.append(name)
                # 等待节点出现
                wait_for_node_count(driver, len(created_nodes))
        
        return {
            'nodes': created_nodes,
            'driver': driver,
            'wait': wait
        }
    except Exception as e:
        print(f"设置测试节点失败: {e}")
        return None

def safe_click(selenium, element):
    """安全点击元素，处理可能的遮挡问题"""
    try:
        # 滚动到元素可见
        selenium.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.2)
        
        # 尝试直接点击
        element.click()
        return True
    except ElementClickInterceptedException:
        try:
            # 如果被遮挡，使用JavaScript点击
            selenium.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            print(f"JavaScript点击失败: {e}")
            return False
    except Exception as e:
        print(f"安全点击失败: {e}")
        return False

 