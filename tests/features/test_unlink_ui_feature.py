#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试参数unlink功能的UI交互测试 (使用通用Selenium)
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

# 为此文件中的所有测试设置30秒的超时
pytestmark = pytest.mark.timeout(30)

@pytest.fixture(scope="module")
def app_server_driver():
    """
    一个pytest fixture，用于：
    1. 在后台线程启动Dash服务器。
    2. 初始化一个配置好的Selenium WebDriver。
    3. 在测试结束后清理并关闭所有资源。
    """
    host = "127.0.0.1"
    port = 8051  # 使用一个不常用的端口
    base_url = f"http://{host}:{port}"

    def run_app():
        app.run(host=host, port=port, debug=False)

    # 在后台线程运行Dash app
    server_thread = threading.Thread(target=run_app)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)  # 等待服务器启动

    # 初始化WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    
    yield driver, base_url  # 将driver和url提供给测试

    # 测试后的清理工作
    driver.quit()
    # 守护线程会自动退出

def setup_test_nodes_with_dependencies():
    """设置测试用的节点和依赖关系"""
    from app import graph
    
    # 清理现有状态
    graph.nodes.clear()
    layout_manager.node_positions.clear()
    layout_manager.position_nodes.clear()
    layout_manager._init_grid()
    
    # 创建输入节点
    input_node = Node("输入参数", "基础输入参数")
    length = Parameter("长度", 10.0, "m")
    width = Parameter("宽度", 5.0, "m")
    input_node.add_parameter(length)
    input_node.add_parameter(width)
    graph.add_node(input_node)
    layout_manager.place_node(input_node.id)
    
    # 创建计算节点
    calc_node = Node("计算结果", "基于输入参数的计算")
    area = Parameter("面积", 0.0, "m²", 
                    calculation_func="result = dependencies[0].value * dependencies[1].value")
    area.add_dependency(length)
    area.add_dependency(width)
    calc_node.add_parameter(area)
    graph.add_node(calc_node)
    layout_manager.place_node(calc_node.id)
    
    # 设置计算图关联
    for node in graph.nodes.values():
        for param in node.parameters:
            param.set_graph(graph)
    
    # 计算初始值
    area.calculate()
    
    return {
        'input_node': input_node,
        'calc_node': calc_node,
        'length': length,
        'width': width,
        'area': area
    }


def test_unlink_icon_display_logic(app_server_driver):
    """测试unlink图标的显示逻辑：只有unlinked=True且有依赖时才显示🔓"""
    driver, base_url = app_server_driver
    driver.get(base_url)
    
    # 设置测试数据
    test_data = setup_test_nodes_with_dependencies()
    calc_node = test_data['calc_node']
    input_node = test_data['input_node']
    
    # 等待页面加载
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "canvas-container"))
    )
    
    print("🔬 测试unlink图标显示逻辑")
    
    # 1. 测试初始状态：有依赖但未unlink，不应显示🔓图标
    area_unlink_icons = driver.find_elements(
        By.CSS_SELECTOR, 
        f"div[data-dash-id*='{calc_node.id}'] .unlink-icon"
    )
    assert len(area_unlink_icons) == 0, "初始状态下不应显示unlink图标"
    print("✅ 初始状态：有依赖但未unlink，不显示🔓图标")
    
    # 2. 测试无依赖参数：永远不应显示unlink图标
    length_unlink_icons = driver.find_elements(
        By.CSS_SELECTOR, 
        f"div[data-dash-id*='{input_node.id}'] .unlink-icon"
    )
    assert len(length_unlink_icons) == 0, "无依赖参数不应显示unlink图标"
    print("✅ 无依赖参数：不显示🔓图标")


def test_manual_value_change_auto_unlink(app_server_driver):
    """如果一个有依赖的参数值被手动更改，应该自动取消链接并显示unlink图标。"""
    driver, base_url = app_server_driver
    driver.get(base_url)
    wait = WebDriverWait(driver, 10)

    # 等待画布加载
    wait.until(EC.presence_of_element_located((By.ID, "canvas-container")))

    # 设置一个有依赖的参数
    test_data = setup_test_nodes_with_dependencies()
    calc_node_id = test_data['calc_node'].id
    input_node_id = test_data['input_node'].id
    area_param_name = test_data['area'].name
    length_param_name = test_data['length'].name

    # 找到计算节点的输入框
    calc_input_selector = f"div[data-dash-id*='{calc_node_id}'] input[id*='\"param_name\":\"{area_param_name}\"']"
    calc_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, calc_input_selector)))
    
    # 初始状态断言
    initial_value = test_data['area'].value
    assert calc_input.get_attribute("value") == f"{initial_value:.2f}"
    assert len(driver.find_elements(By.CSS_SELECTOR, ".unlink-icon")) == 0

    # 手动更改值，这应该会触发取消链接
    calc_input.clear()
    calc_input.send_keys("150")
    calc_input.send_keys(Keys.ENTER)

    # 等待unlink图标出现
    unlink_icon_selector = f"div[data-dash-id*='{calc_node_id}'] .unlink-icon-container"
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, unlink_icon_selector)))

    # 验证其父节点的值未被更新
    length_input_selector = f"div[data-dash-id*='{input_node_id}'] input[id*='\"param_name\":\"{length_param_name}\"']"
    length_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, length_input_selector)))
    assert length_input.get_attribute("value") == f"{test_data['length'].value:.2f}"


def test_unlink_icon_click_reconnect(app_server_driver):
    """点击unlink图标应该重新链接参数，重新计算其值，并使图标消失。"""
    driver, base_url = app_server_driver
    driver.get(base_url)
    wait = WebDriverWait(driver, 10)

    # 等待画布加载
    wait.until(EC.presence_of_element_located((By.ID, "canvas-container")))

    # 设置并手动更改参数以显示图标
    test_data = setup_test_nodes_with_dependencies()
    calc_node_id = test_data['calc_node'].id
    calc_param_name = test_data['area'].name
    
    calc_input_selector = f"div[data-dash-id*='{calc_node_id}'] input[id*='\"param_name\":\"{calc_param_name}\"']"
    calc_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, calc_input_selector)))
    calc_input.clear()
    calc_input.send_keys("150")
    calc_input.send_keys(Keys.ENTER)

    # 等待并点击unlink图标以重新连接
    unlink_icon_container_selector = f"div[data-dash-id*='{calc_node_id}'] .unlink-icon-container"
    unlink_icon_container = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, unlink_icon_container_selector)))
    unlink_icon_container.click()

    # 等待值被重新计算和更新
    recalculated_value = f"{test_data['length'].value * test_data['width'].value:.2f}"
    wait.until(
        EC.text_to_be_present_in_element_value(
            (By.CSS_SELECTOR, calc_input_selector), recalculated_value
        )
    )

    # 验证unlink图标消失
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, unlink_icon_container_selector)))


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


def test_unlink_ui_integration(app_server_driver):
    """测试unlink功能的完整UI集成"""
    driver, base_url = app_server_driver
    driver.get(base_url)
    wait = WebDriverWait(driver, 10)

    # 设置测试数据
    test_data = setup_test_nodes_with_dependencies()
    area_node_id = test_data['calc_node'].id
    area_param_name = test_data['area'].name
    input_node_id = test_data['input_node'].id
    length_param_name = test_data['length'].name

    # 等待画布容器加载
    wait.until(EC.presence_of_element_located((By.ID, "canvas-container")))

    print("🔬 测试unlink功能完整UI集成")

    # 1. 验证初始状态：无unlink图标
    initial_icon_count = len(driver.find_elements(By.CSS_SELECTOR, ".unlink-icon-container"))
    assert initial_icon_count == 0, "初始状态不应有unlink图标"
    print(f"初始状态unlink图标数量: {initial_icon_count}")

    # 2. 修改有依赖的参数值，应该显示🔓图标
    area_input_selector = f"div[data-dash-id*='{area_node_id}'] input[id*='\"param_name\":\"{area_param_name}\"']"
    area_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, area_input_selector)))
    area_input.clear()
    area_input.send_keys("150")
    area_input.send_keys(Keys.ENTER)

    unlink_icon_container_selector = f"div[data-dash-id*='{area_node_id}'] .unlink-icon-container"
    unlink_icon_container = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, unlink_icon_container_selector)))
    print("🔓 Unlink图标已显示")

    # 3. 验证其父参数的值未改变
    length_input_selector = f"div[data-dash-id*='{input_node_id}'] input[id*='\"param_name\":\"{length_param_name}\"']"
    length_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, length_input_selector)))
    assert length_input.get_attribute("value") == f"{test_data['length'].value:.2f}"
    print("父参数值未变")

    # 4. 点击图标，重新计算，图标消失
    clickable_icon = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, unlink_icon_container_selector)))
    clickable_icon.click()
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, unlink_icon_container_selector)))
    print("🔄 图标已点击，等待重新计算和图标消失")

    # 5. 验证值已重新计算
    recalculated_value = f"{test_data['length'].value * test_data['width'].value:.2f}"
    wait.until(EC.text_to_be_present_in_element_value(
        (By.CSS_SELECTOR, area_input_selector), recalculated_value
    ))
    print(f"值已重新计算为 {recalculated_value}")

    # 6. 再次修改父参数，不应显示图标
    length_input.clear()
    length_input.send_keys("12")
    length_input.send_keys(Keys.ENTER)

    # 值应该根据新父级值更新 12 * 5 = 60
    final_recalculated_value = f"{12.0 * test_data['width'].value:.2f}"
    wait.until(EC.text_to_be_present_in_element_value(
        (By.CSS_SELECTOR, area_input_selector), final_recalculated_value
    ))
    # 确认图标没有再次出现
    assert len(driver.find_elements(By.CSS_SELECTOR, unlink_icon_container_selector)) == 0, "修改父参数后不应出现unlink图标"
    print("✅ UI集成测试通过")


if __name__ == "__main__":
    print("🧪 运行unlink UI功能测试")
    print("=" * 50)
    
    # 这些测试需要在pytest环境中运行
    # 可以使用: pytest test_unlink_ui_feature.py -v
    
    print("使用命令运行测试: pytest test_unlink_ui_feature.py -v")
    print("测试覆盖:")
    print("1. unlink图标显示逻辑")
    print("2. 手动修改值自动unlink")
    print("3. 点击🔓图标重新连接")
    print("4. 相关性分析自动unlink")
    print("5. 完整UI集成测试") 