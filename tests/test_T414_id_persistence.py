#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T414 - 测试
从原始测试文件分离出的独立测试
"""

import sys
import os
from app import graph
from models import Node, Parameter, CalculationGraph

def test_id_persistence():
    """测试ID持久性（序列化后ID保持不变）"""
    print("\n🧪 测试ID持久性")
    
    # 清理状态
    graph.nodes.clear()
    
    # 创建测试节点
    original_node = Node(name="持久性测试节点", description="测试ID在序列化后是否保持不变")
    graph.add_node(original_node)
    original_id = original_node.id
    
    # 模拟序列化
    node_dict = original_node.to_dict()
    assert "id" in node_dict, "序列化的字典应该包含ID"
    assert node_dict["id"] == original_id, "序列化的ID应该与原始ID匹配"
    print(f"✅ 序列化ID正确: {node_dict['id']}")
    
    # 验证序列化包含必要信息
    assert "name" in node_dict, "序列化应该包含节点名称"
    assert "description" in node_dict, "序列化应该包含节点描述"
    assert node_dict["name"] == original_node.name, "序列化的名称应该匹配"
    print(f"✅ 序列化数据完整: {node_dict['name']}")
    
    print("✅ ID持久性测试通过")

if __name__ == "__main__":
    test_id_persistence()
    print("✅ T414 测试通过")
