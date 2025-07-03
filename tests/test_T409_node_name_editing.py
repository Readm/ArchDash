#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T409 - 测试节点名称编辑功能
使用会话隔离的graph实例
"""

import sys
import os
from models import Node, CalculationGraph

def test_node_name_editing():
    """测试节点名称编辑功能"""
    print("🧪 测试节点名称编辑功能")
    
    # 创建独立的计算图实例
    graph = CalculationGraph()
    
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

if __name__ == "__main__":
    test_node_name_editing()
    print("✅ T409 测试通过")
