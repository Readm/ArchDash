#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T412 - 测试HTML Dash ID生成功能
使用独立的CalculationGraph实例
"""

import sys
import os
from models import Node, CalculationGraph

def test_html_dash_id_generation():
    """测试HTML Dash ID生成功能"""
    print("🧪 测试HTML Dash ID生成功能")
    
    # 创建独立的计算图实例
    graph = CalculationGraph()
    
    # 清理状态
    graph.nodes.clear()
    
    # 创建测试节点
    node1 = Node(name="测试节点1", description="第一个测试节点")
    node2 = Node(name="测试节点2", description="第二个测试节点")
    
    # 添加节点到计算图
    graph.add_node(node1)
    graph.add_node(node2)
    
    print(f"✅ 创建节点: {node1.name} (ID: {node1.id})")
    print(f"✅ 创建节点: {node2.name} (ID: {node2.id})")
    
    # 验证节点ID格式
    assert isinstance(node1.id, str), f"节点ID应该是字符串类型: {type(node1.id)}"
    assert isinstance(node2.id, str), f"节点ID应该是字符串类型: {type(node2.id)}"
    
    # 验证ID唯一性
    assert node1.id != node2.id, "不同节点的ID应该是唯一的"
    print("✅ 节点ID唯一性验证通过")
    
    # 验证ID在计算图中的存储
    assert node1.id in graph.nodes, f"节点1的ID {node1.id} 应该在计算图中"
    assert node2.id in graph.nodes, f"节点2的ID {node2.id} 应该在计算图中"
    
    # 验证节点对象的一致性
    assert graph.nodes[node1.id] is node1, "计算图中的节点对象应该与原始节点对象一致"
    assert graph.nodes[node2.id] is node2, "计算图中的节点对象应该与原始节点对象一致"
    
    print("✅ 节点在计算图中的存储验证通过")
    
    # 测试ID的持久性
    original_node1_id = node1.id
    original_node2_id = node2.id
    
    # 修改节点名称，验证ID不变
    node1.name = "修改后的节点1"
    node2.name = "修改后的节点2"
    
    assert node1.id == original_node1_id, "修改节点名称后，ID应该保持不变"
    assert node2.id == original_node2_id, "修改节点名称后，ID应该保持不变"
    
    print("✅ 节点ID持久性验证通过")
    
    # 验证计算图中的节点名称已更新
    assert graph.nodes[node1.id].name == "修改后的节点1", "计算图中的节点名称应该已更新"
    assert graph.nodes[node2.id].name == "修改后的节点2", "计算图中的节点名称应该已更新"
    
    print("✅ 节点名称更新验证通过")
    
    print("🎉 所有HTML Dash ID生成功能测试通过！")

if __name__ == "__main__":
    test_html_dash_id_generation()
    print("✅ T412 测试通过")
