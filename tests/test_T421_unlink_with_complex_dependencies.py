from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T421 - 测试
从原始测试文件分离出的独立测试
"""

import sys
import os
from models import *
import traceback

def test_unlink_with_complex_dependencies():
    """测试复杂依赖关系中的unlink功能"""
    print("\n🔬 测试复杂依赖关系中的unlink功能")
    print("=" * 50)
    
    # 创建复杂的依赖链：A -> B -> C -> D
    graph = CalculationGraph()
    
    input_node = Node("输入")
    a = Parameter("A", 10.0, "unit")
    input_node.add_parameter(a)
    graph.add_node(input_node)
    
    calc_node = Node("计算链")
    
    b = Parameter("B", 0.0, "unit", calculation_func="result = dependencies[0].value * 2")
    b.add_dependency(a)
    calc_node.add_parameter(b)
    
    c = Parameter("C", 0.0, "unit", calculation_func="result = dependencies[0].value + 5")
    c.add_dependency(b)
    calc_node.add_parameter(c)
    
    d = Parameter("D", 0.0, "unit", calculation_func="result = dependencies[0].value * 3")
    d.add_dependency(c)
    calc_node.add_parameter(d)
    
    graph.add_node(calc_node)
    
    # 设置计算图关联
    for node in graph.nodes.values():
        for param in node.parameters:
            param.set_graph(graph)
    
    print("1. 计算初始值：")
    b.calculate()
    c.calculate()
    d.calculate()
    print(f"   A = {a.value}")
    print(f"   B = {b.value} (A * 2 = {a.value * 2})")
    print(f"   C = {c.value} (B + 5 = {b.value + 5})")
    print(f"   D = {d.value} (C * 3 = {c.value * 3})")
    
    print("\n2. 在中间节点C处断开连接：")
    c.set_manual_value(100.0)
    print(f"   C手动设置为100.0, unlinked = {c.unlinked}")
    assert c.unlinked == True, "C应该被unlink"
    
    print("\n3. 修改A，检查传播：")
    a.value = 20.0
    
    # B应该更新
    b.calculate()
    print(f"   A修改后 B = {b.value} (应该是40.0)")
    assert b.value == 40.0, "B应该正常更新"
    
    # C应该保持不变（因为unlinked）
    old_c_value = c.value
    c.calculate()
    print(f"   A修改后 C = {c.value} (应该保持100.0)")
    assert c.value == old_c_value, "C应该保持unlinked状态"
    
    # D应该基于C的手动值计算
    d.calculate()
    print(f"   A修改后 D = {d.value} (应该是300.0)")
    assert d.value == 300.0, "D应该基于C的手动值计算"
    
    print("\n4. 重新连接C：")
    c.relink_and_calculate()
    print(f"   C重新连接后 = {c.value}, unlinked = {c.unlinked}")
    assert c.unlinked == False, "C应该重新连接"
    assert c.value == 45.0, "C应该基于新的B值计算 (40 + 5 = 45)"
    
    # D应该基于新的C值更新
    d.calculate()
    print(f"   C重新连接后 D = {d.value} (应该是135.0)")
    assert d.value == 135.0, "D应该基于新的C值计算 (45 * 3 = 135)"
    
    print("✅ 复杂依赖关系unlink测试通过！")

if __name__ == "__main__":
    test_unlink_with_complex_dependencies()
    print("✅ T421 测试通过")
