"""
Graph类 - 扁平化的自动依赖追踪计算图
"""

from typing import Dict, Any, Callable, List, Optional, Set
import threading
from contextlib import contextmanager


class DependencyTracker:
    """依赖关系追踪器"""
    
    def __init__(self):
        self._tracking = threading.local()
    
    @contextmanager
    def track_dependencies(self):
        """上下文管理器，用于追踪依赖关系"""
        if not hasattr(self._tracking, 'dependencies'):
            self._tracking.dependencies = set()
        
        old_deps = getattr(self._tracking, 'dependencies', set())
        self._tracking.dependencies = set()
        
        try:
            yield self._tracking.dependencies
        finally:
            self._tracking.dependencies = old_deps
    
    def record_access(self, param_name: str):
        """记录参数访问"""
        if hasattr(self._tracking, 'dependencies'):
            self._tracking.dependencies.add(param_name)
    
    def is_tracking(self) -> bool:
        """检查是否正在追踪"""
        return hasattr(self._tracking, 'dependencies')


class ComputedParameter:
    """计算参数，支持自动依赖追踪的计算函数"""
    
    def __init__(self, name: str, func: Callable, graph: 'Graph', description: str = "", group: str = ""):
        self.name = name
        self.func = func
        self.graph = graph
        self.description = description
        self.group = group
        self.dependencies: Set[str] = set()
        self._value = None
        self._computed = False
    
    def compute(self) -> Any:
        """执行计算并追踪依赖关系"""
        # 检查是否已经在计算中（循环依赖检测）
        if self.name in self.graph._computing_params:
            raise ValueError(f"检测到循环依赖：参数 '{self.name}' 在计算过程中被重复访问")
        
        self.graph._computing_params.add(self.name)
        
        try:
            with self.graph._dependency_tracker.track_dependencies() as deps:
                try:
                    # 执行计算函数
                    result = self.func()
                    
                    # 记录依赖关系
                    self.dependencies = deps.copy()
                    self._value = result
                    self._computed = True
                    
                    return result
                    
                except ValueError as e:
                    # 循环依赖异常不应该被捕获，直接抛出
                    if "检测到循环依赖" in str(e):
                        raise
                    print(f"计算参数 '{self.name}' 时发生错误: {e}")
                    # 设置错误时的默认值
                    self._value = 0
                    self._computed = True
                    return 0
                except Exception as e:
                    print(f"计算参数 '{self.name}' 时发生错误: {e}")
                    # 设置错误时的默认值
                    self._value = 0
                    self._computed = True
                    return 0
        finally:
            self.graph._computing_params.discard(self.name)
    
    @property
    def value(self):
        """获取计算值"""
        if not self._computed:
            self.compute()
        return self._value
    
    def invalidate(self):
        """使计算结果失效"""
        self._computed = False
        self._value = None


class Graph:
    """
    扁平化的自动依赖追踪计算图
    
    用法示例：
    ```python
    g = Graph("设计")
    
    # 设置基础值
    g["CPU_频率"] = 3.0
    g["CPU_电压"] = 1.8
    g["CPU_核心数"] = 8
    
    # 定义计算函数
    def cpu_power():
        return g["CPU_频率"] * g["CPU_电压"] * g["CPU_核心数"] * 0.5
    
    # 添加计算参数
    g.add_computed("CPU_功耗", cpu_power)
    
    # 访问计算结果
    print(g["CPU_功耗"])  # 自动计算并追踪依赖
    ```
    """
    
    def __init__(self, name: str):
        self.name = name
        self._parameters: Dict[str, Any] = {}  # 参数名 -> 值
        self._computed_parameters: Dict[str, ComputedParameter] = {}  # 计算参数
        self._dependency_tracker = DependencyTracker()
        self._dependency_graph: Dict[str, Set[str]] = {}  # 被依赖者 -> 依赖者集合
        self._parameter_groups: Dict[str, str] = {}  # 参数名 -> 组名
        self._updating_params: Set[str] = set()  # 正在更新的参数集合，用于循环检测
        self._computing_params: Set[str] = set()  # 正在计算的参数集合，用于循环检测
    
    def __getitem__(self, param_name: str) -> Any:
        """支持 g["参数名"] 访问"""
        # 记录依赖关系
        if self._dependency_tracker.is_tracking():
            self._dependency_tracker.record_access(param_name)
        
        # 如果是计算参数，返回计算值
        if param_name in self._computed_parameters:
            return self._computed_parameters[param_name].value
        
        # 如果是普通参数，返回值
        if param_name in self._parameters:
            return self._parameters[param_name]
        
        raise KeyError(f"参数 '{param_name}' 不存在")
    
    def __setitem__(self, param_name: str, value: Any):
        """支持 g["参数名"] = 值 设置"""
        # 设置值
        self._parameters[param_name] = value
        
        # 如果有依赖此参数的计算参数，使其失效
        self._invalidate_dependents(param_name)
    
    def __contains__(self, param_name: str) -> bool:
        """支持 'param' in g 检查"""
        return param_name in self._parameters or param_name in self._computed_parameters
    
    def add_computed(self, param_name: str, func: Callable, description: str = "", group: str = ""):
        """
        添加计算参数
        
        Args:
            param_name: 参数名称
            func: 计算函数
            description: 描述
            group: 分组（可选）
        """
        # 创建计算参数
        computed_param = ComputedParameter(param_name, func, self, description, group)
        
        # 存储计算参数
        self._computed_parameters[param_name] = computed_param
        
        # 设置分组
        if group:
            self._parameter_groups[param_name] = group
        
        # 立即计算一次以建立依赖关系
        computed_param.compute()
        
        # 更新依赖图
        self._update_dependency_graph(param_name, computed_param.dependencies)
    
    def set_group(self, param_name: str, group: str):
        """设置参数分组"""
        self._parameter_groups[param_name] = group
    
    def get_group(self, param_name: str) -> Optional[str]:
        """获取参数分组"""
        return self._parameter_groups.get(param_name)
    
    def get_parameters_by_group(self, group: str) -> List[str]:
        """获取指定组的所有参数"""
        result = []
        for param_name, param_group in self._parameter_groups.items():
            if param_group == group:
                result.append(param_name)
        return result
    
    def get_all_groups(self) -> Set[str]:
        """获取所有组名"""
        return set(self._parameter_groups.values())
    
    def keys(self):
        """获取所有参数名"""
        all_params = set(self._parameters.keys())
        all_params.update(self._computed_parameters.keys())
        return list(all_params)
    
    def values(self):
        """获取所有参数值"""
        result = []
        for param_name in self.keys():
            result.append(self[param_name])
        return result
    
    def items(self):
        """获取所有参数名值对"""
        result = []
        for param_name in self.keys():
            result.append((param_name, self[param_name]))
        return result
    
    def update(self, data: Dict[str, Any]):
        """批量更新参数"""
        for param_name, value in data.items():
            self[param_name] = value
    
    def _update_dependency_graph(self, computed_name: str, dependencies: Set[str]):
        """更新依赖图"""
        # 清除旧的依赖关系
        for dep_param in self._dependency_graph:
            if computed_name in self._dependency_graph[dep_param]:
                self._dependency_graph[dep_param].remove(computed_name)
        
        # 添加新的依赖关系
        for dep_param in dependencies:
            if dep_param not in self._dependency_graph:
                self._dependency_graph[dep_param] = set()
            self._dependency_graph[dep_param].add(computed_name)
    
    def _invalidate_dependents(self, param_name: str, visited: Set[str] = None):
        """使依赖指定参数的所有计算参数失效"""
        if visited is None:
            visited = set()
            # 如果这是顶层调用，清空正在更新的参数集合
            self._updating_params.clear()
        
        # 检查循环依赖
        if param_name in self._updating_params:
            raise ValueError(f"检测到循环依赖：参数 '{param_name}' 在更新链中重复出现")
        
        if param_name in visited:
            return  # 避免重复处理
        
        visited.add(param_name)
        self._updating_params.add(param_name)
        
        if param_name in self._dependency_graph:
            for dependent in self._dependency_graph[param_name]:
                if dependent in self._computed_parameters:
                    self._computed_parameters[dependent].invalidate()
                    # 递归使依赖者的依赖者也失效
                    self._invalidate_dependents(dependent, visited)
        
        # 处理完成后从更新集合中移除
        self._updating_params.discard(param_name)
    
    def get_computed_info(self, param_name: str) -> Dict[str, Any]:
        """获取计算参数信息"""
        if param_name not in self._computed_parameters:
            return {}
        
        computed_param = self._computed_parameters[param_name]
        return {
            'name': computed_param.name,
            'description': computed_param.description,
            'group': computed_param.group,
            'dependencies': list(computed_param.dependencies),
            'computed': computed_param._computed,
            'value': computed_param._value
        }
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """
        获取完整的依赖关系图
        返回格式: {被依赖参数: [依赖它的参数列表]}
        """
        result = {}
        for param_name, dependents in self._dependency_graph.items():
            result[param_name] = list(dependents)
        return result
    
    def get_reverse_dependency_graph(self) -> Dict[str, List[str]]:
        """
        获取反向依赖关系图  
        返回格式: {参数: [它依赖的参数列表]}
        """
        result = {}
        
        # 初始化所有参数
        for param_name in self.keys():
            result[param_name] = []
        
        # 构建反向依赖关系
        for param_name, computed_param in self._computed_parameters.items():
            result[param_name] = list(computed_param.dependencies)
        
        return result
    
    def get_dependency_chain(self, param_name: str) -> List[str]:
        """
        获取参数的完整依赖链
        返回从根参数到目标参数的完整依赖路径
        """
        if param_name not in self._computed_parameters:
            return [param_name]  # 基础参数，无依赖
        
        def _get_chain(current_param: str, visited: Set[str]) -> List[str]:
            if current_param in visited:
                return []  # 避免循环依赖
            
            visited.add(current_param)
            
            if current_param not in self._computed_parameters:
                return [current_param]  # 基础参数
            
            computed_param = self._computed_parameters[current_param]
            chain = []
            
            # 递归获取所有依赖的链
            for dep in computed_param.dependencies:
                dep_chain = _get_chain(dep, visited.copy())
                chain.extend(dep_chain)
            
            chain.append(current_param)
            return chain
        
        return _get_chain(param_name, set())
    
    def get_dependents_chain(self, param_name: str) -> List[str]:
        """
        获取参数的完整依赖者链
        返回从目标参数到所有最终依赖者的完整路径
        """
        def _get_dependents_chain(current_param: str, visited: Set[str]) -> List[str]:
            if current_param in visited:
                return []  # 避免循环依赖
            
            visited.add(current_param)
            chain = [current_param]
            
            if current_param in self._dependency_graph:
                for dependent in self._dependency_graph[current_param]:
                    dependent_chain = _get_dependents_chain(dependent, visited.copy())
                    chain.extend(dependent_chain)
            
            return chain
        
        return _get_dependents_chain(param_name, set())
    
    def refresh_all_computed(self):
        """刷新所有计算参数的值"""
        # 使所有计算参数失效
        for computed_param in self._computed_parameters.values():
            computed_param.invalidate()
        
        # 重新计算所有计算参数
        for param_name in self._computed_parameters:
            _ = self[param_name]  # 触发计算
    
    def refresh_dependents(self, param_name: str):
        """刷新指定参数的所有依赖者"""
        # 使用相同的循环检测机制
        self._invalidate_dependents(param_name)
    
    def detect_circular_dependencies(self) -> List[str]:
        """检测图中的循环依赖"""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(param_name: str, path: List[str]) -> bool:
            if param_name in rec_stack:
                # 找到循环，记录循环路径
                cycle_start = path.index(param_name)
                cycle = path[cycle_start:] + [param_name]
                cycles.append(" -> ".join(cycle))
                return True
            
            if param_name in visited:
                return False
            
            visited.add(param_name)
            rec_stack.add(param_name)
            
            # 检查这个参数的所有依赖者
            if param_name in self._dependency_graph:
                for dependent in self._dependency_graph[param_name]:
                    if dfs(dependent, path + [param_name]):
                        return True
            
            rec_stack.remove(param_name)
            return False
        
        # 检查所有参数
        for param_name in self.keys():
            if param_name not in visited:
                dfs(param_name, [])
        
        return cycles
    
    def print_structure(self):
        """打印图结构"""
        print(f"图: {self.name}")
        print("=" * 50)
        
        # 按组分类显示
        groups = self.get_all_groups()
        ungrouped_params = []
        
        for group in sorted(groups):
            print(f"\n📁 组: {group}")
            params = self.get_parameters_by_group(group)
            for param_name in sorted(params):
                self._print_parameter(param_name)
        
        # 显示未分组的参数
        for param_name in self.keys():
            if param_name not in self._parameter_groups:
                ungrouped_params.append(param_name)
        
        if ungrouped_params:
            print(f"\n📦 未分组参数:")
            for param_name in sorted(ungrouped_params):
                self._print_parameter(param_name)
    
    def _print_parameter(self, param_name: str):
        """打印单个参数信息"""
        if param_name in self._computed_parameters:
            computed_param = self._computed_parameters[param_name]
            deps = ", ".join(computed_param.dependencies) if computed_param.dependencies else "无"
            desc = f" ({computed_param.description})" if computed_param.description else ""
            print(f"  🔹 {param_name}: {computed_param.value} [计算, 依赖: {deps}]{desc}")
        else:
            value = self._parameters.get(param_name, "未知")
            print(f"  🔸 {param_name}: {value}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            'name': self.name,
            'parameters': {},
            'computed_parameters': {},
            'dependency_graph': {},
            'parameter_groups': self._parameter_groups.copy()
        }
        
        # 导出普通参数
        for param_name, value in self._parameters.items():
            result['parameters'][param_name] = {
                'type': 'value',
                'value': value
            }
        
        # 导出计算参数
        for param_name, computed_param in self._computed_parameters.items():
            result['computed_parameters'][param_name] = {
                'type': 'computed',
                'value': computed_param._value,
                'description': computed_param.description,
                'group': computed_param.group,
                'dependencies': list(computed_param.dependencies)
            }
        
        # 导出依赖图
        for dep_param, dependents in self._dependency_graph.items():
            result['dependency_graph'][dep_param] = list(dependents)
        
        return result
    
    def save(self, filepath: str):
        """保存到文件"""
        import json
        data = self.to_dict()
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ 图已保存到: {filepath}")
            return True
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return False
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"Graph(name='{self.name}', params={len(self.keys())})"
    
    def __str__(self) -> str:
        """用户友好的字符串表示"""
        return f"图 '{self.name}' (包含 {len(self.keys())} 个参数)"