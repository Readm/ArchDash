#!/usr/bin/env python3
"""
计算图文件操作测试脚本
测试保存和读取计算图文件的功能
"""

import os
import tempfile
from models import CalculationGraph, Node, Parameter, CanvasLayoutManager, GridPosition

def test_save_and_load_graph():
    """测试计算图的保存和加载功能"""
    print("🧪 开始测试计算图文件操作...")
    
    # 创建测试数据
    print("📝 创建测试计算图...")
    graph = CalculationGraph()
    layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=5)
    graph.set_layout_manager(layout_manager)
    
    # 创建节点1
    node1 = Node("测试节点1", "这是第一个测试节点")
    param1 = Parameter("输入参数", 10.0, "单位1", description="输入值")
    param2 = Parameter("计算参数", 0.0, "单位2", description="计算结果", 
                      calculation_func="result = dependencies[0].value * 2")
    param2.add_dependency(param1)
    
    node1.add_parameter(param1)
    node1.add_parameter(param2)
    graph.add_node(node1)
    
    # 创建节点2
    node2 = Node("测试节点2", "这是第二个测试节点")
    param3 = Parameter("输出参数", 0.0, "单位3", description="最终输出",
                      calculation_func="result = dependencies[0].value + 5")
    param3.add_dependency(param2)
    
    node2.add_parameter(param3)
    graph.add_node(node2)
    
    # 设置布局位置
    layout_manager.place_node(node1.id, GridPosition(0, 0))
    layout_manager.place_node(node2.id, GridPosition(1, 1))
    
    # 执行计算
    print("🔄 执行参数计算...")
    param2.calculate()
    param3.calculate()
    
    print(f"   输入参数: {param1.value} {param1.unit}")
    print(f"   计算参数: {param2.value} {param2.unit}")
    print(f"   输出参数: {param3.value} {param3.unit}")
    
    # 保存到临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        temp_path = temp_file.name
    
    print(f"💾 保存计算图到: {temp_path}")
    success = graph.save_to_file(temp_path, include_layout=True)
    
    if not success:
        print("❌ 保存失败！")
        assert False, "保存失败"
    
    # 验证文件存在
    if not os.path.exists(temp_path):
        print("❌ 保存的文件不存在！")
        assert False, "保存的文件不存在"
    
    print(f"✅ 文件保存成功，大小: {os.path.getsize(temp_path)} 字节")
    
    # 读取文件内容验证
    print("📖 验证保存的文件内容...")
    with open(temp_path, 'r', encoding='utf-8') as f:
        import json
        saved_data = json.load(f)
        
    print(f"   版本: {saved_data.get('version', '未知')}")
    print(f"   节点数: {len(saved_data.get('nodes', {}))}")
    print(f"   包含布局信息: {'layout' in saved_data}")
    
    # 加载计算图
    print("🔼 从文件加载计算图...")
    new_layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=5)
    loaded_graph = CalculationGraph.load_from_file(temp_path, new_layout_manager)
    
    if loaded_graph is None:
        print("❌ 加载失败！")
        assert False, "加载失败"
    
    # 验证加载的数据
    print("✅ 验证加载的计算图...")
    
    # 检查节点数量
    if len(loaded_graph.nodes) != len(graph.nodes):
        print(f"❌ 节点数量不匹配: 原始{len(graph.nodes)}, 加载{len(loaded_graph.nodes)}")
        assert False, f"节点数量不匹配: 原始{len(graph.nodes)}, 加载{len(loaded_graph.nodes)}"
    
    # 检查参数数量
    original_params = sum(len(node.parameters) for node in graph.nodes.values())
    loaded_params = sum(len(node.parameters) for node in loaded_graph.nodes.values())
    
    if original_params != loaded_params:
        print(f"❌ 参数数量不匹配: 原始{original_params}, 加载{loaded_params}")
        assert False, f"参数数量不匹配: 原始{original_params}, 加载{loaded_params}"
    
    # 检查布局信息
    if loaded_graph.layout_manager is None:
        print("❌ 布局管理器未正确加载")
        assert False, "布局管理器未正确加载"
    
    print(f"   节点数: {len(loaded_graph.nodes)}")
    print(f"   参数数: {loaded_params}")
    print(f"   布局节点数: {len(loaded_graph.layout_manager.node_positions)}")
    
    # 测试导出摘要
    print("📋 测试导出摘要功能...")
    summary = loaded_graph.export_summary()
    
    print(f"   摘要-总节点数: {summary['总节点数']}")
    print(f"   摘要-总参数数: {summary['总参数数']}")
    
    # 清理临时文件
    try:
        os.unlink(temp_path)
        print(f"🗑️ 已清理临时文件: {temp_path}")
    except Exception as e:
        print(f"⚠️ 清理临时文件失败: {e}")
    
    print("✅ 所有测试通过！")
    # 使用assert代替return来表示测试通过
    assert True

def test_error_handling():
    """测试错误处理"""
    print("\n🧪 测试错误处理...")
    
    # 测试加载不存在的文件
    print("📂 测试加载不存在的文件...")
    result = CalculationGraph.load_from_file("nonexistent_file.json")
    if result is not None:
        print("❌ 应该返回None但没有")
        assert False, "应该返回None但没有"
    print("✅ 正确处理不存在的文件")
    
    # 测试加载无效JSON
    print("📂 测试加载无效JSON文件...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        temp_file.write("invalid json content")
        temp_path = temp_file.name
    
    try:
        result = CalculationGraph.load_from_file(temp_path)
        if result is not None:
            print("❌ 应该返回None但没有")
            assert False, "应该返回None但没有"
        print("✅ 正确处理无效JSON文件")
    finally:
        os.unlink(temp_path)
    
    # 测试保存到无效路径
    print("💾 测试保存到无效路径...")
    graph = CalculationGraph()
    success = graph.save_to_file("/invalid/path/file.json")
    if success:
        print("❌ 应该失败但成功了")
        assert False, "应该失败但成功了"
    print("✅ 正确处理无效保存路径")
    
    print("✅ 错误处理测试通过！")
    # 使用assert代替return来表示测试通过
    assert True

if __name__ == "__main__":
    print("🚀 启动计算图文件操作测试")
    
    # 运行测试
    test1_passed = test_save_and_load_graph()
    test2_passed = test_error_handling()
    
    print(f"\n📊 测试结果:")
    print(f"   保存/加载测试: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"   错误处理测试: {'✅ 通过' if test2_passed else '❌ 失败'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 所有测试都通过了！计算图文件操作功能正常工作。")
        exit(0)
    else:
        print("\n💥 有测试失败，请检查实现。")
        exit(1) 