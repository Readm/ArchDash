import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time

from app import app, graph, layout_manager

# 为此文件中的所有测试设置3秒的全局超时
pytestmark = pytest.mark.timeout(3)

def safe_click(driver, element, max_attempts=3):
    """安全点击元素，处理ElementClickInterceptedException"""
    for attempt in range(max_attempts):
        try:
            # 先尝试滚动到元素位置
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            
            # 尝试点击
            element.click()
            return True
        except ElementClickInterceptedException:
            if attempt < max_attempts - 1:
                print(f"点击被拦截，重试第 {attempt + 1} 次...")
                time.sleep(1)
                # 尝试使用JavaScript点击
                try:
                    driver.execute_script("arguments[0].click();", element)
                    return True
                except:
                    continue
            else:
                # 最后一次尝试使用ActionChains
                try:
                    ActionChains(driver).move_to_element(element).click().perform()
                    return True
                except:
                    raise
    return False

def find_dropdown_item_safe(driver, text, max_attempts=3):
    """安全查找dropdown菜单项"""
    for attempt in range(max_attempts):
        try:
            # 等待dropdown菜单展开
            time.sleep(0.5)
            
            # 查找菜单项
            dropdown_items = driver.find_elements(By.CSS_SELECTOR, '.dropdown-item')
            for item in dropdown_items:
                if text in item.text and item.is_displayed():
                    return item
            
            # 如果没找到，尝试更通用的选择器
            items = driver.find_elements(By.XPATH, f"//a[contains(text(), '{text}')]")
            for item in items:
                if item.is_displayed():
                    return item
                    
        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"查找菜单项失败，重试第 {attempt + 1} 次: {e}")
                time.sleep(0.5)
            else:
                raise
    return None

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
    
    add_param_btn = node.find_element(By.CSS_SELECTOR, "button[id*='add-param']")
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

def test_add_node_with_grid_layout(selenium):
    """测试添加节点和网格布局"""
    try:
        clean_state(selenium)
        create_node(selenium, "测试节点", "这是一个测试节点")
        wait_for_node_count(selenium, 1)
        
        node = selenium.find_element(By.CSS_SELECTOR, ".node")
        assert "测试节点" in node.text, "节点名称应该正确显示"
        
        print("✅ 添加节点和网格布局测试通过")
        
    except Exception as e:
        pytest.fail(f"添加节点和网格布局测试失败: {str(e)}")

def test_node_dropdown_menu_operations(selenium):
    """测试节点的dropdown菜单操作"""
    try:
        clean_state(selenium)
        
        # 等待页面加载完成
        wait_for_page_load(selenium)
        
        # 等待画布容器可见
        canvas = wait_for_element(selenium, By.ID, "canvas-container")
        assert canvas is not None and canvas.is_displayed(), "画布容器应该存在且可见"
        
        # 等待添加节点按钮可点击
        add_node_btn = wait_for_clickable(selenium, By.ID, "add-node-from-graph-button")
        add_node_btn.click()
        
        # 等待模态框出现并可见
        modal = wait_for_element(selenium, By.ID, "node-add-modal")
        assert modal is not None and modal.is_displayed(), "节点添加模态框应该出现且可见"
        
        # 输入节点信息
        name_input = wait_for_element(selenium, By.ID, "node-add-name")
        name_input.clear()
        name_input.send_keys("DropdownTestNode")
        
        desc_input = wait_for_element(selenium, By.ID, "node-add-description")
        desc_input.clear()
        desc_input.send_keys("测试下拉菜单")
        
        # 等待保存按钮可点击
        save_btn = wait_for_clickable(selenium, By.ID, "node-add-save")
        save_btn.click()
        
        # 等待节点出现在页面上
        wait_for_node_count(selenium, 1)
        
        # 验证节点创建
        assert len(graph.nodes) == 1, "应该创建了一个节点"
        
        # 获取节点ID
        node = list(graph.nodes.values())[0]
        
        # 等待节点元素可见
        node_element = wait_for_element(selenium, By.CSS_SELECTOR, f".node[data-dash-id*='{node.id}']")
        assert node_element.is_displayed(), "节点元素应该可见"
        
        # 等待下拉菜单按钮可点击
        dropdown_btn = wait_for_clickable(selenium, By.CSS_SELECTOR, f"button[data-dash-id*='{node.id}'][id*='dropdown']")
        dropdown_btn.click()
        
        # 等待下拉菜单出现并可见
        menu = wait_for_element(selenium, By.CSS_SELECTOR, ".dropdown-menu.show")
        assert menu.is_displayed(), "下拉菜单应该可见"
        
        # 等待删除按钮可点击
        delete_btn = wait_for_clickable(selenium, By.CSS_SELECTOR, f"button[data-dash-id*='{node.id}'][id*='delete']")
        delete_btn.click()
        
        # 等待节点消失
        WebDriverWait(selenium, 10).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, f".node[data-dash-id*='{node.id}']"))
        )
        
        # 验证节点被删除
        assert len(graph.nodes) == 0, "节点应该被删除"
        assert len(layout_manager.node_positions) == 0, "节点布局信息应该被删除"
        
    except Exception as e:
        pytest.fail(f"下拉菜单操作测试失败: {str(e)}")

def test_node_movement_with_layout_manager(selenium):
    """测试节点移动和布局管理器"""
    try:
        clean_state(selenium)
        create_node(selenium, "MovementTestNode", "测试节点移动")
        wait_for_node_count(selenium, 1)
        
        node = selenium.find_element(By.CSS_SELECTOR, ".node")
        initial_location = node.location
        
        # 移动节点
        actions = ActionChains(selenium)
        actions.drag_and_drop_by_offset(node, 100, 0).perform()
        
        time.sleep(1)  # 等待移动完成
        new_location = node.location
        assert new_location['x'] > initial_location['x'], "节点应该向右移动"
        
        print("✅ 节点移动和布局管理器测试通过")
        
    except Exception as e:
        pytest.fail(f"节点移动和布局管理器测试失败: {str(e)}")

def test_parameter_operations_with_dropdown(selenium):
    """测试参数操作和下拉菜单"""
    try:
        clean_state(selenium)
        create_node(selenium, "ParameterTestNode", "测试参数操作")
        wait_for_node_count(selenium, 1)
        
        param_input = add_parameter(selenium)
        assert param_input is not None, "参数输入框应该出现"
        
        print("✅ 参数操作和下拉菜单测试通过")
        
    except Exception as e:
        pytest.fail(f"参数操作和下拉菜单测试失败: {str(e)}")

def test_multiple_nodes_grid_layout(selenium):
    """测试多节点网格布局"""
    try:
        clean_state(selenium)
        
        for i in range(3):
            create_node(selenium, f"GridNode{i+1}", f"网格布局测试节点{i+1}")
            wait_for_node_count(selenium, i + 1)
        
        nodes = selenium.find_elements(By.CSS_SELECTOR, ".node")
        assert len(nodes) == 3, "应该有3个节点"
        
        print("✅ 多节点网格布局测试通过")
        
    except Exception as e:
        pytest.fail(f"多节点网格布局测试失败: {str(e)}")

def test_node_position_display(selenium):
    """测试节点位置显示"""
    try:
        clean_state(selenium)
        create_node(selenium, "PositionNode", "测试节点位置")
        wait_for_node_count(selenium, 1)
        
        node = selenium.find_element(By.CSS_SELECTOR, ".node")
        assert node.is_displayed(), "节点应该可见"
        assert node.location['x'] >= 0 and node.location['y'] >= 0, "节点应该有有效的位置"
        
        print("✅ 节点位置显示测试通过")
        
    except Exception as e:
        pytest.fail(f"节点位置显示测试失败: {str(e)}")

def test_parameter_cascade_update_in_web_interface(selenium):
    """测试Web界面中的参数级联更新"""
    try:
        clean_state(selenium)
        
        # 创建两个测试节点
        for i in range(2):
            create_node(selenium, f"CascadeNode{i+1}", f"级联更新测试节点{i+1}")
            wait_for_node_count(selenium, i + 1)
            
            # 添加参数
            param_input = add_parameter(selenium, i)
            assert param_input is not None, "参数输入框应该出现"
        
        print("✅ Web界面参数级联更新测试通过")
        
    except Exception as e:
        pytest.fail(f"Web界面参数级联更新测试失败: {str(e)}")

def test_parameter_highlight_functionality(selenium):
    """测试参数高亮功能"""
    try:
        clean_state(selenium)
        create_node(selenium, "HighlightNode", "测试参数高亮")
        wait_for_node_count(selenium, 1)
        
        param_input = add_parameter(selenium)
        assert param_input is not None, "参数输入框应该出现"
        
        # 点击参数以触发高亮
        param_input.click()
        
        # 验证高亮效果
        highlighted = selenium.find_elements(By.CSS_SELECTOR, ".parameter-highlight")
        assert len(highlighted) > 0, "应该有参数被高亮"
        
        print("✅ 参数高亮功能测试通过")
        
    except Exception as e:
        pytest.fail(f"参数高亮功能测试失败: {str(e)}")

def test_parameter_edit_modal_functionality(selenium):
    """测试参数编辑模态框功能"""
    try:
        clean_state(selenium)
        create_node(selenium, "EditModalNode", "测试参数编辑模态框")
        wait_for_node_count(selenium, 1)
        
        param_input = add_parameter(selenium)
        assert param_input is not None, "参数输入框应该出现"
        
        # 打开参数编辑模态框
        edit_btn = wait_for_clickable(selenium, By.CSS_SELECTOR, "button[id*='edit-param']")
        edit_btn.click()
        
        # 验证模态框
        edit_modal = wait_for_element(selenium, By.ID, "parameter-edit-modal")
        assert edit_modal is not None, "参数编辑模态框应该出现"
        
        print("✅ 参数编辑模态框功能测试通过")
        
    except Exception as e:
        pytest.fail(f"参数编辑模态框功能测试失败: {str(e)}")

def test_canvas_auto_refresh_on_parameter_change(selenium):
    """测试参数变化时画布自动刷新"""
    try:
        clean_state(selenium)
        create_node(selenium, "RefreshNode", "测试画布刷新")
        wait_for_node_count(selenium, 1)
        
        param_input = add_parameter(selenium)
        assert param_input is not None, "参数输入框应该出现"
        
        # 修改参数值
        param_input.clear()
        param_input.send_keys("新值")
        param_input.send_keys(Keys.RETURN)
        
        # 验证画布更新
        time.sleep(1)  # 等待画布刷新
        canvas = selenium.find_element(By.ID, "canvas-container")
        assert canvas.is_displayed(), "画布应该保持可见"
        
        print("✅ 参数变化时画布自动刷新测试通过")
        
    except Exception as e:
        pytest.fail(f"参数变化时画布自动刷新测试失败: {str(e)}")

def test_recently_updated_params_tracking(selenium):
    """测试最近更新的参数追踪"""
    try:
        clean_state(selenium)
        create_node(selenium, "TrackingNode", "测试参数追踪")
        wait_for_node_count(selenium, 1)
        
        param_input = add_parameter(selenium)
        assert param_input is not None, "参数输入框应该出现"
        
        # 修改参数值
        param_input.clear()
        param_input.send_keys("新值")
        param_input.send_keys(Keys.RETURN)
        
        # 验证最近更新列表
        recent_list = wait_for_element(selenium, By.ID, "recent-params-list")
        assert recent_list is not None, "最近更新列表应该存在"
        assert "新值" in recent_list.text, "最近更新列表应该包含新值"
        
        print("✅ 最近更新的参数追踪测试通过")
        
    except Exception as e:
        pytest.fail(f"最近更新的参数追踪测试失败: {str(e)}")

def test_duplicate_node_name_prevention(selenium):
    """测试重复节点名称预防"""
    try:
        clean_state(selenium)
        create_node(selenium, "DuplicateNode", "测试重复名称")
        wait_for_node_count(selenium, 1)
        
        # 尝试创建同名节点
        add_node_btn = wait_for_clickable(selenium, By.ID, "add-node-from-graph-button")
        add_node_btn.click()
        
        modal = wait_for_element(selenium, By.ID, "node-add-modal")
        name_input = wait_for_element(selenium, By.ID, "node-add-name")
        name_input.clear()
        name_input.send_keys("DuplicateNode")
        
        desc_input = wait_for_element(selenium, By.ID, "node-add-description")
        desc_input.clear()
        desc_input.send_keys("测试重复名称2")
        
        save_btn = wait_for_clickable(selenium, By.ID, "node-add-save")
        save_btn.click()
        
        # 验证错误提示
        error_msg = wait_for_element(selenium, By.CSS_SELECTOR, ".alert-danger")
        assert "已存在" in error_msg.text, "应该显示重复名称错误"
        
        print("✅ 重复节点名称预防测试通过")
        
    except Exception as e:
        pytest.fail(f"重复节点名称预防测试失败: {str(e)}")

def test_empty_node_name_validation(selenium):
    """测试空节点名称验证"""
    try:
        clean_state(selenium)
        
        # 尝试创建空名称节点
        add_node_btn = wait_for_clickable(selenium, By.ID, "add-node-from-graph-button")
        add_node_btn.click()
        
        modal = wait_for_element(selenium, By.ID, "node-add-modal")
        save_btn = wait_for_clickable(selenium, By.ID, "node-add-save")
        save_btn.click()
        
        # 验证错误提示
        error_msg = wait_for_element(selenium, By.CSS_SELECTOR, ".alert-danger")
        assert "不能为空" in error_msg.text, "应该显示名称为空错误"
        
        print("✅ 空节点名称验证测试通过")
        
    except Exception as e:
        pytest.fail(f"空节点名称验证测试失败: {str(e)}")

def test_column_management(selenium):
    """测试列管理"""
    try:
        clean_state(selenium)
        
        # 获取初始列数
        initial_cols = len(selenium.find_elements(By.CSS_SELECTOR, ".grid-column"))
        
        # 添加列
        add_col_btn = wait_for_clickable(selenium, By.ID, "add-column-btn")
        add_col_btn.click()
        
        # 验证列数增加
        time.sleep(1)  # 等待列添加完成
        new_cols = len(selenium.find_elements(By.CSS_SELECTOR, ".grid-column"))
        assert new_cols == initial_cols + 1, "应该增加了一列"
        
        print("✅ 列管理测试通过")
        
    except Exception as e:
        pytest.fail(f"列管理测试失败: {str(e)}")

def test_remove_column_functionality(selenium):
    """测试删除列功能"""
    try:
        clean_state(selenium)
        
        # 获取初始列数
        initial_cols = len(selenium.find_elements(By.CSS_SELECTOR, ".grid-column"))
        
        # 添加列
        add_col_btn = wait_for_clickable(selenium, By.ID, "add-column-btn")
        add_col_btn.click()
        
        # 等待列添加完成
        time.sleep(1)
        
        # 删除列
        remove_col_btn = wait_for_clickable(selenium, By.ID, "remove-column-btn")
        remove_col_btn.click()
        
        # 验证列数恢复
        time.sleep(1)  # 等待列删除完成
        final_cols = len(selenium.find_elements(By.CSS_SELECTOR, ".grid-column"))
        assert final_cols == initial_cols, "列数应该恢复到初始值"
        
        print("✅ 删除列功能测试通过")
        
    except Exception as e:
        pytest.fail(f"删除列功能测试失败: {str(e)}")

 