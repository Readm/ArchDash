# Parameter编辑功能开发任务分析

## 任务概述
开发一个复杂的参数编辑功能，包含依赖管理、代码编辑和实时计算。

## 核心需求分析

### 1. 新窗口界面设计
- **模态窗口**：用于参数编辑
- **参数基本信息编辑**：名称、值、单位、描述
- **依赖选择器**：选择其他节点或当前节点的参数作为依赖
- **代码编辑器**：输入计算函数代码
- **Reset按钮**：生成基础函数模板
- **预览/测试**：实时显示计算结果

### 2. 后端模型理解（基于models.py分析）

#### Parameter类关键属性：
- `dependencies: List[Parameter]` - 依赖参数列表
- `calculation_func: Optional[str]` - 计算函数字符串
- `calculate()` - 执行计算的方法

#### 计算机制：
```python
# 计算环境
local_env = {
    'self': self,
    'dependencies': self.dependencies,  # 依赖参数列表
    'value': self.value,                # 当前值
    'datetime': datetime
}

# 执行代码
exec(self.calculation_func, {"__builtins__": {}}, local_env)
result = local_env.get('result', None)  # 获取result变量
```

#### 依赖管理：
- `add_dependency(param)` - 添加依赖
- 检查循环依赖（参数不能依赖自身）
- 依赖参数必须有值才能计算

### 3. 功能分解

#### 阶段1：基础UI结构
- [ ] 创建参数编辑模态窗口
- [ ] 基本信息编辑表单
- [ ] 依赖参数选择器
- [ ] 代码编辑文本框
- [ ] 按钮组（保存、取消、Reset、测试）

#### 阶段2：依赖管理系统
- [ ] 获取所有可用参数（全局参数收集）
- [ ] 依赖选择组件（多选下拉框）
- [ ] 依赖关系验证（防止循环依赖）
- [ ] 依赖同步到后端模型

#### 阶段3：代码编辑与模板生成
- [ ] Reset功能：生成基础函数模板
- [ ] 代码语法高亮（可选）
- [ ] 代码验证和错误处理

#### 阶段4：实时计算与预览
- [ ] 测试计算功能
- [ ] 错误信息显示
- [ ] 结果预览

#### 阶段5：数据持久化
- [ ] 保存参数修改到模型
- [ ] 更新UI显示
- [ ] 触发相关计算更新

### 4. 技术挑战

#### 4.1 全局参数收集
需要遍历所有节点的所有参数，构建可选择的依赖列表：
```python
def get_all_available_parameters(graph, current_node_id, current_param_name):
    """获取所有可用的参数，排除当前参数自身"""
    available_params = []
    for node_id, node in graph.nodes.items():
        for param in node.parameters:
            if not (node_id == current_node_id and param.name == current_param_name):
                available_params.append({
                    'node_name': node.name,
                    'param_name': param.name,
                    'param_obj': param,
                    'display_name': f"{node.name}.{param.name}"
                })
    return available_params
```

#### 4.2 依赖关系管理
- 防止循环依赖
- 动态更新依赖列表
- 参数引用同步

#### 4.3 代码模板生成
基于选择的依赖生成函数模板：
```python
def generate_code_template(dependencies):
    """生成基础计算函数模板"""
    if not dependencies:
        return "# 无依赖参数\nresult = value"
    
    code_lines = ["# 计算函数"]
    for i, dep in enumerate(dependencies):
        code_lines.append(f"# {dep.name} = dependencies[{i}].value")
    
    code_lines.extend([
        "",
        "# 在这里编写计算逻辑",
        "result = value  # 修改这里"
    ])
    
    return "\n".join(code_lines)
```

### 5. UI设计草图

```
┌─────────────────────────────────────────────────────────┐
│                     编辑参数: [参数名]                      │
├─────────────────────────────────────────────────────────┤
│ 参数名称: [_______________]  单位: [_____]                │
│ 参数值:   [_______________]                              │
│ 描述:     [_______________]                              │
├─────────────────────────────────────────────────────────┤
│ 依赖参数:                                                │
│ ☐ Node1.param1  ☐ Node1.param2  ☐ Node2.param1         │
│ ☐ Node2.param2  ☐ 当前节点.其他参数                       │
├─────────────────────────────────────────────────────────┤
│ 计算函数:                              [Reset] [测试]     │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ # 计算函数                                              │ │
│ │ # param1 = dependencies[0].value                      │ │
│ │ # param2 = dependencies[1].value                      │ │
│ │                                                       │ │
│ │ # 在这里编写计算逻辑                                      │ │
│ │ result = value                                        │ │
│ └───────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ 预览结果: [计算结果或错误信息]                              │
├─────────────────────────────────────────────────────────┤
│                                    [取消] [保存]          │
└─────────────────────────────────────────────────────────┘
```

## 下一步行动
开始阶段1：创建基础UI结构 