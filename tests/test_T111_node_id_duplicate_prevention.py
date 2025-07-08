#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T111 - 节点ID重复防护测试
从原始测试文件分离出的独立测试
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from app import app, graph, layout_manager
import pytest
from models import Parameter, Node, CalculationGraph
import json
import math

def test_node_id_duplicate_prevention():
    """测试计算图中阻止重复ID节点的功能（现有功能验证）"""
    graph = CalculationGraph()
    
    # 创建第一个节点
    node1 = Node("Node1", "第一个节点")
    graph.add_node(node1)
    
    # 创建具有相同ID的节点
    node2 = Node("Node2", "第二个节点", id=node1.id)  # 使用相同的ID
    
    with pytest.raises(ValueError, match=f"Node with id {node1.id} already exists."):
        graph.add_node(node2)
    
    # 验证只有第一个节点存在
    assert len(graph.nodes) == 1
    assert graph.nodes[node1.id].name == "Node1"
    
    print("✅ 计算图重复ID检查功能正常工作")

if __name__ == "__main__":
    test_node_id_duplicate_prevention()
    print("✅ T111 节点ID重复防护测试通过")
