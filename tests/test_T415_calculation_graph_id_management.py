#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T415 - 测试
从原始测试文件分离出的独立测试
"""

import sys
import os
from models import Node, Parameter, CalculationGraph

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
    test_calculation_graph_id_management()
    print("✅ T415 测试通过")
