import pytest
from app import (
    get_all_available_parameters,
    generate_code_template,
    create_dependency_checkboxes,
    get_plotting_parameters,
    perform_sensitivity_analysis,
    create_empty_plot
)
from models import CalculationGraph, Node, Parameter
import dash_bootstrap_components as dbc
import numpy as np

@pytest.fixture
def test_graph():
    """提供一个包含节点的测试图"""
    graph = CalculationGraph()
    node1 = Node(name="Node1", description="First Node")
    param1 = Parameter(name="param1", value=10, unit="m", param_type="float")
    param2 = Parameter(name="param2", value=20, unit="kg", param_type="float")
    node1.add_parameter(param1)
    node1.add_parameter(param2)
    graph.add_node(node1)

    node2 = Node(name="Node2", description="Second Node")
    param3 = Parameter(name="param3", value=5, unit="s", param_type="float")
    node2.add_parameter(param3)
    graph.add_node(node2)
    
    return graph, node1.id, node2.id

def test_get_all_available_parameters(test_graph):
    """测试获取所有可用参数的函数"""
    graph, node1_id, _ = test_graph
    # 注入全局 `graph` 实例以供测试
    import app
    app.graph = graph
    
    available = get_all_available_parameters(node1_id, "param1")
    
    assert len(available) == 2
    param_names = {p['display_name'] for p in available}
    assert "Node1.param2" in param_names
    assert "Node2.param3" in param_names
    assert "Node1.param1" not in param_names

def test_generate_code_template():
    """测试生成代码模板的函数"""
    # 无依赖
    template = generate_code_template([])
    assert "无依赖参数" in template
    
    # 有依赖
    deps = [{'param_name': 'dep1'}, {'param_name': 'dep2'}]
    template = generate_code_template(deps)
    assert "# dep1 = dependencies[0].value" in template
    assert "# dep2 = dependencies[1].value" in template

def test_create_dependency_checkboxes(test_graph):
    """测试创建依赖复选框列表的函数"""
    graph, _, _ = test_graph
    import app
    app.graph = graph
    
    params = get_all_available_parameters("some_node", "some_param")
    checkboxes = create_dependency_checkboxes(params)
    
    assert len(checkboxes) == 3
    assert isinstance(checkboxes[0], dbc.Checkbox)

def test_get_plotting_parameters(test_graph):
    """测试获取所有可用于绘图的参数"""
    graph, _, _ = test_graph
    import app
    app.graph = graph
    
    # 添加一个非数值参数
    str_node = Node("StringNode")
    str_param = Parameter("str_param", "text", param_type="str")
    str_node.add_parameter(str_param)
    graph.add_node(str_node)
    
    plot_params = get_plotting_parameters()
    
    assert len(plot_params) == 3  # 应该只返回3个数值参数
    param_labels = {p['label'] for p in plot_params}
    assert "Node1.param1" in param_labels
    assert "StringNode.str_param" not in param_labels

def test_perform_sensitivity_analysis(test_graph):
    """测试参数敏感性分析函数"""
    graph, node1_id, node2_id = test_graph
    import app
    app.graph = graph
    
    # 设置依赖关系: param3 = param1 * 2
    param3 = graph.nodes[node2_id].get_parameter("param3")
    param1 = graph.nodes[node1_id].get_parameter("param1")
    param3.dependencies = [param1]
    param3.calculation_func = "result = dependencies[0].value * 2"
    param3.calculate()
    
    x_info = {'value': f'{node1_id}|param1', 'label': 'Node1.param1', 'unit': 'm'}
    y_info = {'value': f'{node2_id}|param3', 'label': 'Node2.param3', 'unit': 's'}
    
    result = perform_sensitivity_analysis(x_info, y_info, 10, 20, 2)
    
    assert result['success']
    assert len(result['x_values']) == 6
    assert result['x_values'] == [10.0, 12.0, 14.0, 16.0, 18.0, 20.0]
    assert result['y_values'] == [20.0, 24.0, 28.0, 32.0, 36.0, 40.0]

def test_create_empty_plot():
    """测试创建空图表对象"""
    fig = create_empty_plot()
    assert fig is not None
    assert 'data' in fig
    assert len(fig['data']) == 0
    assert 'layout' in fig
    assert 'title' in fig['layout']
    assert fig['layout']['title']['text'] == "请选择参数以生成图表"
