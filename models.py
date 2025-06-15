from typing import Dict, List, Optional, Any, Union, Callable, TypeVar, cast
from dataclasses import dataclass, field
import numpy as np
import json
from datetime import datetime
import uuid

# 定义类型变量
T = TypeVar('T', float, int, str)

@dataclass
class Parameter:
    """参数类，用于存储和管理单个参数
    
    Attributes:
        name: 参数名称
        value: 参数值（float、int或str类型）
        unit: 参数单位
        description: 参数描述
        confidence: 参数置信度（0-1之间）
        calculation_func: 计算函数（字符串形式）
        dependencies: 依赖参数列表
        history: 参数历史记录
        _graph: 所属的计算图（用于自动更新传播）
    """
    name: str
    unit: str
    description: str = ""
    confidence: float = 1.0
    calculation_func: Optional[str] = None
    dependencies: List['Parameter'] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)
    _value: T = 0.0  # 内部值存储
    _graph: Optional['CalculationGraph'] = field(default=None, repr=False)  # 计算图引用
    
    def __init__(self, name: str, value: T = 0.0, unit: str = "", **kwargs):
        self.name = name
        self._value = value
        self.unit = unit
        self.description = kwargs.get('description', "")
        self.confidence = kwargs.get('confidence', 1.0)
        self.calculation_func = kwargs.get('calculation_func', None)
        self.dependencies = kwargs.get('dependencies', [])
        self.history = kwargs.get('history', [])
        self._graph = kwargs.get('_graph', None)
    
    @property
    def value(self) -> T:
        """获取参数值"""
        return self._value
    
    @value.setter 
    def value(self, new_value: T):
        """设置参数值并触发数据流更新"""
        old_value = self._value
        self._value = new_value
        
        # 如果值确实发生了变化并且有关联的计算图，触发更新传播
        if old_value != new_value and self._graph is not None:
            try:
                update_result = self._graph.propagate_updates(self)
                if update_result:
                    print(f"🔄 数据流更新: {self.name} 值从 {old_value} 变为 {new_value}")
                    for update_info in update_result:
                        param = update_info['param']
                        print(f"   └── {param.name}: {update_info['old_value']} → {update_info['new_value']}")
            except Exception as e:
                print(f"⚠️ 更新传播失败: {e}")
    
    def set_graph(self, graph: 'CalculationGraph'):
        """设置参数所属的计算图"""
        self._graph = graph
    
    def validate(self) -> bool:
        """验证参数值是否有效"""
        if self.value is None:
            return False
        if isinstance(self.value, (float, int)):
            return True
        if isinstance(self.value, str):
            return len(self.value) > 0
        return False
    
    def add_dependency(self, param: 'Parameter') -> None:
        """添加依赖参数"""
        if not isinstance(param, Parameter):
            raise TypeError("依赖参数必须是Parameter类型")
        if param is self:
            raise ValueError("参数不能依赖自身")
        if param not in self.dependencies:
            self.dependencies.append(param)
    
    def calculate(self) -> T:
        """计算参数值，支持多行代码，结果通过result变量返回
        
        Returns:
            T: 计算后的参数值（float、int或str类型）
        
        Raises:
            ValueError: 如果依赖参数的值缺失或计算失败
        """
        if not self.calculation_func:
            return self.value if self.value is not None else 0.0
        
        # 检查所有依赖是否都有值
        for dep in self.dependencies:
            if dep.value is None:
                raise ValueError(f"依赖参数 {dep.name} 的值缺失")
        
        # 设置较为宽松的计算环境，允许常用模块和函数
        import math
        import builtins
        
        # 创建安全但功能完整的全局环境
        safe_globals = {
            '__builtins__': builtins.__dict__.copy(),  # 允许所有内置函数
            'math': math,
            'datetime': datetime,
        }
        
        local_env = {
            'dependencies': self.dependencies,
            'value': self.value,
            'datetime': datetime,
            'self': self
        }
        
        try:
            # 如果计算函数是字符串，则使用exec执行
            if isinstance(self.calculation_func, str):
                exec(self.calculation_func, safe_globals, local_env)
                result = local_env.get('result', None)
                if result is None:
                    raise ValueError("计算函数未设置result变量作为输出")
            else:
                # 如果计算函数是函数对象，则直接调用
                result = self.calculation_func(self)
            
            self.value = result
            self.history.append({
                "timestamp": datetime.now().isoformat(),
                "value": result,
                "dependencies": [dep.name for dep in self.dependencies]
            })
            return result
        except Exception as e:
            raise ValueError(f"计算失败: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """将参数转换为字典"""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "description": self.description,
            "confidence": self.confidence,
            "calculation_func": self.calculation_func,
            "dependencies": [dep.name for dep in self.dependencies],
            "history": self.history
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], param_dict: Dict[str, 'Parameter']) -> 'Parameter':
        """从字典创建参数"""
        param = cls(
            name=data["name"],
            value=data["value"],
            unit=data["unit"],
            description=data["description"],
            confidence=data["confidence"],
            calculation_func=data["calculation_func"]
        )
        
        # 添加依赖
        for dep_name in data["dependencies"]:
            if dep_name in param_dict:
                param.add_dependency(param_dict[dep_name])
        
        # 恢复历史记录
        param.history = data["history"]
        
        return param

@dataclass
class Node:
    """节点类，用于管理一组相关参数
    
    Attributes:
        name: 节点名称
        description: 节点描述
        parameters: 参数字典
    """
    name: str
    description: str = ""
    parameters: List[Parameter] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_type: str = "default"
    
    def __init__(self, name, description="", id=None, **kwargs):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.node_type = kwargs.get('node_type', "default")
        self.parameters = []  # 确保每个Node实例都有parameters属性
        for key, value in kwargs.items():
            if key != 'node_type':
                setattr(self, key, value)
    
    def add_parameter(self, parameter: Parameter) -> None:
        """添加参数到节点"""
        self.parameters.append(parameter)
    
    def remove_parameter(self, name: str) -> None:
        """从节点移除参数"""
        self.parameters = [param for param in self.parameters if param.name != name]
    
    def get_parameter_history(self, name: str) -> List[Dict[str, Any]]:
        """获取参数历史记录"""
        param = next((param for param in self.parameters if param.name == name), None)
        return param.history if param else []
    
    def calculate_all(self) -> None:
        """计算所有参数"""
        for param in self.parameters:
            if param.calculation_func:
                param.calculate()
    
    def to_dict(self) -> Dict[str, Any]:
        """将节点转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": [param.to_dict() for param in self.parameters],
            "node_type": self.node_type,
            "id": self.id
        }

class CalculationGraph:
    def __init__(self):
        self.nodes = {}
        self.dependencies = {}
        # 新增：反向依赖图，记录哪些参数依赖于当前参数
        self._dependents_map = {}  # param_id -> [dependent_param_ids]
        # 新增：所有参数的全局映射，便于快速查找
        self._all_parameters = {}  # param_id -> parameter_object

    def add_node(self, node: Node) -> None:
        if node.id in self.nodes:
            raise ValueError(f"Node with id {node.id} already exists.")
        
        # 检查节点名称是否已存在
        for existing_node in self.nodes.values():
            if existing_node.name == node.name:
                raise ValueError(f"Node with name '{node.name}' already exists.")
        
        self.nodes[node.id] = node
        
        # 将节点的所有参数添加到全局参数映射，并设置graph引用
        for param in node.parameters:
            param_id = id(param)  # 使用内存地址作为唯一ID
            self._all_parameters[param_id] = param
            self._dependents_map[param_id] = []
            # 为参数设置计算图引用，启用自动数据流更新
            param.set_graph(self)
        
        # 构建反向依赖图
        self._rebuild_dependency_graph()

    def add_parameter_to_node(self, node_id: str, param: 'Parameter'):
        """向现有节点添加参数"""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.add_parameter(param)
            
            # 添加到全局参数映射
            param_id = id(param)
            self._all_parameters[param_id] = param
            self._dependents_map[param_id] = []
            # 设置graph引用
            param.set_graph(self)
            
            # 重新构建依赖图
            self._rebuild_dependency_graph()

    def update_parameter_dependencies(self, param):
        """更新单个参数的依赖关系"""
        param_id = id(param)
        
        # 确保参数在全局映射中
        if param_id not in self._all_parameters:
            self._all_parameters[param_id] = param
            self._dependents_map[param_id] = []
            # 设置graph引用
            param.set_graph(self)
        
        # 重新构建依赖图
        self._rebuild_dependency_graph()

    def _rebuild_dependency_graph(self):
        """重新构建反向依赖图"""
        # 清空现有的反向依赖图
        for param_id in self._dependents_map:
            self._dependents_map[param_id] = []
        
        # 遍历所有参数，构建反向依赖关系
        for param_id, param in self._all_parameters.items():
            for dependency in param.dependencies:
                dep_id = id(dependency)
                if dep_id in self._dependents_map:
                    if param_id not in self._dependents_map[dep_id]:
                        self._dependents_map[dep_id].append(param_id)

    def propagate_updates(self, changed_param, visited=None):
        """传播更新：当参数值改变时，更新所有依赖它的参数
        
        Args:
            changed_param: 值发生改变的参数
            visited: 已访问的参数集合，用于避免循环更新
        
        Returns:
            list: 所有被更新的参数列表
        """
        if visited is None:
            visited = set()
        
        param_id = id(changed_param)
        updated_params = []
        
        # 避免循环更新
        if param_id in visited:
            return updated_params
        
        visited.add(param_id)
        
        # 获取所有依赖于当前参数的参数
        dependent_param_ids = self._dependents_map.get(param_id, [])
        
        # 按拓扑顺序更新依赖参数
        for dependent_id in dependent_param_ids:
            if dependent_id in self._all_parameters:
                dependent_param = self._all_parameters[dependent_id]
                
                # 只有当参数有计算函数时才进行重新计算
                if dependent_param.calculation_func:
                    try:
                        old_value = dependent_param.value
                        new_value = dependent_param.calculate()
                        
                        updated_params.append({
                            'param': dependent_param,
                            'old_value': old_value,
                            'new_value': new_value
                        })
                        
                        # 如果值确实发生了变化，继续传播更新
                        if old_value != new_value:
                            cascaded_updates = self.propagate_updates(dependent_param, visited.copy())
                            updated_params.extend(cascaded_updates)
                            
                    except Exception as e:
                        # 记录计算错误，但不中断整个更新流程
                        print(f"警告：参数 {dependent_param.name} 计算失败: {e}")
        
        return updated_params

    def set_parameter_value(self, param, new_value):
        """设置参数值并触发更新传播
        
        Args:
            param: 要更新的参数对象
            new_value: 新的参数值
        
        Returns:
            dict: 更新结果，包含被影响的所有参数
        """
        old_value = param.value
        param.value = new_value
        
        # 记录主参数的变化
        update_result = {
            'primary_change': {
                'param': param,
                'old_value': old_value,
                'new_value': new_value
            },
            'cascaded_updates': [],
            'total_updated_params': 1
        }
        
        # 传播更新
        cascaded_updates = self.propagate_updates(param)
        update_result['cascaded_updates'] = cascaded_updates
        update_result['total_updated_params'] += len(cascaded_updates)
        
        return update_result

    def get_dependency_chain(self, param):
        """获取参数的完整依赖链信息
        
        Args:
            param: 参数对象
            
        Returns:
            dict: 包含依赖链信息的字典
        """
        param_id = id(param)
        
        def get_dependents_recursive(param_id, depth=0, max_depth=10):
            if depth > max_depth:  # 防止过深递归
                return []
                
            dependents = []
            dependent_ids = self._dependents_map.get(param_id, [])
            
            for dep_id in dependent_ids:
                if dep_id in self._all_parameters:
                    dependent = self._all_parameters[dep_id]
                    dependents.append({
                        'param': dependent,
                        'depth': depth,
                        'children': get_dependents_recursive(dep_id, depth + 1, max_depth)
                    })
            
            return dependents
        
        return {
            'root_param': param,
            'dependents': get_dependents_recursive(param_id)
        }

    def get_node(self, node_id: str) -> Optional[Node]:
        return self.nodes.get(node_id)

    def add_dependency(self, source: Node, target: Node) -> None:
        self.dependencies.append((source.id, target.id))

    def get_dependencies(self, node: Node) -> List[Node]:
        return [self.nodes[target_id] for source_id, target_id in self.dependencies if source_id == node.id]

    def get_dependents(self, node: Node) -> List[Node]:
        return [self.nodes[source_id] for source_id, target_id in self.dependencies if target_id == node.id]

    def remove_node(self, node: Node) -> None:
        if node.id in self.nodes:
            del self.nodes[node.id]
            self.dependencies = [(s, t) for s, t in self.dependencies if s != node.id and t != node.id]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {node_id: {
                "name": node.name,
                "description": node.description,
                "parameters": [param.to_dict() for param in node.parameters]
            } for node_id, node in self.nodes.items()},
            "dependencies": self.dependencies
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalculationGraph':
        graph = cls()
        for node_id, node_data in data["nodes"].items():
            node = Node(
                name=node_data["name"],
                description=node_data["description"],
                id=node_id
            )
            for param_data in node_data["parameters"]:
                param = Parameter(
                    name=param_data["name"],
                    value=param_data["value"],
                    unit=param_data["unit"],
                    description=param_data["description"]
                )
                node.add_parameter(param)
            graph.add_node(node)
        graph.dependencies = data["dependencies"]
        return graph

    def to_json(self) -> str:
        """将计算图转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'CalculationGraph':
        """从JSON字符串创建计算图"""
        data = json.loads(json_str)
        return cls.from_dict(data) 