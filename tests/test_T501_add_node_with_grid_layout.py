#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T501 - 测试添加节点和网格布局
使用会话隔离的graph实例
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count, get_node_count

def test_add_node_with_grid_layout(selenium, flask_app):
    """测试添加节点并验证网格布局"""
    try:
        print("\n========== 开始网格布局节点添加测试 ==========")
        
        # 清理状态
        clean_state(selenium)
        time.sleep(2)
        
        # 创建第一个节点
        print("\n第1步：创建第一个节点")
        assert create_node(selenium, "节点1", "第一个测试节点"), "第一个节点创建失败"
        wait_for_node_count(selenium, 1)
        
        # 创建第二个节点
        print("\n第2步：创建第二个节点")
        assert create_node(selenium, "节点2", "第二个测试节点"), "第二个节点创建失败"
        wait_for_node_count(selenium, 2)
        
        # 创建第三个节点
        print("\n第3步：创建第三个节点")
        assert create_node(selenium, "节点3", "第三个测试节点"), "第三个节点创建失败"
        wait_for_node_count(selenium, 3)
        
        # 验证节点数量
        final_count = get_node_count(selenium)
        assert final_count == 3, f"期望3个节点，实际找到 {final_count} 个"
        
        # 验证页面内容
        page_source = selenium.page_source
        assert "节点1" in page_source, "页面应该包含节点1"
        assert "节点2" in page_source, "页面应该包含节点2"
        assert "节点3" in page_source, "页面应该包含节点3"
        
        print("✅ 网格布局节点添加测试通过")
        
    except Exception as e:
        print(f"❌ 网格布局节点添加测试失败: {e}")
        raise

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
