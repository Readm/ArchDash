# ArchDash 测试迁移计划

## 📊 测试分析结果

### 测试分类统计
- **总测试文件数**: 80个测试文件
- **核心逻辑测试**: 17个 (T1xx系列)
- **UI/布局测试**: 29个 (T2xx, T4xx, T5xx系列)
- **示例测试**: 8个 (T3xx系列)
- **功能测试**: 21个 (T4xx系列)
- **其他工具类**: 5个

### 依赖关系分析
- **使用旧models系统**: 65个测试文件
- **包含Selenium UI测试**: 37个测试文件
- **纯逻辑测试**: 约28个测试文件

## 🎯 核心测试迁移优先级

### 🔥 最高优先级 - 立即迁移 (核心逻辑)

这些测试直接对应新Graph系统的核心功能：

#### 1. 参数基础功能 (已有对应功能)
- `test_T101_parameter_validation.py` → **需要迁移**
  - 测试参数验证逻辑
  - 新系统对应：Graph基础参数设置和验证

#### 2. 依赖关系管理 (已有对应功能)
- `test_T102_parameter_dependencies.py` → **需要迁移**
  - 测试参数依赖关系
  - 新系统对应：自动依赖追踪
  
- `test_T115_dependency_chain_analysis.py` → **需要迁移**
  - 测试依赖链分析
  - 新系统对应：get_dependency_chain()

#### 3. 计算和更新传播 (已有对应功能)
- `test_T103_parameter_calculation.py` → **需要迁移**
  - 测试参数计算
  - 新系统对应：add_computed()功能
  
- `test_T112_parameter_update_propagation.py` → **需要迁移**
  - 测试更新传播
  - 新系统对应：自动刷新和refresh_dependents()

#### 4. 计算图核心功能 (已有对应功能)
- `test_T107_calculation_graph.py` → **需要迁移**
  - 测试计算图基础功能
  - 新系统对应：Graph类核心功能

#### 5. 错误处理 (已有对应功能)
- `test_T108_missing_dependency.py` → **需要迁移**
  - 测试缺失依赖处理
  - 新系统对应：错误处理机制
  
- `test_T114_propagate_updates_with_calculation_errors.py` → **需要迁移**
  - 测试计算错误处理
  - 新系统对应：计算错误处理

#### 6. 数据序列化 (已有对应功能)
- `test_T116_save_and_load_graph.py` → **需要迁移**
  - 测试图的保存和加载
  - 新系统对应：save()和to_dict()功能

### 🔶 中等优先级 - 后续迁移

#### 7. 计算函数安全性
- `test_T104_calculation_function_safety.py` → **需要迁移**
  - 测试计算函数的安全性
  - 新系统对应：计算函数执行安全

#### 8. 计算函数作用域
- `test_T105_calculation_function_scope.py` → **需要迁移**
  - 测试计算函数作用域
  - 新系统对应：函数执行环境

#### 9. 循环依赖检测
- `test_T113_circular_dependency_detection.py` → **需要迁移**
  - 测试循环依赖检测
  - 新系统对应：循环依赖检测机制

#### 10. 节点操作
- `test_T106_node_operations.py` → **部分迁移**
  - 测试节点操作
  - 新系统对应：参数分组功能

### 🔷 低优先级 - 选择性迁移

#### 11. 通用错误处理
- `test_T117_error_handling.py` → **可选迁移**
  - 通用错误处理测试

#### 12. 性能测试
- `test_T308_example_performance.py` → **可选迁移**
  - 性能测试，可用于对比

### ❌ 不需要迁移的测试

以下测试主要针对GUI和布局功能，新Graph系统不涉及：

#### UI/布局测试 (T2xx, T4xx, T5xx系列)
- 所有T2xx系列（UI渲染）
- 所有T4xx系列（布局管理）
- 所有T5xx系列（界面交互）

#### 示例测试 (T3xx系列)
- 大部分T3xx系列（示例功能）

## 📋 迁移实施计划

### 阶段1: 核心功能迁移 (第1周)

#### Day 1-2: 基础功能迁移
- [ ] **T101_parameter_validation** → `test_new_parameter_validation.py`
- [ ] **T103_parameter_calculation** → `test_new_parameter_calculation.py`
- [ ] **T107_calculation_graph** → `test_new_graph_core.py`

#### Day 3-4: 依赖关系迁移
- [ ] **T102_parameter_dependencies** → `test_new_dependency_tracking.py`
- [ ] **T115_dependency_chain_analysis** → `test_new_dependency_analysis.py`
- [ ] **T112_parameter_update_propagation** → `test_new_update_propagation.py`

#### Day 5: 错误处理和序列化
- [ ] **T108_missing_dependency** → `test_new_error_handling.py`
- [ ] **T114_propagate_updates_with_calculation_errors** → `test_new_calculation_errors.py`
- [ ] **T116_save_and_load_graph** → `test_new_serialization.py`

### 阶段2: 高级功能迁移 (第2周)

#### Day 1-2: 安全性和作用域
- [ ] **T104_calculation_function_safety** → `test_new_function_safety.py`
- [ ] **T105_calculation_function_scope** → `test_new_function_scope.py`

#### Day 3-4: 循环依赖和节点操作
- [ ] **T113_circular_dependency_detection** → `test_new_circular_dependency.py`
- [ ] **T106_node_operations** → `test_new_parameter_grouping.py`

#### Day 5: 性能和集成测试
- [ ] **T117_error_handling** → `test_new_comprehensive_errors.py`
- [ ] **T308_example_performance** → `test_new_performance.py`

## 🔧 迁移技术方案

### 1. 测试文件结构
```
tests/
├── new_graph_tests/
│   ├── __init__.py
│   ├── test_new_parameter_validation.py
│   ├── test_new_parameter_calculation.py
│   ├── test_new_dependency_tracking.py
│   ├── test_new_dependency_analysis.py
│   ├── test_new_update_propagation.py
│   ├── test_new_graph_core.py
│   ├── test_new_error_handling.py
│   ├── test_new_calculation_errors.py
│   ├── test_new_serialization.py
│   └── ...
└── old_tests/ (保留原有测试)
```

### 2. 测试代码模板
```python
#!/usr/bin/env python3
"""
测试新Graph系统的[功能名称]
从旧测试 test_T[xxx] 迁移而来
"""

import pytest
from core import Graph

def test_[功能名称]():
    """测试[功能描述]"""
    # 使用新的Graph API
    g = Graph("测试")
    
    # 具体测试逻辑
    # ...
    
    assert [验证条件]

def test_[功能名称]_edge_cases():
    """测试[功能名称]的边界情况"""
    # 边界情况测试
    # ...
```

### 3. 测试运行配置
```python
# pytest.ini 添加新的测试路径
[tool:pytest]
testpaths = tests/new_graph_tests tests/old_tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

## 📊 迁移成功指标

### 功能覆盖率
- [ ] 核心功能测试覆盖率 ≥ 90%
- [ ] 依赖关系测试覆盖率 ≥ 95%
- [ ] 错误处理测试覆盖率 ≥ 85%
- [ ] 性能测试基准建立

### 测试质量
- [ ] 所有迁移测试通过
- [ ] 新测试执行时间 ≤ 原测试的150%
- [ ] 测试代码可读性和维护性良好
- [ ] 测试用例的边界情况覆盖完整

### 兼容性验证
- [ ] 新旧系统功能对等性验证
- [ ] 性能对比测试
- [ ] 错误处理行为一致性验证

## 🎯 下一步行动

### 立即开始 (今天)
1. 创建 `tests/new_graph_tests/` 目录
2. 开始迁移 `test_T101_parameter_validation.py`
3. 建立测试基础框架和工具函数

### 本周完成
1. 完成第一阶段的9个核心测试迁移
2. 验证所有迁移测试通过
3. 建立持续集成流程

### 下周目标
1. 完成第二阶段的高级功能测试迁移
2. 进行性能对比测试
3. 完善测试文档和维护指南

这个计划确保了核心功能的测试覆盖，同时避免了不必要的UI测试迁移工作。