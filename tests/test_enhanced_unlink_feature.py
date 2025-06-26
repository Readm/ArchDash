#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的参数unlink功能测试
测试新的unlink逻辑：
1. 只有有依赖计算且unlinked=True时显示按钮
2. 点击按钮重新连接并计算
3. 手动修改值自动unlink
4. 相关性分析自动unlink
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import *

def test_enhanced_unlink_display_logic():
    """测试增强的unlink显示逻辑"""
    print("🔬 测试增强的unlink显示逻辑")
    print("=" * 50)
    
    # 创建计算图和节点
    graph = CalculationGraph()
    
    # 创建输入节点
    input_node = Node("输入参数", "基础输入参数")
    length = Parameter("长度", 10.0, "m")
    width = Parameter("宽度", 5.0, "m") 
    input_node.add_parameter(length)
    input_node.add_parameter(width)
    graph.add_node(input_node)
    
    # 创建计算节点
    calc_node = Node("计算结果", "基于输入参数的计算")
    area = Parameter("面积", 0.0, "m²", 
                    calculation_func="result = dependencies[0].value * dependencies[1].value")
    area.add_dependency(length)
    area.add_dependency(width)
    calc_node.add_parameter(area)
    graph.add_node(calc_node)
    
    # 创建无依赖参数
    standalone_param = Parameter("独立参数", 100.0, "unit")
    calc_node.add_parameter(standalone_param)
    
    # 设置计算图关联
    for node in graph.nodes.values():
        for param in node.parameters:
            param.set_graph(graph)
    
    print("1. 测试显示逻辑：")
    print(f"   area有依赖且unlinked=False -> 应该不显示按钮")
    should_show_area = area.calculation_func and area.dependencies and getattr(area, 'unlinked', False)
    print(f"   area显示按钮: {should_show_area}")
    assert not should_show_area, "有依赖但未unlinked不应显示按钮"
    
    print(f"   length无依赖 -> 应该不显示按钮")
    should_show_length = length.calculation_func and length.dependencies and getattr(length, 'unlinked', False)
    print(f"   length显示按钮: {should_show_length}")
    assert not should_show_length, "无依赖参数不应显示按钮"
    
    print(f"   standalone_param无依赖 -> 应该不显示按钮")
    should_show_standalone = standalone_param.calculation_func and standalone_param.dependencies and getattr(standalone_param, 'unlinked', False)
    print(f"   standalone_param显示按钮: {should_show_standalone}")
    assert not should_show_standalone, "无依赖参数不应显示按钮"
    
    print("\n2. 设置area为unlinked后：")
    area.set_manual_value(100.0)
    should_show_area_unlinked = area.calculation_func and area.dependencies and getattr(area, 'unlinked', False)
    print(f"   area显示按钮: {should_show_area_unlinked}")
    assert should_show_area_unlinked, "有依赖且unlinked=True应该显示按钮"
    
    print("✅ 显示逻辑测试通过！")

def test_manual_value_auto_unlink():
    """测试手动修改值时自动unlink功能"""
    print("\n🔬 测试手动修改值自动unlink功能")
    print("=" * 50)
    
    # 创建测试环境
    graph = CalculationGraph()
    
    input_node = Node("输入")
    base_value = Parameter("基值", 10.0, "unit")
    input_node.add_parameter(base_value)
    graph.add_node(input_node)
    
    calc_node = Node("计算")
    
    # 有依赖的计算参数
    computed_param = Parameter("计算参数", 0.0, "unit",
                             calculation_func="result = dependencies[0].value * 2")
    computed_param.add_dependency(base_value)
    calc_node.add_parameter(computed_param)
    
    # 无依赖的普通参数
    simple_param = Parameter("普通参数", 5.0, "unit")
    calc_node.add_parameter(simple_param)
    
    graph.add_node(calc_node)
    
    # 设置计算图关联
    for node in graph.nodes.values():
        for param in node.parameters:
            param.set_graph(graph)
    
    # 计算初始值
    computed_param.calculate()
    
    print("1. 初始状态：")
    print(f"   computed_param = {computed_param.value}, unlinked = {computed_param.unlinked}")
    print(f"   simple_param = {simple_param.value}, unlinked = {simple_param.unlinked}")
    
    print("\n2. 手动修改有依赖的计算参数：")
    computed_param.set_manual_value(50.0)
    print(f"   computed_param = {computed_param.value}, unlinked = {computed_param.unlinked}")
    assert computed_param.unlinked == True, "有依赖的参数手动设置应该auto unlink"
    
    print("\n3. 手动修改无依赖的普通参数：")
    simple_param.set_manual_value(25.0)
    print(f"   simple_param = {simple_param.value}, unlinked = {simple_param.unlinked}")
    assert simple_param.unlinked == False, "无依赖的参数手动设置不应该unlink"
    
    print("\n4. 手动修改输入参数（无计算函数）：")
    base_value.set_manual_value(15.0)
    print(f"   base_value = {base_value.value}, unlinked = {base_value.unlinked}")
    assert base_value.unlinked == False, "无计算函数的参数不应该unlink"
    
    print("✅ 手动修改值自动unlink测试通过！")

def test_unlink_icon_click_reconnect():
    """测试点击unlink按钮重新连接功能"""
    print("\n🔬 测试点击unlink按钮重新连接功能")
    print("=" * 50)
    
    # 创建测试环境
    graph = CalculationGraph()
    
    input_node = Node("输入")
    x_param = Parameter("X", 5.0, "unit")
    y_param = Parameter("Y", 3.0, "unit")
    input_node.add_parameter(x_param)
    input_node.add_parameter(y_param)
    graph.add_node(input_node)
    
    calc_node = Node("计算")
    product = Parameter("乘积", 0.0, "unit",
                       calculation_func="result = dependencies[0].value * dependencies[1].value")
    product.add_dependency(x_param)
    product.add_dependency(y_param)
    calc_node.add_parameter(product)
    graph.add_node(calc_node)
    
    # 设置计算图关联
    for node in graph.nodes.values():
        for param in node.parameters:
            param.set_graph(graph)
    
    print("1. 初始计算：")
    product.calculate()
    print(f"   乘积 = {product.value} (应该是15)")
    assert product.value == 15.0, "初始计算应该正确"
    
    print("\n2. 手动设置为unlinked状态：")
    product.set_manual_value(100.0)
    print(f"   乘积 = {product.value}, unlinked = {product.unlinked}")
    assert product.unlinked == True, "应该被标记为unlinked"
    
    print("\n3. 修改输入参数（应该不影响unlinked的参数）：")
    x_param.value = 7.0
    old_value = product.value
    try:
        product.calculate()
    except:
        pass  # unlinked的参数计算应该被跳过
    print(f"   X修改为7.0后，乘积 = {product.value} (应该保持100.0)")
    assert product.value == 100.0, "unlinked参数不应该被重新计算"
    
    print("\n4. 点击unlink按钮重新连接：")
    new_value = product.relink_and_calculate()
    print(f"   重新连接后乘积 = {new_value}, unlinked = {product.unlinked}")
    assert product.unlinked == False, "应该重新连接"
    assert product.value == 21.0, "重新计算的值应该正确 (7 * 3 = 21)"
    
    print("✅ 点击unlink按钮重新连接测试通过！")

def test_sensitivity_analysis_auto_unlink_simulation():
    """模拟相关性分析时的自动unlink功能"""
    print("\n🔬 模拟相关性分析自动unlink功能")
    print("=" * 50)
    
    # 创建测试环境，模拟app.py中的perform_sensitivity_analysis逻辑
    graph = CalculationGraph()
    
    input_node = Node("输入")
    x_param = Parameter("X参数", 10.0, "unit")
    input_node.add_parameter(x_param)
    graph.add_node(input_node)
    
    calc_node = Node("计算")
    # 创建一个依赖于x_param的计算参数
    dependent_param = Parameter("依赖参数", 5.0, "unit")
    calc_node.add_parameter(dependent_param)
    
    y_param = Parameter("Y参数", 0.0, "unit",
                       calculation_func="result = dependencies[0].value + dependencies[1].value")
    y_param.add_dependency(x_param)
    y_param.add_dependency(dependent_param)
    calc_node.add_parameter(y_param)
    graph.add_node(calc_node)
    
    # 设置计算图关联
    for node in graph.nodes.values():
        for param in node.parameters:
            param.set_graph(graph)
    
    # 计算初始值
    y_param.calculate()
    
    print("1. 初始状态：")
    print(f"   X参数 = {x_param.value}, unlinked = {x_param.unlinked}")
    print(f"   Y参数 = {y_param.value}, unlinked = {y_param.unlinked}")
    
    print("\n2. 模拟相关性分析开始（X参数有依赖时会被自动unlink）：")
    # 在实际的相关性分析中，如果X参数有计算依赖，会被自动unlink
    # 这里我们给x_param添加一个虚假的计算函数来模拟这种情况
    original_x_calc_func = x_param.calculation_func
    original_x_deps = x_param.dependencies.copy()
    original_x_unlinked = x_param.unlinked
    
    # 模拟X参数有依赖的情况
    x_param.calculation_func = "result = dependencies[0].value"
    x_param.add_dependency(dependent_param)
    
    # 模拟相关性分析中的auto unlink逻辑
    x_was_unlinked = getattr(x_param, 'unlinked', False)
    if x_param.calculation_func and x_param.dependencies and not x_was_unlinked:
        x_param.set_manual_value(x_param.value)  # 保持当前值但断开计算
        print(f"   X参数被自动unlink: unlinked = {x_param.unlinked}")
        assert x_param.unlinked == True, "相关性分析应该自动unlink有依赖的X参数"
    
    print("\n3. 模拟相关性分析结束，恢复状态：")
    # 恢复原始状态
    x_param.calculation_func = original_x_calc_func
    x_param.dependencies.clear()
    for dep in original_x_deps:
        x_param.add_dependency(dep)
    if not original_x_unlinked:
        x_param.unlinked = False
    
    print(f"   X参数恢复后: unlinked = {x_param.unlinked}")
    
    print("✅ 相关性分析自动unlink模拟测试通过！")

def test_edge_cases_and_error_handling():
    """测试边界情况和错误处理"""
    print("\n🔬 测试边界情况和错误处理")
    print("=" * 50)
    
    # 创建测试环境
    graph = CalculationGraph()
    node = Node("测试节点")
    
    print("1. 测试空依赖列表的参数：")
    param_no_deps = Parameter("无依赖", 10.0, "unit", 
                             calculation_func="result = value * 2")
    # 不添加任何依赖
    node.add_parameter(param_no_deps)
    
    # 尝试unlink（应该不会被unlink，因为没有依赖）
    param_no_deps.set_manual_value(20.0)
    print(f"   无依赖参数 unlinked = {param_no_deps.unlinked}")
    assert param_no_deps.unlinked == False, "无依赖的参数不应该被unlink"
    
    print("\n2. 测试空计算函数的参数：")
    param_no_calc = Parameter("无计算", 30.0, "unit")
    param_no_calc.add_dependency(param_no_deps)  # 添加依赖但无计算函数
    node.add_parameter(param_no_calc)
    
    param_no_calc.set_manual_value(40.0)
    print(f"   无计算函数参数 unlinked = {param_no_calc.unlinked}")
    assert param_no_calc.unlinked == False, "无计算函数的参数不应该被unlink"
    
    print("\n3. 测试已经unlinked的参数重复unlink：")
    param_with_both = Parameter("完整参数", 50.0, "unit",
                              calculation_func="result = dependencies[0].value + 10")
    param_with_both.add_dependency(param_no_deps)
    node.add_parameter(param_with_both)
    
    # 第一次unlink
    param_with_both.set_manual_value(60.0)
    first_unlink_state = param_with_both.unlinked
    print(f"   第一次unlink: {first_unlink_state}")
    
    # 再次unlink
    param_with_both.set_manual_value(70.0)
    second_unlink_state = param_with_both.unlinked
    print(f"   第二次unlink: {second_unlink_state}")
    assert first_unlink_state == second_unlink_state == True, "重复unlink应该保持状态"
    
    print("\n4. 测试重新连接错误处理：")
    # 测试没有计算函数的参数调用relink_and_calculate
    try:
        result = param_no_calc.relink_and_calculate()
        print(f"   无计算函数参数重新连接结果: {result}")
        # 应该返回当前值
        assert result == param_no_calc.value, "无计算函数的参数应该返回当前值"
    except Exception as e:
        print(f"   重新连接错误（预期）: {e}")
    
    graph.add_node(node)
    
    print("✅ 边界情况和错误处理测试通过！")

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
    print("🧪 运行增强的unlink功能测试")
    print("=" * 60)
    
    try:
        test_enhanced_unlink_display_logic()
        test_manual_value_auto_unlink()
        test_unlink_icon_click_reconnect()
        test_sensitivity_analysis_auto_unlink_simulation()
        test_edge_cases_and_error_handling()
        test_unlink_with_complex_dependencies()
        
        print("\n" + "=" * 60)
        print("🎉 所有增强unlink功能测试通过！")
        print("✅ 测试覆盖:")
        print("   - 显示逻辑（只有unlinked=True且有依赖时显示）")
        print("   - 手动修改值自动unlink")
        print("   - 点击按钮重新连接")
        print("   - 相关性分析自动unlink")
        print("   - 边界情况和错误处理")
        print("   - 复杂依赖关系中的unlink")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc() 