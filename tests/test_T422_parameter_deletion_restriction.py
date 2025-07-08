from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T422 - 测试
从原始测试文件分离出的独立测试
"""

import sys
import os
from app import check_parameter_has_dependents, check_node_has_dependents, graph
from models import Node, Parameter

def test_parameter_deletion_restriction():
    """测试参数删除的依赖关系限制"""
    print("🧪 测试参数删除依赖关系限制")
    
    # 清理状态
    graph.nodes.clear()
    
    # 创建输入节点
    input_node = Node(name="输入节点", description="提供基础数据")
    voltage_param = Parameter(name="电压", value=12.0, unit="V", description="输入电压")
    current_param = Parameter(name="电流", value=2.0, unit="A", description="输入电流")
    
    input_node.add_parameter(voltage_param)
    input_node.add_parameter(current_param)
    graph.add_node(input_node)
    
    # 创建计算节点
    calc_node = Node(name="计算节点", description="执行功率计算")
    power_param = Parameter(
        name="功率", 
        value=0.0, 
        unit="W", 
        description="计算的功率值",
        calculation_func="result = dependencies[0].value * dependencies[1].value"
    )
    power_param.add_dependency(voltage_param)
    power_param.add_dependency(current_param)
    
    calc_node.add_parameter(power_param)
    graph.add_node(calc_node)
    
    # 创建高级计算节点
    advanced_node = Node(name="高级计算", description="基于功率的进一步计算")
    efficiency_param = Parameter(
        name="效率",
        value=0.0,
        unit="%",
        description="系统效率",
        calculation_func="result = dependencies[0].value / 30.0 * 100"  # 假设最大功率为30W
    )
    efficiency_param.add_dependency(power_param)
    
    advanced_node.add_parameter(efficiency_param)
    graph.add_node(advanced_node)
    
    print(f"✅ 创建了依赖链: 电压,电流 → 功率 → 效率")
    
    # 测试1: 尝试删除有依赖的电压参数（应该被阻止）
    print("\n📝 测试1: 删除有依赖的电压参数")
    result = check_parameter_has_dependents(voltage_param, graph)
    has_dependents = result[0] if isinstance(result, tuple) else result
    print(f"电压参数是否有依赖者: {has_dependents}")
    assert has_dependents == True, "电压参数应该有依赖者（功率参数依赖它）"
    
    # 测试2: 尝试删除有依赖的功率参数（应该被阻止）
    print("\n📝 测试2: 删除有依赖的功率参数")
    result = check_parameter_has_dependents(power_param, graph)
    has_dependents = result[0] if isinstance(result, tuple) else result
    print(f"功率参数是否有依赖者: {has_dependents}")
    assert has_dependents == True, "功率参数应该有依赖者（效率参数依赖它）"
    
    # 测试3: 删除末端的效率参数（应该被允许）
    print("\n📝 测试3: 删除末端的效率参数")
    result = check_parameter_has_dependents(efficiency_param, graph)
    has_dependents = result[0] if isinstance(result, tuple) else result
    print(f"效率参数是否有依赖者: {has_dependents}")
    assert has_dependents == False, "效率参数应该没有依赖者（可以安全删除）"
    
    print("✅ 参数删除依赖关系限制测试通过")

if __name__ == "__main__":
    test_parameter_deletion_restriction()
    print("✅ T422 测试通过")
