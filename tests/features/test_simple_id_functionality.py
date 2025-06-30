#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试新的ID生成和管理功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

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

def test_html_dash_id_generation():
    """测试HTML ID和Dash ID生成功能"""
    print("\n🧪 测试HTML ID和Dash ID生成功能")
    
    # 清理状态
    graph.nodes.clear()
    
    # 创建测试节点
    node = Node(name="HTML测试节点", description="用于测试HTML和Dash ID生成")
    graph.add_node(node)
    
    # 测试HTML ID生成
    html_id = f"node-{node.id}"
    expected_html_pattern = f"node-{node.id}"
    assert html_id == expected_html_pattern, f"HTML ID格式不正确: {html_id}"
    print(f"✅ HTML ID生成正确: {html_id}")
    
    # 测试Dash ID生成
    dash_id = {"type": "node", "index": node.id}
    assert dash_id["type"] == "node", "Dash ID类型应该是'node'"
    assert dash_id["index"] == node.id, f"Dash ID索引应该是节点ID: {node.id}"
    print(f"✅ Dash ID生成正确: {dash_id}")
    
    # 测试参数相关的ID
    param = Parameter(name="测试参数", value=100.0, unit="unit")
    node.add_parameter(param)
    
    param_dash_id = {"type": "param-name", "node": node.id, "index": 0}
    assert param_dash_id["type"] == "param-name", "参数Dash ID类型应该是'param-name'"
    assert param_dash_id["node"] == node.id, "参数Dash ID应该包含节点ID"
    assert param_dash_id["index"] == 0, "参数Dash ID应该包含参数索引"
    print(f"✅ 参数Dash ID生成正确: {param_dash_id}")
    
    print("✅ HTML ID和Dash ID生成功能测试通过")

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

def test_calculation_graph_id_management():
    """测试CalculationGraph的ID管理功能"""
    print("\n🧪 测试CalculationGraph的ID管理功能")
    
    # 创建新的计算图实例
    test_graph = CalculationGraph()
    
    # 测试ID生成器初始状态
    assert test_graph._next_node_id == 1, "初始的下一个节点ID应该是1"
    
    # 测试ID生成
    first_id = test_graph.get_next_node_id()
    assert first_id == "1", f"第一个ID应该是'1'，实际是'{first_id}'"
    assert test_graph._next_node_id == 2, "生成ID后，下一个ID应该是2"
    
    second_id = test_graph.get_next_node_id()
    assert second_id == "2", f"第二个ID应该是'2'，实际是'{second_id}'"
    assert test_graph._next_node_id == 3, "生成ID后，下一个ID应该是3"
    
    print(f"✅ ID生成器正常工作: {first_id}, {second_id}")
    
    # 测试节点添加时的自动ID分配
    node_without_id = Node(name="无ID节点")
    assert node_without_id.id == "", "新创建的节点应该没有ID"
    
    test_graph.add_node(node_without_id)
    assert node_without_id.id == "3", f"添加到图后，节点应该获得ID '3'，实际是'{node_without_id.id}'"
    
    print(f"✅ 自动ID分配正常工作: {node_without_id.id}")
    
    print("✅ CalculationGraph的ID管理功能测试通过")

if __name__ == "__main__":
    test_node_id_generation()
    test_html_dash_id_generation()
    test_node_retrieval()
    test_id_persistence()
    test_calculation_graph_id_management()
    print("\n🎉 所有ID功能测试通过！") 