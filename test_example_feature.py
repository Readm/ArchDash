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

from app import create_example_soc_graph, app, graph, layout_manager, id_mapper, IDMapper
from models import CalculationGraph, CanvasLayoutManager, GridPosition
from dash.testing.application_runners import import_app
from dash.testing.composite import DashComposite


class TestExampleFeature:
    """测试示例计算图功能"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        # 重置全局变量，确保测试隔离
        global graph, layout_manager, id_mapper
        graph = CalculationGraph()
        layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=10)
        id_mapper = IDMapper()
        graph.set_layout_manager(layout_manager)
    
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
        assert result["total_params"] == 26, f"期望总共26个参数，实际有{result['total_params']}个"
        assert result["calculated_params"] == 15, f"期望15个计算参数，实际有{result['calculated_params']}个"
    
    def test_example_graph_nodes_structure(self):
        """测试示例计算图的节点结构"""
        create_example_soc_graph()
        
        # 验证全局图对象
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
        create_example_soc_graph()
        
        # 期望的每个节点参数数量
        expected_params_count = {
            "工艺技术": 3,
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
        create_example_soc_graph()
        
        # 验证有依赖关系的参数数量
        params_with_deps = 0
        total_deps = 0
        
        for node in graph.nodes.values():
            for param in node.parameters:
                if param.dependencies:
                    params_with_deps += 1
                    total_deps += len(param.dependencies)
        
        assert params_with_deps == 15, f"期望15个参数有依赖关系，实际{params_with_deps}个"
        assert total_deps > 0, "应该有依赖关系存在"
        
        # 验证特定的依赖关系
        # 找到CPU核心节点的最大频率参数
        cpu_node = None
        for node in graph.nodes.values():
            if node.name == "CPU核心":
                cpu_node = node
                break
        
        assert cpu_node is not None, "应该找到CPU核心节点"
        
        # 找到最大频率参数
        max_freq_param = None
        for param in cpu_node.parameters:
            if param.name == "最大频率":
                max_freq_param = param
                break
        
        assert max_freq_param is not None, "应该找到最大频率参数"
        assert len(max_freq_param.dependencies) == 2, "最大频率参数应该有2个依赖"
    
    def test_example_graph_calculations(self):
        """测试参数计算功能"""
        create_example_soc_graph()
        
        # 验证计算函数存在
        calc_params = []
        for node in graph.nodes.values():
            for param in node.parameters:
                if param.calculation_func:
                    calc_params.append(param)
        
        assert len(calc_params) == 15, f"期望15个计算参数，实际{len(calc_params)}个"
        
        # 测试一个具体的计算
        # 找到总缓存参数并测试其计算
        cache_node = None
        for node in graph.nodes.values():
            if node.name == "缓存系统":
                cache_node = node
                break
        
        assert cache_node is not None, "应该找到缓存系统节点"
        
        total_cache_param = None
        for param in cache_node.parameters:
            if param.name == "总缓存":
                total_cache_param = param
                break
        
        assert total_cache_param is not None, "应该找到总缓存参数"
        assert total_cache_param.calculation_func is not None, "总缓存应该有计算函数"
        
        # 执行计算
        try:
            result = total_cache_param.calculate()
            assert isinstance(result, (int, float)), "计算结果应该是数值"
            assert result > 0, "总缓存大小应该大于0"
        except Exception as e:
            pytest.fail(f"计算总缓存时出错: {e}")
    
    def test_example_graph_layout(self):
        """测试布局管理"""
        create_example_soc_graph()
        
        # 验证布局管理器状态
        assert layout_manager.cols >= 4, "布局应该至少有4列"
        assert layout_manager.rows >= 3, "布局应该至少有3行"
        
        # 验证所有节点都已放置
        placed_nodes = len(layout_manager.node_positions)
        assert placed_nodes == 9, f"应该放置9个节点，实际放置了{placed_nodes}个"
        
        # 验证ID映射器
        assert len(id_mapper._node_mapping) == 9, "ID映射器应该包含9个节点映射"
    
    def test_example_graph_parameter_values(self):
        """测试参数值的合理性"""
        create_example_soc_graph()
        
        # 定义期望的参数值范围
        value_ranges = {
            "工艺节点": (1, 100),      # nm
            "电压": (0.1, 5.0),        # V
            "温度": (-50, 200),        # °C
            "基础频率": (0.1, 10.0),   # GHz
            "核心数量": (1, 128),      # 个
            "最大频率": (0.1, 15.0),   # GHz
            "总功耗": (1, 500),        # W
            "性能功耗比": (10, 1000),  # 分/W
        }
        
        for node in graph.nodes.values():
            for param in node.parameters:
                if param.name in value_ranges:
                    min_val, max_val = value_ranges[param.name]
                    assert min_val <= param.value <= max_val, \
                        f"参数 {param.name} 的值 {param.value} 超出合理范围 [{min_val}, {max_val}]"
    
    def test_example_graph_error_handling(self):
        """测试错误处理"""
        # 测试在异常情况下是否能正常处理
        
        # 保存原始状态
        original_graph = graph
        original_layout = layout_manager
        original_mapper = id_mapper
        
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
            pass
    
    def test_example_graph_data_flow(self):
        """测试数据流传播"""
        create_example_soc_graph()
        
        # 找到一个基础参数（工艺节点的电压）
        process_node = None
        for node in graph.nodes.values():
            if node.name == "工艺技术":
                process_node = node
                break
        
        assert process_node is not None, "应该找到工艺技术节点"
        
        voltage_param = None
        for param in process_node.parameters:
            if param.name == "电压":
                voltage_param = param
                break
        
        assert voltage_param is not None, "应该找到电压参数"
        
        # 记录初始值
        initial_value = voltage_param.value
        
        # 修改电压值
        new_voltage = initial_value * 1.1
        old_values = {}
        
        # 记录修改前的所有参数值
        for node in graph.nodes.values():
            for param in node.parameters:
                old_values[f"{node.name}.{param.name}"] = param.value
        
        # 修改电压值，这应该触发数据流传播
        voltage_param.value = new_voltage
        
        # 验证数据流传播
        changed_params = 0
        for node in graph.nodes.values():
            for param in node.parameters:
                key = f"{node.name}.{param.name}"
                if key in old_values and old_values[key] != param.value:
                    changed_params += 1
        
        # 应该有多个参数因为数据流传播而改变
        assert changed_params > 1, f"数据流传播应该影响多个参数，实际只影响了{changed_params}个"
    
    def test_example_graph_parameter_types(self):
        """测试参数类型和属性"""
        create_example_soc_graph()
        
        param_count = 0
        calc_param_count = 0
        
        for node in graph.nodes.values():
            for param in node.parameters:
                param_count += 1
                
                # 验证基本属性
                assert param.name is not None and param.name != "", "参数名称不能为空"
                assert param.unit is not None, "参数单位不能为None"
                assert isinstance(param.value, (int, float, str)), "参数值类型应该是数值或字符串"
                assert 0 <= param.confidence <= 1, f"参数 {param.name} 的置信度 {param.confidence} 应该在0-1之间"
                
                # 检查计算参数
                if param.calculation_func:
                    calc_param_count += 1
                    assert isinstance(param.calculation_func, str), "计算函数应该是字符串"
                    assert len(param.calculation_func.strip()) > 0, "计算函数不能为空"
                    
                    if param.dependencies:
                        assert len(param.dependencies) > 0, "有计算函数的参数通常应该有依赖"
        
        assert param_count == 26, f"总参数数应该是26，实际{param_count}"
        assert calc_param_count == 15, f"计算参数数应该是15，实际{calc_param_count}"


class TestExampleFeatureIntegration:
    """测试示例功能的集成测试"""
    
    def test_example_button_callback_exists(self):
        """测试示例按钮的回调函数是否存在"""
        # 检查app中是否有相关的回调函数
        callbacks = app.callback_map
        
        # 查找示例按钮相关的回调
        example_callback_found = False
        for callback_id, callback_func in callbacks.items():
            if "load-example-graph-button" in str(callback_id):
                example_callback_found = True
                break
        
        assert example_callback_found, "应该找到示例按钮的回调函数"
    
    def test_example_creates_valid_graph_state(self):
        """测试示例创建的图状态是否有效"""
        # 重置状态
        global graph, layout_manager, id_mapper
        graph = CalculationGraph()
        layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=10)
        id_mapper = IDMapper()
        graph.set_layout_manager(layout_manager)
        
        # 创建示例
        result = create_example_soc_graph()
        
        # 验证图状态
        assert graph is not None, "全局图对象应该存在"
        assert layout_manager is not None, "布局管理器应该存在"
        assert id_mapper is not None, "ID映射器应该存在"
        
        # 验证图的完整性
        total_nodes = len(graph.nodes)
        total_mapped_nodes = len(id_mapper._node_mapping)
        total_placed_nodes = len(layout_manager.node_positions)
        
        assert total_nodes == total_mapped_nodes == total_placed_nodes == 9, \
            f"节点数量不一致: 图中{total_nodes}, 映射{total_mapped_nodes}, 布局{total_placed_nodes}"


class TestExampleFeaturePerformance:
    """测试示例功能的性能"""
    
    def test_example_creation_performance(self):
        """测试示例创建的性能"""
        import time
        
        start_time = time.time()
        result = create_example_soc_graph()
        end_time = time.time()
        
        creation_time = end_time - start_time
        
        # 创建时间应该在合理范围内（比如5秒以内）
        assert creation_time < 5.0, f"示例创建时间过长: {creation_time:.2f}秒"
        
        # 验证创建成功
        assert result["nodes_created"] == 9, "性能测试中示例应该成功创建"
    
    def test_example_calculation_performance(self):
        """测试示例计算的性能"""
        import time
        
        create_example_soc_graph()
        
        # 测试重新计算所有参数的性能
        start_time = time.time()
        
        calculation_count = 0
        for node in graph.nodes.values():
            for param in node.parameters:
                if param.calculation_func:
                    try:
                        param.calculate()
                        calculation_count += 1
                    except Exception as e:
                        pytest.fail(f"参数 {param.name} 计算失败: {e}")
        
        end_time = time.time()
        calculation_time = end_time - start_time
        
        # 计算时间应该在合理范围内
        assert calculation_time < 2.0, f"计算时间过长: {calculation_time:.2f}秒"
        assert calculation_count == 15, f"应该执行15次计算，实际{calculation_count}次"


def run_example_tests():
    """运行所有示例功能测试的便捷函数"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    # 直接运行测试
    run_example_tests() 