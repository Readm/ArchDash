# ArchDash API

## 🎯 概述

ArchDash 具有扁平化的API设计，实现了终极简化的计算图操作。通过完全去除节点层级，用户可以直接操作参数，享受极致简单的使用体验。

## 🚀 核心特性

### 1. 终极简化的语法
```python
from core import Graph

g = Graph("我的设计")
g["电压"] = 1.8        # 直接设置参数
g["频率"] = 3.0        # 无需节点概念
g["核心数"] = 8

print(g["电压"])       # 直接访问参数
```

### 2. 自动依赖追踪
```python
def power():
    return g["电压"] ** 2 * g["核心数"] * 0.5

g.add_computed("功耗", power)  # 自动检测依赖 [电压, 核心数]
```

### 3. 实时计算与更新
```python
print(g["功耗"])       # 12.96
g["电压"] = 1.2        # 修改参数
print(g["功耗"])       # 5.76 (自动重算)
```

## 📚 完整使用指南

### 基础操作

#### 创建图并设置参数
```python
from core import Graph

g = Graph("处理器设计")

# 直接设置参数
g["工艺_节点"] = 7      # nm
g["工艺_电压"] = 1.8    # V  
g["工艺_频率"] = 3.0    # GHz
g["CPU_核心数"] = 8
g["CPU_缓存"] = 32     # MB
```

#### 批量设置参数
```python
g.update({
    "基础频率": 2.5,
    "加速频率": 3.8,
    "电压": 1.8,
    "核心数": 8,
    "线程数": 16
})
```

### 计算参数

#### 添加计算函数
```python
def cpu_power():
    """CPU功耗计算"""
    voltage = g["工艺_电压"]
    cores = g["CPU_核心数"]
    return voltage ** 2 * cores * 0.5

def cpu_performance():
    """CPU性能计算"""
    cores = g["CPU_核心数"]
    frequency = g["工艺_频率"]
    return cores * frequency * 8  # GFLOPS

def efficiency():
    """能效比计算"""
    perf = g["CPU_性能"]
    power = g["CPU_功耗"]
    return perf / power if power > 0 else 0

# 添加计算参数
g.add_computed("CPU_功耗", cpu_power, "CPU功耗计算")
g.add_computed("CPU_性能", cpu_performance, "CPU性能计算")
g.add_computed("能效比", efficiency, "能效比计算")
```

#### 访问计算结果
```python
print(f"CPU功耗: {g['CPU_功耗']:.2f}W")
print(f"CPU性能: {g['CPU_性能']:.0f}GFLOPS")
print(f"能效比: {g['能效比']:.2f}GFLOPS/W")
```

### 参数分组（可选）

```python
# 设置参数分组
g.set_group("工艺_节点", "工艺参数")
g.set_group("工艺_电压", "工艺参数")
g.set_group("工艺_频率", "工艺参数")
g.set_group("CPU_核心数", "CPU参数")
g.set_group("CPU_缓存", "CPU参数")

# 查看结构
g.print_structure()
```

### 依赖关系查看

```python
# 查看计算参数的依赖关系
info = g.get_computed_info("CPU_功耗")
print(f"依赖: {info['dependencies']}")  # ['工艺_电压', 'CPU_核心数']

# 查看所有参数
print(f"所有参数: {g.keys()}")
```

### 保存和加载

```python
# 保存图
g.save("/path/to/design.json")

# 加载图
g2 = Graph.load("/path/to/design.json")
```

## 🎯 实际使用示例

### 示例1: 简单的处理器设计
```python
from core import Graph

g = Graph("简单处理器")

# 设置基础参数
g["电压"] = 1.8
g["频率"] = 3.0
g["核心数"] = 8

# 定义计算
def power():
    return g["电压"] ** 2 * g["核心数"] * 0.5

def performance():
    return g["核心数"] * g["频率"] * 8

def efficiency():
    return g["性能"] / g["功耗"]

# 添加计算参数
g.add_computed("功耗", power)
g.add_computed("性能", performance)
g.add_computed("效率", efficiency)

# 查看结果
print(f"功耗: {g['功耗']:.2f}W")
print(f"性能: {g['性能']:.0f}GFLOPS")
print(f"效率: {g['效率']:.2f}GFLOPS/W")

# 优化参数
g["电压"] = 1.2  # 降低电压
g["频率"] = 3.5  # 提高频率
print(f"优化后效率: {g['效率']:.2f}GFLOPS/W")
```

### 示例2: 复杂系统设计
```python
from core import Graph

g = Graph("复杂系统")

# 批量设置参数
params = {
    "CPU_核心数": 16,
    "CPU_频率": 3.5,
    "CPU_电压": 1.2,
    "GPU_核心数": 2048,
    "GPU_频率": 2.5,
    "内存_容量": 64,
    "内存_频率": 3200,
    "环境温度": 25
}
g.update(params)

# 定义复杂计算
def cpu_power():
    return g["CPU_电压"] ** 2 * g["CPU_核心数"] * g["CPU_频率"] * 0.3

def gpu_power():
    return g["GPU_核心数"] * g["GPU_频率"] * 0.0005

def memory_power():
    return g["内存_容量"] * g["内存_频率"] * 0.001

def total_power():
    return g["CPU_功耗"] + g["GPU_功耗"] + g["内存_功耗"] + 20  # 20W基础功耗

def temperature():
    return g["环境温度"] + g["总功耗"] * 0.8  # 热阻计算

def cpu_score():
    return g["CPU_核心数"] * g["CPU_频率"] * 10

def gpu_score():
    return g["GPU_核心数"] * g["GPU_频率"] * 0.1

def total_score():
    return g["CPU_评分"] + g["GPU_评分"]

def efficiency():
    return g["总评分"] / g["总功耗"]

# 批量添加计算参数
computations = [
    ("CPU_功耗", cpu_power, "CPU功耗"),
    ("GPU_功耗", gpu_power, "GPU功耗"),
    ("内存_功耗", memory_power, "内存功耗"),
    ("总功耗", total_power, "总功耗"),
    ("芯片温度", temperature, "芯片温度"),
    ("CPU_评分", cpu_score, "CPU评分"),
    ("GPU_评分", gpu_score, "GPU评分"),
    ("总评分", total_score, "总评分"),
    ("能效比", efficiency, "能效比")
]

for name, func, desc in computations:
    g.add_computed(name, func, desc)

# 查看结果
print(f"总功耗: {g['总功耗']:.2f}W")
print(f"芯片温度: {g['芯片温度']:.1f}°C")
print(f"总评分: {g['总评分']:.0f}")
print(f"能效比: {g['能效比']:.2f}")
```

## 🔄 与旧API的对比

| 功能 | 旧API (节点-属性) | 新API (完全扁平) |
|------|------------------|-----------------|
| 设置参数 | `g["CPU"]["频率"] = 3.0` | `g["CPU_频率"] = 3.0` |
| 访问参数 | `g["CPU"]["频率"]` | `g["CPU_频率"]` |
| 计算函数 | `g["CPU"]["频率"] * g["CPU"]["电压"]` | `g["CPU_频率"] * g["CPU_电压"]` |
| 添加计算 | `g.add_computed("功耗", "CPU", func)` | `g.add_computed("CPU_功耗", func)` |
| 复杂度 | 中等 | 极简 |
| 学习成本 | 需要理解节点概念 | 几乎无学习成本 |
| 代码可读性 | 良好 | 优秀 |

## 💡 最佳实践

### 1. 参数命名约定
- 使用下划线分隔逻辑组件：`CPU_频率`、`GPU_显存`
- 保持命名简洁但具描述性
- 使用一致的命名模式

### 2. 分组策略
```python
# 按功能分组
g.set_group("CPU_频率", "处理器")
g.set_group("CPU_核心数", "处理器")
g.set_group("GPU_频率", "显卡")
g.set_group("GPU_显存", "显卡")

# 按计算类型分组
g.add_computed("CPU_功耗", func, "功耗计算", "功耗分析")
g.add_computed("GPU_功耗", func, "功耗计算", "功耗分析")
```

### 3. 计算函数设计
```python
def good_function():
    """清晰的函数：单一职责，清晰的依赖"""
    voltage = g["电压"]
    cores = g["核心数"]
    return voltage ** 2 * cores * 0.5

# 避免过于复杂的计算函数
def avoid_complex_function():
    """避免：过于复杂，难以理解依赖关系"""
    return (g["A"] + g["B"]) * (g["C"] - g["D"]) / (g["E"] ** g["F"])
```

### 4. 批量操作
```python
# 利用批量更新提高效率
updates = {
    "param1": value1,
    "param2": value2,
    "param3": value3
}
g.update(updates)

# 批量添加计算参数
for name, func, desc in computations:
    g.add_computed(name, func, desc)
```

## 🎉 总结

ArchDash 的扁平化API实现了：

- **🎯 终极简化**: `g["参数"] = 值` 的极简语法
- **🔄 零配置依赖**: 完全自动的依赖检测和管理
- **📦 扁平结构**: 去除所有不必要的嵌套结构
- **🏷️ 灵活组织**: 可选的参数分组功能
- **⚡ 高效操作**: 支持批量设置和更新
- **🚀 极致性能**: 最直接的参数访问方式
- **💡 零学习成本**: 接近原生Python字典的使用体验

这种设计让 ArchDash 成为了市面上最简单易用的计算图库，同时保持了强大的功能和优秀的性能。