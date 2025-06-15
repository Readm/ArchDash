import pytest
from models import Parameter, Node, CalculationGraph
import json

def test_parameter_validation():
    """测试参数验证"""
    # 测试有效参数
    param1 = Parameter("param1", 10.0, "V", "测试参数1")
    assert param1.validate()
    
    param2 = Parameter("param2", "test", "A", "测试参数2")
    assert param2.validate()
    
    # 测试无效参数
    param3 = Parameter("param3", None, "W", "测试参数3")
    assert not param3.validate()
    
    param4 = Parameter("param4", "", "W", "测试参数4")
    assert not param4.validate()

def test_parameter_dependencies():
    """测试参数依赖关系"""
    # 创建参数
    param1 = Parameter("param1", 2.0, "V", "Test parameter 1")
    param2 = Parameter("param2", 3, "A", "Test parameter 2")
    
    # 测试添加有效依赖
    param1.add_dependency(param2)
    assert param2 in param1.dependencies
    
    # 测试添加无效类型依赖
    with pytest.raises(TypeError):
        param1.add_dependency("invalid")
    
    # 测试添加自身作为依赖
    with pytest.raises(ValueError):
        param1.add_dependency(param1)
    
    # 测试重复添加依赖
    param1.add_dependency(param2)  # 应该不会抛出异常
    assert param1.dependencies.count(param2) == 1  # 确保没有重复添加

def test_parameter_calculation():
    """测试参数计算"""
    # 创建参数
    param1 = Parameter("param1", 10.0, "V", "测试参数1")
    param2 = Parameter("param2", 20.0, "A", "测试参数2")
    
    # 测试字符串形式的计算函数
    calc_func_str = "result = dependencies[0].value * dependencies[1].value"
    result_param = Parameter("result", 0.0, "W", "计算结果", calculation_func=calc_func_str)
    result_param.add_dependency(param1)
    result_param.add_dependency(param2)
    
    # 计算并验证结果
    result = result_param.calculate()
    assert result == 200.0  # 10.0 * 20.0
    
    # 测试函数对象形式的计算函数
    def calc_func(param: Parameter) -> float:
        return param.dependencies[0].value * param.dependencies[1].value
    
    result_param2 = Parameter("result2", 0.0, "W", "计算结果2", calculation_func=calc_func)
    result_param2.add_dependency(param1)
    result_param2.add_dependency(param2)
    
    # 计算并验证结果
    result = result_param2.calculate()
    assert result == 200.0  # 10.0 * 20.0

def test_calculation_function_safety():
    """测试计算函数的安全性"""
    # 创建基础参数
    param1 = Parameter("param1", 2.0, "V", "Test parameter 1")
    param2 = Parameter("param2", 3, "A", "Test parameter 2")
    
    # 测试危险操作（应该被阻止）
    dangerous_calc = "result = __import__('os').system('ls')"  # 尝试执行系统命令
    dangerous_param = Parameter(
        name="dangerous",
        value=0.0,
        unit="V",
        description="Dangerous calculation",
        calculation_func=dangerous_calc
    )
    dangerous_param.add_dependency(param1)
    
    # 验证危险操作被阻止
    with pytest.raises(ValueError, match="计算失败: name '__import__' is not defined"):
        dangerous_param.calculate()
    
    # 测试访问内置函数（应该被阻止）
    builtin_calc = "result = len(dependencies)"  # 尝试使用内置函数
    builtin_param = Parameter(
        name="builtin",
        value=0.0,
        unit="V",
        description="Builtin function test",
        calculation_func=builtin_calc
    )
    builtin_param.add_dependency(param1)
    
    # 验证内置函数访问被阻止
    with pytest.raises(ValueError, match="计算失败: name 'len' is not defined"):
        builtin_param.calculate()
    
    # 测试复杂计算表达式（未设置result变量，应该报错）
    complex_calc = """
sum = 0
for dep in dependencies:
    sum += dep.value
"""
    complex_param = Parameter(
        name="complex",
        value=0.0,
        unit="V",
        description="Complex calculation",
        calculation_func=complex_calc
    )
    complex_param.add_dependency(param1)
    complex_param.add_dependency(param2)
    
    # 验证未设置result变量被阻止
    with pytest.raises(ValueError, match="计算函数未设置result变量作为输出"):
        complex_param.calculate()
    
    # 测试正确的计算表达式
    valid_calc = "result = dependencies[0].value + dependencies[1].value"
    valid_param = Parameter(
        name="valid",
        value=0.0,
        unit="V",
        description="Valid calculation",
        calculation_func=valid_calc
    )
    valid_param.add_dependency(param1)
    valid_param.add_dependency(param2)
    
    # 验证正确的计算表达式可以执行
    result = valid_param.calculate()
    assert result == 5.0

def test_calculation_function_scope():
    """测试计算函数的作用域"""
    # 创建基础参数
    param1 = Parameter("param1", 2.0, "V", "Test parameter 1")
    param2 = Parameter("param2", 3, "A", "Test parameter 2")
    
    # 测试访问本地变量（未设置result变量，应该报错）
    local_var_calc = "local_var = 10"
    local_var_param = Parameter(
        name="local_var",
        value=0.0,
        unit="V",
        description="Local variable test",
        calculation_func=local_var_calc
    )
    local_var_param.add_dependency(param1)
    
    # 验证未设置result变量被阻止
    with pytest.raises(ValueError, match="计算函数未设置result变量作为输出"):
        local_var_param.calculate()
    
    # 测试访问全局变量
    global_var_calc = "result = global_var + dependencies[0].value"
    global_var_param = Parameter(
        name="global_var",
        value=0.0,
        unit="V",
        description="Global variable test",
        calculation_func=global_var_calc
    )
    global_var_param.add_dependency(param1)
    
    # 验证全局变量访问被阻止
    with pytest.raises(ValueError, match="计算失败: name 'global_var' is not defined"):
        global_var_param.calculate()
    
    # 测试访问提供的环境变量
    env_var_calc = "result = datetime.now().isoformat()"
    env_var_param = Parameter(
        name="env_var",
        value="",
        unit="",
        description="Environment variable test",
        calculation_func=env_var_calc
    )
    env_var_param.add_dependency(param1)
    
    # 验证环境变量访问正常
    result = env_var_param.calculate()
    assert isinstance(result, str)
    assert len(result) > 0

def test_node_operations():
    """测试节点操作"""
    # 创建节点
    node = Node("test_node", "测试节点")
    
    # 创建参数
    param1 = Parameter("param1", 10.0, "V", "测试参数1")
    param2 = Parameter("param2", 20.0, "A", "测试参数2")
    
    # 测试添加参数
    node.add_parameter(param1)
    node.add_parameter(param2)
    assert len(node.parameters) == 2
    assert "param1" in node.parameters
    assert "param2" in node.parameters
    
    # 测试移除参数
    node.remove_parameter("param1")
    assert len(node.parameters) == 1
    assert "param1" not in node.parameters
    assert "param2" in node.parameters
    
    # 测试参数历史记录（通过 calculate 触发历史记录）
    param2.calculation_func = "result = value + 10"
    param2.calculate()  # 第一次计算
    param2.calculate()  # 第二次计算
    history = node.get_parameter_history("param2")
    assert len(history) == 2
    assert history[0]["value"] == 30.0  # 20+10
    assert history[1]["value"] == 40.0  # 30+10

def test_calculation_graph():
    """测试计算图"""
    # 创建计算图
    graph = CalculationGraph()
    
    # 创建全局参数
    global_param = Parameter("global_param", 100.0, "V", "全局参数")
    graph.add_global_parameter(global_param)
    
    # 创建节点和参数
    node = Node("test_node", "测试节点")
    param1 = Parameter("param1", 10.0, "V", "测试参数1")
    param2 = Parameter("param2", 20.0, "A", "测试参数2")
    
    # 设置计算函数
    calc_func = "result = dependencies[0].value * 2"
    param2.calculation_func = calc_func
    param2.add_dependency(param1)
    
    # 添加参数到节点
    node.add_parameter(param1)
    node.add_parameter(param2)
    
    # 添加节点到计算图
    graph.add_node(node)
    
    # 测试计算
    graph.calculate_all()
    assert param2.value == 20.0  # 10.0 * 2
    
    # 测试参数历史记录
    param1.value = 15.0
    graph.calculate_all()
    history = graph.get_parameter_history("test_node", "param2")
    assert len(history) == 2
    assert history[0]["value"] == 20.0
    assert history[1]["value"] == 30.0  # 15.0 * 2
    
    # 测试移除节点
    graph.remove_node("test_node")
    assert "test_node" not in graph.nodes

def test_missing_dependency():
    """测试缺失依赖的情况"""
    # 创建参数
    param1 = Parameter("param1", None, "V", "测试参数1")
    param2 = Parameter("param2", 20.0, "A", "测试参数2")
    
    # 创建计算函数
    calc_func = "result = dependencies[0].value * dependencies[1].value"
    result_param = Parameter("result", 0.0, "W", "计算结果", calculation_func=calc_func)
    result_param.add_dependency(param1)
    result_param.add_dependency(param2)
    
    # 测试计算失败
    with pytest.raises(ValueError, match="依赖参数 param1 的值缺失"):
        result_param.calculate()

def test_serialization():
    """测试序列化和反序列化"""
    # 创建计算图
    graph = CalculationGraph()
    
    # 创建全局参数
    global_param = Parameter("global_param", 100.0, "V", "全局参数")
    graph.add_global_parameter(global_param)
    
    # 创建节点和参数
    node = Node("test_node", "测试节点")
    param1 = Parameter("param1", 10.0, "V", "测试参数1")
    param2 = Parameter("param2", 20.0, "A", "测试参数2")
    
    # 设置计算函数
    calc_func = "result = dependencies[0].value * 2"
    param2.calculation_func = calc_func
    param2.add_dependency(param1)
    
    # 添加参数到节点
    node.add_parameter(param1)
    node.add_parameter(param2)
    
    # 添加节点到计算图
    graph.add_node(node)
    
    # 测试序列化
    json_str = graph.to_json()
    assert isinstance(json_str, str)
    
    # 测试反序列化
    new_graph = CalculationGraph.from_json(json_str)
    
    # 验证反序列化后的对象
    assert new_graph.global_parameters["global_param"].value == 100.0
    assert new_graph.nodes["test_node"].parameters["param1"].value == 10.0
    assert new_graph.nodes["test_node"].parameters["param2"].value == 20.0
    
    # 测试计算功能是否正常
    new_graph.calculate_all()
    assert new_graph.nodes["test_node"].parameters["param2"].value == 20.0  # 10.0 * 2

def test_duplicate_node_name_prevention():
    """测试计算图中阻止重名节点的功能"""
    graph = CalculationGraph()
    
    # 创建第一个节点
    node1 = Node("TestNode", "第一个测试节点")
    graph.add_node(node1)
    
    # 验证节点已成功添加
    assert len(graph.nodes) == 1
    assert node1.id in graph.nodes
    
    # 尝试添加相同名称的节点（应该被阻止）
    node2 = Node("TestNode", "第二个测试节点")  # 相同的名称
    
    with pytest.raises(ValueError, match="Node with name 'TestNode' already exists."):
        graph.add_node(node2)
    
    # 验证第二个节点没有被添加
    assert len(graph.nodes) == 1
    assert node2.id not in graph.nodes
    
    # 添加不同名称的节点（应该成功）
    node3 = Node("DifferentNode", "不同名称的节点")
    graph.add_node(node3)
    
    # 验证不同名称的节点成功添加
    assert len(graph.nodes) == 2
    assert node3.id in graph.nodes
    
    print("✅ 计算图重名节点检查功能正常工作")

def test_node_id_duplicate_prevention():
    """测试计算图中阻止重复ID节点的功能（现有功能验证）"""
    graph = CalculationGraph()
    
    # 创建第一个节点
    node1 = Node("Node1", "第一个节点")
    graph.add_node(node1)
    
    # 创建具有相同ID的节点
    node2 = Node("Node2", "第二个节点", id=node1.id)  # 使用相同的ID
    
    with pytest.raises(ValueError, match=f"Node with id {node1.id} already exists."):
        graph.add_node(node2)
    
    # 验证只有第一个节点存在
    assert len(graph.nodes) == 1
    assert graph.nodes[node1.id].name == "Node1"
    
    print("✅ 计算图重复ID检查功能正常工作") 