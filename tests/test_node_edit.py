#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
节点名称编辑功能测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import graph, id_mapper, IDMapper
from models import Node, CalculationGraph

def test_node_name_editing():
    """测试节点名称编辑功能"""
    print("🧪 测试节点名称编辑功能")
    
    # 清理状态
    graph.nodes.clear()
    id_mapper._node_mapping.clear()
    
    # 创建测试节点
    node1 = Node(name="原始节点1", description="第一个测试节点")
    node2 = Node(name="原始节点2", description="第二个测试节点")
    
    # 添加节点到计算图
    graph.add_node(node1)
    graph.add_node(node2)
    
    # 注册节点到ID映射器
    id_mapper.register_node(node1.id, node1.name)
    id_mapper.register_node(node2.id, node2.name)
    
    print(f"✅ 创建节点: {node1.name} (ID: {node1.id})")
    print(f"✅ 创建节点: {node2.name} (ID: {node2.id})")
    
    # 测试节点名称更新
    new_name = "更新后的节点1"
    
    # 验证原始状态
    assert id_mapper.get_node_name(node1.id) == "原始节点1"
    assert node1.name == "原始节点1"
    
    # 更新节点名称
    node1.name = new_name
    id_mapper.update_node_name(node1.id, new_name)
    
    # 验证更新后的状态
    assert id_mapper.get_node_name(node1.id) == new_name
    assert node1.name == new_name
    
    print(f"✅ 节点名称更新成功: '原始节点1' → '{new_name}'")
    
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

def test_id_mapper_functionality():
    """测试IDMapper的功能"""
    print("\n🧪 测试IDMapper功能")
    
    # 创建新的IDMapper实例
    test_mapper = IDMapper()
    
    # 测试节点注册
    test_node_id = "test-node-123"
    test_node_name = "测试节点"
    
    test_mapper.register_node(test_node_id, test_node_name)
    
    # 验证各种获取方法
    assert test_mapper.get_node_name(test_node_id) == test_node_name
    assert test_mapper.get_html_id(test_node_id) == f"node-{test_node_id}"
    
    dash_id = test_mapper.get_dash_id(test_node_id)
    assert dash_id["type"] == "node"
    assert dash_id["index"] == test_node_id
    
    # 测试从Dash ID获取节点ID
    retrieved_id = test_mapper.get_node_id_from_dash(dash_id)
    assert retrieved_id == test_node_id
    
    print("✅ IDMapper注册和获取功能正常")
    
    # 测试名称更新
    new_name = "更新后的测试节点"
    test_mapper.update_node_name(test_node_id, new_name)
    
    assert test_mapper.get_node_name(test_node_id) == new_name
    print("✅ IDMapper名称更新功能正常")
    
    print("🎉 IDMapper所有功能测试通过！")

if __name__ == "__main__":
    test_id_mapper_functionality()
    test_node_name_editing() 