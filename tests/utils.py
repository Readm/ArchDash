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


def get_current_graph():
    """获取当前会话的graph实例"""
    from session_graph import get_graph
    return get_graph()


def get_current_layout_manager():
    """获取当前会话的layout_manager实例"""
    graph = get_current_graph()
    return graph.layout_manager


def clean_state(selenium):
    """清理测试状态"""
    try:
        # 使用当前会话的graph和layout_manager
        graph = get_current_graph()
        layout_manager = get_current_layout_manager()
        
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
        # 等待页面完全加载
        time.sleep(2)
        
        # 等待添加节点按钮可点击
        add_node_btn = wait_for_clickable(selenium, By.ID, "add-node-from-graph-button")
        if not add_node_btn:
            print("添加节点按钮不可点击")
            return False
            
        print(f"点击添加节点按钮，准备创建节点: {name}")
        add_node_btn.click()
        
        # 等待模态框出现
        time.sleep(1)  # 等待模态框加载
        modal = wait_for_element(selenium, By.ID, "node-add-modal")
        if not modal:
            print("模态框元素未找到")
            return False
            
        if not modal.is_displayed():
            print("模态框不可见")
            return False
            
        print("模态框已出现")
        
        # 输入节点信息
        name_input = wait_for_element(selenium, By.ID, "node-add-name")
        if not name_input:
            print("节点名称输入框未找到")
            return False
            
        name_input.clear()
        name_input.send_keys(name)
        print(f"已输入节点名称: {name}")
        
        desc_input = wait_for_element(selenium, By.ID, "node-add-description")
        if not desc_input:
            print("节点描述输入框未找到")
            return False
            
        desc_input.clear()
        desc_input.send_keys(description)
        print(f"已输入节点描述: {description}")
        
        # 保存节点
        save_btn = wait_for_clickable(selenium, By.ID, "node-add-save")
        if not save_btn:
            print("保存按钮不可点击")
            return False
            
        print(f"找到保存按钮: {save_btn.text}, 是否显示: {save_btn.is_displayed()}, 是否启用: {save_btn.is_enabled()}")
        print("点击保存按钮")
        # 使用JavaScript点击确保点击成功
        try:
            save_btn.click()
            print("直接点击成功")
        except Exception as e:
            print(f"直接点击失败，尝试JavaScript点击: {e}")
            selenium.execute_script("arguments[0].click();", save_btn)
            print("JavaScript点击完成")
        
        # 等待一段时间让保存操作完成
        time.sleep(2)
        
        # 等待模态框消失
        try:
            WebDriverWait(selenium, 10).until_not(
                EC.visibility_of_element_located((By.ID, "node-add-modal"))
            )
            print("模态框已消失")
        except TimeoutException:
            print("模态框消失超时，但继续执行")
        
        # 等待节点出现
        time.sleep(3)  # 增加等待时间
        
        # 验证节点是否真的创建成功 - 尝试多种选择器
        selectors = [
            '[data-testid="node-container"]',
            '.node-container',
            '[data-dash-id*="node"]'
        ]
        
        for selector in selectors:
            nodes = selenium.find_elements(By.CSS_SELECTOR, selector)
            if len(nodes) > 0:
                print(f"节点创建成功，使用选择器 '{selector}' 找到 {len(nodes)} 个节点")
                return True
        
        print("节点创建失败，所有选择器都未找到节点")
        return False
    except Exception as e:
        print(f"创建节点失败: {e}")
        return False

def wait_for_node_count(selenium, expected_count, timeout=10):
    """等待节点数量达到预期值"""
    try:
        WebDriverWait(selenium, timeout).until(
            lambda driver: len(driver.find_elements(By.CSS_SELECTOR, '[data-testid="node-container"]')) == expected_count
        )
        return True
    except TimeoutException:
        print(f"等待节点数量超时，期望: {expected_count}")
        return False

def delete_node(selenium, node_id):
    """删除指定节点"""
    try:
        # 点击节点的下拉菜单 - 使用data-testid查找
        dropdown_btn = wait_for_clickable(selenium, By.CSS_SELECTOR, f'[data-testid="node-dropdown-btn"][data-dash-id*="node": "{node_id}"]')
        if not dropdown_btn:
            print(f"未找到节点 {node_id} 的下拉菜单按钮")
            return False
        dropdown_btn.click()
        
        # 点击删除按钮 - 使用data-testid查找
        delete_btn = wait_for_clickable(selenium, By.CSS_SELECTOR, f'[data-testid="node-delete-btn"][data-dash-id*="node": "{node_id}"]')
        if not delete_btn:
            print(f"未找到节点 {node_id} 的删除按钮")
            return False
        delete_btn.click()
        
        # 等待节点消失
        WebDriverWait(selenium, 10).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, f'[data-testid="node-container"][data-dash-id*="node": "{node_id}"]'))
        )
        
        return True
    except Exception as e:
        print(f"删除节点失败: {e}")
        return False

def add_parameter(selenium, node_id, param_name, param_value, param_unit):
    """为节点添加参数"""
    try:
        # 点击节点的参数添加按钮
        add_param_btn = wait_for_clickable(selenium, By.CSS_SELECTOR, f'[data-testid="add-param-btn"][data-dash-id*="node": "{node_id}"]')
        if not add_param_btn:
            print(f"未找到节点 {node_id} 的参数添加按钮")
            return False
        add_param_btn.click()
        
        # 等待参数添加模态框
        modal = wait_for_element(selenium, By.ID, "parameter-add-modal")
        if not modal or not modal.is_displayed():
            print("参数添加模态框未出现")
            return False
        
        # 输入参数信息
        name_input = wait_for_element(selenium, By.ID, "parameter-add-name")
        if not name_input:
            print("参数名称输入框未找到")
            return False
        name_input.clear()
        name_input.send_keys(param_name)
        
        value_input = wait_for_element(selenium, By.ID, "parameter-add-value")
        if not value_input:
            print("参数值输入框未找到")
            return False
        value_input.clear()
        value_input.send_keys(str(param_value))
        
        unit_input = wait_for_element(selenium, By.ID, "parameter-add-unit")
        if not unit_input:
            print("参数单位输入框未找到")
            return False
        unit_input.clear()
        unit_input.send_keys(param_unit)
        
        # 保存参数
        save_btn = wait_for_clickable(selenium, By.ID, "parameter-add-save")
        if not save_btn:
            print("参数保存按钮不可点击")
            return False
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
        param_input = wait_for_element(selenium, By.CSS_SELECTOR, f'[data-testid="param-input"][data-dash-id*="node": "{node_id}"][data-param="{param_name}"]')
        if not param_input:
            print(f"未找到参数 {param_name} 的输入框")
            return False
        
        param_input.clear()
        param_input.send_keys(str(new_value))
        
        # 触发失去焦点事件
        param_input.send_keys(Keys.TAB)
        
        return True
    except Exception as e:
        print(f"编辑参数失败: {e}")
        return False

def get_node_element(selenium, node_name):
    """获取指定名称的节点元素"""
    try:
        # 使用多种选择器查找节点
        selectors = [
            f'[data-testid="node-container"]:has(.node-name:contains("{node_name}"))',
            f'.node-container:has(.node-name:contains("{node_name}"))',
            f'[data-dash-id*="node"]:has(.node-name:contains("{node_name}"))'
        ]
        
        for selector in selectors:
            try:
                element = selenium.find_element(By.CSS_SELECTOR, selector)
                if element:
                    return element
            except:
                continue
        
        return None
    except Exception as e:
        print(f"获取节点元素失败: {e}")
        return None

def setup_test_nodes_with_ui(driver, wait):
    """通过UI设置测试节点"""
    try:
        # 创建第一个节点
        create_node(driver, "节点1", "测试节点1")
        wait_for_node_count(driver, 1)
        
        # 创建第二个节点
        create_node(driver, "节点2", "测试节点2")
        wait_for_node_count(driver, 2)
        
        return True
    except Exception as e:
        print(f"设置测试节点失败: {e}")
        return False

def safe_click(selenium, element):
    """安全点击元素，处理可能的拦截"""
    try:
        # 滚动到元素可见
        selenium.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.2)
        
        # 尝试直接点击
        element.click()
        return True
    except ElementClickInterceptedException:
        try:
            # 如果被拦截，使用JavaScript点击
            selenium.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            print(f"JavaScript点击也失败: {e}")
            return False
    except Exception as e:
        print(f"点击元素失败: {e}")
        return False

def wait_for_error_message(selenium, expected_message, timeout=10):
    """等待错误消息出现"""
    try:
        WebDriverWait(selenium, timeout).until(
            lambda driver: expected_message in driver.page_source
        )
        return True
    except TimeoutException:
        print(f"等待错误消息超时: {expected_message}")
        return False

def wait_for_success_message(selenium, expected_message, timeout=10):
    """等待成功消息出现"""
    try:
        WebDriverWait(selenium, timeout).until(
            lambda driver: expected_message in driver.page_source
        )
        return True
    except TimeoutException:
        print(f"等待成功消息超时: {expected_message}")
        return False

def wait_for_modal_to_disappear(selenium, modal_testid, timeout=10):
    """等待模态框消失"""
    try:
        WebDriverWait(selenium, timeout).until_not(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f'[data-testid="{modal_testid}"]'))
        )
        return True
    except TimeoutException:
        print(f"等待模态框消失超时: {modal_testid}")
        return False

def get_node_count(selenium):
    """获取当前节点数量"""
    try:
        nodes = selenium.find_elements(By.CSS_SELECTOR, '[data-testid="node-container"]')
        return len(nodes)
    except Exception as e:
        print(f"获取节点数量失败: {e}")
        return 0

def find_parameter_input(selenium, node_id, param_name):
    """查找参数输入框"""
    try:
        selectors = [
            f'[data-testid="param-input"][data-dash-id*="node": "{node_id}"][data-param="{param_name}"]',
            f'input[data-dash-id*="node": "{node_id}"][data-param="{param_name}"]',
            f'input[data-dash-id*="param-value"][data-dash-id*="node": "{node_id}"]'
        ]
        
        for selector in selectors:
            try:
                element = selenium.find_element(By.CSS_SELECTOR, selector)
                if element:
                    return element
            except:
                continue
        
        return None
    except Exception as e:
        print(f"查找参数输入框失败: {e}")
        return None