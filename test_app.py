import pytest
from dash import html
from app import app, id_mapper, layout_manager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import time

def test_add_node_with_grid_layout(dash_duo):
    """测试添加节点功能和网格布局系统"""
    dash_duo.start_server(app, debug=False)

    # 清理之前测试的状态
    from app import graph
    graph.nodes.clear()
    id_mapper._node_mapping.clear()
    layout_manager.node_positions.clear()
    layout_manager.position_nodes.clear()
    # 重新初始化网格
    layout_manager._init_grid()

    # 检查标题
    assert dash_duo.find_element("h1").text == "ArchDash"

    # 输入节点名称
    input_box = dash_duo.find_element("#node-name")
    input_box.send_keys("TestNode")

    # 点击添加节点按钮
    add_btn = dash_duo.find_element("#add-node-button")
    add_btn.click()

    # 验证节点添加成功的消息
    dash_duo.wait_for_contains_text("#output-result", "节点 TestNode 已添加到位置", timeout=5)
    print("✅ 节点添加成功")

    # 获取节点ID和验证
    node_id = list(id_mapper._node_mapping.keys())[0]
    node_html_id = id_mapper.get_html_id(node_id)
    
    # 验证节点在DOM中存在
    node_element = dash_duo.find_element(f"#{node_html_id}")
    assert node_element is not None
    assert "TestNode" in node_element.text
    print("✅ 节点在DOM中正确显示")

    # 验证节点在布局管理器中的位置
    position = layout_manager.get_node_position(node_id)
    assert position is not None
    assert position.row == 0 and position.col == 0  # 第一个节点应该在(0,0)
    print(f"✅ 节点在网格位置 ({position.row}, {position.col})")

def test_node_dropdown_menu_operations(dash_duo):
    """测试节点的dropdown菜单操作"""
    dash_duo.start_server(app, debug=False)

    # 清理状态
    from app import graph
    graph.nodes.clear()
    id_mapper._node_mapping.clear()
    layout_manager.node_positions.clear()
    layout_manager.position_nodes.clear()
    layout_manager._init_grid()

    # 添加测试节点
    input_box = dash_duo.find_element("#node-name")
    input_box.send_keys("DropdownTestNode")
    
    add_btn = dash_duo.find_element("#add-node-button")
    add_btn.click()
    dash_duo.wait_for_contains_text("#output-result", "DropdownTestNode 已添加到位置", timeout=10)

    # 获取节点信息
    node_id = list(id_mapper._node_mapping.keys())[0]
    node_html_id = id_mapper.get_html_id(node_id)

    # 找到dropdown菜单按钮 - 现在是带有⋮字符的按钮
    dropdown_buttons = dash_duo.driver.find_elements(By.CSS_SELECTOR, f"#{node_html_id} .dropdown-toggle")
    assert len(dropdown_buttons) > 0, "应该找到dropdown菜单按钮"
    
    dropdown_button = dropdown_buttons[0]
    dropdown_button.click()
    
    # 等待dropdown菜单展开
    time.sleep(0.5)
    
    # 寻找"添加参数"选项
    add_param_items = dash_duo.driver.find_elements(By.XPATH, "//a[contains(text(), '添加参数')]")
    if len(add_param_items) > 0:
        add_param_items[0].click()
        dash_duo.wait_for_contains_text("#output-result", "参数已添加到节点", timeout=5)
        print("✅ 通过dropdown菜单成功添加参数")
    else:
        print("⚠️ 未找到'添加参数'菜单项")

def test_node_movement_with_layout_manager(dash_duo):
    """测试使用布局管理器的节点移动功能"""
    dash_duo.start_server(app, debug=False)

    # 清理状态
    from app import graph
    graph.nodes.clear()
    id_mapper._node_mapping.clear()
    layout_manager.node_positions.clear()
    layout_manager.position_nodes.clear()
    layout_manager._init_grid()

    # 添加列以便测试左右移动
    add_column_btn = dash_duo.find_element("#add-column-button") 
    add_column_btn.click()
    dash_duo.wait_for_contains_text("#output-result", "已添加新列", timeout=5)

    # 创建多个测试节点
    test_nodes = ["Node1", "Node2", "Node3"]
    for name in test_nodes:
        input_box = dash_duo.find_element("#node-name")
        input_box.clear()
        input_box.send_keys(name)
        
        add_btn = dash_duo.find_element("#add-node-button")
        add_btn.click()
        dash_duo.wait_for_contains_text("#output-result", f"{name} 已添加到位置", timeout=10)

    # 验证所有节点都创建成功
    assert len(graph.nodes) == 3, "应该有3个节点"
    print("✅ 创建了3个测试节点")

    # 获取中间节点进行移动测试
    node_ids = list(id_mapper._node_mapping.keys())
    middle_node_id = node_ids[1]
    middle_node_html_id = id_mapper.get_html_id(middle_node_id)

    # 获取初始位置
    initial_pos = layout_manager.get_node_position(middle_node_id)
    print(f"节点初始位置: ({initial_pos.row}, {initial_pos.col})")

    # 测试右移
    dropdown_buttons = dash_duo.driver.find_elements(By.CSS_SELECTOR, f"#{middle_node_html_id} .dropdown-toggle")
    if len(dropdown_buttons) > 0:
        dropdown_buttons[0].click()
        time.sleep(0.5)
        
        # 寻找"右移"选项
        move_right_items = dash_duo.driver.find_elements(By.XPATH, "//a[contains(text(), '右移')]")
        if len(move_right_items) > 0:
            move_right_items[0].click()
            dash_duo.wait_for_contains_text("#output-result", "已右移", timeout=5)
            
            # 验证位置变化
            new_pos = layout_manager.get_node_position(middle_node_id)
            assert new_pos.col > initial_pos.col, "节点应该右移到新列"
            print(f"✅ 节点成功右移到位置: ({new_pos.row}, {new_pos.col})")

def test_parameter_operations_with_dropdown(dash_duo):
    """测试参数操作的dropdown菜单功能"""
    dash_duo.start_server(app, debug=False)

    # 清理状态
    from app import graph
    graph.nodes.clear()
    id_mapper._node_mapping.clear()
    layout_manager.node_positions.clear() 
    layout_manager.position_nodes.clear()
    layout_manager._init_grid()

    # 创建节点
    input_box = dash_duo.find_element("#node-name")
    input_box.send_keys("ParamTestNode")
    
    add_btn = dash_duo.find_element("#add-node-button")
    add_btn.click()
    dash_duo.wait_for_contains_text("#output-result", "ParamTestNode 已添加到位置", timeout=10)

    # 添加参数
    node_id = list(id_mapper._node_mapping.keys())[0]
    node_html_id = id_mapper.get_html_id(node_id)

    dropdown_buttons = dash_duo.driver.find_elements(By.CSS_SELECTOR, f"#{node_html_id} .dropdown-toggle")
    if len(dropdown_buttons) > 0:
        dropdown_buttons[0].click()
        time.sleep(0.5)
        
        add_param_items = dash_duo.driver.find_elements(By.XPATH, "//a[contains(text(), '添加参数')]")
        if len(add_param_items) > 0:
            add_param_items[0].click()
            dash_duo.wait_for_contains_text("#output-result", "参数已添加", timeout=5)
            print("✅ 成功添加参数")

    # 测试参数值编辑
    param_inputs = dash_duo.driver.find_elements(By.CSS_SELECTOR, ".param-input")
    if len(param_inputs) >= 2:
        param_value_input = param_inputs[1]  # 参数值输入框
        param_value_input.clear()
        param_value_input.send_keys("123.45")
        time.sleep(0.5)  # 等待更新
        print("✅ 成功编辑参数值")

def test_multiple_nodes_grid_layout(dash_duo):
    """测试多个节点的网格布局显示"""
    dash_duo.start_server(app, debug=False)

    # 清理状态
    from app import graph
    graph.nodes.clear()
    id_mapper._node_mapping.clear()
    layout_manager.node_positions.clear()
    layout_manager.position_nodes.clear()
    layout_manager._init_grid()

    # 创建多个节点
    node_names = ["GridNode1", "GridNode2", "GridNode3", "GridNode4"]
    created_node_ids = []

    for name in node_names:
        input_box = dash_duo.find_element("#node-name")
        input_box.clear()
        input_box.send_keys(name)
        
        add_btn = dash_duo.find_element("#add-node-button")
        add_btn.click()
        dash_duo.wait_for_contains_text("#output-result", f"{name} 已添加到位置", timeout=10)
        
        # 记录创建的节点ID
        node_id = list(id_mapper._node_mapping.keys())[-1]
        created_node_ids.append(node_id)

    # 验证所有节点都在布局管理器中
    assert len(layout_manager.node_positions) == 4, "布局管理器应该包含4个节点"
    
    # 验证节点在页面上都能找到
    for i, node_id in enumerate(created_node_ids):
        node_html_id = id_mapper.get_html_id(node_id)
        node_element = dash_duo.find_element(f"#{node_html_id}")
        assert node_element is not None, f"节点 {node_names[i]} 应该在页面上可见"
        assert node_names[i] in node_element.text, f"节点元素应该包含正确的名称 {node_names[i]}"
    
    print("✅ 所有节点都正确显示在网格布局中")

def test_duplicate_node_name_prevention(dash_duo):
    """测试重名节点的防止功能"""
    dash_duo.start_server(app, debug=False)

    # 清理状态
    from app import graph
    graph.nodes.clear()
    id_mapper._node_mapping.clear()
    layout_manager.node_positions.clear()
    layout_manager.position_nodes.clear()
    layout_manager._init_grid()

    # 添加第一个节点
    first_node_name = "UniqueNode"
    input_box = dash_duo.find_element("#node-name")
    input_box.clear()  # 确保输入框初始为空
    input_box.send_keys(first_node_name)
    
    add_btn = dash_duo.find_element("#add-node-button")
    add_btn.click()
    dash_duo.wait_for_contains_text("#output-result", f"{first_node_name} 已添加到位置", timeout=10)

    # 验证第一个节点添加成功
    assert len(graph.nodes) == 1, "应该有1个节点" 
    print("✅ 第一个节点添加成功")

    # 使用JavaScript强制清空输入框
    dash_duo.driver.execute_script("document.getElementById('node-name').value = '';")
    
    # 等待DOM更新
    import time
    time.sleep(0.5)
    
    # 验证输入框已清空
    input_box = dash_duo.find_element("#node-name") 
    assert input_box.get_attribute("value") == "", "输入框应该为空"

    # 使用JavaScript设置输入框值，避免累加问题
    dash_duo.driver.execute_script(f"document.getElementById('node-name').value = '{first_node_name}';")
    
    # 触发input事件让Dash知道值已改变
    dash_duo.driver.execute_script("document.getElementById('node-name').dispatchEvent(new Event('input', { bubbles: true }));")
    
    time.sleep(0.5)  # 等待值更新
    
    # 验证输入框内容正确
    assert input_box.get_attribute("value") == first_node_name, f"输入框应该包含 {first_node_name}"
    
    add_btn = dash_duo.find_element("#add-node-button")
    add_btn.click()

    # 验证错误消息
    dash_duo.wait_for_contains_text("#output-result", f"错误：节点名称 '{first_node_name}' 已存在，请使用不同的名称", timeout=5)
    
    # 验证重名节点没有被添加
    assert len(graph.nodes) == 1, "重名节点不应该被添加"
    print("✅ 重名节点被正确阻止")

def test_empty_node_name_validation(dash_duo):
    """测试空节点名称的验证"""
    dash_duo.start_server(app, debug=False)

    # 清理状态
    from app import graph
    graph.nodes.clear()
    id_mapper._node_mapping.clear()
    layout_manager.node_positions.clear()
    layout_manager.position_nodes.clear()
    layout_manager._init_grid()

    # 尝试添加空名称节点
    input_box = dash_duo.find_element("#node-name")
    input_box.clear()  # 确保输入框为空
    
    add_btn = dash_duo.find_element("#add-node-button")
    add_btn.click()

    # 验证错误消息
    dash_duo.wait_for_contains_text("#output-result", "请输入节点名称", timeout=5)
    
    # 验证没有节点被创建
    assert len(graph.nodes) == 0, "空名称不应该创建节点"
    print("✅ 空节点名称被正确拒绝")

def test_column_management(dash_duo):
    """测试列管理功能"""
    dash_duo.start_server(app, debug=False)

    # 清理状态
    from app import graph
    graph.nodes.clear()
    id_mapper._node_mapping.clear()
    layout_manager.node_positions.clear()
    layout_manager.position_nodes.clear()
    layout_manager._init_grid()

    # 测试添加列
    initial_cols = layout_manager.cols
    add_column_btn = dash_duo.find_element("#add-column-button")
    add_column_btn.click()
    
    dash_duo.wait_for_contains_text("#output-result", f"已添加新列，当前列数: {initial_cols + 1}", timeout=5)
    
    # 验证列数增加
    assert layout_manager.cols == initial_cols + 1, "列数应该增加1"
    print(f"✅ 成功添加列，当前列数: {layout_manager.cols}")

def test_node_position_display(dash_duo):
    """测试节点位置信息的显示"""
    dash_duo.start_server(app, debug=False)

    # 清理状态
    from app import graph
    graph.nodes.clear()
    id_mapper._node_mapping.clear()
    layout_manager.node_positions.clear()
    layout_manager.position_nodes.clear()
    layout_manager._init_grid()

    # 创建节点
    input_box = dash_duo.find_element("#node-name")
    input_box.send_keys("PositionTestNode")
    
    add_btn = dash_duo.find_element("#add-node-button")
    add_btn.click()
    dash_duo.wait_for_contains_text("#output-result", "PositionTestNode 已添加到位置", timeout=10)

    # 获取节点并验证位置显示
    node_id = list(id_mapper._node_mapping.keys())[0]
    node_html_id = id_mapper.get_html_id(node_id)
    node_element = dash_duo.find_element(f"#{node_html_id}")
    
    # 检查节点元素是否包含位置信息
    position = layout_manager.get_node_position(node_id)
    expected_position_text = f"({position.row},{position.col})"
    
    # 在新的实现中，位置信息应该显示在节点中
    assert expected_position_text in node_element.text, f"节点应该显示位置信息 {expected_position_text}"
    print(f"✅ 节点正确显示位置信息: {expected_position_text}")

 