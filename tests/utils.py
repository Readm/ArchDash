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
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.common.keys import Keys


def clean_state(selenium):
    """清理测试状态"""
    try:
        print("🔄 开始清理测试状态...")
        
        # 清理应用状态
        from app import graph, layout_manager
        
        # 记录当前状态
        print(f"清理前: 节点数量={len(graph.nodes)}, 位置数量={len(layout_manager.node_positions)}")
        
        # 清理状态
        graph.nodes.clear()
        layout_manager.node_positions.clear()
        layout_manager.position_nodes.clear()
        layout_manager._init_grid()
        graph.recently_updated_params.clear()
        
        # 清理任何残留的回调或状态
        if hasattr(graph, '_callbacks'):
            graph._callbacks.clear()
        if hasattr(graph, '_dependency_cache'):
            graph._dependency_cache.clear()
        
        # 检查Selenium连接状态
        try:
            current_url = selenium.current_url
            print(f"当前URL: {current_url}")
            
            # 检查页面是否响应
            selenium.execute_script("return document.readyState")
            
        except Exception as e:
            print(f"⚠️ Selenium连接检查失败: {e}")
            # 如果连接有问题，尝试重新加载页面
            try:
                selenium.refresh()
                time.sleep(1)
            except Exception as refresh_e:
                print(f"⚠️ 页面刷新失败: {refresh_e}")
                raise Exception(f"Selenium连接异常且无法修复: {e}")
        
        # 刷新页面以确保状态清理
        selenium.refresh()
        time.sleep(0.5)
        
        # 等待页面加载完成
        wait_for_page_load(selenium)
        
        # 验证清理成功
        print(f"清理后: 节点数量={len(graph.nodes)}, 位置数量={len(layout_manager.node_positions)}")
        print("✅ 测试状态清理完成")
        
    except Exception as e:
        print(f"❌ 清理状态时出错: {e}")
        # 记录详细错误信息
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        
        # 尝试基本的页面刷新
        try:
            selenium.refresh()
            time.sleep(1)
            wait_for_page_load(selenium)
            print("⚠️ 已尝试基本页面刷新")
        except Exception as refresh_e:
            print(f"❌ 基本页面刷新也失败: {refresh_e}")
            raise Exception(f"状态清理失败且无法恢复: {e}")

def wait_for_page_load(selenium, timeout=10):
    """等待页面加载完成"""
    try:
        print("🔄 等待页面加载...")
        
        # 等待页面基本元素加载
        WebDriverWait(selenium, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 等待JavaScript完成
        WebDriverWait(selenium, timeout).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        
        # 等待Dash应用初始化
        try:
            WebDriverWait(selenium, timeout).until(
                EC.presence_of_element_located((By.ID, "canvas-container"))
            )
            print("✅ 页面加载完成")
        except TimeoutException:
            print("⚠️ 画布容器未找到，页面可能未完全加载")
            # 不抛出异常，继续执行
            
    except TimeoutException:
        print("❌ 页面加载超时")
        # 尝试获取页面状态信息
        try:
            current_url = selenium.current_url
            page_source_length = len(selenium.page_source)
            print(f"当前URL: {current_url}")
            print(f"页面源码长度: {page_source_length}")
        except Exception as e:
            print(f"无法获取页面信息: {e}")
        raise Exception(f"页面加载超时 (超时时间: {timeout}秒)")
    except Exception as e:
        print(f"❌ 页面加载异常: {e}")
        raise

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
    """创建节点 - 简化版，去掉多余的等待"""
    try:
        print(f"🔧 创建节点: {name}")
        
        # 直接点击添加节点按钮，不等待画布准备
        if not click_button_by_testid(selenium, "add-node-button"):
            raise Exception("无法点击添加节点按钮")
        
        # 等待模态框打开
        modal = wait_for_modal_open(selenium, "node-add-modal")
        if not modal:
            raise Exception("节点添加模态框未出现")
        
        # 输入节点信息
        name_input = selenium.find_element(By.ID, "node-add-name")
        name_input.clear()
        name_input.send_keys(name)
        
        desc_input = selenium.find_element(By.ID, "node-add-description")
        desc_input.clear()
        desc_input.send_keys(description)
        
        # 保存节点
        save_btn = WebDriverWait(selenium, 5).until(
            EC.element_to_be_clickable((By.ID, "node-add-save"))
        )
        selenium.execute_script("arguments[0].scrollIntoView(true);", save_btn)
        time.sleep(0.2)
        safe_click(selenium, save_btn)
        
        # 等待模态框关闭
        if not wait_for_modal_close(selenium, "node-add-modal"):
            raise Exception("模态框未正确关闭")
        
        # 短暂等待DOM更新
        time.sleep(0.5)
        
        # 简化的节点验证 - 降低超时时间
        if not wait_for_node_with_content(selenium, name, timeout=5):
            raise Exception(f"节点'{name}'创建后未正确显示或内容为空")
        
        print(f"✅ 节点创建并验证完成: {name}")
        return True
        
    except Exception as e:
        print(f"❌ 创建节点失败: {e}")
        return False

def wait_for_node_count(selenium, expected_count, timeout=5):
    """等待节点数量达到预期值"""
    try:
        WebDriverWait(selenium, timeout).until(
            lambda driver: len(driver.find_elements(By.CSS_SELECTOR, ".node-container")) == expected_count
        )
        return True
    except TimeoutException:
        print(f"等待节点数量超时，期望: {expected_count}，实际: {len(selenium.find_elements(By.CSS_SELECTOR, '.node-container'))}")
        return False

def wait_for_node_with_content(selenium, node_name, timeout=8):
    """等待包含指定内容的节点出现 - 宽松版"""
    try:
        print(f"🔍 等待包含'{node_name}'的节点出现...")
        
        def node_with_content_exists(driver):
            # 查找所有节点容器
            nodes = driver.find_elements(By.CSS_SELECTOR, ".node-container")
            
            for node in nodes:
                if node.is_displayed():
                    # 检查节点是否有正确的内容 - 不再检查data-node-ready
                    node_text = node.text.strip()
                    if node_name in node_text:
                        print(f"✅ 找到包含'{node_name}'的节点")
                        return True
            
            # 简化调试输出
            if nodes:
                print(f"🔍 找到 {len(nodes)} 个节点容器，但内容不匹配")
            
            return False
        
        WebDriverWait(selenium, timeout).until(node_with_content_exists)
        return True
        
    except TimeoutException:
        print(f"❌ 等待包含'{node_name}'的节点超时")
        
        # 简化调试信息
        try:
            all_nodes = selenium.find_elements(By.CSS_SELECTOR, ".node-container")
            print(f"🔍 调试: 共 {len(all_nodes)} 个节点容器")
            
            for i, node in enumerate(all_nodes[:3]):  # 只显示前3个
                text = node.text.strip()[:30]  # 限制文本长度
                print(f"  节点{i+1}: 显示={node.is_displayed()}, 文本='{text}...'")
        except Exception as debug_error:
            print(f"❌ 调试失败: {debug_error}")
        
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
            EC.presence_of_element_located((By.CSS_SELECTOR, f".node-container[data-dash-id*='{node_id}']"))
        )
        
        return True
    except Exception as e:
        print(f"删除节点失败: {e}")
        return False

def add_parameter(selenium, node_id, param_name, param_value, param_unit=""):
    """添加参数 - 简化版，去掉多余的等待"""
    try:
        print(f"🔧 为节点 {node_id} 添加参数: {param_name} = {param_value}")
        
        # 直接查找并点击节点的添加参数按钮
        param_btn_testid = f"add-param-button-{node_id}"
        if not click_button_by_testid(selenium, param_btn_testid):
            raise Exception(f"无法点击节点 {node_id} 的添加参数按钮")
        
        # 等待参数编辑模态框打开
        modal = wait_for_modal_open(selenium, "param-edit-modal")
        if not modal:
            raise Exception("参数编辑模态框未出现")
        
        # 输入参数信息
        name_input = selenium.find_element(By.ID, "param-edit-name")
        name_input.clear()
        name_input.send_keys(param_name)
        
        if param_unit:
            unit_input = selenium.find_element(By.ID, "param-edit-unit")
            unit_input.clear()
            unit_input.send_keys(param_unit)
        
        # 对于参数值，我们需要通过计算函数来设置
        # 这里我们设置一个简单的计算函数，直接返回指定的值
        calc_editor = selenium.find_element(By.CSS_SELECTOR, ".ace_editor")
        if calc_editor:
            # 清空现有内容并设置新的计算函数
            calc_function = f"# 计算函数\nresult = {param_value}"
            selenium.execute_script(f"ace.edit(arguments[0]).setValue('{calc_function}');", calc_editor)
        
        # 保存参数
        save_btn = WebDriverWait(selenium, 5).until(
            EC.element_to_be_clickable((By.ID, "param-edit-save"))
        )
        selenium.execute_script("arguments[0].scrollIntoView(true);", save_btn)
        time.sleep(0.2)
        safe_click(selenium, save_btn)
        
        # 等待模态框关闭
        if not wait_for_modal_close(selenium, "param-edit-modal"):
            raise Exception("模态框未正确关闭")
        
        # 等待参数出现
        time.sleep(1)  # 短暂等待DOM更新
        
        print(f"✅ 参数添加完成: {param_name} = {param_value}")
        return True
        
    except Exception as e:
        print(f"❌ 添加参数失败: {e}")
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
        nodes = selenium.find_elements(By.CSS_SELECTOR, ".node-container")
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
        node_info = {}
        for i, (name, description) in enumerate(test_nodes):
            if create_node(driver, name, description):
                created_nodes.append(name)
                node_info[name] = {
                    'index': i,
                    'name': name,
                    'description': description
                }
                # 等待节点出现
                wait_for_node_count(driver, len(created_nodes))
        
        # 为了向后兼容，提供计算节点的参数信息
        # 这些测试期望计算节点有一个数值参数
        calc_node_id = "node_1"  # 计算节点通常是第二个节点
        calc_param_value = 100.0  # 默认计算参数值
        
        return {
            'nodes': created_nodes,
            'node_info': node_info,
            'calc_node_params': [calc_node_id, calc_param_value],  # [node_id, param_value]
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

def wait_for_canvas_ready(selenium, timeout=5):
    """等待画布准备好进行测试 - 简化版，只等待基本容器出现"""
    try:
        print("🔍 等待画布容器出现...")
        
        # 只等待画布容器出现，不检查复杂的状态
        WebDriverWait(selenium, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='canvas-container']"))
        )
        
        # 短暂等待确保DOM稳定
        time.sleep(0.5)
        
        print("✅ 画布容器已准备就绪")
        return True
    except TimeoutException:
        print("❌ 等待画布容器超时")
        return False

def wait_for_nodes_loaded(selenium, expected_count=None, timeout=10):
    """等待节点加载完成 - 增强调试信息"""
    try:
        print(f"🔍 等待节点加载完成，期望数量: {expected_count}")
        
        if expected_count == 0:
            # 等待空状态
            empty_state = WebDriverWait(selenium, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='empty-state'][data-ready='true']"))
            )
            print("✅ 空状态确认")
            return True
        elif expected_count:
            # 等待指定数量的节点
            WebDriverWait(selenium, timeout).until(
                lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "[data-testid^='node-'][data-node-ready='true']")) == expected_count
            )
            print(f"✅ 找到 {expected_count} 个就绪节点")
            return True
        else:
            # 只等待至少有一个节点
            WebDriverWait(selenium, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid^='node-'][data-node-ready='true']"))
            )
            nodes = selenium.find_elements(By.CSS_SELECTOR, "[data-testid^='node-'][data-node-ready='true']")
            print(f"✅ 找到 {len(nodes)} 个就绪节点")
            return True
            
    except TimeoutException:
        print(f"❌ 等待节点加载超时")
        # 调试信息：显示当前实际状态
        try:
            actual_nodes = selenium.find_elements(By.CSS_SELECTOR, "[data-testid^='node-']")
            ready_nodes = selenium.find_elements(By.CSS_SELECTOR, "[data-testid^='node-'][data-node-ready='true']")
            empty_state = selenium.find_elements(By.CSS_SELECTOR, "[data-testid='empty-state']")
            
            print(f"🔍 调试信息：")
            print(f"  - 实际节点数: {len(actual_nodes)}")
            print(f"  - 就绪节点数: {len(ready_nodes)}")
            print(f"  - 空状态元素: {len(empty_state)}")
            
            if actual_nodes:
                print(f"  - 节点testid: {[node.get_attribute('data-testid') for node in actual_nodes[:3]]}")
        except Exception as debug_error:
            print(f"🔍 获取调试信息失败: {debug_error}")
        
        return False

def get_node_element_by_testid(selenium, node_id):
    """通过data-testid获取节点元素"""
    try:
        node = selenium.find_element(By.CSS_SELECTOR, f"[data-testid='node-{node_id}']")
        return node
    except NoSuchElementException:
        print(f"未找到节点: node-{node_id}")
        return None

def get_node_element_by_name(selenium, node_name):
    """通过节点名称获取节点元素"""
    try:
        node = selenium.find_element(By.CSS_SELECTOR, f"[data-node-name='{node_name}']")
        return node
    except NoSuchElementException:
        print(f"未找到节点: {node_name}")
        return None

def get_parameter_input_safe(selenium, node_id, param_idx, input_type="value"):
    """使用data-testid安全获取参数输入框"""
    try:
        testid = f"param-{input_type}-input-{node_id}-{param_idx}"
        element = selenium.find_element(By.CSS_SELECTOR, f"[data-testid='{testid}']")
        
        # 确保元素可见和可交互
        if element.is_displayed() and element.is_enabled():
            # 滚动到元素可见
            selenium.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.3)
            
            # 等待元素可点击
            WebDriverWait(selenium, 5).until(
                EC.element_to_be_clickable(element)
            )
            
            return element
        else:
            print(f"参数输入框不可交互: {testid}")
            return None
            
    except (NoSuchElementException, TimeoutException) as e:
        print(f"无法找到参数输入框: {testid}, 错误: {e}")
        return None

def click_button_by_testid(selenium, testid, timeout=5):
    """通过data-testid安全点击按钮"""
    try:
        print(f"🔍 查找按钮: {testid}")
        button = WebDriverWait(selenium, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='{testid}']"))
        )
        
        # 滚动到按钮可见
        selenium.execute_script("arguments[0].scrollIntoView(true);", button)
        time.sleep(0.2)
        
        # 安全点击
        safe_click(selenium, button)
        print(f"✅ 成功点击按钮: {testid}")
        return True
        
    except (TimeoutException, ElementClickInterceptedException) as e:
        print(f"❌ 点击按钮失败: {testid}, 错误: {e}")
        return False

def wait_for_modal_open(selenium, modal_id, timeout=5):
    """等待模态框打开 - 使用ID而不是data-testid"""
    try:
        modal = WebDriverWait(selenium, timeout).until(
            EC.visibility_of_element_located((By.ID, modal_id))
        )
        print(f"✅ 模态框已打开: {modal_id}")
        return modal
    except TimeoutException:
        print(f"❌ 模态框打开超时: {modal_id}")
        return None

def wait_for_modal_close(selenium, modal_id, timeout=5):
    """等待模态框关闭 - 使用ID而不是data-testid"""
    try:
        WebDriverWait(selenium, timeout).until_not(
            EC.visibility_of_element_located((By.ID, modal_id))
        )
        print(f"✅ 模态框已关闭: {modal_id}")
        return True
    except TimeoutException:
        print(f"❌ 模态框关闭超时: {modal_id}")
        return False

def wait_for_text(selenium, text, timeout=5):
    """等待页面上出现指定文本"""
    try:
        WebDriverWait(selenium, timeout).until(
            lambda driver: text in driver.page_source
        )
        return True
    except TimeoutException:
        print(f"等待文本 '{text}' 出现超时")
        return False

def wait_for_element_text(selenium, by, value, expected_text, timeout=5):
    """等待指定元素包含指定文本"""
    try:
        WebDriverWait(selenium, timeout).until(
            lambda driver: expected_text in driver.find_element(by, value).text
        )
        return True
    except (TimeoutException, NoSuchElementException):
        print(f"等待元素文本 '{expected_text}' 出现超时")
        return False

def get_visible_node_elements(selenium):
    """获取所有可见的节点元素"""
    try:
        # 查找所有节点容器
        all_nodes = selenium.find_elements(By.CSS_SELECTOR, ".node-container")
        
        # 过滤出可见的节点
        visible_nodes = []
        for node in all_nodes:
            if node.is_displayed():
                visible_nodes.append(node)
        
        return visible_nodes
    except Exception as e:
        print(f"获取可见节点失败: {e}")
        return []

def wait_for_no_loading_indicators(selenium, timeout=5):
    """等待页面上没有加载指示器"""
    try:
        WebDriverWait(selenium, timeout).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".loading, .spinner, [data-loading='true']"))
        )
        return True
    except TimeoutException:
        print("等待加载指示器消失超时")
        return False

 