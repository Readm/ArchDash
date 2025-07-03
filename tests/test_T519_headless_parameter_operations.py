from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count, add_parameter
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T519 - 测试
从原始测试文件分离出的独立测试
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import time
from app import app, graph, layout_manager

def test_headless_parameter_operations(selenium):
    """测试无头模式下的参数操作"""
    try:
        clean_state(selenium)
        
        # 等待页面加载完成
        wait_for_page_load(selenium)
        
        # 创建测试节点
        success = create_node(selenium, "参数测试节点", "用于测试参数操作")
        assert success, "节点创建应该成功"
        
        # 等待UI更新
        time.sleep(3)
        
        # 验证节点数量
        nodes = selenium.find_elements(By.CSS_SELECTOR, '[data-testid="node-container"]')
        assert len(nodes) >= 1, f"应该有至少1个节点，实际找到: {len(nodes)}"
        
        # 获取节点ID（假设是第一个节点）
        nodes = selenium.find_elements(By.CSS_SELECTOR, ".node-container")
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
        success = add_parameter(selenium, node_id, "测试参数", "100", "个")
        assert success, "添加参数应该成功"
        
        # 等待参数出现
        param_input = wait_for_element(selenium, By.CSS_SELECTOR, f"input[data-dash-id*='{node_id}'][data-param='测试参数']")
        assert param_input is not None and param_input.is_displayed(), "参数输入框应该出现且可见"
        
        # 验证参数值
        assert param_input.get_attribute("value") == "100", "参数值应该正确"
        
        print("✅ 无头模式参数操作测试通过")
        
    except Exception as e:
        pytest.fail(f"无头模式参数测试失败: {str(e)}")

if __name__ == "__main__":
    test_headless_parameter_operations()
    print("✅ T519 测试通过")
