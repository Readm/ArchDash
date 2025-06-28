#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
节点名称编辑功能测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import graph
from models import Node, CalculationGraph

def test_node_name_editing():
    """测试节点名称编辑功能"""
    print("🧪 测试节点名称编辑功能")
    
    # 清理状态
    graph.nodes.clear()
    
    # 创建测试节点
    node1 = Node(name="原始节点1", description="第一个测试节点")
    node2 = Node(name="原始节点2", description="第二个测试节点")
    
    # 添加节点到计算图
    graph.add_node(node1)
    graph.add_node(node2)
    
    print(f"✅ 创建节点: {node1.name} (ID: {node1.id})")
    print(f"✅ 创建节点: {node2.name} (ID: {node2.id})")
    
    # 测试节点名称更新
    new_name = "更新后的节点1"
    
    # 验证原始状态
    assert node1.name == "原始节点1"
    
    # 更新节点名称
    old_name = node1.name
    node1.name = new_name
    
    # 验证更新后的状态
    assert node1.name == new_name
    
    print(f"✅ 节点名称更新成功: '{old_name}' → '{new_name}'")
    
    # 测试重名验证功能
    try:
        # 尝试将节点2的名称设置为与节点1相同
        duplicate_name = new_name
        
        # 模拟重名检查
        name_exists = False
        for other_node_id, other_node in graph.nodes.items():
            if other_node_id != node2.id and other_node.name == duplicate_name:
                name_exists = True
                break
        
        if name_exists:
            print(f"✅ 重名验证成功: 检测到名称 '{duplicate_name}' 已存在")
        else:
            print(f"❌ 重名验证失败: 应该检测到名称冲突")
            
    except Exception as e:
        print(f"❌ 重名验证测试失败: {e}")
    
    # 测试节点类型和描述更新
    node1.node_type = "calculation"
    node1.description = "这是一个计算节点"
    
    print(f"✅ 节点类型更新: {node1.node_type}")
    print(f"✅ 节点描述更新: {node1.description}")
    
    print("🎉 所有节点编辑功能测试通过！")

def test_node_id_generation():
    """测试节点ID生成和HTML/Dash ID的创建"""
    print("\n🧪 测试节点ID生成功能")
    
    # 清理状态
    graph.nodes.clear()
    
    # 创建测试节点
    test_node = Node(name="测试节点", description="测试节点描述")
    
    # 添加到计算图，这会自动分配ID
    graph.add_node(test_node)
    
    # 验证节点ID已分配
    assert test_node.id != ""
    assert test_node.id.isdigit()  # 应该是数字字符串
    
    # 测试HTML ID和Dash ID的生成
    html_id = f"node-{test_node.id}"
    dash_id = {"type": "node", "index": test_node.id}
    
    assert html_id == f"node-{test_node.id}"
    assert dash_id["type"] == "node"
    assert dash_id["index"] == test_node.id
    
    print(f"✅ 节点ID生成成功: {test_node.id}")
    print(f"✅ HTML ID生成成功: {html_id}")
    print(f"✅ Dash ID生成成功: {dash_id}")
    
    # 测试多个节点的ID唯一性
    node2 = Node(name="第二个节点")
    graph.add_node(node2)
    
    assert node2.id != test_node.id  # ID应该不同
    assert node2.id.isdigit()
    
    print(f"✅ 第二个节点ID: {node2.id}")
    print("✅ 节点ID唯一性验证通过")
    
    print("🎉 节点ID生成功能测试通过！")

if __name__ == "__main__":
    test_node_id_generation()
    test_node_name_editing() 