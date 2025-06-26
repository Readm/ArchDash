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

from app import create_example_soc_graph, app, graph, layout_manager, id_mapper, IDMapper, ColumnManager
from models import CalculationGraph, CanvasLayoutManager, GridPosition, Node, Parameter
from dash.testing.application_runners import import_app
from dash.testing.composite import DashComposite


class TestExampleFeature:
    """测试示例计算图功能"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        import app
        app.graph = CalculationGraph()
        app.layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=10)
        app.id_mapper = IDMapper()
        app.graph.set_layout_manager(app.layout_manager)
        app.column_manager = ColumnManager(app.layout_manager)
    
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
        import app
        result = create_example_soc_graph()
        
        # 验证全局图对象
        assert len(app.graph.nodes) == 9, "计算图应该包含9个节点"
        
        # 验证节点名称
        expected_node_names = {
            "工艺技术", "CPU核心", "缓存系统", "内存系统", 
            "功耗分析", "性能分析", "热设计", "成本分析", "能效分析"
        }
        
        actual_node_names = {node.name for node in app.graph.nodes.values()}
        assert actual_node_names == expected_node_names, f"节点名称不匹配: 期望{expected_node_names}, 实际{actual_node_names}"
        
        # 验证每个节点都有参数
        for node in app.graph.nodes.values():
            assert len(node.parameters) > 0, f"节点 {node.name} 应该有参数"
    
    def test_example_graph_parameters_count(self):
        """测试各节点的参数数量"""
        import app
        result = create_example_soc_graph()
        
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
        
        for node in app.graph.nodes.values():
            expected_count = expected_params_count[node.name]
            actual_count = len(node.parameters)
            assert actual_count == expected_count, f"节点 {node.name} 期望{expected_count}个参数，实际有{actual_count}个"
    
    def test_example_graph_dependencies(self):
        """测试参数依赖关系"""
        import app
        result = create_example_soc_graph()
        
        # 验证有依赖关系的参数数量
        params_with_deps = 0
        total_deps = 0
        
        for node in app.graph.nodes.values():
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
        import app
        result = create_example_soc_graph()
        
        # 验证布局管理器状态
        assert app.layout_manager.cols == 3, "布局应该是3列"
        assert app.layout_manager.rows >= 3, "布局应该至少有3行"
        
        # 验证所有节点都已放置
        placed_nodes = len(app.layout_manager.node_positions)
        assert placed_nodes == 9, f"应该放置9个节点，实际放置了{placed_nodes}个"
        
        # 验证ID映射器
        assert len(app.id_mapper._node_mapping) == 9, "ID映射器应该包含9个节点映射"
    
    def test_example_graph_parameter_values(self):
        """测试参数的初始值和单位"""
        import app
        result = create_example_soc_graph()
        
        # 验证一些关键参数的值和单位
        process_node = None
        for node in app.graph.nodes.values():
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
        """测试数据流动和计算顺序"""
        import app
        result = create_example_soc_graph()
        
        # 找到工艺技术节点
        process_node = None
        for node in app.graph.nodes.values():
            if node.name == "工艺技术":
                process_node = node
                break
        
        assert process_node is not None, "应该找到工艺技术节点"
        
        # 修改工艺节点的电压参数
        voltage_param = None
        for param in process_node.parameters:
            if param.name == "电压":
                voltage_param = param
                break
        
        assert voltage_param is not None, "应该找到电压参数"
        
        # 修改电压值，触发依赖计算
        old_voltage = voltage_param.value
        voltage_param.value = 1.0
        
        # 验证依赖参数是否更新
        cpu_node = None
        for node in app.graph.nodes.values():
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
        assert max_freq_param.value != 3.2, "最大频率应该已经更新"
    
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

    def test_example_button_callback_exists(self):
        """测试示例按钮的回调函数是否存在"""
        import app
        from app import load_example_soc_graph
        import dash
        
        # 检查是否存在加载示例图的函数
        assert callable(load_example_soc_graph), "应该存在加载示例图的函数"
        
        # 测试无点击时的行为
        try:
            result = load_example_soc_graph(None)
            pytest.fail("n_clicks=None时应该抛出PreventUpdate异常")
        except dash.exceptions.PreventUpdate:
            # 这是正常的，因为这是Dash的标准行为
            pass
        except Exception as e:
            pytest.fail(f"回调执行失败: {e}")
        
        # 测试有点击时的行为
        try:
            result = load_example_soc_graph(1)
            assert isinstance(result, tuple), "回调应该返回一个元组（canvas和message）"
            assert len(result) == 2, "回调应该返回两个值"
            
            canvas, message = result
            assert canvas is not None, "canvas不应该为None"
            assert message is not None, "message不应该为None"
            
        except dash.exceptions.PreventUpdate:
            pytest.fail("n_clicks=1时不应该抛出PreventUpdate异常")
        except Exception as e:
            pytest.fail(f"回调执行失败: {e}")


class TestExampleFeatureIntegration:
    """测试示例功能的集成测试"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        import app
        app.graph = CalculationGraph()
        app.layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=10)
        app.id_mapper = IDMapper()
        app.graph.set_layout_manager(app.layout_manager)
        app.column_manager = ColumnManager(app.layout_manager)
    
    def test_example_creates_valid_graph_state(self):
        """测试示例创建的图状态是否有效"""
        import app
        # 创建示例
        result = create_example_soc_graph()
        
        # 验证图状态
        assert app.graph is not None, "全局图对象应该存在"
        assert app.layout_manager is not None, "布局管理器应该存在"
        assert app.id_mapper is not None, "ID映射器应该存在"
        
        # 验证图的完整性
        total_nodes = len(app.graph.nodes)
        total_mapped_nodes = len(app.id_mapper._node_mapping)
        total_placed_nodes = len(app.layout_manager.node_positions)
        
        assert total_nodes == total_mapped_nodes == total_placed_nodes == 9, \
            f"节点数量不一致: 图中{total_nodes}, 映射{total_mapped_nodes}, 布局{total_placed_nodes}"


class TestExampleFeaturePerformance:
    """测试示例功能的性能"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        import app
        app.graph = CalculationGraph()
        app.layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=10)
        app.id_mapper = IDMapper()
        app.graph.set_layout_manager(app.layout_manager)
        app.column_manager = ColumnManager(app.layout_manager)
    
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
        import app
        import time
        
        result = create_example_soc_graph()
        
        # 测试重新计算所有参数的性能
        start_time = time.time()
        
        calculation_count = 0
        for node in app.graph.nodes.values():
            for param in node.parameters:
                if hasattr(param, 'calculation_func') and param.calculation_func:
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

    def test_memory_usage(self):
        """测试示例图的内存使用情况"""
        import psutil
        import os
        import gc
        
        # 强制进行垃圾回收
        gc.collect()
        
        # 获取初始内存使用
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 创建示例图
        result = create_example_soc_graph()
        
        # 再次强制垃圾回收
        gc.collect()
        
        # 获取创建后的内存使用
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 内存增加不应超过10MB（考虑到示例图的规模）
        assert memory_increase < 10 * 1024 * 1024, f"内存使用增加过多: {memory_increase / 1024 / 1024:.2f}MB"

    def test_concurrent_calculations(self):
        """测试并发计算性能"""
        import app
        import time
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        result = create_example_soc_graph()
        
        # 获取所有可计算的参数
        calc_params = []
        for node in app.graph.nodes.values():
            for param in node.parameters:
                if hasattr(param, 'calculation_func') and param.calculation_func:
                    calc_params.append(param)
        
        def calculate_param(param):
            try:
                param.calculate()
                return True
            except Exception as e:
                return False
        
        start_time = time.time()
        
        # 使用线程池并发计算
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(calculate_param, param) for param in calc_params]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        # 验证所有计算都成功
        assert all(results), "并发计算中有失败的计算"
        # 并发计算应该比串行计算快
        assert concurrent_time < 1.0, f"并发计算时间过长: {concurrent_time:.2f}秒"

    def test_stress_parameter_updates(self):
        """测试参数频繁更新的性能"""
        import app
        import time
        import random
        
        result = create_example_soc_graph()
        
        # 获取工艺技术节点的参数
        process_node = None
        for node in app.graph.nodes.values():
            if node.name == "工艺技术":
                process_node = node
                break
        
        assert process_node is not None
        
        # 获取电压参数
        voltage_param = None
        for param in process_node.parameters:
            if param.name == "电压":
                voltage_param = param
                break
        
        assert voltage_param is not None
        
        start_time = time.time()
        update_count = 100
        
        # 快速更新参数多次
        for _ in range(update_count):
            # 在0.7V到1.2V之间随机变化电压
            new_voltage = random.uniform(0.7, 1.2)
            voltage_param.value = new_voltage
            
            # 验证依赖参数是否正确更新
            for node in app.graph.nodes.values():
                for param in node.parameters:
                    if hasattr(param, 'calculation_func') and param.calculation_func:
                        assert param.value is not None, f"参数 {param.name} 更新后值为None"
        
        end_time = time.time()
        update_time = end_time - start_time
        
        # 平均每次更新应该在10ms以内
        assert update_time / update_count < 0.01, f"参数更新性能过低: 平均{(update_time/update_count)*1000:.2f}ms/次"


class TestExampleFeatureErrorStates:
    """测试示例功能的错误状态处理"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        import app
        app.graph = CalculationGraph()
        app.layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=10)
        app.id_mapper = IDMapper()
        app.graph.set_layout_manager(app.layout_manager)
        app.column_manager = ColumnManager(app.layout_manager)
    
    def test_invalid_parameter_values(self):
        """测试参数值的有效性验证"""
        import app
        result = create_example_soc_graph()
        
        # 获取工艺技术节点
        process_node = None
        for node in app.graph.nodes.values():
            if node.name == "工艺技术":
                process_node = node
                break
        
        assert process_node is not None, "应该能找到工艺技术节点"
        
        # 测试电压参数
        voltage_param = None
        for param in process_node.parameters:
            if param.name == "电压":
                voltage_param = param
                break
        
        assert voltage_param is not None, "应该能找到电压参数"
        
        # 记录原始值
        original_value = voltage_param.value
        original_confidence = voltage_param.confidence
        
        try:
            # 测试设置正常值
            voltage_param.value = 1.2
            assert voltage_param.value == 1.2, "应该能设置正常的电压值"
            assert voltage_param.confidence > 0, "置信度应该大于0"
            
            # 测试设置边界值
            voltage_param.value = 0.1
            assert voltage_param.value == 0.1, "应该能设置较低的电压值"
            
            voltage_param.value = 2.0
            assert voltage_param.value == 2.0, "应该能设置较高的电压值"
            
        finally:
            # 恢复原始值
            voltage_param.value = original_value
            voltage_param.confidence = original_confidence
    
    def test_missing_dependencies(self):
        """测试参数依赖关系检查"""
        import app
        result = create_example_soc_graph()
        
        # 获取功耗分析节点
        power_node = None
        for node in app.graph.nodes.values():
            if node.name == "功耗分析":
                power_node = node
                break
        
        assert power_node is not None, "应该能找到功耗分析节点"
        
        # 获取CPU功耗参数
        cpu_power_param = None
        for param in power_node.parameters:
            if param.name == "CPU功耗":
                cpu_power_param = param
                break
        
        assert cpu_power_param is not None, "应该能找到CPU功耗参数"
        
        # 验证依赖关系
        assert len(cpu_power_param.dependencies) == 3, "CPU功耗应该有3个依赖参数"
        
        # 验证依赖参数的存在性
        dependency_names = ["最大频率", "电压", "核心数量"]
        for dep, expected_name in zip(cpu_power_param.dependencies, dependency_names):
            assert dep is not None, f"依赖参数 {expected_name} 不应为None"
            assert dep.name == expected_name, f"依赖参数名称应为 {expected_name}"
            
        # 验证计算函数存在
        assert cpu_power_param.calculation_func is not None, "应该有计算函数"
        
        # 验证计算结果
        try:
            result = cpu_power_param.calculate()
            assert result > 0, "CPU功耗应该大于0"
            assert cpu_power_param.confidence > 0, "计算结果的置信度应该大于0"
        except Exception as e:
            pytest.fail(f"计算失败: {e}")
    
    def test_circular_dependencies(self):
        """测试参数间的依赖关系是否合理（无循环依赖）"""
        import app
        result = create_example_soc_graph()
        
        def find_circular_dependencies(param, visited=None, path=None):
            """递归检查是否存在循环依赖"""
            if visited is None:
                visited = []
            if path is None:
                path = []
            
            if param in path:
                return path[path.index(param):]
            
            if param in visited:
                return None
            
            visited.append(param)
            path.append(param)
            
            for dep in param.dependencies:
                cycle = find_circular_dependencies(dep, visited, path)
                if cycle:
                    return cycle
            
            path.pop()
            return None
        
        # 检查所有计算参数
        for node in app.graph.nodes.values():
            for param in node.parameters:
                if param.calculation_func and param.dependencies:
                    cycle = find_circular_dependencies(param)
                    assert cycle is None, f"参数 {param.name} 存在循环依赖: {' -> '.join(p.name for p in cycle if cycle)}"
        
        # 特别检查一些关键的依赖链
        # 1. 功耗链：CPU频率 -> CPU功耗 -> 总功耗
        power_chain = []
        for node in app.graph.nodes.values():
            if node.name == "功耗分析":
                for param in node.parameters:
                    if param.name == "总功耗":
                        power_chain.append(param)
                        # 验证其依赖中包含CPU功耗
                        cpu_power = next((dep for dep in param.dependencies if dep.name == "CPU功耗"), None)
                        assert cpu_power is not None, "总功耗应该依赖于CPU功耗"
                        power_chain.append(cpu_power)
        
        assert len(power_chain) > 0, "应该能找到功耗相关的参数链"
        
        # 2. 性能链：工艺 -> 频率 -> 性能
        performance_chain = []
        for node in app.graph.nodes.values():
            if node.name == "性能分析":
                for param in node.parameters:
                    if param.name == "单核性能":
                        performance_chain.append(param)
                        # 验证其依赖中包含最大频率
                        max_freq = next((dep for dep in param.dependencies if dep.name == "最大频率"), None)
                        assert max_freq is not None, "单核性能应该依赖于最大频率"
                        performance_chain.append(max_freq)
        
        assert len(performance_chain) > 0, "应该能找到性能相关的参数链"
    
    def test_calculation_errors(self):
        """测试计算错误的处理"""
        import app
        result = create_example_soc_graph()
        
        # 获取CPU核心节点
        cpu_node = None
        for node in app.graph.nodes.values():
            if node.name == "CPU核心":
                cpu_node = node
                break
        
        assert cpu_node is not None, "应该能找到CPU核心节点"
        
        # 获取最大频率参数
        max_freq_param = None
        for param in cpu_node.parameters:
            if param.name == "最大频率":
                max_freq_param = param
                break
        
        assert max_freq_param is not None, "应该能找到最大频率参数"
        assert max_freq_param.calculation_func is not None, "应该有计算函数"
        
        # 保存原始计算函数
        original_calc_func = max_freq_param.calculation_func
        
        try:
            # 设置一个会导致错误的计算函数
            max_freq_param.calculation_func = """
# 这是一个会导致错误的计算函数
result = 1/0  # 除以零错误
"""
            # 尝试计算，应该捕获到错误
            try:
                max_freq_param.calculate()
                pytest.fail("应该抛出计算错误")
            except ValueError as e:
                assert "division by zero" in str(e), "应该包含原始错误信息"
            
            # 设置另一个错误的计算函数（语法错误）
            max_freq_param.calculation_func = """
# 这是一个语法错误的计算函数
result = 未定义的变量
"""
            # 尝试计算，应该捕获到错误
            try:
                max_freq_param.calculate()
                pytest.fail("应该抛出计算错误")
            except ValueError as e:
                assert "未定义的变量" in str(e), "应该包含原始错误信息"
            
        finally:
            # 恢复原始计算函数
            max_freq_param.calculation_func = original_calc_func
            
        # 验证恢复后可以正常计算
        try:
            result = max_freq_param.calculate()
            assert result > 0, "恢复后应该能正常计算"
            assert max_freq_param.confidence > 0, "恢复后置信度应该大于0"
        except Exception as e:
            pytest.fail(f"恢复后计算失败: {e}")
    
    def test_invalid_graph_modifications(self):
        """测试图结构修改的合法性"""
        import app
        result = create_example_soc_graph()
        
        # 获取CPU核心和功耗分析节点
        cpu_node = None
        power_node = None
        cache_node = None
        for node in app.graph.nodes.values():
            if node.name == "CPU核心":
                cpu_node = node
            elif node.name == "功耗分析":
                power_node = node
            elif node.name == "缓存系统":
                cache_node = node
        
        assert cpu_node is not None, "应该能找到CPU核心节点"
        assert power_node is not None, "应该能找到功耗分析节点"
        assert cache_node is not None, "应该能找到缓存系统节点"
        
        # 获取CPU功耗参数和总缓存参数
        cpu_power_param = None
        total_cache_param = None
        for param in power_node.parameters:
            if param.name == "CPU功耗":
                cpu_power_param = param
                break
        for param in cache_node.parameters:
            if param.name == "总缓存":
                total_cache_param = param
                break
        
        assert cpu_power_param is not None, "应该能找到CPU功耗参数"
        assert total_cache_param is not None, "应该能找到总缓存参数"
        
        # 保存原始状态
        original_graph_nodes = list(app.graph.nodes.keys())
        original_power_deps = list(cpu_power_param.dependencies)
        original_cache_deps = list(total_cache_param.dependencies)
        
        try:
            # 1. 测试删除有依赖关系的节点
            # 首先清理所有依赖于CPU核心节点参数的依赖关系
            for node in app.graph.nodes.values():
                for param in node.parameters:
                    new_deps = []
                    for dep in param.dependencies:
                        # 检查依赖参数是否属于要删除的节点
                        found_in_deleted = False
                        for cpu_param in cpu_node.parameters:
                            if dep.name == cpu_param.name and dep.value == cpu_param.value:
                                found_in_deleted = True
                                break
                        if not found_in_deleted:
                            new_deps.append(dep)
                    param.dependencies = new_deps
            
            # 然后删除节点
            app.graph.remove_node(cpu_node)
            
            # 验证节点被删除
            assert cpu_node.id not in app.graph.nodes, "节点应该被成功删除"
            
            # 验证相关依赖被清理
            for node in app.graph.nodes.values():
                for param in node.parameters:
                    for dep in param.dependencies:
                        # 检查依赖参数是否属于已删除的节点
                        found_in_deleted = False
                        for cpu_param in cpu_node.parameters:
                            if dep.name == cpu_param.name and dep.value == cpu_param.value:
                                found_in_deleted = True
                                break
                        assert not found_in_deleted, f"参数 {param.name} 不应该依赖于已删除节点的参数 {dep.name}"
            
            # 2. 测试添加新节点
            from models import Node, Parameter
            new_node = Node(name="测试节点", description="测试用节点")
            new_param = Parameter("测试参数", 1.0, "单位", description="测试用参数")
            new_node.add_parameter(new_param)
            
            app.graph.add_node(new_node)
            assert new_node.id in app.graph.nodes, "新节点应该被成功添加"
            
        finally:
            # 恢复原始状态
            app.graph = CalculationGraph()
            app.layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=10)
            app.id_mapper = IDMapper()
            app.graph.set_layout_manager(app.layout_manager)
            app.column_manager = ColumnManager(app.layout_manager)
            create_example_soc_graph()


class TestExampleFeatureDataFlow:
    """测试示例功能的数据流动"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        import app
        app.graph = CalculationGraph()
        app.layout_manager = CanvasLayoutManager(initial_cols=3, initial_rows=10)
        app.id_mapper = IDMapper()
        app.graph.set_layout_manager(app.layout_manager)
        app.column_manager = ColumnManager(app.layout_manager)
    
    def test_complex_calculation_chain(self):
        """测试复杂的计算链"""
        import app
        result = create_example_soc_graph()
        
        # 获取相关节点
        nodes = {}
        for node in app.graph.nodes.values():
            nodes[node.name] = node
        
        # 测试工艺->CPU->功耗->热设计->能效的计算链
        # 1. 工艺技术影响
        process_node = nodes["工艺技术"]
        voltage_param = next(p for p in process_node.parameters if p.name == "电压")
        original_voltage = voltage_param.value
        
        try:
            # 改变电压，观察影响
            voltage_param.value = original_voltage * 1.2  # 增加20%电压
            
            # 检查CPU最大频率的变化
            cpu_node = nodes["CPU核心"]
            max_freq_param = next(p for p in cpu_node.parameters if p.name == "最大频率")
            max_freq = max_freq_param.calculate()
            assert max_freq > 0, "最大频率应该大于0"
            
            # 检查功耗的变化
            power_node = nodes["功耗分析"]
            cpu_power_param = next(p for p in power_node.parameters if p.name == "CPU功耗")
            total_power_param = next(p for p in power_node.parameters if p.name == "总功耗")
            
            cpu_power = cpu_power_param.calculate()
            total_power = total_power_param.calculate()
            assert cpu_power > 0, "CPU功耗应该大于0"
            assert total_power > cpu_power, "总功耗应该大于CPU功耗"
            
            # 检查热设计的影响
            thermal_node = nodes["热设计"]
            junction_temp_param = next(p for p in thermal_node.parameters if p.name == "结温")
            junction_temp = junction_temp_param.calculate()
            assert junction_temp > 25, "结温应该高于环境温度(25°C)"
            
            # 检查能效分析
            efficiency_node = nodes["能效分析"]
            perf_power_ratio_param = next(p for p in efficiency_node.parameters if p.name == "性能功耗比")
            perf_power_ratio = perf_power_ratio_param.calculate()
            assert perf_power_ratio > 0, "性能功耗比应该大于0"
            
        finally:
            # 恢复原始值
            voltage_param.value = original_voltage
            
        # 测试缓存系统的计算链
        cache_node = nodes["缓存系统"]
        l3_cache_param = next(p for p in cache_node.parameters if p.name == "L3缓存")
        total_cache_param = next(p for p in cache_node.parameters if p.name == "总缓存")
        
        original_l3 = l3_cache_param.value
        try:
            # 改变L3缓存大小
            l3_cache_param.value = original_l3 * 2  # 翻倍L3缓存
            
            # 检查总缓存的变化
            total_cache = total_cache_param.calculate()
            assert total_cache > 0, "总缓存应该大于0"
            
            # 检查性能的影响
            perf_node = nodes["性能分析"]
            single_core_param = next(p for p in perf_node.parameters if p.name == "单核性能")
            single_core_perf = single_core_param.calculate()
            assert single_core_perf > 0, "单核性能应该大于0"
            
        finally:
            # 恢复原始值
            l3_cache_param.value = original_l3
    
    def test_parameter_update_propagation(self):
        """测试参数更新的传播"""
        import app
        result = create_example_soc_graph()
        
        # 获取相关节点
        nodes = {}
        for node in app.graph.nodes.values():
            nodes[node.name] = node
        
        # 测试工艺参数变化的传播
        process_node = nodes["工艺技术"]
        voltage_param = next(p for p in process_node.parameters if p.name == "电压")
        original_voltage = voltage_param.value
        
        # 记录所有计算参数的初始值
        initial_values = {}
        for node in app.graph.nodes.values():
            for param in node.parameters:
                if param.calculation_func:
                    initial_values[f"{node.name}.{param.name}"] = param.calculate()
        
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
                node = nodes[node_name]
                param = next(p for p in node.parameters if p.name == param_name)
                new_value = param.calculate()
                initial_value = initial_values[f"{node_name}.{param_name}"]
                assert new_value != initial_value, f"参数 {node_name}.{param_name} 应该因电压变化而更新"
                assert param.confidence > 0, f"参数 {node_name}.{param_name} 的置信度应该大于0"
        
        finally:
            # 恢复原始值
            voltage_param.value = original_voltage
        
        # 测试缓存参数变化的传播
        cache_node = nodes["缓存系统"]
        l3_cache_param = next(p for p in cache_node.parameters if p.name == "L3缓存")
        original_l3 = l3_cache_param.value
        
        try:
            # 改变L3缓存大小
            l3_cache_param.value = original_l3 * 2  # 翻倍L3缓存
            
            # 检查受影响的参数
            affected_cache_params = [
                ("缓存系统", "总缓存"),
                ("功耗分析", "缓存功耗"),
                ("功耗分析", "总功耗"),
                ("性能分析", "单核性能"),
                ("性能分析", "多核性能"),
                ("能效分析", "性能功耗比")
            ]
            
            for node_name, param_name in affected_cache_params:
                node = nodes[node_name]
                param = next(p for p in node.parameters if p.name == param_name)
                new_value = param.calculate()
                initial_value = initial_values[f"{node_name}.{param_name}"]
                assert new_value != initial_value, f"参数 {node_name}.{param_name} 应该因缓存变化而更新"
                assert param.confidence > 0, f"参数 {node_name}.{param_name} 的置信度应该大于0"
        
        finally:
            # 恢复原始值
            l3_cache_param.value = original_l3
    
    def test_calculation_order_validation(self):
        """测试计算顺序的正确性"""
        import app
        result = create_example_soc_graph()
        
        # 获取所有节点
        nodes = {}
        for node in app.graph.nodes.values():
            nodes[node.name] = node
        
        # 定义预期的计算顺序关系
        expected_order = {
            "工艺技术": [],  # 工艺技术不依赖其他节点
            "CPU核心": ["工艺技术"],  # CPU核心依赖工艺技术（电压）
            "缓存系统": ["CPU核心"],  # 缓存系统依赖CPU核心（核心数量）
            "内存系统": [],  # 内存系统是独立的
            "功耗分析": ["工艺技术", "CPU核心", "缓存系统", "内存系统"],  # 功耗分析依赖工艺、CPU、缓存和内存
            "性能分析": ["CPU核心", "缓存系统"],  # 性能分析依赖CPU和缓存
            "热设计": ["工艺技术", "功耗分析"],  # 热设计依赖工艺和功耗
            "成本分析": ["工艺技术", "缓存系统"],  # 成本分析依赖工艺和缓存
            "能效分析": ["性能分析", "功耗分析", "成本分析"]  # 能效分析依赖性能、功耗和成本
        }
        
        # 验证每个节点的依赖关系
        for node_name, expected_deps in expected_order.items():
            node = nodes[node_name]
            actual_deps = set()
            
            # 收集所有参数的依赖节点
            for param in node.parameters:
                if param.calculation_func and param.dependencies:
                    for dep in param.dependencies:
                        dep_node = None
                        # 查找依赖参数所属的节点
                        for n in app.graph.nodes.values():
                            if dep in n.parameters:
                                dep_node = n
                                break
                        if dep_node and dep_node.name != node.name:  # 排除自身依赖
                            actual_deps.add(dep_node.name)
            
            # 验证依赖关系
            for expected_dep in expected_deps:
                assert expected_dep in actual_deps, \
                    f"{node_name} 应该依赖于 {expected_dep}"
            
            # 验证没有意外的依赖
            for actual_dep in actual_deps:
                assert actual_dep in expected_deps, \
                    f"{node_name} 不应该依赖于 {actual_dep}"
    
    def test_parameter_value_consistency(self):
        """测试参数值的一致性"""
        import app
        result = create_example_soc_graph()
        
        # 获取所有节点
        nodes = {}
        for node in app.graph.nodes.values():
            nodes[node.name] = node
        
        # 定义需要验证一致性的参数组
        consistency_groups = [
            {
                # 功耗相关参数
                "功耗分析.CPU功耗": lambda x: x > 0,
                "功耗分析.总功耗": lambda x: x > 0,
                "热设计.结温": lambda x: x > 25
            },
            {
                # 性能相关参数
                "CPU核心.最大频率": lambda x: 1.0 <= x <= 5.0,
                "性能分析.单核性能": lambda x: x > 0,
                "性能分析.多核性能": lambda x: x > 0
            }
        ]
        
        # 验证每组参数的一致性
        for group in consistency_groups:
            values = {}
            for param_path, validator in group.items():
                node_name, param_name = param_path.split('.')
                node = nodes[node_name]
                param = None
                for p in node.parameters:
                    if p.name == param_name:
                        param = p
                        break
                assert param is not None, f"未找到参数 {param_path}"
                
                # 计算参数值
                value = param.calculate()
                values[param_path] = value
                
                # 验证值的合理性
                assert validator(value), f"参数 {param_path} 的值 {value} 不在合理范围内"
            
            # 打印参数值（用于调试）
            print(f"\n参数组值：")
            for path, value in values.items():
                print(f"{path}: {value}")


def run_example_tests():
    """运行所有示例功能测试的便捷函数"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    # 直接运行测试
    run_example_tests() 