#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试示例计算图功能
测试创建多核SoC示例计算图的各个方面
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_example_soc_graph, app, graph, layout_manager
from models import CalculationGraph, CanvasLayoutManager, GridPosition, Node, Parameter
from session_graph import set_graph, get_graph
from dash.testing.application_runners import import_app
from dash.testing.composite import DashComposite


class TestExampleFeature:
    """测试示例计算图功能"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        # 创建新的计算图和布局管理器
        new_graph = CalculationGraph()
        layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=10)
        new_graph.set_layout_manager(layout_manager)
        # 设置为当前会话的图
        set_graph(new_graph)
        app.graph = new_graph
        app.layout_manager = layout_manager
    
    def test_create_example_soc_graph_basic(self):
        """测试基本的示例计算图创建功能"""
        # 执行创建函数
        result = create_example_soc_graph()
        
        # 验证返回结果结构
        assert isinstance(result, dict)
        assert "nodes_created" in result
        assert "total_params" in result
        assert "calculated_params" in result
        
        # 验证创建的数量
        assert result["nodes_created"] == 9, f"期望创建9个节点，实际创建了{result['nodes_created']}个"
        assert result["total_params"] == 27, f"期望总共27个参数，实际有{result['total_params']}个"
        assert result["calculated_params"] == 15, f"期望15个计算参数，实际有{result['calculated_params']}个"
    
    def test_example_graph_nodes_structure(self):
        """测试示例计算图的节点结构"""
        result = create_example_soc_graph()
        graph = get_graph()
        
        # 验证图对象
        assert len(graph.nodes) == 9, "计算图应该包含9个节点"
        
        # 验证节点名称
        expected_node_names = {
            "工艺技术", "CPU核心", "缓存系统", "内存系统", 
            "功耗分析", "性能分析", "热设计", "成本分析", "能效分析"
        }
        
        actual_node_names = {node.name for node in graph.nodes.values()}
        assert actual_node_names == expected_node_names, f"节点名称不匹配: 期望{expected_node_names}, 实际{actual_node_names}"
        
        # 验证每个节点都有参数
        for node in graph.nodes.values():
            assert len(node.parameters) > 0, f"节点 {node.name} 应该有参数"
    
    def test_example_graph_parameters_count(self):
        """测试各节点的参数数量"""
        result = create_example_soc_graph()
        graph = get_graph()
        
        # 期望的每个节点参数数量
        expected_params_count = {
            "工艺技术": 4,  # 更新为4个参数
            "CPU核心": 3,
            "缓存系统": 4,
            "内存系统": 4,
            "功耗分析": 4,
            "性能分析": 2,
            "热设计": 2,
            "成本分析": 2,
            "能效分析": 2
        }
        
        for node in graph.nodes.values():
            expected_count = expected_params_count[node.name]
            actual_count = len(node.parameters)
            assert actual_count == expected_count, f"节点 {node.name} 期望{expected_count}个参数，实际有{actual_count}个"
    
    def test_example_graph_dependencies(self):
        """测试参数依赖关系"""
        result = create_example_soc_graph()
        graph = get_graph()
        
        # 验证有依赖关系的参数数量
        params_with_deps = 0
        total_deps = 0
        
        for node in graph.nodes.values():
            for param in node.parameters:
                if param.dependencies:
                    params_with_deps += 1
                    total_deps += len(param.dependencies)
        
        assert params_with_deps == 15, f"期望15个参数有依赖关系，实际{params_with_deps}个"
        assert total_deps > 20, f"依赖关系总数应该大于20，实际{total_deps}个"
    
    def test_example_graph_calculations(self):
        """测试参数计算功能"""
        import app
        result = create_example_soc_graph()
        
        # 验证计算函数存在
        calc_params = []
        for node in app.graph.nodes.values():
            for param in node.parameters:
                if param.calculation_func:
                    calc_params.append(param)
        
        assert len(calc_params) == 15, f"期望15个计算参数，实际{len(calc_params)}个"
        
        # 验证计算结果
        for param in calc_params:
            try:
                old_value = param.value
                param.calculate()
                assert param.value is not None, f"参数 {param.name} 计算结果为None"
                assert isinstance(param.value, (int, float, str)), f"参数 {param.name} 计算结果类型错误"
            except Exception as e:
                pytest.fail(f"参数 {param.name} 计算失败: {e}")
    
    def test_example_graph_layout(self):
        """测试布局管理"""
        result = create_example_soc_graph()
        graph = get_graph()
        layout_manager = graph.layout_manager
        
        # 验证布局管理器状态
        assert layout_manager.cols == 3, "布局应该是3列"
        assert layout_manager.rows >= 3, "布局应该至少有3行"
        
        # 验证所有节点都已放置
        placed_nodes = len(layout_manager.node_positions)
        assert placed_nodes == 9, f"应该放置9个节点，实际放置了{placed_nodes}个"
    
    def test_example_graph_parameter_values(self):
        """测试参数的初始值和单位"""
        result = create_example_soc_graph()
        graph = get_graph()
        
        # 获取工艺技术节点
        process_node = None
        for node in graph.nodes.values():
            if node.name == "工艺技术":
                process_node = node
                break
        
        assert process_node is not None, "应该找到工艺技术节点"
        
        # 验证工艺节点的参数
        param_values = {param.name: (param.value, param.unit) for param in process_node.parameters}
        assert param_values["工艺节点"] == (7, "nm"), "工艺节点参数不正确"
        assert param_values["电压"] == (0.8, "V"), "电压参数不正确"
        assert param_values["温度"] == (85, "°C"), "温度参数不正确"
        assert param_values["工艺厂商"] == ("TSMC", ""), "工艺厂商参数不正确"
    
    def test_example_graph_error_handling(self):
        """测试错误处理"""
        # 测试在异常情况下是否能正常处理
        
        # 保存原始状态
        original_graph = get_graph()
        original_layout = original_graph.layout_manager if original_graph else None
        
        try:
            # 测试重复创建
            result1 = create_example_soc_graph()
            result2 = create_example_soc_graph()
            
            # 两次创建的结果应该一致
            assert result1["nodes_created"] == result2["nodes_created"]
            assert result1["total_params"] == result2["total_params"]
            assert result1["calculated_params"] == result2["calculated_params"]
        
        except Exception as e:
            pytest.fail(f"重复创建示例图时出错: {e}")
        
        finally:
            # 恢复状态（如果需要）
            if original_graph:
                set_graph(original_graph)
    
    def test_example_graph_data_flow(self):
        """测试数据流动和计算顺序"""
        result = create_example_soc_graph()
        graph = get_graph()
        
        # 找到工艺技术节点
        process_node = None
        for node in graph.nodes.values():
            if node.name == "工艺技术":
                process_node = node
                break
        
        assert process_node is not None, "应该找到工艺技术节点"
        
        # 获取电压参数
        voltage_param = None
        for param in process_node.parameters:
            if param.name == "电压":
                voltage_param = param
                break
        
        assert voltage_param is not None, "应该找到电压参数"
        
        # 记录原始值
        original_voltage = voltage_param.value
        
        try:
            # 改变电压值
            voltage_param.value = original_voltage * 1.5  # 增加50%电压
            
            # 检查所有受影响的参数
            affected_params = [
                ("CPU核心", "最大频率"),
                ("功耗分析", "CPU功耗"),
                ("功耗分析", "总功耗"),
                ("热设计", "结温"),
                ("性能分析", "单核性能"),
                ("性能分析", "多核性能"),
                ("能效分析", "性能功耗比")
            ]
            
            for node_name, param_name in affected_params:
                node = None
                for n in graph.nodes.values():
                    if n.name == node_name:
                        node = n
                break
                assert node is not None, f"应该找到节点 {node_name}"
                
                param = None
                for p in node.parameters:
                    if p.name == param_name:
                        param = p
                        break
                assert param is not None, f"应该找到参数 {param_name}"
                
                # 计算新值
                new_value = param.calculate()
                assert new_value is not None, f"参数 {node_name}.{param_name} 计算结果不应为None"
                assert param.confidence > 0, f"参数 {node_name}.{param_name} 的置信度应该大于0"
        
        finally:
            # 恢复原始值
            voltage_param.value = original_voltage
    
    def test_example_graph_parameter_types(self):
        """测试参数类型的正确性"""
        import app
        result = create_example_soc_graph()
        
        # 统计不同类型的参数
        param_types = {"int": 0, "float": 0, "string": 0}
        total_params = 0
        
        for node in app.graph.nodes.values():
            for param in node.parameters:
                total_params += 1
                if hasattr(param, 'param_type'):
                    param_types[param.param_type] += 1
        
        assert total_params == 27, f"总参数数应该是27，实际{total_params}"
        assert param_types["int"] > 0, "应该有整数类型的参数"
        assert param_types["float"] > 0, "应该有浮点数类型的参数"
        assert param_types["string"] > 0, "应该有字符串类型的参数"


class TestExampleFeatureIntegration:
    """测试示例计算图功能的集成测试"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        # 创建新的计算图和布局管理器
        new_graph = CalculationGraph()
        layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=10)
        new_graph.set_layout_manager(layout_manager)
        # 设置为当前会话的图
        set_graph(new_graph)
    
    def test_example_creates_valid_graph_state(self):
        """测试示例创建的图状态是否有效"""
        # 创建示例
        result = create_example_soc_graph()
        graph = get_graph()
        
        # 验证图状态
        assert graph is not None, "全局图对象应该存在"
        assert graph.layout_manager is not None, "布局管理器应该存在"
        
        # 验证图的完整性
        total_nodes = len(graph.nodes)
        total_placed_nodes = len(graph.layout_manager.node_positions)
        
        assert total_nodes == total_placed_nodes == 9, \
            f"节点数量不一致: 图中{total_nodes}, 布局{total_placed_nodes}"


class TestExampleFeaturePerformance:
    """测试示例计算图功能的性能"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        # 创建新的计算图和布局管理器
        new_graph = CalculationGraph()
        layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=10)
        new_graph.set_layout_manager(layout_manager)
        # 设置为当前会话的图
        set_graph(new_graph)


class TestExampleFeatureErrorStates:
    """测试示例计算图功能的错误状态处理"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        # 创建新的计算图和布局管理器
        new_graph = CalculationGraph()
        layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=10)
        new_graph.set_layout_manager(layout_manager)
        # 设置为当前会话的图
        set_graph(new_graph)


class TestExampleFeatureDataFlow:
    """测试示例计算图功能的数据流"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        # 创建新的计算图和布局管理器
        new_graph = CalculationGraph()
        layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=10)
        new_graph.set_layout_manager(layout_manager)
        # 设置为当前会话的图
        set_graph(new_graph)


def run_example_tests():
    """运行所有示例功能测试的便捷函数"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    # 直接运行测试
    run_example_tests() 