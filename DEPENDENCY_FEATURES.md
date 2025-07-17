# ArchDash 依赖关系图功能

## 🎯 功能概述

ArchDash 的新图系统实现了强大的依赖关系管理和自动刷新功能，为用户提供了完整的参数依赖关系分析和管理工具。

## 🚀 核心功能

### 1. 依赖关系图获取

#### `get_dependency_graph()` - 正向依赖关系图
获取每个参数的依赖者列表，显示哪些参数依赖于某个参数。

```python
from core import Graph

g = Graph("设计")
g["电压"] = 1.8
g["核心数"] = 8

def power():
    return g["电压"] ** 2 * g["核心数"] * 0.5

g.add_computed("功耗", power)

# 获取正向依赖关系图
dep_graph = g.get_dependency_graph()
print(dep_graph)
# 输出: {'电压': ['功耗'], '核心数': ['功耗']}
```

#### `get_reverse_dependency_graph()` - 反向依赖关系图
获取每个参数依赖的参数列表，显示某个参数依赖于哪些参数。

```python
reverse_deps = g.get_reverse_dependency_graph()
print(reverse_deps)
# 输出: {'功耗': ['电压', '核心数'], '电压': [], '核心数': []}
```

### 2. 依赖链分析

#### `get_dependency_chain()` - 完整依赖链
获取从根参数到目标参数的完整依赖路径。

```python
chain = g.get_dependency_chain("功耗")
print(chain)
# 输出: ['电压', '核心数', '功耗']
```

#### `get_dependents_chain()` - 依赖者链
获取从目标参数到所有最终依赖者的完整路径。

```python
dependents = g.get_dependents_chain("电压")
print(dependents)
# 输出: ['电压', '功耗', ...]
```

### 3. 自动依赖更新

#### 实时自动更新
参数修改时自动刷新所有依赖者。

```python
g["电压"] = 1.2  # 修改参数
print(g["功耗"])  # 自动重新计算，返回新值
```

#### `refresh_all_computed()` - 刷新所有计算参数
手动刷新图中所有计算参数的值。

```python
g.refresh_all_computed()
```

#### `refresh_dependents()` - 刷新指定参数的依赖者
手动刷新指定参数的所有依赖者。

```python
g.refresh_dependents("电压")
```

## 📊 实际应用示例

### 示例1：处理器功耗分析

```python
from core import Graph

g = Graph("处理器功耗分析")

# 设置基础参数
g["工艺_节点"] = 7
g["工艺_电压"] = 1.8
g["工艺_频率"] = 3.0
g["CPU_核心数"] = 8
g["GPU_核心数"] = 1024

# 定义计算函数
def cpu_power():
    return g["工艺_电压"] ** 2 * g["CPU_核心数"] * g["工艺_频率"] * 0.3

def gpu_power():
    return g["GPU_核心数"] * g["工艺_电压"] * 0.001

def total_power():
    return g["CPU_功耗"] + g["GPU_功耗"] + 10  # 10W基础功耗

def efficiency():
    return g["CPU_核心数"] * g["工艺_频率"] / g["总功耗"]

# 添加计算参数
g.add_computed("CPU_功耗", cpu_power, "CPU功耗计算")
g.add_computed("GPU_功耗", gpu_power, "GPU功耗计算")
g.add_computed("总功耗", total_power, "总功耗计算")
g.add_computed("能效比", efficiency, "能效比计算")

# 分析依赖关系
dep_graph = g.get_dependency_graph()
print("关键参数的依赖者:")
for param in ["工艺_电压", "工艺_频率", "CPU_核心数"]:
    if param in dep_graph:
        print(f"  {param} -> {dep_graph[param]}")

# 查看复杂参数的依赖链
chain = g.get_dependency_chain("能效比")
print(f"能效比的完整依赖链: {' -> '.join(chain)}")

# 测试工艺升级影响
print(f"原始总功耗: {g['总功耗']:.2f}W")
print(f"原始能效比: {g['能效比']:.2f}")

g["工艺_节点"] = 5
g["工艺_电压"] = 1.2
g["工艺_频率"] = 3.5

print(f"升级后总功耗: {g['总功耗']:.2f}W")
print(f"升级后能效比: {g['能效比']:.2f}")
```

### 示例2：多级依赖管理

```python
from core import Graph

g = Graph("多级依赖测试")

# 创建多级依赖结构
g["基础值"] = 10
g["乘数"] = 2
g["加数"] = 5

def level1():
    return g["基础值"] * g["乘数"]

def level2():
    return g["一级结果"] + g["加数"]

def level3():
    return g["二级结果"] * 1.5

def final_result():
    return g["一级结果"] + g["二级结果"] + g["三级结果"]

g.add_computed("一级结果", level1)
g.add_computed("二级结果", level2)
g.add_computed("三级结果", level3)
g.add_computed("最终结果", final_result)

# 分析依赖关系
reverse_deps = g.get_reverse_dependency_graph()
print("多级依赖结构:")
for param in ["一级结果", "二级结果", "三级结果", "最终结果"]:
    deps = reverse_deps.get(param, [])
    print(f"  {param} <- {deps}")

# 测试批量修改和自动更新
print(f"原始最终结果: {g['最终结果']}")

g["基础值"] = 20
g["乘数"] = 3
print(f"修改后最终结果: {g['最终结果']}")

# 手动刷新验证
g.refresh_all_computed()
print(f"手动刷新后最终结果: {g['最终结果']}")
```

## 🔧 高级功能

### 1. 循环依赖检测
系统自动检测并处理循环依赖，避免无限递归。

### 2. 性能优化
- 惰性计算：只在需要时计算参数值
- 智能失效：只失效真正需要更新的参数
- 避免重复计算：相同参数在一次更新中只计算一次

### 3. 错误处理
- 计算错误时返回默认值
- 详细的错误信息和调试支持
- 优雅的错误恢复机制

## 🎉 与旧系统的对比

| 功能 | 旧系统 (models.py) | 新系统 (core/graph.py) |
|------|-------------------|------------------------|
| 依赖关系图 | 复杂的内部映射 | 简单的API调用 |
| 依赖链分析 | 有限的功能 | 完整的链式分析 |
| 自动更新 | 手动触发 | 完全自动 |
| 性能 | 重复计算 | 智能缓存 |
| 易用性 | 复杂的接口 | 极简的API |
| 调试支持 | 有限 | 完整的工具链 |

## 📈 性能特点

- **📊 实时分析**: 即时获取依赖关系图
- **🔄 自动更新**: 参数修改时自动刷新依赖者
- **🎯 精准失效**: 只更新真正需要更新的参数
- **⚡ 高效计算**: 避免重复计算和无效操作
- **🛡️ 错误处理**: 完善的错误检测和恢复机制
- **🔍 调试友好**: 详细的依赖链和状态信息

## 💡 最佳实践

1. **合理使用依赖链分析**：
   - 使用 `get_dependency_chain()` 理解复杂参数的依赖关系
   - 使用 `get_dependents_chain()` 评估参数修改的影响范围

2. **智能刷新策略**：
   - 让系统自动处理大部分更新
   - 在批量修改后使用 `refresh_all_computed()` 确保一致性
   - 使用 `refresh_dependents()` 进行精确的局部更新

3. **性能优化**：
   - 避免创建过深的依赖链
   - 合理分组相关参数
   - 使用描述性的参数名称便于调试

4. **错误处理**：
   - 在计算函数中添加适当的错误处理
   - 使用 `get_computed_info()` 检查计算状态
   - 定期检查依赖关系图的完整性

这些功能使得 ArchDash 具有了工业级的依赖关系管理能力，为复杂的参数化设计提供了强大的支持。