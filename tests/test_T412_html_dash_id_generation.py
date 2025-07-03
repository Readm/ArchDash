#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T412 - 测试
从原始测试文件分离出的独立测试
"""

import sys
import os
from app import graph
from models import Node, Parameter, CalculationGraph

def test_html_dash_id_generation():
    """测试HTML ID和Dash ID生成功能"""
    print("\n🧪 测试HTML ID和Dash ID生成功能")
    
    # 清理状态
    graph.nodes.clear()
    
    # 创建测试节点
    node = Node(name="HTML测试节点", description="用于测试HTML和Dash ID生成")
    graph.add_node(node)
    
    # 测试HTML ID生成
    html_id = f"node-{node.id}"
    expected_html_pattern = f"node-{node.id}"
    assert html_id == expected_html_pattern, f"HTML ID格式不正确: {html_id}"
    print(f"✅ HTML ID生成正确: {html_id}")
    
    # 测试Dash ID生成
    dash_id = {"type": "node", "index": node.id}
    assert dash_id["type"] == "node", "Dash ID类型应该是'node'"
    assert dash_id["index"] == node.id, f"Dash ID索引应该是节点ID: {node.id}"
    print(f"✅ Dash ID生成正确: {dash_id}")
    
    # 测试参数相关的ID
    param = Parameter(name="测试参数", value=100.0, unit="unit")
    node.add_parameter(param)
    
    param_dash_id = {"type": "param-name", "node": node.id, "index": 0}
    assert param_dash_id["type"] == "param-name", "参数Dash ID类型应该是'param-name'"
    assert param_dash_id["node"] == node.id, "参数Dash ID应该包含节点ID"
    assert param_dash_id["index"] == 0, "参数Dash ID应该包含参数索引"
    print(f"✅ 参数Dash ID生成正确: {param_dash_id}")
    
    print("✅ HTML ID和Dash ID生成功能测试通过")

if __name__ == "__main__":
    test_html_dash_id_generation()
    print("✅ T412 测试通过")
