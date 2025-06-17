#!/usr/bin/env python3
"""
无头模式 vs 有头模式测试对比

使用方法：
1. 无头模式: pytest --headless test_headless_demo.py -v
2. 有头模式: pytest test_headless_demo.py -v
"""

import pytest
import time
from app import app

def test_headless_demo(dash_duo):
    """演示测试 - 可以用来对比无头和有头模式"""
    print("🧪 开始测试演示...")
    start_time = time.time()
    
    # 启动应用
    dash_duo.start_server(app, debug=False)
    
    # 检查页面标题
    title = dash_duo.find_element("h1")
    assert title.text == "ArchDash"
    print("✅ 页面标题验证成功")
    
    # 检查输入框是否存在
    input_box = dash_duo.find_element("#node-name")
    assert input_box is not None
    print("✅ 输入框元素验证成功")
    
    # 模拟一些操作
    input_box.send_keys("DemoNode")
    add_btn = dash_duo.find_element("#add-node-button")
    add_btn.click()
    
    # 等待操作完成
    dash_duo.wait_for_contains_text("#output-result", "DemoNode 已添加到位置", timeout=10)
    print("✅ 节点添加操作成功")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"🕐 测试总耗时: {duration:.2f} 秒")
    print("🎉 测试演示完成！")
    
    # 清理测试数据
    from app import graph, id_mapper, layout_manager
    graph.nodes.clear()
    id_mapper._node_mapping.clear()
    layout_manager.node_positions.clear()
    layout_manager.position_nodes.clear() 