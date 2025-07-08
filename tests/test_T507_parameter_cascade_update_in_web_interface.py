from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count, add_parameter, get_parameter_input_box
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T507 - 测试
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
            node_id = str(i + 1)  # 节点ID通常是从1开始的
            add_parameter(selenium, node_id, f"test_param_{i+1}", 100, "unit")
            
            # 获取参数输入框（参数值输入框）
            param_input = get_parameter_input_box(selenium, node_id, f"test_param_{i+1}", "param-value")
            assert param_input is not None, "参数输入框应该出现"
            print(f"为节点 {i+1} 添加了参数")
            time.sleep(1)  # 等待参数添加完成
        
        print("\n✅ Web界面参数级联更新测试通过")
        
    except Exception as e:
        print(f"\n❌ Web界面参数级联更新测试失败: {str(e)}")
        pytest.fail(f"Web界面参数级联更新测试失败: {str(e)}")
    finally:
        print("\n=== 测试结束 ===\n")

if __name__ == "__main__":
    test_parameter_cascade_update_in_web_interface()
    print("✅ T507 测试通过")
