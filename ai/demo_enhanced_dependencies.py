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
sys.path.insert(0, os.path.dirname(__file__))

from app import graph, id_mapper
from models import Node, Parameter

def create_demo_graph():
    """创建一个演示计算图，展示复杂的依赖关系和计算过程"""
    print("🏗️ 创建增强的演示计算图...")
    
    # 清理现有数据
    graph.nodes.clear()
    id_mapper._node_mapping.clear()
    
    # 1. 输入参数节点
    input_node = Node(name="输入参数", description="系统的基础输入参数")
    
    # 基础参数
    length = Parameter(name="长度", value=10.0, unit="m", description="结构长度", confidence=0.95)
    width = Parameter(name="宽度", value=5.0, unit="m", description="结构宽度", confidence=0.90)
    height = Parameter(name="高度", value=3.0, unit="m", description="结构高度", confidence=0.85)
    
    input_node.add_parameter(length)
    input_node.add_parameter(width)
    input_node.add_parameter(height)
    
    # 2. 计算节点 - 面积和体积
    geometry_node = Node(name="几何计算", description="基础几何参数计算")
    
    # 面积计算（依赖于长度和宽度）
    area = Parameter(name="面积", value=0.0, unit="m²", description="底面面积", confidence=0.80)
    area.add_dependency(length)
    area.add_dependency(width)
    area.calculation_func = """# 计算底面面积
result = dependencies[0].value * dependencies[1].value
print(f"计算面积: {dependencies[0].value} × {dependencies[1].value} = {result}")"""
    
    # 体积计算（依赖于面积和高度）
    volume = Parameter(name="体积", value=0.0, unit="m³", description="结构体积", confidence=0.75)
    volume.add_dependency(area)
    volume.add_dependency(height)
    volume.calculation_func = """# 计算体积
result = dependencies[0].value * dependencies[1].value
print(f"计算体积: {dependencies[0].value} × {dependencies[1].value} = {result}")"""
    
    geometry_node.add_parameter(area)
    geometry_node.add_parameter(volume)
    
    # 3. 材料属性节点
    material_node = Node(name="材料属性", description="材料相关参数")
    
    density = Parameter(name="密度", value=2500.0, unit="kg/m³", description="材料密度", confidence=0.90)
    elastic_modulus = Parameter(name="弹性模量", value=30000.0, unit="MPa", description="材料弹性模量", confidence=0.85)
    
    material_node.add_parameter(density)
    material_node.add_parameter(elastic_modulus)
    
    # 4. 结构分析节点
    analysis_node = Node(name="结构分析", description="结构力学分析")
    
    # 重量计算（依赖于体积和密度）
    weight = Parameter(name="重量", value=0.0, unit="kg", description="结构总重量", confidence=0.70)
    weight.add_dependency(volume)
    weight.add_dependency(density)
    weight.calculation_func = """# 计算结构重量
result = dependencies[0].value * dependencies[1].value
print(f"计算重量: {dependencies[0].value} × {dependencies[1].value} = {result}")"""
    
    # 刚度计算（复杂计算）
    stiffness = Parameter(name="刚度", value=0.0, unit="N/m", description="结构刚度", confidence=0.65)
    stiffness.add_dependency(elastic_modulus)
    stiffness.add_dependency(area)
    stiffness.add_dependency(length)
    stiffness.calculation_func = """# 计算结构刚度 (简化公式)
# K = E * A / L
E = dependencies[0].value * 1e6  # MPa转Pa
A = dependencies[1].value  # m²
L = dependencies[2].value  # m
result = E * A / L
print(f"计算刚度: ({E:.0f} × {A}) / {L} = {result:.0f}")"""
    
    analysis_node.add_parameter(weight)
    analysis_node.add_parameter(stiffness)
    
    # 5. 性能评估节点
    performance_node = Node(name="性能评估", description="综合性能评估")
    
    # 效率指标（依赖于多个参数）
    efficiency = Parameter(name="效率指标", value=0.0, unit="无量纲", description="结构效率", confidence=0.60)
    efficiency.add_dependency(stiffness)
    efficiency.add_dependency(weight)
    efficiency.calculation_func = """# 计算效率指标 (刚度/重量比)
stiffness_val = dependencies[0].value
weight_val = dependencies[1].value
if weight_val > 0:
    result = stiffness_val / weight_val / 1000  # 标准化
    print(f"计算效率: {stiffness_val:.0f} / {weight_val:.0f} = {result:.3f}")
else:
    result = 0
    print("无法计算效率：重量为零")"""
    
    performance_node.add_parameter(efficiency)
    
    # 添加所有节点到计算图
    nodes = [input_node, geometry_node, material_node, analysis_node, performance_node]
    for node in nodes:
        graph.add_node(node)
        id_mapper.register_node(node.id, node.name)
    
    print("✅ 演示计算图创建完成!")
    print(f"📊 总节点数: {len(nodes)}")
    total_params = sum(len(node.parameters) for node in nodes)
    calc_params = sum(1 for node in nodes for param in node.parameters if param.calculation_func)
    print(f"📈 总参数数: {total_params}")
    print(f"⚙️ 计算参数: {calc_params}")
    
    return nodes

def perform_calculation_cascade():
    """执行级联计算并展示过程"""
    print("\n🔄 执行级联计算...")
    
    try:
        # 模拟参数更新，触发级联计算
        result = graph.recalculate_all()
        
        if result.get('success'):
            print("✅ 计算成功完成!")
            
            if 'calculations_performed' in result:
                print(f"📊 执行了 {result['calculations_performed']} 次计算")
            
            if 'updated_parameters' in result:
                print("🔄 更新的参数:")
                for param_info in result['updated_parameters']:
                    print(f"  • {param_info['name']}: {param_info['old_value']} → {param_info['new_value']} {param_info['unit']}")
        else:
            print(f"❌ 计算失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 执行计算时发生错误: {str(e)}")

def demonstrate_dependency_analysis():
    """演示依赖关系分析功能"""
    print("\n🔍 依赖关系分析演示...")
    
    # 分析每个参数的依赖关系
    for node_id, node in graph.nodes.items():
        node_name = id_mapper.get_node_name(node_id)
        print(f"\n📦 节点: {node_name}")
        
        for param in node.parameters:
            print(f"  📌 {param.name}:")
            print(f"    值: {param.value} {param.unit}")
            print(f"    置信度: {getattr(param, 'confidence', 1.0):.1%}")
            
            if param.dependencies:
                print(f"    依赖于:")
                for dep in param.dependencies:
                    # 找到依赖参数所在的节点
                    dep_node_name = "未知节点"
                    for search_node_id, search_node in graph.nodes.items():
                        if dep in search_node.parameters:
                            dep_node_name = id_mapper.get_node_name(search_node_id)
                            break
                    print(f"      → {dep_node_name}.{dep.name} ({dep.value} {dep.unit})")
            
            if param.calculation_func:
                print(f"    计算函数: 已定义")
                # 计算复杂度
                lines = param.calculation_func.count('\n') + 1
                complexity = "简单" if lines <= 5 else "中等" if lines <= 10 else "复杂"
                print(f"    复杂度: {complexity} ({lines} 行)")
            else:
                print(f"    计算函数: 无 (输入参数)")

def main():
    """主演示函数"""
    print("🎨 ArchDash 增强的依赖关系和计算过程演示")
    print("=" * 60)
    
    try:
        # 1. 创建演示图
        nodes = create_demo_graph()
        
        # 2. 执行计算
        perform_calculation_cascade()
        
        # 3. 分析依赖关系
        demonstrate_dependency_analysis()
        
        print("\n" + "=" * 60)
        print("✅ 演示完成!")
        print("\n📝 功能说明:")
        print("1. 🔗 依赖关系标签页 - 查看完整的参数依赖网络")
        print("2. ⚙️ 计算流程标签页 - 可视化计算执行过程")
        print("3. 📈 实时分析标签页 - 分析参数敏感性和影响范围")
        print("\n🌐 在浏览器中访问 http://localhost:8051 查看可视化界面")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 