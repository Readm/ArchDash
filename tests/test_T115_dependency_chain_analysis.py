#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T115 - 依赖链分析测试
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

def test_dependency_chain_analysis():
    """测试依赖链分析功能"""
    # 创建计算图
    graph = CalculationGraph()
    node = Node("ChainTestNode", "依赖链测试节点")
    
    # 创建三级依赖链：A -> B -> C
    param_a = Parameter("param_a", 1.0, "V")
    param_b = Parameter("param_b", 0.0, "A", 
                       calculation_func="result = dependencies[0].value * 2")
    param_c = Parameter("param_c", 0.0, "W",
                       calculation_func="result = dependencies[0].value + 5")
    
    param_b.add_dependency(param_a)
    param_c.add_dependency(param_b)
    
    node.add_parameter(param_a)
    node.add_parameter(param_b)
    node.add_parameter(param_c)
    graph.add_node(node)
    
    # 测试依赖链分析
    chain_info = graph.get_dependency_chain(param_a)
    
    # 验证返回结构
    assert 'upstream' in chain_info
    assert 'downstream' in chain_info

    # 验证下游依赖
    downstream_names = [p.name for p in chain_info['downstream']]
    assert 'param_b' in downstream_names
    assert 'param_c' in downstream_names
    assert len(downstream_names) == 2

    # 验证上游依赖（此例中应为空）
    assert len(chain_info['upstream']) == 0

    print("✅ 依赖链分析功能正常工作")

if __name__ == "__main__":
    test_dependency_chain_analysis()
    print("✅ T115 依赖链分析测试通过")
