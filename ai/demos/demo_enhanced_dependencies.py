#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强的依赖关系和计算过程展示功能演示
这个脚本演示了如何：
1. 创建带有复杂计算依赖关系的节点
2. 展示计算过程和结果
3. 进行实时分析
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import graph
from models import Node, Parameter

def create_demo_nodes():
    """创建演示用的节点和参数"""
    # 清理现有状态
    graph.nodes.clear()
    
    # 创建节点
    nodes = []
    for i in range(5):
        node = Node(f"节点{i+1}", f"演示节点{i+1}")
        graph.add_node(node)
        nodes.append(node)
        
        # 为每个节点添加一些参数
        for j in range(2):
            param = Parameter(f"参数{j+1}", value=10.0, unit="m")
            node.add_parameter(param)
            param.set_graph(graph)
    
    # 设置一些依赖关系
    nodes[1].parameters[0].calculation_func = "result = dependencies[0].value * 2"
    nodes[1].parameters[0].add_dependency(nodes[0].parameters[0])
    
    nodes[2].parameters[0].calculation_func = "result = dependencies[0].value + dependencies[1].value"
    nodes[2].parameters[0].add_dependency(nodes[0].parameters[1])
    nodes[2].parameters[0].add_dependency(nodes[1].parameters[0])
    
    nodes[3].parameters[1].calculation_func = "result = sum(dep.value for dep in dependencies)"
    nodes[3].parameters[1].add_dependency(nodes[1].parameters[1])
    nodes[3].parameters[1].add_dependency(nodes[2].parameters[0])
    
    nodes[4].parameters[0].calculation_func = "result = dependencies[0].value * 1.5"
    nodes[4].parameters[0].add_dependency(nodes[3].parameters[1])
    
    # 计算所有参数
    for node in nodes:
        for param in node.parameters:
            if param.calculation_func:
                param.calculate()
    
    return nodes

def print_dependency_info(nodes):
    """打印依赖关系信息"""
    print("\n🔍 依赖关系分析:")
    
    for node in nodes:
        print(f"\n📦 {node.name}:")
        for param in node.parameters:
            print(f"  └── 📊 {param.name}:")
            if param.calculation_func:
                print(f"      └── 🔢 计算: {param.calculation_func}")
                print(f"      └── 📈 当前值: {param.value}")
                if param.dependencies:
                    print("      └── 🔗 依赖:")
                    for dep in param.dependencies:
                        for search_node in nodes:
                            if dep in search_node.parameters:
                                print(f"          └── {search_node.name}.{dep.name} = {dep.value}")
                                break
            else:
                print(f"      └── 📈 值: {param.value} (无计算)")

def main():
    """主函数"""
    print("🚀 开始增强依赖关系演示...")
    
    # 创建演示节点
    nodes = create_demo_nodes()
    
    # 打印依赖信息
    print_dependency_info(nodes)
    
    print("\n✨ 演示完成！")

if __name__ == "__main__":
    main() 