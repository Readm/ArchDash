#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T414 - 测试ID持久性功能
使用独立的CalculationGraph实例
"""

import sys
import os
from models import Node, CalculationGraph

def test_id_persistence():
    """测试ID持久性功能"""
    print("🧪 测试ID持久性功能")
    
    # 创建独立的计算图实例
    graph = CalculationGraph()
    
    # 清理状态
    graph.nodes.clear()
    
    # 创建测试节点
    node1 = Node(name="持久性测试节点1", description="第一个持久性测试节点")
    node2 = Node(name="持久性测试节点2", description="第二个持久性测试节点")
    
    # 添加节点到计算图
    graph.add_node(node1)
    graph.add_node(node2)
    
    print(f"✅ 创建节点: {node1.name} (ID: {node1.id})")
    print(f"✅ 创建节点: {node2.name} (ID: {node2.id})")
    
    # 保存原始ID
    original_node1_id = node1.id
    original_node2_id = node2.id
    
    print(f"📝 保存原始ID: 节点1={original_node1_id}, 节点2={original_node2_id}")
    
    # 验证ID在计算图中的存储
    assert node1.id in graph.nodes, f"节点1的ID {node1.id} 应该在计算图中"
    assert node2.id in graph.nodes, f"节点2的ID {node2.id} 应该在计算图中"
    
    # 测试节点属性修改后ID保持不变
    print("\n🔄 测试节点属性修改...")
    
    # 修改节点名称
    node1.name = "修改后的节点1"
    node2.name = "修改后的节点2"
    
    # 验证ID保持不变
    assert node1.id == original_node1_id, "修改节点名称后，节点1的ID应该保持不变"
    assert node2.id == original_node2_id, "修改节点名称后，节点2的ID应该保持不变"
    
    print("✅ 节点名称修改后ID持久性验证通过")
    
    # 修改节点描述
    node1.description = "修改后的描述1"
    node2.description = "修改后的描述2"
    
    # 验证ID保持不变
    assert node1.id == original_node1_id, "修改节点描述后，节点1的ID应该保持不变"
    assert node2.id == original_node2_id, "修改节点描述后，节点2的ID应该保持不变"
    
    print("✅ 节点描述修改后ID持久性验证通过")
    
    # 修改节点类型
    node1.node_type = "calculation"
    node2.node_type = "output"
    
    # 验证ID保持不变
    assert node1.id == original_node1_id, "修改节点类型后，节点1的ID应该保持不变"
    assert node2.id == original_node2_id, "修改节点类型后，节点2的ID应该保持不变"
    
    print("✅ 节点类型修改后ID持久性验证通过")
    
    # 验证计算图中的节点属性已更新
    assert graph.nodes[node1.id].name == "修改后的节点1", "计算图中的节点1名称应该已更新"
    assert graph.nodes[node1.id].description == "修改后的描述1", "计算图中的节点1描述应该已更新"
    assert graph.nodes[node1.id].node_type == "calculation", "计算图中的节点1类型应该已更新"
    
    assert graph.nodes[node2.id].name == "修改后的节点2", "计算图中的节点2名称应该已更新"
    assert graph.nodes[node2.id].description == "修改后的描述2", "计算图中的节点2描述应该已更新"
    assert graph.nodes[node2.id].node_type == "output", "计算图中的节点2类型应该已更新"
    
    print("✅ 计算图中节点属性更新验证通过")
    
    # 测试节点对象引用的一致性
    assert graph.nodes[node1.id] is node1, "计算图中的节点1对象引用应该与原始对象一致"
    assert graph.nodes[node2.id] is node2, "计算图中的节点2对象引用应该与原始对象一致"
    
    print("✅ 节点对象引用一致性验证通过")
    
    # 测试重新创建计算图后的ID持久性
    print("\n🔄 测试重新创建计算图...")
    
    # 创建新的计算图实例
    new_graph = CalculationGraph()
    
    # 重新创建节点
    new_node1 = Node(name="新节点1", description="新节点1描述")
    new_node2 = Node(name="新节点2", description="新节点2描述")
    
    new_graph.add_node(new_node1)
    new_graph.add_node(new_node2)
    
    # 验证新节点的ID也是唯一的
    assert new_node1.id != new_node2.id, "新节点的ID应该是唯一的"
    assert new_node1.id in new_graph.nodes, "新节点1的ID应该在新计算图中"
    assert new_node2.id in new_graph.nodes, "新节点2的ID应该在新计算图中"
    
    print("✅ 新计算图中ID持久性验证通过")
    
    print("🎉 所有ID持久性功能测试通过！")

if __name__ == "__main__":
    test_id_persistence()
    print("✅ T414 测试通过")
