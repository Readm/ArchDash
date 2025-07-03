#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T413 - 测试节点检索功能
使用独立的CalculationGraph实例
"""

import sys
import os
from models import Node, CalculationGraph

def test_node_retrieval():
    """测试节点检索功能"""
    print("🧪 测试节点检索功能")
    
    # 创建独立的计算图实例
    graph = CalculationGraph()
    
    # 清理状态
    graph.nodes.clear()
    
    # 创建测试节点
    node1 = Node(name="检索测试节点1", description="第一个检索测试节点")
    node2 = Node(name="检索测试节点2", description="第二个检索测试节点")
    node3 = Node(name="检索测试节点3", description="第三个检索测试节点")
    
    # 添加节点到计算图
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_node(node3)
    
    print(f"✅ 创建节点: {node1.name} (ID: {node1.id})")
    print(f"✅ 创建节点: {node2.name} (ID: {node2.id})")
    print(f"✅ 创建节点: {node3.name} (ID: {node3.id})")
    
    # 测试通过ID检索节点
    retrieved_node1 = graph.nodes.get(node1.id)
    retrieved_node2 = graph.nodes.get(node2.id)
    retrieved_node3 = graph.nodes.get(node3.id)
    
    assert retrieved_node1 is not None, f"应该能够通过ID {node1.id} 检索到节点1"
    assert retrieved_node2 is not None, f"应该能够通过ID {node2.id} 检索到节点2"
    assert retrieved_node3 is not None, f"应该能够通过ID {node3.id} 检索到节点3"
    
    print("✅ 通过ID检索节点验证通过")
    
    # 验证检索到的节点对象一致性
    assert retrieved_node1 is node1, "检索到的节点1对象应该与原始节点对象一致"
    assert retrieved_node2 is node2, "检索到的节点2对象应该与原始节点对象一致"
    assert retrieved_node3 is node3, "检索到的节点3对象应该与原始节点对象一致"
    
    print("✅ 节点对象一致性验证通过")
    
    # 测试通过名称检索节点
    nodes_by_name = {}
    for node_id, node in graph.nodes.items():
        nodes_by_name[node.name] = node
    
    assert "检索测试节点1" in nodes_by_name, "应该能够通过名称检索到节点1"
    assert "检索测试节点2" in nodes_by_name, "应该能够通过名称检索到节点2"
    assert "检索测试节点3" in nodes_by_name, "应该能够通过名称检索到节点3"
    
    print("✅ 通过名称检索节点验证通过")
    
    # 验证通过名称检索的节点对象一致性
    assert nodes_by_name["检索测试节点1"] is node1, "通过名称检索的节点1对象应该与原始节点对象一致"
    assert nodes_by_name["检索测试节点2"] is node2, "通过名称检索的节点2对象应该与原始节点对象一致"
    assert nodes_by_name["检索测试节点3"] is node3, "通过名称检索的节点3对象应该与原始节点对象一致"
    
    print("✅ 通过名称检索的节点对象一致性验证通过")
    
    # 测试检索不存在的节点
    non_existent_node = graph.nodes.get("non_existent_id")
    assert non_existent_node is None, "检索不存在的节点ID应该返回None"
    
    assert "不存在的节点" not in nodes_by_name, "检索不存在的节点名称应该返回False"
    
    print("✅ 检索不存在节点的处理验证通过")
    
    # 测试节点数量
    assert len(graph.nodes) == 3, f"计算图中应该有3个节点，实际有 {len(graph.nodes)} 个"
    
    print("✅ 节点数量验证通过")
    
    print("🎉 所有节点检索功能测试通过！")

if __name__ == "__main__":
    test_node_retrieval()
    print("✅ T413 测试通过")
