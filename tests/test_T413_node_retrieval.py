#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T413 - 测试
从原始测试文件分离出的独立测试
"""

import sys
import os
from app import graph
from models import Node, Parameter, CalculationGraph

def test_node_retrieval():
    """测试节点检索功能"""
    print("\n🧪 测试节点检索功能")
    
    # 清理状态
    graph.nodes.clear()
    
    # 创建测试节点
    test_nodes = []
    for i in range(3):
        node = Node(name=f"检索测试节点{i+1}", description=f"用于测试检索的节点{i+1}")
        graph.add_node(node)
        test_nodes.append(node)
    
    # 测试通过ID检索节点
    for node in test_nodes:
        retrieved_node = graph.nodes.get(node.id)
        assert retrieved_node is not None, f"应该能够检索到节点: {node.id}"
        assert retrieved_node.name == node.name, "检索到的节点名称应该匹配"
        assert retrieved_node.id == node.id, "检索到的节点ID应该匹配"
        print(f"✅ 成功检索节点: {node.name} (ID: {node.id})")
    
    # 测试检索不存在的节点
    non_existent_node = graph.nodes.get("999999")
    assert non_existent_node is None, "不存在的节点应该返回None"
    print("✅ 不存在节点的检索正确返回None")
    
    print("✅ 节点检索功能测试通过")

if __name__ == "__main__":
    test_node_retrieval()
    print("✅ T413 测试通过")
