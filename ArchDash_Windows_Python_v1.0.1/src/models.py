from typing import Dict, List, Optional, Any, Union, Callable, TypeVar, cast, Tuple
from dataclasses import dataclass, field
import numpy as np
import json
from datetime import datetime
import uuid
import os
import traceback

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
        unlinked: 是否断开计算连接（用户手动设置值时为True）
        _graph: 所属的计算图（用于自动更新传播）
        _calculation_traceback: 新增属性
    """
    name: str
    unit: str
    description: str = ""
    confidence: float = 1.0
    calculation_func: Optional[str] = None
    dependencies: List['Parameter'] = field(default_factory=list)
    unlinked: bool = False  # 是否断开计算连接

    _value: T = 0.0  # 内部值存储
    _graph: Optional['CalculationGraph'] = field(default=None, repr=False)  # 计算图引用
    _internal_id: uuid.UUID = field(default_factory=uuid.uuid4, repr=False)  # 内部唯一ID
    _calculation_traceback: Optional[str] = field(default=None, repr=False) # 新增属性
    
    def __init__(self, name: str, value: T = 0.0, unit: str = "", **kwargs):
        self.name = name
        self._value = value
        self.unit = unit
        self.description = kwargs.get('description', "")
        self.confidence = kwargs.get('confidence', 1.0)
        self.calculation_func = kwargs.get('calculation_func', None)
        self.dependencies = kwargs.get('dependencies', [])
        self.unlinked = kwargs.get('unlinked', False)
        self.param_type = kwargs.get('param_type', "float")  # 新增：参数类型，默认为float
        self._graph = kwargs.get('_graph', None)
        self._internal_id = uuid.uuid4()
    
    @property
    def value(self) -> T:
        """获取参数值"""
        return self._value
    
    @value.setter 
    def value(self, new_value: T):
        """设置参数值"""
        # Setter只负责更新值，不再触发传播
        # 传播将由CalculationGraph统一管理
        if self._value != new_value:
            self._value = new_value
    
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
        """添加依赖参数，并立即在图上注册此关系"""
        if not isinstance(param, Parameter):
            raise TypeError("依赖参数必须是Parameter类型")
        if param is self:
            raise ValueError("参数不能依赖自身")
        if param not in self.dependencies:
            self.dependencies.append(param)
            # 立即在图上更新依赖关系
            if self._graph:
                self._graph.register_dependency(dependent=self, dependency=param)
    
    def calculate(self) -> T:
        """计算参数值并返回结果，但不直接修改内部状态。
        
        Returns:
            T: 计算后的参数值
        
        Raises:
            ValueError: 如果计算失败
        """
        if not self.calculation_func or self.unlinked:
            return self._value

        for dep in self.dependencies:
            if dep.value is None:
                raise ValueError(f"依赖参数 {dep.name} 的值缺失")

        # 如果 calculation_func 是一个可调用对象（例如函数）
        if callable(self.calculation_func):
            try:
                # 直接调用该函数，并将参数自身作为参数传递
                result = self.calculation_func(self)
                self._value = result
                self._calculation_traceback = None # 计算成功，清除回溯
                return result
            except Exception as e:
                self._calculation_traceback = traceback.format_exc() # 捕获回溯
                print(f"计算错误: 在执行参数 '{self.name}' 的计算函数时发生错误: {e}")
                return self._value

        import math
        import builtins
        
        safe_globals = {
            '__builtins__': builtins.__dict__.copy(), # 修改这里
            'math': math,
            'datetime': datetime,
        }
        
        local_env = {
            'dependencies': self.dependencies,
            'value': self._value,
            'datetime': datetime,
            'self': self
        }
        
        try:
            exec(self.calculation_func, safe_globals, local_env)
            result = local_env.get('result')
            if result is None:
                # 如果计算函数没有产生 'result'，也视为一种计算失败
                raise ValueError("计算函数未设置result变量作为输出")
            self._value = result
            self._calculation_traceback = None # 计算成功，清除回溯
            return result
        except Exception as e:
            self._calculation_traceback = traceback.format_exc() # 捕获回溯
            print(f"计算错误: 在执行参数 '{self.name}' 的计算时发生错误: {e}")
            raise ValueError(f"计算失败: {e}") from e
    
    def relink_and_calculate(self) -> T:
        """重新连接参数，计算并更新其值，然后返回新值。"""
        self.unlinked = False
        if self.calculation_func:
            new_value = self.calculate()
            # 通过图来传播更新
            if self._graph:
                self._graph.set_parameter_value(self, new_value)
            return new_value
        return self.value
    
    def set_manual_value(self, new_value: T) -> None:
        """手动设置参数值并标记为unlinked
        
        Args:
            new_value: 新的参数值
        """
        if self.calculation_func and self.dependencies:
            # 只有有计算函数和依赖的参数才能被unlink
            self.unlinked = True
            import warnings
            warnings.warn(f"参数 {self.name} 已断开自动计算连接")
        self.value = new_value
    
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
            "unlinked": self.unlinked,
            "param_type": self.param_type,  # 新增：包含参数类型
            "calculation_traceback": self._calculation_traceback
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
            calculation_func=data["calculation_func"],
            unlinked=data.get("unlinked", False),
            param_type=data.get("param_type", "float")  # 新增：读取参数类型，默认为float（兼容旧格式）
        )
        
        # 添加依赖
        for dep_name in data["dependencies"]:
            if dep_name in param_dict:
                param.add_dependency(param_dict[dep_name])
        
        return param

    def __hash__(self):
        return hash(self._internal_id)

    def __eq__(self, other):
        if not isinstance(other, Parameter):
            return NotImplemented
        return self._internal_id == other._internal_id

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
    id: str = ""  # 默认为空字符串，由CalculationGraph分配
    node_type: str = "default"
    
    def __init__(self, name, description="", id=None, **kwargs):
        self.id = id or ""  # 如果没有提供ID，使用空字符串
        self.name = name
        self.description = description
        self.node_type = kwargs.get('node_type', "default")
        self.parameters = []  # 确保每个Node实例都有parameters属性
        
        # 为节点分配一个唯一的内部ID，用于哈希和相等性比较
        self._internal_id = uuid.uuid4()

        for key, value in kwargs.items():
            if key != 'node_type':
                setattr(self, key, value)
    
    def __hash__(self):
        return hash(self._internal_id)

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return self._internal_id == other._internal_id
    
    def add_parameter(self, parameter: Parameter) -> None:
        """添加参数到节点"""
        self.parameters.append(parameter)
    
    def remove_parameter(self, name: str) -> None:
        """从节点移除参数"""
        self.parameters = [param for param in self.parameters if param.name != name]
    
    def get_parameter(self, name: str) -> Optional[Parameter]:
        """通过名称获取参数对象"""
        for param in self.parameters:
            if param.name == name:
                return param
        return None
    
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
        self._dependents_map: Dict[int, List[int]] = {}
        self._all_parameters: Dict[int, Parameter] = {}
        self.layout_manager: Optional['CanvasLayoutManager'] = None
        self._next_node_id = 1
        self.recently_updated_params: set[str] = set()
        
    def get_next_node_id(self) -> str:
        """生成下一个唯一的节点ID"""
        node_id = self._next_node_id
        self._next_node_id += 1
        return str(node_id)

    def add_node(self, node: Node, auto_place: bool = True) -> None:
        """向计算图中添加一个节点"""
        # 检查节点ID和名称是否已存在
        if node.id and node.id in self.nodes:
            raise ValueError(f"Node with id {node.id} already exists.")
        for existing_node in self.nodes.values():
            if existing_node.name == node.name:
                raise ValueError(f"Node with name '{node.name}' already exists.")

        if not node.id:
            node.id = self.get_next_node_id()
        
        self.nodes[node.id] = node
        
        # 为节点中的所有参数设置图引用
        for param in node.parameters:
            param.set_graph(self)
        
        if auto_place and self.layout_manager:
            self.layout_manager.place_node(node.id)
        
        # 节点加入后，强制重建依赖图以确保所有关系都被注册
        self._rebuild_dependency_graph()

    def add_parameter_to_node(self, node_id: str, param: 'Parameter'):
        """向指定节点添加参数，并建立图的引用"""
        node = self.nodes.get(node_id)
        if not node:
            raise ValueError(f"ID为 {node_id} 的节点不存在")
        
        # 建立参数与图的双向引用
        param.set_graph(self)
        
        node.add_parameter(param)
        
        # 参数加入后其依赖关系会被自动注册
        self._rebuild_dependency_graph()

    def update_parameter_dependencies(self, param):
        """更新单个参数的依赖关系"""
        param_id = id(param)
        
        if param_id not in self._all_parameters:
            self._all_parameters[param_id] = param
            self._dependents_map[param_id] = []
            param.set_graph(self)
        
        # 重建依赖图以反映变化
        self._rebuild_dependency_graph()

    def register_dependency(self, dependent: 'Parameter', dependency: 'Parameter'):
        """直接注册一个依赖关系"""
        if dependency not in self._dependents_map:
            self._dependents_map[dependency] = []
        if dependent not in self._dependents_map[dependency]:
            self._dependents_map[dependency].append(dependent)

    def _rebuild_dependency_graph(self):
        """完全重建图的依赖关系映射"""
        self._dependents_map.clear()
        
        all_params = [p for node in self.nodes.values() for p in node.parameters]
        
        for param in all_params:
            # 确保每个参数都在依赖图中有一个条目
            if param not in self._dependents_map:
                self._dependents_map[param] = []
            
            # 遍历其依赖项，并将自己添加到依赖项的"依赖者"列表中
            for dep in param.dependencies:
                if dep not in self._dependents_map:
                    self._dependents_map[dep] = []
                if param not in self._dependents_map[dep]:
                    self._dependents_map[dep].append(param)

    def propagate_updates(self, changed_param: 'Parameter') -> List[Dict[str, Any]]:
        """从一个改变的参数开始，递归地更新所有依赖它的下游参数"""
        
        # visited 集合应在每次顶级调用时初始化
        visited: set['Parameter'] = set()
        
        def _propagate(param: 'Parameter'):
            if param in visited:
                return []
            visited.add(param)
            
            updated_params_info = []
            dependents = self._dependents_map.get(param, [])

            for dependent_param in dependents:
                if not dependent_param.unlinked:
                    old_value = dependent_param.value
                    try:
                        new_value = dependent_param.calculate()
                        
                        if old_value != new_value:
                            # 直接更新内部值以避免循环
                            dependent_param._value = new_value 
                            
                            updated_params_info.append({
                                'param': dependent_param,
                                'old_value': old_value,
                                'new_value': new_value
                            })
                            # 显式递归
                            updated_params_info.extend(_propagate(dependent_param))
                    except Exception as e:
                        print(f"在更新传播期间，参数 {dependent_param.name} 计算失败: {e}")

            return updated_params_info

        # 从最初改变的参数开始传播
        return _propagate(changed_param)

    def set_parameter_value(self, param, new_value):
        """通过图来设置参数值，并返回所有更新的摘要"""
        old_value = param.value
        
        if old_value == new_value:
            return {
                'primary_change': None,
                'cascaded_updates': [],
                'total_updated_params': 0
            }

        # 更新主参数的值
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
        
        # 从这里统一启动传播
        cascaded_updates = self.propagate_updates(param)
        update_result['cascaded_updates'] = cascaded_updates
        update_result['total_updated_params'] += len(cascaded_updates)
        
        return update_result

    def recalculate_all(self):
        """重新计算所有参数"""
        for node in self.nodes.values():
            node.calculate_all()

    def get_dependency_chain(self, param):
        """获取一个参数的所有上游和下游依赖"""
        
        # 确保依赖图是最新的
        self._rebuild_dependency_graph()

        # 获取上游依赖（它依赖的）
        upstream = []
        visited_up = set()
        
        # 获取下游依赖（依赖它的）
        downstream = []
        visited_down = set()
        
        def get_dependents_recursive(p, depth=0, max_depth=10):
            if p in visited_down or depth >= max_depth:
                return
            visited_down.add(p)
            
            # 使用重建后的 _dependents_map
            dependents = self._dependents_map.get(p, [])
            for dep_param in dependents:
                downstream.append(dep_param)
                get_dependents_recursive(dep_param, depth + 1)
        
        get_dependents_recursive(param)
        
        return {"upstream": upstream, "downstream": downstream}

    def get_node(self, node_id: str) -> Optional[Node]:
        """通过ID获取节点"""
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
                    unlinked=param_data.get("unlinked", False)
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

    @property
    def lm(self) -> Optional['CanvasLayoutManager']:
        """布局管理器的快捷访问属性(等同于 self.layout_manager)"""
        return self.layout_manager

    # 向后兼容，若尝试访问未定义属性且 layout_manager 存在，则代理到 layout_manager
    def __getattr__(self, item):
        if self.layout_manager and hasattr(self.layout_manager, item):
            return getattr(self.layout_manager, item)
        raise AttributeError(f"{self.__class__.__name__} 对象没有属性 {item}")

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
        self.cols = initial_cols
        self.rows = initial_rows
        self.reset()
    
    def reset(self):
        """重置布局管理器状态"""
        self.grid = [[None] * self.cols for _ in range(self.rows)]
        self.node_positions = {}
        self.position_nodes = {}
    
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
    
    def remove_column(self) -> bool:
        """删除最后一列，但需要先确认最后一列是空的
        
        Returns:
            bool: 删除是否成功
        """
        if self.cols <= 1:
            return False  # 至少保留一列
        
        # 检查最后一列是否为空
        last_col = self.cols - 1
        for row in range(self.rows):
            if self.grid[row][last_col] is not None:
                return False  # 最后一列不为空，不能删除
        
        # 删除最后一列
        for row in self.grid:
            row.pop()
        self.cols -= 1
        
        return True
        
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

    def ensure_minimum_columns(self, minimum_cols: int = 3) -> bool:
        """确保列数不少于 minimum_cols, 不足时自动扩展"""
        while self.cols < minimum_cols:
            self.add_column()
        return self.cols >= minimum_cols

    def can_remove_column(self, minimum_cols: int = 3) -> Tuple[bool, str]:
        """检查是否可以删除最后一列 (空列且不低于最小列数)"""
        if self.cols <= minimum_cols:
            return False, "已达到最小列数限制"

        last_col = self.cols - 1
        for row in range(self.rows):
            if self.grid[row][last_col] is not None:
                return False, "最后一列不为空, 无法删除"
        return True, "可以删除"

    def can_add_column(self, max_cols: int = 6) -> Tuple[bool, str]:
        """检查是否可以添加列"""
        if self.cols >= max_cols:
            return False, f"已达到最大列数限制({max_cols})"
        return True, "可以添加"

    def remove_last_column_if_empty(self, minimum_cols: int = 3) -> bool:
        """如果最后一列为空，则删除它，并返回True，否则返回False"""
        if self.cols <= minimum_cols:
            return False
            
        last_col_index = self.cols - 1
        nodes_in_last_col = self.get_column_nodes(last_col_index)
        
        if not nodes_in_last_col:
            self.cols -= 1
            return True
        return False

    def auto_remove_empty_last_columns(self, minimum_cols: int = 3) -> int:
        """从后向前检查并删除所有连续的空列，返回删除的列数"""
        removed_count = 0
        while self.remove_last_column_if_empty(minimum_cols):
            removed_count += 1
        return removed_count

    def auto_expand_for_node_movement(self, node_id: str, direction: str, max_cols: int = 6) -> bool:
        """当节点向右移动时，如果需要，自动扩展列"""
        if direction != "right":
            return False
        pos = self.get_node_position(node_id)
        if not pos:
            return False
        if pos.col >= self.cols - 1:
            can_add, _ = self.can_add_column(max_cols)
            if can_add:
                self.add_column()
                return True
        return False 