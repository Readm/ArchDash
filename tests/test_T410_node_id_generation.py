#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T410 - 测试
从原始测试文件分离出的独立测试
"""

import sys
import os
from app import graph
from models import Node, Parameter, CalculationGraph

def test_node_id_generation():
    """测试节点ID生成功能"""
    print("🧪 测试节点ID生成功能")
    
    # 清理状态
    graph.nodes.clear()
    
    # 创建多个节点，验证ID生成
    nodes = []
    for i in range(5):
        node = Node(name=f"测试节点{i+1}", description=f"第{i+1}个测试节点")
        graph.add_node(node)
        nodes.append(node)
        print(f"✅ 创建节点: {node.name}, ID: {node.id}")
    
    # 验证ID唯一性
    node_ids = [node.id for node in nodes]
    assert len(set(node_ids)) == len(node_ids), "所有节点ID应该是唯一的"
    
    # 验证ID是数字字符串
    for node_id in node_ids:
        assert node_id.isdigit(), f"节点ID应该是数字字符串，实际是: {node_id}"
    
    # 验证ID递增
    for i in range(1, len(node_ids)):
        assert int(node_ids[i]) > int(node_ids[i-1]), "节点ID应该是递增的"
    
    print("✅ 节点ID生成功能测试通过")

if __name__ == "__main__":
    test_node_id_generation()
    print("✅ T410 测试通过")
