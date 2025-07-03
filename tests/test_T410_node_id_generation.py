#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T410 - 测试节点ID生成功能
使用独立的CalculationGraph实例
"""

import sys
import os
from models import Node, CalculationGraph

def test_node_id_generation():
    """测试节点ID生成功能"""
    print("🧪 测试节点ID生成功能")
    
    # 创建独立的计算图实例
    graph = CalculationGraph()
    
    # 清理状态
    graph.nodes.clear()
    
    # 创建测试节点
    node1 = Node(name="节点1", description="第一个测试节点")
    node2 = Node(name="节点2", description="第二个测试节点")
    node3 = Node(name="节点3", description="第三个测试节点")
    
    # 添加节点到计算图
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_node(node3)
    
    print(f"✅ 创建节点: {node1.name} (ID: {node1.id})")
    print(f"✅ 创建节点: {node2.name} (ID: {node2.id})")
    print(f"✅ 创建节点: {node3.name} (ID: {node3.id})")
    
    # 验证ID唯一性
    node_ids = [node1.id, node2.id, node3.id]
    unique_ids = set(node_ids)
    
    assert len(node_ids) == len(unique_ids), "所有节点ID应该是唯一的"
    print("✅ 节点ID唯一性验证通过")
    
    # 验证ID格式
    for node_id in node_ids:
        assert isinstance(node_id, str), f"节点ID应该是字符串类型: {type(node_id)}"
        assert len(node_id) > 0, f"节点ID不应该为空: {node_id}"
        print(f"✅ 节点ID格式验证通过: {node_id}")
    
    # 验证节点在计算图中的存储
    assert len(graph.nodes) == 3, f"计算图中应该有3个节点，实际有 {len(graph.nodes)} 个"
    
    for node_id in node_ids:
        assert node_id in graph.nodes, f"节点ID {node_id} 应该在计算图中"
        assert graph.nodes[node_id].name in ["节点1", "节点2", "节点3"], f"节点名称验证失败: {graph.nodes[node_id].name}"
    
    print("✅ 节点在计算图中的存储验证通过")
    
    # 测试ID持久性
    original_ids = node_ids.copy()
    
    # 重新创建计算图
    new_graph = CalculationGraph()
    
    # 重新添加节点
    new_node1 = Node(name="节点1", description="第一个测试节点")
    new_node2 = Node(name="节点2", description="第二个测试节点")
    new_node3 = Node(name="节点3", description="第三个测试节点")
    
    new_graph.add_node(new_node1)
    new_graph.add_node(new_node2)
    new_graph.add_node(new_node3)
    
    new_node_ids = [new_node1.id, new_node2.id, new_node3.id]
    
    # 验证新ID也是唯一的
    new_unique_ids = set(new_node_ids)
    assert len(new_node_ids) == len(new_unique_ids), "新节点ID也应该是唯一的"
    
    print("✅ 新节点ID唯一性验证通过")
    
    print("🎉 所有节点ID生成功能测试通过！")

if __name__ == "__main__":
    test_node_id_generation()
    print("✅ T410 测试通过")
