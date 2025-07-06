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

def get_parameter_input_box(selenium, node_id=None, param_name=None, input_type="param-value"):
    """获取参数输入框元素，用于测试中直接操作参数
    
    Args:
        selenium: WebDriver实例
        node_id: 节点ID（可选）
        param_name: 参数名称（可选，暂时未使用，因为需要根据索引查找）
        input_type: 输入框类型，"param-value" 或 "param-name"
    
    Returns:
        WebElement: 参数输入框元素，如果未找到则返回None
    """
    try:
        print(f"🔍 开始查找参数输入框: 节点{node_id}, 类型{input_type}")
        
        # 首先等待页面稳定
        time.sleep(2)
        
        # 方法1: 使用简化的选择器，专注于可交互的输入框
        if node_id:
            # 简化选择器：查找节点内的可见参数输入框
            simple_selectors = [
                'input.param-input',  # 任何param-input
                f'input[data-dash-id*="{node_id}"]',  # 带有节点ID的输入框
                f'div[data-dash-id*="{node_id}"] input',  # 节点内的任何输入框
            ]
            
            for selector in simple_selectors:
                try:
                    # 查找所有匹配的输入框
                    elements = selenium.find_elements(By.CSS_SELECTOR, selector)
                    print(f"🔍 选择器 '{selector}' 找到 {len(elements)} 个元素")
                    
                    for i, element in enumerate(elements):
                        # 检查元素是否可见和可交互
                        if element.is_displayed() and element.is_enabled():
                            try:
                                # 尝试滚动到元素
                                selenium.execute_script("arguments[0].scrollIntoView(true);", element)
                                time.sleep(0.5)
                                
                                # 检查是否真的可以交互
                                WebDriverWait(selenium, 3).until(
                                    EC.element_to_be_clickable(element)
                                )
                                
                                print(f"✅ 找到可交互的参数输入框: 元素{i}")
                                return element
                                
                            except Exception as e:
                                print(f"⚠️ 元素{i}不可交互: {e}")
                                continue
                except Exception as e:
                    print(f"⚠️ 选择器失败: {selector}, 错误: {e}")
                    continue
        
        # 方法2: 全局查找第一个可交互的param-input
        try:
            all_param_inputs = selenium.find_elements(By.CSS_SELECTOR, 'input.param-input')
            print(f"🔍 全局找到 {len(all_param_inputs)} 个 param-input 元素")
            
            for i, element in enumerate(all_param_inputs):
                if element.is_displayed() and element.is_enabled():
                    try:
                        # 滚动到元素并等待可交互
                        selenium.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(0.5)
                        
                        WebDriverWait(selenium, 3).until(
                            EC.element_to_be_clickable(element)
                        )
                        
                        print(f"✅ 全局找到可交互的参数输入框: 元素{i}")
                        return element
                        
                    except Exception as e:
                        print(f"⚠️ 全局元素{i}不可交互: {e}")
                        continue
        except Exception as e:
            print(f"⚠️ 全局查找失败: {e}")
        
        # 方法3: 最后的备用方法
        print("🔍 尝试备用选择器...")
        fallback_selectors = [
            'input[type="text"]:not([style*="display: none"])',
            'input[type="number"]:not([style*="display: none"])',
            'input[type="text"]',
            'input'
        ]
        
        for selector in fallback_selectors:
            try:
                elements = selenium.find_elements(By.CSS_SELECTOR, selector)
                print(f"🔍 备用选择器 '{selector}' 找到 {len(elements)} 个元素")
                
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        try:
                            selenium.execute_script("arguments[0].scrollIntoView(true);", element)
                            time.sleep(0.5)
                            
                            WebDriverWait(selenium, 2).until(
                                EC.element_to_be_clickable(element)
                            )
                            
                            print(f"✅ 备用方法找到可交互输入框")
                            return element
                            
                        except:
                            continue
            except Exception as e:
                print(f"⚠️ 备用选择器失败: {selector}, 错误: {e}")
                continue
        
        print(f"❌ 未找到可交互的参数输入框: 节点{node_id}, 类型{input_type}")
        
        # 调试信息：详细分析页面状态
        print("\n🔍 页面调试信息:")
        all_inputs = selenium.find_elements(By.TAG_NAME, "input")
        print(f"   总输入框数量: {len(all_inputs)}")
        
        visible_inputs = [inp for inp in all_inputs if inp.is_displayed()]
        print(f"   可见输入框数量: {len(visible_inputs)}")
        
        enabled_inputs = [inp for inp in visible_inputs if inp.is_enabled()]
        print(f"   可用输入框数量: {len(enabled_inputs)}")
        
        for i, inp in enumerate(enabled_inputs[:5]):  # 只显示前5个
            try:
                dash_id = inp.get_attribute("data-dash-id")
                class_name = inp.get_attribute("class")
                value = inp.get_attribute("value")
                print(f"   输入框{i}: class='{class_name}', value='{value}', dash_id='{dash_id[:50]}...' ")
            except:
                print(f"   输入框{i}: 无法获取属性")
        
        return None
        
    except Exception as e:
        print(f"❌ 获取参数输入框失败: {e}")
        import traceback
        print(f"完整错误: {traceback.format_exc()}")
        return None

def add_parameter_and_get_input(selenium, node_id, param_name="test_param", param_value=100, param_unit="unit"):
    """添加参数并返回参数输入框元素
    
    Args:
        selenium: WebDriver实例
        node_id: 节点ID
        param_name: 参数名称
        param_value: 参数值
        param_unit: 参数单位
    
    Returns:
        WebElement: 参数输入框元素，如果失败则返回None
    """
    try:
        print(f"🔄 开始添加参数: 节点{node_id}, 名称{param_name}")
        
        # 先添加参数
        success = add_parameter(selenium, node_id, param_name, param_value, param_unit)
        if not success:
            print(f"❌ 添加参数失败")
            return None
        
        print(f"✅ 参数添加成功，等待页面更新...")
        
        # 等待更长时间确保参数已经添加并渲染完成
        time.sleep(3)
        
        # 多次尝试获取参数输入框
        max_attempts = 5
        for attempt in range(max_attempts):
            print(f"🔍 第{attempt+1}次尝试获取参数输入框...")
            
            # 获取参数输入框（参数值输入框）
            param_input = get_parameter_input_box(selenium, node_id, param_name, "param-value")
            
            if param_input:
                print(f"✅ 第{attempt+1}次尝试成功获取参数输入框")
                return param_input
            
            # 如果失败，等待一段时间再重试
            if attempt < max_attempts - 1:
                print(f"⚠️ 第{attempt+1}次尝试失败，等待2秒后重试...")
                time.sleep(2)
        
        print(f"❌ 经过{max_attempts}次尝试，仍无法获取参数输入框")
        return None
        
    except Exception as e:
        print(f"❌ 添加参数并获取输入框失败: {e}")
        import traceback
        print(f"完整错误: {traceback.format_exc()}")
        return None

 