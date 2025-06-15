import pytest
from dash import html
from app import app, id_mapper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def test_add_node(dash_duo):
    dash_duo.start_server(app, debug=False)

    # Check title
    assert dash_duo.find_element("h1").text == "ArchDash"

    # Input node name
    input_box = dash_duo.find_element("#node-name")
    input_box.send_keys("TestNode")

    # Click add node button
    add_btn = dash_duo.find_element("#add-node-button")
    add_btn.click()

    # Print actual content, help debug
    print("Actual output:", dash_duo.find_element("#output-result").text)

    # Check if new node appears in canvas
    dash_duo.wait_for_contains_text("#output-result", "节点 TestNode 已添加", timeout=5)

    # Print all element IDs on the page for debugging
    print("All element IDs on the page:", dash_duo.driver.find_elements(By.CSS_SELECTOR, "*[id]"))

    # Get the first node's id
    node_id = list(id_mapper._node_mapping.keys())[0]
    node_html_id = id_mapper.get_html_id(node_id)
    print("Generated node_html_id:", node_html_id)  # 打印生成的 node_html_id
    node = dash_duo.find_element(f"#{node_html_id}")
    assert node is not None
    assert "TestNode" in node.text

    # Print any errors from the Dash app
    errors = dash_duo.get_logs()
    if errors:
        print("Dash app errors:", errors)

    # 选择左移 - 点击菜单按钮而不是整个节点
    menu_button = dash_duo.find_element(f"#{node_html_id} button")
    menu_button.click()
    dash_duo.wait_for_element("#context-menu", timeout=5)
    move_left_button = dash_duo.find_element("#move-left")
    move_left_button.click()
    dash_duo.wait_for_text_to_equal("#output-result", "节点 TestNode 已左移", timeout=2)

    # 选择右移
    menu_button = dash_duo.find_element(f"#{node_html_id} button")
    menu_button.click()
    dash_duo.wait_for_element("#context-menu", timeout=5)
    move_right_button = dash_duo.find_element("#move-right")
    move_right_button.click()
    dash_duo.wait_for_text_to_equal("#output-result", "节点 TestNode 已右移", timeout=2)

    # 添加参数
    menu_button = dash_duo.find_element(f"#{node_html_id} button")
    menu_button.click()
    dash_duo.wait_for_element("#context-menu", timeout=5)
    add_param_button = dash_duo.find_element("#add-param")
    add_param_button.click()
    dash_duo.wait_for_text_to_equal("#output-result", "参数 test_param 已添加到节点 TestNode", timeout=2)

def test_parameter_editing_no_context_menu(dash_duo):
    """测试编辑参数时不会弹出context-menu（回归测试）
    
    这个测试验证了一个重要的修复：当用户编辑参数名称或值时，
    不应该意外地触发context-menu弹出。
    
    问题原因：之前的实现在参数更新时会重新渲染整个画布，
    导致DOM元素重新创建，从而触发意外的按钮点击事件。
    
    修复方案：移除参数更新回调中的画布重新渲染，仅更新数据模型。
    """
    dash_duo.start_server(app, debug=False)

    # 步骤1：添加一个节点
    input_box = dash_duo.find_element("#node-name")
    input_box.send_keys("TestParamNode")
    
    add_btn = dash_duo.find_element("#add-node-button")
    add_btn.click()
    dash_duo.wait_for_contains_text("#output-result", "节点 TestParamNode 已添加", timeout=5)
    
    # 步骤2：为节点添加参数
    # 获取最新添加的节点ID（最后一个）
    node_id = list(id_mapper._node_mapping.keys())[-1]
    node_html_id = id_mapper.get_html_id(node_id)
    
    menu_button = dash_duo.find_element(f"#{node_html_id} button")
    menu_button.click()
    dash_duo.wait_for_element("#context-menu", timeout=5)
    
    add_param_button = dash_duo.find_element("#add-param")
    add_param_button.click()
    dash_duo.wait_for_contains_text("#output-result", "参数 test_param 已添加到节点 TestParamNode", timeout=5)
    
    # 确保context-menu已关闭
    dash_duo.wait_for_element_by_css_selector(".modal:not(.show)", timeout=5)
    
    # 步骤3：获取参数输入框
    param_inputs = dash_duo.driver.find_elements(By.CSS_SELECTOR, ".param-input")
    assert len(param_inputs) >= 2, "应该至少有2个参数输入框（名称和值）"
    
    param_name_input = param_inputs[0]  # 参数名称输入框
    param_value_input = param_inputs[1]  # 参数值输入框
    
    def assert_no_context_menu():
        """辅助函数：确保context-menu没有弹出"""
        try:
            dash_duo.driver.find_element(By.CSS_SELECTOR, "#context-menu.show")
            assert False, "context-menu意外弹出"
        except:
            pass  # 这是期望的行为
    
    # 步骤4：测试编辑参数名称
    param_name_input.clear()
    param_name_input.send_keys("new_param_name")
    dash_duo.wait_for_text_to_equal("#output-result", "参数 test_param 已添加到节点 TestParamNode", timeout=3)
    assert_no_context_menu()
    
    # 步骤5：测试编辑参数值
    param_value_input.clear()
    param_value_input.send_keys("42.5")
    dash_duo.wait_for_text_to_equal("#output-result", "参数 test_param 已添加到节点 TestParamNode", timeout=3)
    assert_no_context_menu()
    
    # 步骤6：验证菜单按钮仍然正常工作
    menu_button = dash_duo.find_element(f"#{node_html_id} button")
    menu_button.click()
    dash_duo.wait_for_element("#context-menu", timeout=5)
    
    # 验证context-menu正确显示
    context_menu = dash_duo.find_element("#context-menu")
    assert context_menu.is_displayed(), "点击菜单按钮应该显示context-menu" 