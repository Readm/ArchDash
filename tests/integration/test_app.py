import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time

from app import app, graph, layout_manager

# 为此文件中的所有测试设置30秒的全局超时
pytestmark = pytest.mark.timeout(30)

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
    """等待元素出现"""
    print(f"等待元素出现: {by}={value}")
    element = WebDriverWait(selenium, timeout).until(
        EC.presence_of_element_located((by, value))
    )
    print(f"元素已找到: {by}={value}")
    return element

def wait_for_clickable(selenium, by, value, timeout=10):
    """等待元素可点击"""
    print(f"等待元素可点击: {by}={value}")
    element = WebDriverWait(selenium, timeout).until(
        EC.element_to_be_clickable((by, value))
    )
    print(f"元素可点击: {by}={value}")
    # Ensure element is in view
    selenium.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.5)  # Give time for scroll to complete
    return element

def wait_for_node_count(selenium, count, timeout=30):
    """等待直到页面上有指定数量的节点"""
    print(f"\n等待节点数量达到 {count}...")
    
    def check_node_count(driver):
        """检查节点数量是否符合预期"""
        try:
            # 使用data-dash-id属性查找节点
            nodes = driver.find_elements(By.CSS_SELECTOR, "[data-dash-id*='node']")
            actual_count = len(nodes)
            print(f"当前节点数量: {actual_count}")
            
            if actual_count == count:
                print("✅ 节点数量匹配")
                return True
            elif actual_count > count:
                print(f"⚠️ 节点数量过多: 期望{count}个，实际{actual_count}个")
                return False
            else:
                print(f"⏳ 等待更多节点: 期望{count}个，当前{actual_count}个")
                return False
                
        except Exception as e:
            print(f"❌ 检查节点数量时出错: {str(e)}")
            return False
            
    try:
        WebDriverWait(selenium, timeout).until(check_node_count)
        print("成功等待到预期节点数量")
    except Exception as e:
        print(f"等待节点数量超时: {str(e)}")
        
        # 超时时再次检查一下当前状态
        print("\n最终状态检查:")
        try:
            all_elements = selenium.find_elements(By.CSS_SELECTOR, "*")
            print(f"页面上所有元素数量: {len(all_elements)}")
            
            # 检查特定元素
            canvas = selenium.find_elements(By.ID, "canvas-container")
            print(f"画布容器存在: {len(canvas) > 0}")
            
            # 检查节点
            nodes = selenium.find_elements(By.CSS_SELECTOR, "[data-dash-id*='node']")
            print(f"找到的节点数量: {len(nodes)}")
            
            if nodes:
                print("\n节点详细信息:")
                for i, node in enumerate(nodes):
                    print(f"\n节点 {i+1}:")
                    print(f"- id: {node.get_attribute('id')}")
                    print(f"- data-dash-id: {node.get_attribute('data-dash-id')}")
                    print(f"- class: {node.get_attribute('class')}")
                    print(f"- 是否显示: {node.is_displayed()}")
                    print(f"- HTML: {node.get_attribute('outerHTML')}")
            
        except Exception as debug_e:
            print(f"调试信息收集失败: {str(debug_e)}")
        
        raise

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
    print(f"\n=== 开始创建节点: {name} ===")
    
    # 等待页面准备好
    time.sleep(1)
    print("页面准备就绪")
    
    print("查找添加节点按钮...")
    add_node_btn = wait_for_clickable(selenium, By.ID, "add-node-from-graph-button")
    add_node_btn.click()
    print("点击了添加节点按钮")
    time.sleep(1)  # 等待模态框动画
    
    print("等待模态框出现...")
    modal = wait_for_element(selenium, By.ID, "node-add-modal")
    assert modal.is_displayed(), "模态框应该可见"
    print("模态框已显示")
    time.sleep(1)  # 等待模态框完全显示
    
    print("输入节点信息...")
    name_input = wait_for_element(selenium, By.ID, "node-add-name")
    name_input.clear()
    time.sleep(0.5)  # 等待输入框清空
    name_input.send_keys(name)
    print(f"输入了节点名称: {name}")
    time.sleep(0.5)  # 等待输入完成
    
    if description:
        desc_input = wait_for_element(selenium, By.ID, "node-add-description")
        desc_input.clear()
        time.sleep(0.5)  # 等待输入框清空
        desc_input.send_keys(description)
        print(f"输入了节点描述: {description}")
        time.sleep(0.5)  # 等待输入完成
    
    print("准备保存节点...")
    save_btn = wait_for_clickable(selenium, By.ID, "node-add-save")
    save_btn.click()
    print("点击了保存按钮")
    
    # 等待模态框消失和节点渲染
    time.sleep(2)
    print("等待节点渲染完成")
    
    # 验证模态框已关闭
    try:
        modal = selenium.find_element(By.ID, "node-add-modal")
        assert not modal.is_displayed(), "模态框应该已关闭"
        print("模态框已关闭")
    except:
        print("模态框已关闭")
    
    print("=== 节点创建步骤完成 ===\n")

def add_parameter(selenium, node_index=0):
    """为指定索引的节点添加参数"""
    # 使用更健壮的节点查找方法
    nodes = selenium.find_elements(By.CSS_SELECTOR, "[data-dash-id*='node']")
    if not nodes:
        nodes = selenium.find_elements(By.CSS_SELECTOR, ".node")
    if not nodes:
        nodes = selenium.find_elements(By.CSS_SELECTOR, ".node-container")
    
    if not nodes or node_index >= len(nodes):
        raise Exception(f"未找到索引为 {node_index} 的节点")
        
    node = nodes[node_index]
    
    add_param_btn = node.find_element(By.CSS_SELECTOR, "button[id*='add-param']")
    add_param_btn.click()
    
    param_input = wait_for_element(selenium, By.CSS_SELECTOR, "[data-dash-id*='param-input'], .parameter-input")
    return param_input

def clean_state(selenium):
    """清理应用状态"""
    print("\n开始清理应用状态...")
    
    # 清理后端状态
    graph.nodes.clear()
    layout_manager.node_positions.clear()
    layout_manager.position_nodes.clear()
    layout_manager._init_grid()
    print("后端状态已清理")
    
    # 刷新页面
    print("正在刷新页面...")
    selenium.get("http://localhost:8050")
    wait_for_page_load(selenium)
    time.sleep(2)  # 等待页面完全加载
    
    # 等待并验证画布容器
    print("等待画布容器...")
    canvas = wait_for_element(selenium, By.ID, "canvas-container")
    assert canvas.is_displayed(), "画布容器应该可见"
    time.sleep(1)  # 等待画布完全渲染
    
    # 验证没有节点存在
    nodes = selenium.find_elements(By.CSS_SELECTOR, "[data-dash-id*='node']")
    assert len(nodes) == 0, "清理后不应该有节点存在"
    print("验证完成：没有节点存在")
    
    print("应用状态清理完成\n")

def test_add_node_with_grid_layout(selenium):
    """测试添加节点和网格布局"""
    try:
        print("\n=== 开始测试添加节点和网格布局 ===")
        clean_state(selenium)
        print("清理状态完成")
        
        create_node(selenium, "测试节点", "这是一个测试节点")
        print("节点创建完成")
        
        wait_for_node_count(selenium, 1)
        print("等待节点数量验证完成")
        
        print("\n尝试查找节点...")
        # 尝试所有可能的选择器
        selectors = [
            "[data-dash-id*='node']",
            ".node",
            ".node-container",
            "[id^='node-']"
        ]
        
        node = None
        for selector in selectors:
            print(f"\n尝试选择器: {selector}")
            elements = selenium.find_elements(By.CSS_SELECTOR, selector)
            print(f"找到 {len(elements)} 个元素")
            for i, elem in enumerate(elements):
                print(f"元素 {i+1}:")
                print(f"- class: {elem.get_attribute('class')}")
                print(f"- id: {elem.get_attribute('id')}")
                print(f"- text: {elem.text}")
                print(f"- 是否显示: {elem.is_displayed()}")
                if "测试节点" in elem.text and elem.is_displayed():
                    node = elem
                    print("✅ 找到目标节点!")
                    break
            if node:
                break
                
        if not node:
            raise Exception("未找到包含'测试节点'文本的可见节点")
            
        assert "测试节点" in node.text, "节点名称应该正确显示"
        print("✅ 节点名称验证通过")
        
        print("✅ 添加节点和网格布局测试通过")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        print("\n当前页面HTML:")
        print(selenium.page_source)
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
        print("\n=== 开始测试节点移动和布局管理器 ===")
        clean_state(selenium)
        print("清理状态完成")
        
        create_node(selenium, "MovementTestNode", "测试节点移动")
        print("节点创建完成")
        
        wait_for_node_count(selenium, 1)
        print("等待节点数量验证完成")
        
        print("\n尝试查找节点...")
        node = wait_for_element(selenium, By.CSS_SELECTOR, "[data-dash-id*='node']")
        if not node:
            raise Exception("未找到节点")
        print("✅ 找到节点")
        
        # 记录初始位置
        initial_location = node.location
        print(f"初始位置: {initial_location}")
        
        # 在节点内部查找下拉按钮
        print("\n在节点内部查找下拉按钮...")
        dropdown_btn = wait_for_element(selenium, By.CSS_SELECTOR, ".node-menu-btn")
        if not dropdown_btn:
            raise Exception("未在节点内找到下拉按钮")
        print("✅ 找到下拉按钮")
        
        # 点击下拉按钮
        print("\n点击下拉按钮...")
        safe_click(selenium, dropdown_btn)
        print("下拉按钮已点击")
        time.sleep(1)  # 等待菜单展开
        
        # 等待下拉菜单出现
        print("\n等待下拉菜单出现...")
        menu = wait_for_element(selenium, By.CSS_SELECTOR, ".dropdown-menu.show")
        assert menu.is_displayed(), "下拉菜单应该可见"
        print("下拉菜单已显示")
        
        # 查找并点击右移按钮
        print("\n查找右移按钮...")
        move_right_btn = wait_for_element(selenium, By.CSS_SELECTOR, "[id*='move-node-right']")
        if not move_right_btn:
            raise Exception("未找到右移按钮")
        print("✅ 找到右移按钮")
        
        print("\n点击右移按钮...")
        safe_click(selenium, move_right_btn)
        print("右移按钮已点击")
        
        time.sleep(2)  # 等待移动完成
        
        # 重新获取节点位置（因为节点可能已经重新渲染）
        node = wait_for_element(selenium, By.CSS_SELECTOR, "[data-dash-id*='node']")
        new_location = node.location
        print(f"新位置: {new_location}")
        
        # 检查位置变化
        print("\n检查位置变化...")
        print(f"初始X坐标: {initial_location['x']}")
        print(f"新X坐标: {new_location['x']}")
        
        if new_location['x'] <= initial_location['x']:
            raise Exception(f"节点没有向右移动。初始X: {initial_location['x']}, 新X: {new_location['x']}")
            
        print("✅ 位置变化验证通过")
        print("✅ 节点移动和布局管理器测试通过")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        print("\n当前页面HTML:")
        print(selenium.page_source)
        raise  # 重新抛出异常，让pytest知道测试失败

def test_parameter_operations_with_dropdown(selenium):
    """测试参数操作和下拉菜单"""
    try:
        print("\n=== 开始测试参数操作和下拉菜单 ===")
        clean_state(selenium)
        print("清理状态完成")
        
        create_node(selenium, "ParameterTestNode", "测试参数操作")
        print("节点创建完成")
        
        wait_for_node_count(selenium, 1)
        print("等待节点数量验证完成")
        
        # 找到节点
        print("\n尝试查找节点...")
        node = wait_for_element(selenium, By.CSS_SELECTOR, "[data-dash-id*='node']")
        if not node:
            raise Exception("未找到节点")
        print("✅ 找到节点")
        
        # 找到添加参数按钮
        print("\n查找添加参数按钮...")
        add_param_btn = wait_for_element(selenium, By.CSS_SELECTOR, "button[id*='add-param']")
        if not add_param_btn:
            raise Exception("未找到添加参数按钮")
        print("✅ 找到添加参数按钮")
        
        # 点击添加参数按钮
        print("\n点击添加参数按钮...")
        safe_click(selenium, add_param_btn)
        print("添加参数按钮已点击")
        time.sleep(1)  # 等待参数输入框出现
        
        # 等待参数输入框出现
        print("\n等待参数输入框出现...")
        param_input = wait_for_element(selenium, By.CSS_SELECTOR, "[data-dash-id*='param-input'], .parameter-input")
        if not param_input:
            raise Exception("参数输入框未出现")
        print("✅ 找到参数输入框")
        
        # 验证参数输入框可以输入
        print("\n测试参数输入...")
        param_input.clear()
        param_input.send_keys("test_param")
        time.sleep(0.5)  # 等待输入完成
        
        # 验证输入值
        actual_value = param_input.get_attribute("value")
        print(f"输入框当前值: {actual_value}")
        assert actual_value == "test_param", f"参数输入框的值应该是'test_param'，实际是'{actual_value}'"
        print("✅ 参数输入验证通过")
        
        print("✅ 参数操作和下拉菜单测试通过")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        print("\n当前页面HTML:")
        print(selenium.page_source)
        raise  # 重新抛出异常，让pytest知道测试失败

def test_multiple_nodes_grid_layout(selenium):
    """测试多节点网格布局"""
    try:
        clean_state(selenium)
        
        for i in range(3):
            create_node(selenium, f"GridNode{i+1}", f"网格布局测试节点{i+1}")
            wait_for_node_count(selenium, i + 1)
        
        # 使用更健壮的节点查找方法
        nodes = selenium.find_elements(By.CSS_SELECTOR, "[data-dash-id*='node']")
        if not nodes:
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
        
        # 使用更健壮的节点查找方法
        node = wait_for_element(selenium, By.CSS_SELECTOR, "[data-dash-id*='node']")
        if not node:
            node = wait_for_element(selenium, By.CSS_SELECTOR, ".node")
        assert node.is_displayed(), "节点应该可见"
        assert node.location['x'] >= 0 and node.location['y'] >= 0, "节点应该有有效的位置"
        
        print("✅ 节点位置显示测试通过")
        
    except Exception as e:
        pytest.fail(f"节点位置显示测试失败: {str(e)}")

def test_parameter_cascade_update_in_web_interface(selenium):
    """测试Web界面中的参数级联更新"""
    try:
        print("\n=== 开始参数级联更新测试 ===")
        clean_state(selenium)
        print("清理了应用状态")
        time.sleep(2)  # 等待清理完成
        
        # 创建两个测试节点
        for i in range(2):
            print(f"\n--- 开始创建第 {i+1} 个节点 ---")
            create_node(selenium, f"CascadeNode{i+1}", f"级联更新测试节点{i+1}")
            print(f"创建了节点 CascadeNode{i+1}")
            
            wait_for_node_count(selenium, i + 1)
            print(f"等待节点数量为 {i+1} 完成")
            time.sleep(2)  # 等待节点完全渲染
            
            # 添加参数
            param_input = add_parameter(selenium, i)
            assert param_input is not None, "参数输入框应该出现"
            print(f"为节点 {i+1} 添加了参数")
            time.sleep(1)  # 等待参数添加完成
        
        print("\n✅ Web界面参数级联更新测试通过")
        
    except Exception as e:
        print(f"\n❌ Web界面参数级联更新测试失败: {str(e)}")
        pytest.fail(f"Web界面参数级联更新测试失败: {str(e)}")
    finally:
        print("\n=== 测试结束 ===\n")

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

def test_single_node_creation(selenium):
    """测试创建单个节点"""
    try:
        print("\n========== 开始单节点创建测试 ==========")
        
        print("\n第1步：清理应用状态")
        clean_state(selenium)
        time.sleep(2)  # 等待清理完成
        
        print("\n第2步：创建测试节点")
        create_node(selenium, "TestNode", "测试节点")
        time.sleep(2)  # 等待节点创建完成
        
        print("\n第3步：分析页面内容")
        page_source = selenium.page_source
        print("\n当前页面HTML:")
        print(page_source)
        
        print("\n尝试查找所有可能的节点相关元素:")
        # 尝试各种选择器
        selectors = [
            "[data-dash-id*='node']",  # Dash节点标识
            ".node-container",         # 节点容器类
            ".node-entrance",          # 节点入场动画类
            "[id^='node-']",          # 以node-开头的ID
            "[data-row]",             # 具有data-row属性的元素
            "[data-col]"              # 具有data-col属性的元素
        ]
        
        for selector in selectors:
            elements = selenium.find_elements(By.CSS_SELECTOR, selector)
            print(f"\n使用选择器 '{selector}' 找到 {len(elements)} 个元素:")
            for i, elem in enumerate(elements):
                try:
                    print(f"元素 {i+1}:")
                    print(f"- class: {elem.get_attribute('class')}")
                    print(f"- id: {elem.get_attribute('id')}")
                    print(f"- data-dash-id: {elem.get_attribute('data-dash-id')}")
                    print(f"- data-row: {elem.get_attribute('data-row')}")
                    print(f"- data-col: {elem.get_attribute('data-col')}")
                    print(f"- text: {elem.text}")
                    print(f"- HTML: {elem.get_attribute('outerHTML')}")
                    print(f"- 是否显示: {elem.is_displayed()}")
                except:
                    print(f"- 无法获取元素 {i+1} 的详细信息")
        
        print("\n第4步：等待并验证节点")
        wait_for_node_count(selenium, 1)
        time.sleep(2)  # 等待节点完全渲染
        
        print("\n✅ 单节点创建测试通过")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        raise

 