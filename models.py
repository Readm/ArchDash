from typing import Dict, List, Optional, Any, Union, Callable, TypeVar, cast, Tuple
from dataclasses import dataclass, field
import numpy as np
import json
from datetime import datetime
import uuid
import os

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
    """计算图类，管理所有节点和参数之间的依赖关系"""
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.dependencies = {}
        self.dependency_graph: Dict[str, List[str]] = {}
        self.reverse_dependency_graph: Dict[str, List[str]] = {}
        # 新增：反向依赖图，记录哪些参数依赖于当前参数
        self._dependents_map: Dict[int, List[int]] = {}  # param_id -> [dependent_param_ids]
        # 新增：所有参数的全局映射，便于快速查找
        self._all_parameters: Dict[int, Parameter] = {}  # param_id -> parameter_object
        self.layout_manager: Optional['CanvasLayoutManager'] = None
        
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

    def set_layout_manager(self, layout_manager: 'CanvasLayoutManager') -> None:
        """设置布局管理器"""
        self.layout_manager = layout_manager
    
    def to_dict(self, include_layout: bool = True) -> Dict[str, Any]:
        """将计算图转换为字典格式
        
        Args:
            include_layout: 是否包含布局信息
            
        Returns:
            包含计算图信息的字典
        """
        # 创建所有参数的映射，供依赖关系使用
        all_params = {}
        for node in self.nodes.values():
            for param in node.parameters:
                all_params[param.name] = param
        
        graph_dict = {
            "nodes": {},
            "dependencies": {},
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "node_count": len(self.nodes),
                "total_parameters": sum(len(node.parameters) for node in self.nodes.values())
            }
        }
        
        # 添加节点信息
        for node_id, node in self.nodes.items():
            graph_dict["nodes"][node_id] = node.to_dict()
        
        # 添加依赖关系
        for node_id, node in self.nodes.items():
            for param in node.parameters:
                if param.dependencies:
                    dep_key = f"{node_id}.{param.name}"
                    graph_dict["dependencies"][dep_key] = [
                        dep.name for dep in param.dependencies
                    ]
        
        # 添加布局信息
        if include_layout and self.layout_manager:
            graph_dict["layout"] = self.layout_manager.to_dict()
        
        return graph_dict

    def to_json(self, include_layout: bool = True) -> str:
        """将计算图转换为JSON字符串
        
        Args:
            include_layout: 是否包含布局信息
            
        Returns:
            JSON格式的字符串
        """
        return json.dumps(self.to_dict(include_layout), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str, layout_manager: Optional['CanvasLayoutManager'] = None) -> 'CalculationGraph':
        """从JSON字符串创建计算图
        
        Args:
            json_str: JSON格式的字符串
            layout_manager: 可选的布局管理器
            
        Returns:
            新的计算图实例
        """
        data = json.loads(json_str)
        return cls.from_dict(data, layout_manager)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], layout_manager: Optional['CanvasLayoutManager'] = None) -> 'CalculationGraph':
        """从字典创建计算图
        
        Args:
            data: 包含计算图数据的字典
            layout_manager: 可选的布局管理器
            
        Returns:
            重建的计算图对象
        """
        graph = cls()
        
        # 设置布局管理器
        if layout_manager:
            graph.set_layout_manager(layout_manager)
        
        # 第一遍：创建所有节点和参数（不包含依赖关系）
        param_dict = {}  # 用于解析依赖关系
        
        for node_id, node_data in data["nodes"].items():
            node = Node(
                name=node_data["name"],
                description=node_data.get("description", ""),
                id=node_data.get("id", node_id)
            )
            
            # 设置节点类型
            if "node_type" in node_data:
                node.node_type = node_data["node_type"]
            
            # 创建参数（暂不设置依赖）
            for param_data in node_data["parameters"]:
                param = Parameter(
                    name=param_data["name"],
                    value=param_data["value"],
                    unit=param_data["unit"],
                    description=param_data.get("description", ""),
                    confidence=param_data.get("confidence", 1.0),
                    calculation_func=param_data.get("calculation_func"),
                    history=param_data.get("history", [])
                )
                
                # 设置计算图引用
                param.set_graph(graph)
                
                node.add_parameter(param)
                param_dict[f"{node_id}.{param.name}"] = param
            
            graph.add_node(node)
        
        # 第二遍：重建参数依赖关系
        for node_id, node_data in data["nodes"].items():
            node = graph.nodes[node_id]
            
            for i, param_data in enumerate(node_data["parameters"]):
                param = node.parameters[i]
                
                # 重建依赖关系
                for dep_name in param_data.get("dependencies", []):
                    # 查找依赖参数
                    for dep_key, dep_param in param_dict.items():
                        if dep_param.name == dep_name:
                            param.add_dependency(dep_param)
                            break
        
        # 恢复节点依赖关系
        if "dependencies" in data:
            graph.dependencies = data["dependencies"]
        
        # 重建依赖图
        graph._rebuild_dependency_graph()
        
        # 恢复布局信息
        if "layout" in data and graph.layout_manager:
            layout_data = data["layout"]
            
            # 调整布局管理器大小
            required_cols = layout_data.get("cols", 3)
            required_rows = layout_data.get("rows", 10)
            
            while graph.layout_manager.cols < required_cols:
                graph.layout_manager.add_column()
            
            while graph.layout_manager.rows < required_rows:
                graph.layout_manager.add_rows(5)
            
            # 恢复节点位置
            for node_id, pos_data in layout_data.get("node_positions", {}).items():
                if node_id in graph.nodes:
                    try:
                        position = GridPosition(pos_data["row"], pos_data["col"])
                        graph.layout_manager.place_node(node_id, position)
                    except Exception as e:
                        print(f"⚠️ 恢复节点 {node_id} 位置失败: {e}")
        
        return graph

    def save_to_file(self, filepath: str, include_layout: bool = True) -> bool:
        """保存计算图到文件
        
        Args:
            filepath: 保存路径
            include_layout: 是否包含布局信息
            
        Returns:
            保存是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # 转换为字典并保存
            data = self.to_dict(include_layout=include_layout)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 计算图已保存到: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ 保存计算图失败: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: str, layout_manager: Optional['CanvasLayoutManager'] = None) -> Optional['CalculationGraph']:
        """从文件加载计算图
        
        Args:
            filepath: 文件路径
            layout_manager: 可选的布局管理器
            
        Returns:
            加载的计算图对象，失败时返回None
        """
        try:
            if not os.path.exists(filepath):
                print(f"❌ 文件不存在: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证文件格式
            if "nodes" not in data:
                print("❌ 无效的计算图文件格式")
                return None
            
            graph = cls.from_dict(data, layout_manager)
            print(f"✅ 计算图已从文件加载: {filepath}")
            return graph
            
        except Exception as e:
            print(f"❌ 加载计算图失败: {e}")
            return None
    
    def export_summary(self) -> Dict[str, Any]:
        """导出计算图摘要信息"""
        summary = {
            "总节点数": len(self.nodes),
            "总参数数": sum(len(node.parameters) for node in self.nodes.values()),
            "节点信息": []
        }
        
        for node_id, node in self.nodes.items():
            node_summary = {
                "节点ID": node_id,
                "节点名称": node.name,
                "参数数量": len(node.parameters),
                "参数列表": [
                    {
                        "名称": param.name,
                        "值": param.value,
                        "单位": param.unit,
                        "有计算函数": bool(param.calculation_func),
                        "依赖数量": len(param.dependencies)
                    }
                    for param in node.parameters
                ]
            }
            
            if self.layout_manager and node_id in self.layout_manager.node_positions:
                pos = self.layout_manager.node_positions[node_id]
                node_summary["位置"] = f"({pos.row}, {pos.col})"
            
            summary["节点信息"].append(node_summary)
        
        return summary

@dataclass 
class GridPosition:
    """网格位置类"""
    row: int
    col: int
    
    def __post_init__(self):
        if self.row < 0 or self.col < 0:
            raise ValueError("行和列索引必须非负")

class CanvasLayoutManager:
    """画布布局管理器
    
    使用二维数组来精确管理节点位置，提供友好的测试和维护接口
    """
    
    def __init__(self, initial_cols: int = 3, initial_rows: int = 10):
        """初始化布局管理器
        
        Args:
            initial_cols: 初始列数
            initial_rows: 初始行数（每列最大节点数）
        """
        self.grid: List[List[Optional[str]]] = []
        self.cols = initial_cols
        self.rows = initial_rows
        self._init_grid()
        
        # 节点位置映射：node_id -> GridPosition
        self.node_positions: Dict[str, GridPosition] = {}
        
        # 反向映射：position -> node_id
        self.position_nodes: Dict[Tuple[int, int], str] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """将布局管理器转换为字典"""
        return {
            "cols": self.cols,
            "rows": self.rows,
            "node_positions": {
                node_id: {"row": pos.row, "col": pos.col}
                for node_id, pos in self.node_positions.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CanvasLayoutManager':
        """从字典创建布局管理器"""
        layout_manager = cls(
            initial_cols=data.get("cols", 3),
            initial_rows=data.get("rows", 10)
        )
        
        # 恢复节点位置
        for node_id, pos_data in data.get("node_positions", {}).items():
            try:
                position = GridPosition(pos_data["row"], pos_data["col"])
                layout_manager.place_node(node_id, position)
            except Exception as e:
                print(f"⚠️ 恢复节点 {node_id} 位置失败: {e}")
        
        return layout_manager

    def _init_grid(self):
        """初始化网格"""
        self.grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]
    
    def add_column(self):
        """添加新列"""
        for row in self.grid:
            row.append(None)
        self.cols += 1
        
    def add_rows(self, num_rows: int = 5):
        """添加新行"""
        for _ in range(num_rows):
            self.grid.append([None] * self.cols)
        self.rows += num_rows
    
    def place_node(self, node_id: str, position: GridPosition = None) -> GridPosition:
        """放置节点到指定位置，如果位置为空则自动寻找合适位置
        
        Args:
            node_id: 节点ID
            position: 目标位置，如果为None则自动寻找
            
        Returns:
            实际放置的位置
            
        Raises:
            ValueError: 如果指定位置已被占用
        """
        if position is None:
            position = self._find_next_available_position()
        
        if not self._is_position_valid(position):
            raise ValueError(f"位置 ({position.row}, {position.col}) 超出网格范围")
            
        if self._is_position_occupied(position):
            raise ValueError(f"位置 ({position.row}, {position.col}) 已被节点 {self.grid[position.row][position.col]} 占用")
        
        # 如果节点已存在于其他位置，先移除
        if node_id in self.node_positions:
            self.remove_node(node_id)
        
        # 放置节点
        self.grid[position.row][position.col] = node_id
        self.node_positions[node_id] = position
        self.position_nodes[(position.row, position.col)] = node_id
        
        return position
    
    def move_node(self, node_id: str, new_position: GridPosition) -> bool:
        """移动节点到新位置
        
        Args:
            node_id: 节点ID
            new_position: 新位置
            
        Returns:
            移动是否成功
        """
        if node_id not in self.node_positions:
            return False
            
        if not self._is_position_valid(new_position):
            return False
            
        if self._is_position_occupied(new_position):
            return False
        
        # 移除旧位置
        old_position = self.node_positions[node_id]
        self.grid[old_position.row][old_position.col] = None
        del self.position_nodes[(old_position.row, old_position.col)]
        
        # 放置到新位置
        self.grid[new_position.row][new_position.col] = node_id
        self.node_positions[node_id] = new_position
        self.position_nodes[(new_position.row, new_position.col)] = node_id
        
        return True
    
    def move_node_up(self, node_id: str) -> bool:
        """节点上移"""
        if node_id not in self.node_positions:
            return False
            
        current_pos = self.node_positions[node_id]
        if current_pos.row == 0:
            return False  # 已经在顶部
            
        new_position = GridPosition(current_pos.row - 1, current_pos.col)
        if self._is_position_occupied(new_position):
            # 如果目标位置被占用，交换节点
            return self._swap_nodes(node_id, self.grid[new_position.row][new_position.col])
        else:
            return self.move_node(node_id, new_position)
    
    def move_node_down(self, node_id: str) -> bool:
        """节点下移"""
        if node_id not in self.node_positions:
            return False
            
        current_pos = self.node_positions[node_id]
        if current_pos.row >= self.rows - 1:
            # 需要扩展行数
            self.add_rows(5)
            
        new_position = GridPosition(current_pos.row + 1, current_pos.col)
        if self._is_position_occupied(new_position):
            # 如果目标位置被占用，交换节点
            return self._swap_nodes(node_id, self.grid[new_position.row][new_position.col])
        else:
            return self.move_node(node_id, new_position)
    
    def move_node_left(self, node_id: str) -> bool:
        """节点左移"""
        if node_id not in self.node_positions:
            return False
            
        current_pos = self.node_positions[node_id]
        if current_pos.col == 0:
            return False  # 已经在最左边
            
        # 在新列中寻找合适位置
        target_col = current_pos.col - 1
        new_position = self._find_position_in_column(target_col, preferred_row=current_pos.row)
        return self.move_node(node_id, new_position)
    
    def move_node_right(self, node_id: str) -> bool:
        """节点右移"""
        if node_id not in self.node_positions:
            return False
            
        current_pos = self.node_positions[node_id]
        if current_pos.col >= self.cols - 1:
            # 需要添加新列
            self.add_column()
            
        # 在新列中寻找合适位置
        target_col = current_pos.col + 1
        new_position = self._find_position_in_column(target_col, preferred_row=current_pos.row)
        return self.move_node(node_id, new_position)
    
    def remove_node(self, node_id: str) -> bool:
        """移除节点"""
        if node_id not in self.node_positions:
            return False
            
        position = self.node_positions[node_id]
        self.grid[position.row][position.col] = None
        del self.node_positions[node_id]
        del self.position_nodes[(position.row, position.col)]
        return True
    
    def get_node_position(self, node_id: str) -> Optional[GridPosition]:
        """获取节点位置"""
        return self.node_positions.get(node_id)
    
    def get_node_at_position(self, position: GridPosition) -> Optional[str]:
        """获取指定位置的节点"""
        if not self._is_position_valid(position):
            return None
        return self.grid[position.row][position.col]
    
    def get_column_nodes(self, col: int) -> List[Tuple[str, int]]:
        """获取指定列的所有节点，按行排序
        
        Returns:
            List of (node_id, row) tuples
        """
        if col >= self.cols:
            return []
            
        nodes = []
        for row in range(self.rows):
            if self.grid[row][col] is not None:
                nodes.append((self.grid[row][col], row))
        return nodes
    
    def get_layout_dict(self) -> Dict[str, Any]:
        """获取布局的字典表示，用于序列化和API交互"""
        return {
            "grid_size": {"rows": self.rows, "cols": self.cols},
            "node_positions": {
                node_id: {"row": pos.row, "col": pos.col} 
                for node_id, pos in self.node_positions.items()
            },
            "column_layouts": [
                [self.grid[row][col] for row in range(self.rows) if self.grid[row][col] is not None]
                for col in range(self.cols)
            ]
        }
    
    def _find_next_available_position(self) -> GridPosition:
        """寻找下一个可用位置"""
        # 优先填满第一列，然后是第二列...
        for col in range(self.cols):
            for row in range(self.rows):
                if self.grid[row][col] is None:
                    return GridPosition(row, col)
        
        # 如果所有位置都满了，添加新行
        self.add_rows(5)
        return GridPosition(self.rows - 5, 0)
    
    def _find_position_in_column(self, col: int, preferred_row: int = None) -> GridPosition:
        """在指定列中寻找位置"""
        if col >= self.cols:
            raise ValueError(f"列索引 {col} 超出范围")
        
        # 如果指定了优选行且该位置可用，使用它
        if preferred_row is not None and preferred_row < self.rows:
            if self.grid[preferred_row][col] is None:
                return GridPosition(preferred_row, col)
        
        # 否则寻找该列的第一个空位
        for row in range(self.rows):
            if self.grid[row][col] is None:
                return GridPosition(row, col)
        
        # 如果该列已满，添加新行
        self.add_rows(5)
        return GridPosition(self.rows - 5, col)
    
    def _is_position_valid(self, position: GridPosition) -> bool:
        """检查位置是否有效"""
        return (0 <= position.row < self.rows and 
                0 <= position.col < self.cols)
    
    def _is_position_occupied(self, position: GridPosition) -> bool:
        """检查位置是否被占用"""
        if not self._is_position_valid(position):
            return False
        return self.grid[position.row][position.col] is not None
    
    def _swap_nodes(self, node_id1: str, node_id2: str) -> bool:
        """交换两个节点的位置"""
        if node_id1 not in self.node_positions or node_id2 not in self.node_positions:
            return False
        
        pos1 = self.node_positions[node_id1]
        pos2 = self.node_positions[node_id2]
        
        # 交换网格中的位置
        self.grid[pos1.row][pos1.col] = node_id2
        self.grid[pos2.row][pos2.col] = node_id1
        
        # 更新映射
        self.node_positions[node_id1] = pos2
        self.node_positions[node_id2] = pos1
        self.position_nodes[(pos1.row, pos1.col)] = node_id2
        self.position_nodes[(pos2.row, pos2.col)] = node_id1
        
        return True
    
    def compact_layout(self):
        """压缩布局，移除空行和列"""
        # 移除空行
        used_rows = set()
        for node_id, pos in self.node_positions.items():
            used_rows.add(pos.row)
        
        if used_rows:
            max_used_row = max(used_rows)
            # 保留一些空行用于扩展
            self.rows = max_used_row + 5
            self.grid = self.grid[:self.rows]
    
    def print_layout(self) -> str:
        """打印布局，用于调试"""
        result = []
        result.append(f"布局 ({self.rows}x{self.cols}):")
        result.append("+" + "-" * (self.cols * 12 + 1) + "+")
        
        for row in range(min(self.rows, 10)):  # 只显示前10行
            row_str = "|"
            for col in range(self.cols):
                node_id = self.grid[row][col]
                if node_id:
                    # 截断长ID
                    display_id = node_id[:10] if len(node_id) > 10 else node_id
                    row_str += f"{display_id:^11}|"
                else:
                    row_str += f"{'':^11}|"
            result.append(row_str)
        
        if self.rows > 10:
            result.append("|" + "..." * self.cols + "|")
        
        result.append("+" + "-" * (self.cols * 12 + 1) + "+")
        return "\n".join(result) 