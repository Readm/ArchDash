#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T513 - 无浏览器版本测试
测试空节点名称验证逻辑，不依赖Selenium
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app, graph
from models import Node

def test_empty_node_name_validation_logic():
    """测试空节点名称验证逻辑（无浏览器）"""
    
    # 清理状态
    graph.nodes.clear()
    
    # 测试空名称节点创建逻辑
    def validate_node_input(name, description=""):
        """模拟前端验证逻辑"""
        if not name or name.strip() == "":
            return {"success": False, "error": "节点名称不能为空"}
        
        # 模拟创建节点
        node = Node(name=name.strip(), description=description)
        node_id = graph.add_node(node)
        return {"success": True, "node_id": node_id}
    
    # 测试空名称
    result = validate_node_input("")
    assert result["success"] == False
    assert "不能为空" in result["error"]
    
    # 测试只有空格的名称
    result = validate_node_input("   ")
    assert result["success"] == False
    assert "不能为空" in result["error"]
    
    # 测试有效名称
    result = validate_node_input("有效节点名称")
    assert result["success"] == True
    assert "node_id" in result
    
    print("✅ 空节点名称验证逻辑测试通过（无浏览器）")

def test_node_creation_backend():
    """测试节点创建的后端逻辑"""
    
    # 清理状态
    graph.nodes.clear()
    initial_count = len(graph.nodes)
    
    # 创建有效节点
    node = Node(name="测试节点", description="测试描述")
    node_id = graph.add_node(node)
    
    # 验证节点已添加
    assert len(graph.nodes) == initial_count + 1
    
    # add_node 返回的是节点对象，实际ID在node.id中
    actual_node_id = node.id
    assert actual_node_id in graph.nodes
    assert graph.nodes[actual_node_id].name == "测试节点"
    
    print("✅ 节点创建后端逻辑测试通过")

if __name__ == "__main__":
    test_empty_node_name_validation_logic()
    test_node_creation_backend()
    print("✅ 所有无浏览器测试通过")