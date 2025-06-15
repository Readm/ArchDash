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
    """
    name: str
    value: T
    unit: str
    description: str = ""
    confidence: float = 1.0
    calculation_func: Optional[str] = None
    dependencies: List['Parameter'] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)
    
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
        
        local_env = {
            'self': self,
            'dependencies': self.dependencies,
            'value': self.value,
            'datetime': datetime
        }
        try:
            # 如果计算函数是字符串，则使用exec执行
            if isinstance(self.calculation_func, str):
                exec(self.calculation_func, {"__builtins__": {}}, local_env)
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

    def add_node(self, node: Node) -> None:
        if node.id in self.nodes:
            raise ValueError(f"Node with id {node.id} already exists.")
        
        # 检查节点名称是否已存在
        for existing_node in self.nodes.values():
            if existing_node.name == node.name:
                raise ValueError(f"Node with name '{node.name}' already exists.")
        
        self.nodes[node.id] = node

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