#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的示例计算图功能测试
专注于测试核心功能是否正常工作
"""

import pytest
import sys
import os
import app
from dash import callback
from models import CalculationGraph, CanvasLayoutManager
from session_graph import set_graph, get_graph
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_function():
    """每个测试函数执行前的设置"""
    # 创建新的计算图和布局管理器
    new_graph = CalculationGraph()
    layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=10)
    new_graph.set_layout_manager(layout_manager)
    # 设置为当前会话的图
    set_graph(new_graph)

def test_example_function_import():
    """测试能否正确导入示例函数"""
    try:
        from app import create_example_soc_graph
        assert callable(create_example_soc_graph), "create_example_soc_graph应该是可调用的函数"
        print("✅ 示例函数导入成功")
    except ImportError as e:
        pytest.fail(f"无法导入示例函数: {e}")

def test_example_function_execution():
    """测试示例函数是否能正常执行"""
    try:
        from app import create_example_soc_graph
        
        # 执行示例创建函数
        result = create_example_soc_graph()
        
        # 验证返回结果
        assert isinstance(result, dict), "函数应该返回字典"
        assert "nodes_created" in result, "结果应该包含nodes_created"
        assert "total_params" in result, "结果应该包含total_params"
        assert "calculated_params" in result, "结果应该包含calculated_params"
        
        print(f"✅ 示例函数执行成功: {result}")
        
        # 验证创建的数量是否合理
        assert result["nodes_created"] > 0, "应该创建至少1个节点"
        assert result["total_params"] > 0, "应该创建至少1个参数"
        assert result["calculated_params"] >= 0, "计算参数数量应该非负"
        
        print(f"✅ 创建了{result['nodes_created']}个节点，{result['total_params']}个参数，其中{result['calculated_params']}个是计算参数")
        
    except Exception as e:
        pytest.fail(f"示例函数执行失败: {e}")

def test_example_function_consistency():
    """测试示例函数的一致性（多次调用应该产生相同结果）"""
    try:
        from app import create_example_soc_graph
        
        # 第一次调用
        result1 = create_example_soc_graph()
        
        # 第二次调用
        result2 = create_example_soc_graph()
        
        # 验证结果一致性
        assert result1["nodes_created"] == result2["nodes_created"], "节点数量应该一致"
        assert result1["total_params"] == result2["total_params"], "参数数量应该一致"
        assert result1["calculated_params"] == result2["calculated_params"], "计算参数数量应该一致"
        
        print("✅ 示例函数多次调用结果一致")
        
    except Exception as e:
        pytest.fail(f"一致性测试失败: {e}")

def test_example_creates_valid_data():
    """测试示例创建的数据是否有效"""
    try:
        # 执行示例创建
        result = app.create_example_soc_graph()
        test_graph = result["graph"]
        
        # 验证图结构
        assert len(test_graph.nodes) > 0, "应该创建节点"
        
        # 验证节点有参数
        total_params = 0
        calc_params = 0
        for node in test_graph.nodes.values():
            total_params += len(node.parameters)
            for param in node.parameters:
                if param.calculation_func:
                    calc_params += 1
        
        assert total_params > 0, "应该有参数"
        print(f"✅ 验证通过: {len(test_graph.nodes)}个节点, {total_params}个参数, {calc_params}个计算参数")
        
        # 验证返回值与实际创建的一致
        assert result["nodes_created"] == len(test_graph.nodes), "返回的节点数应该与实际一致"
        assert result["total_params"] == total_params, "返回的参数数应该与实际一致"
        assert result["calculated_params"] == calc_params, "返回的计算参数数应该与实际一致"
        
    except Exception as e:
        pytest.fail(f"数据有效性测试失败: {e}")

def test_example_parameter_calculations():
    """测试示例参数的计算功能"""
    try:
        # 创建示例
        result = app.create_example_soc_graph()
        test_graph = result["graph"]
        
        # 测试计算功能
        calculation_tests = 0
        calculation_successes = 0
        
        for node in test_graph.nodes.values():
            for param in node.parameters:
                if param.calculation_func and param.dependencies:
                    calculation_tests += 1
                    try:
                        # 执行计算
                        calc_result = param.calculate()
                        assert calc_result is not None, f"参数 {param.name} 的计算结果不应为None"
                        calculation_successes += 1
                    except Exception as calc_error:
                        print(f"⚠️ 参数 {param.name} 计算失败: {calc_error}")
        
        print(f"✅ 计算测试: {calculation_successes}/{calculation_tests} 个参数计算成功")
        
        # 至少应该有一些计算参数能够成功计算
        if calculation_tests > 0:
            assert calculation_successes > 0, "至少应该有一些计算参数能够成功计算"
            success_rate = calculation_successes / calculation_tests
            assert success_rate >= 0.7, f"计算成功率应该至少70%，实际{success_rate:.1%}"
            print(f"✅ 计算成功率: {success_rate:.1%}")
        
    except Exception as e:
        pytest.fail(f"计算功能测试失败: {e}")

def test_example_performance():
    """测试示例创建的性能"""
    try:
        import time
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行示例创建
        result = app.create_example_soc_graph()
        
        # 计算执行时间
        execution_time = time.time() - start_time
        
        # 验证性能
        assert execution_time < 2.0, f"示例创建应该在2秒内完成，实际用时{execution_time:.2f}秒"
        print(f"✅ 性能测试通过: 创建用时{execution_time:.2f}秒")
        
    except Exception as e:
        pytest.fail(f"性能测试失败: {e}")

if __name__ == "__main__":
    print("🧪 运行示例功能简化测试...")
    
    # 手动运行每个测试
    tests = [
        test_example_function_import,
        test_example_function_execution,
        test_example_function_consistency,
        test_example_creates_valid_data,
        test_example_parameter_calculations,
        test_example_performance,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            print(f"\n📋 运行测试: {test_func.__name__}")
            test_func()
            print(f"✅ {test_func.__name__} 通过")
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} 失败: {e}")
            failed += 1
    
    print(f"\n📊 测试总结: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("🎉 所有测试通过！示例功能工作正常。")
    else:
        print(f"⚠️ 有 {failed} 个测试失败，需要检查。") 