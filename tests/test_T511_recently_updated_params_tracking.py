from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count, add_parameter
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T511 - 测试
从原始测试文件分离出的独立测试
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
import time
from app import app, graph, layout_manager

def test_recently_updated_params_tracking(selenium):
    """测试最近更新的参数追踪"""
    try:
        clean_state(selenium)
        create_node(selenium, "TrackingNode", "测试参数追踪")
        wait_for_node_count(selenium, 1)
        
        # 获取节点ID
        nodes = selenium.find_elements(By.CSS_SELECTOR, '[data-testid="node-container"]')
        assert len(nodes) > 0, "应该有节点存在"
        
        # 解析data-dash-id属性
        data_dash_id = nodes[0].get_attribute("data-dash-id")
        if data_dash_id:
            import json
            try:
                node_data = json.loads(data_dash_id)
                node_id = node_data.get("index", "1")
            except:
                node_id = "1"
        else:
            node_id = "1"
        
        # 添加参数
        success = add_parameter(selenium, node_id, "追踪参数", "初始值", "个")
        assert success, "添加参数应该成功"
        
        # 等待参数出现并编辑
        param_input = wait_for_element(selenium, By.CSS_SELECTOR, f"input[data-dash-id*='{node_id}'][data-param='追踪参数']")
        assert param_input is not None, "参数输入框应该出现"
        
        # 修改参数值
        param_input.clear()
        param_input.send_keys("新值")
        param_input.send_keys(Keys.TAB)
        time.sleep(0.5)
        
        # 验证最近更新列表（如果存在）
        recent_list = wait_for_element(selenium, By.ID, "recent-params-list")
        if recent_list is not None:
            assert "新值" in recent_list.text, "最近更新列表应该包含新值"
        
        print("✅ 最近更新的参数追踪测试通过")
        
    except Exception as e:
        pytest.fail(f"最近更新的参数追踪测试失败: {str(e)}")

if __name__ == "__main__":
    test_recently_updated_params_tracking()
    print("✅ T511 测试通过")
