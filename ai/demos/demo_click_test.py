#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
点击测试演示
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import graph
from models import Node, Parameter

def create_test_nodes():
    """创建测试用的节点和参数"""
    # 清理现有状态
    graph.nodes.clear()
    
    # 创建输入节点
    input_node = Node("输入节点", "测试输入节点")
    input_node_id = input_node.id
    
    # 添加参数
    length = Parameter("长度", 10.0, "m")
    width = Parameter("宽度", 5.0, "m")
    input_node.add_parameter(length)
    input_node.add_parameter(width)
    graph.add_node(input_node)
    
    # 创建计算节点
    calc_node = Node("计算节点", "测试计算节点")
    calc_node_id = calc_node.id
    
    # 添加计算参数
    area = Parameter("面积", 0.0, "m²", 
                    calculation_func="result = dependencies[0].value * dependencies[1].value")
    area.add_dependency(length)
    area.add_dependency(width)
    calc_node.add_parameter(area)
    graph.add_node(calc_node)
    
    # 设置计算图关联
    for node in graph.nodes.values():
        for param in node.parameters:
            param.set_graph(graph)
    
    # 计算初始值
    area.calculate()
    
    return input_node_id, calc_node_id

def print_node_info(node_id):
    """打印节点信息"""
    node = graph.nodes.get(node_id)
    if node:
        print(f"\n📦 {node.name}:")
        for param in node.parameters:
            print(f"  └── 📊 {param.name}:")
            print(f"      └── 📈 值: {param.value} {param.unit}")
            if param.calculation_func:
                print(f"      └── 🔢 计算: {param.calculation_func}")
                if param.dependencies:
                    print("      └── 🔗 依赖:")
                    for dep in param.dependencies:
                        for search_node in graph.nodes.values():
                            if dep in search_node.parameters:
                                print(f"          └── {search_node.name}.{dep.name} = {dep.value}")
                                break

def main():
    """主函数"""
    print("🚀 开始点击测试演示...")
    
    # 创建测试节点
    input_node_id, calc_node_id = create_test_nodes()
    
    # 打印节点信息
    print_node_info(input_node_id)
    print_node_info(calc_node_id)
    
    print("\n✨ 演示完成！")

if __name__ == "__main__":
    main() 