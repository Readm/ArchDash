# ArchDash App.py 重构计划

## 概述
将 `app.py` (3271行) 拆分为模块化的结构，每个模块约1000行，提高代码可维护性和可读性。

## 项目目标
- 保持所有现有功能不变
- 确保所有测试在重构前后都能通过
- 提高代码的模块化和可维护性
- 建立更清晰的代码组织结构

## 测试覆盖现状
- ✅ 集成测试：`tests/integration/test_app.py` (1336行)
- ✅ 核心功能测试：`tests/core/test_models.py`, `test_file_ops.py`
- ✅ 特性测试：`tests/features/` (7个特性测试文件)
- ✅ 测试配置：`tests/conftest.py` (完整的测试环境设置)

---

## 阶段1: 准备阶段和基础重构
**预计时间**: 1-2天

### 任务1.1: 创建目录结构
- [ ] 创建 `callbacks/` 目录
- [ ] 创建 `utils/` 目录
- [ ] 创建 `__init__.py` 文件确保导入正常

### 任务1.2: 运行基线测试
```bash
# 运行所有测试并记录基线结果
pytest tests/ -v --tb=short > baseline_test_results.txt
```
- [ ] 验证所有现有测试通过
- [ ] 记录测试覆盖率基线
- [ ] 确认测试环境正常

### 任务1.3: 补充缺失的测试覆盖
基于代码分析，需要补充以下测试：

#### 新增测试文件1: `tests/callbacks/test_utils_functions.py`
```python
# 测试辅助函数的独立测试
- test_get_all_available_parameters()
- test_generate_code_template()
- test_create_dependency_checkboxes()
- test_get_plotting_parameters()
- test_perform_sensitivity_analysis()
```

#### 新增测试文件2: `tests/callbacks/test_canvas_operations.py`
```python
# 测试画布相关功能
- test_update_canvas()
- test_create_arrows()
- test_auto_remove_empty_last_column()
- test_ensure_minimum_columns()
```

### 验证点1.3
- [ ] 新增测试通过
- [ ] 所有原有测试仍然通过
- [ ] 测试覆盖率不降低

---

## 阶段2: 拆分辅助函数模块
**预计时间**: 1天

### 任务2.1: 创建 `utils/app_utils.py`
迁移以下函数（约600-700行）：
- `get_all_available_parameters()`
- `generate_code_template()`
- `create_dependency_checkboxes()`
- `get_plotting_parameters()`
- `perform_sensitivity_analysis()`
- `create_empty_plot()`
- `auto_remove_empty_last_column()`
- `ensure_minimum_columns()`
- `get_all_parameter_dependencies()`
- `format_dependencies_display()`
- `create_calculation_flow_visualization()`
- `get_arrow_connections_data()`
- `check_parameter_has_dependents()`
- `check_node_has_dependents()`

### 任务2.2: 更新导入和引用
- [ ] 在 `app.py` 中添加: `from utils.app_utils import *`
- [ ] 确保所有函数调用路径正确

### 验证点2.2
```bash
# 运行相关测试
pytest tests/core/test_models.py -v
pytest tests/integration/test_app.py::test_add_node_with_grid_layout -v
pytest tests/callbacks/test_utils_functions.py -v
```
- [ ] 所有测试通过
- [ ] 功能保持一致
- [ ] 无导入错误

---

## 阶段3: 拆分画布相关回调
**预计时间**: 1天

### 任务3.1: 创建 `callbacks/canvas_callbacks.py`
迁移以下回调函数（约500-600行）：
- `update_arrow_connections_data()`
- `trigger_arrow_update_on_data_change()`
- `initialize_dependencies_display()`
- `initialize_calculation_flow_display()`
- `refresh_all_displays()`
- `auto_update_all_displays_on_change()`
- `clear_parameter_highlights()`

### 任务3.2: 补充专门的画布测试
#### 新增: `tests/callbacks/test_canvas_callbacks.py`
```python
# 测试画布回调函数
- test_update_arrow_connections_data()
- test_trigger_arrow_update_on_data_change()
- test_initialize_dependencies_display()
- test_auto_update_all_displays_on_change()
```

### 验证点3.2
```bash
pytest tests/integration/test_app.py::test_multiple_nodes_grid_layout -v
pytest tests/features/test_layout.py -v
pytest tests/callbacks/test_canvas_callbacks.py -v
```
- [ ] 箭头连接显示正常
- [ ] 依赖关系显示正常
- [ ] 布局更新功能正常

---

## 阶段4: 拆分节点操作回调
**预计时间**: 1-2天

### 任务4.1: 创建 `callbacks/node_operations.py`
迁移以下回调函数（约900-1000行）：
- `handle_node_operations()`
- `open_node_edit_modal()` / `close_node_edit_modal()` / `save_node_changes()`
- `toggle_node_add_modal()` / `create_new_node()`
- `handle_column_management()`
- `update_remove_button_status()`
- `clear_calculation_graph()`

### 任务4.2: 补充节点操作测试
#### 更新: `tests/features/test_node_edit.py`
```python
# 扩展现有节点编辑测试
- test_node_edit_modal_validation()
- test_node_creation_edge_cases()
- test_column_management_constraints()
```

### 验证点4.2
```bash
pytest tests/integration/test_app.py::test_node_dropdown_menu_operations -v
pytest tests/integration/test_app.py::test_column_management -v
pytest tests/features/test_node_edit.py -v
```
- [ ] 节点创建、编辑、删除功能正常
- [ ] 列管理功能正常
- [ ] 模态窗口交互正常

---

## 阶段5: 拆分参数操作回调
**预计时间**: 1-2天

### 任务5.1: 创建 `callbacks/parameter_operations.py`
迁移以下回调函数（约1000-1100行）：
- `update_parameter()`
- `handle_parameter_operations()`
- `handle_unlink_toggle()`
- `open_param_edit_modal()` / `close_param_edit_modal()` / `save_parameter_changes()`
- `reset_calculation_code()` / `test_calculation()`

### 任务5.2: 补充参数操作测试
#### 新增: `tests/callbacks/test_parameter_operations.py`
```python
# 测试参数操作回调
- test_update_parameter_validation()
- test_parameter_calculation_code_test()
- test_circular_dependency_detection()
```

### 验证点5.2
```bash
pytest tests/integration/test_app.py::test_parameter_operations_with_dropdown -v
pytest tests/features/test_unlink.py -v
pytest tests/features/test_enhanced_unlink_feature.py -v
pytest tests/callbacks/test_parameter_operations.py -v
```
- [ ] 参数编辑功能正常
- [ ] 参数计算功能正常
- [ ] 解绑功能正常
- [ ] 循环依赖检测正常

---

## 阶段6: 拆分绘图相关回调
**预计时间**: 1天

### 任务6.1: 创建 `callbacks/plotting_callbacks.py`
迁移以下回调函数（约800-900行）：
- `update_param_selectors()`
- `initialize_plot()` / `generate_sensitivity_plot()`
- `clear_plot()` / `export_plot_data()`
- `auto_update_series_name()` / `auto_update_range()`
- `toggle_enlarged_plot()`

### 任务6.2: 补充绘图测试
#### 新增: `tests/callbacks/test_plotting_callbacks.py`
```python
# 测试绘图功能
- test_sensitivity_analysis_plot_generation()
- test_plot_data_export()
- test_plot_parameter_selection()
- test_enlarged_plot_modal()
```

### 验证点6.2
```bash
pytest tests/callbacks/test_plotting_callbacks.py -v
# 手动验证绘图功能在浏览器中正常工作
```
- [ ] 敏感性分析绘图正常
- [ ] 参数选择器更新正常
- [ ] 图表导出功能正常

---

## 阶段7: 拆分UI控制回调
**预计时间**: 1天

### 任务7.1: 创建 `callbacks/ui_callbacks.py`
迁移以下回调函数（约700-800行）：
- `toggle_theme()`
- `save_calculation_graph()` / `load_calculation_graph()`
- `load_example_soc_graph_callback()`
- `toggle_dependencies_collapse()` / `toggle_dependencies_collapse_modal()`

### 任务7.2: 补充UI控制测试
#### 新增: `tests/callbacks/test_ui_callbacks.py`
```python
# 测试UI控制功能
- test_theme_toggle()
- test_file_save_load()
- test_example_graph_loading()
- test_dependencies_collapse()
```

### 验证点7.2
```bash
pytest tests/core/test_file_ops.py -v
pytest tests/callbacks/test_ui_callbacks.py -v
```
- [ ] 主题切换功能正常
- [ ] 文件保存加载功能正常
- [ ] 示例图加载功能正常

---

## 阶段8: 最终整理和验证
**预计时间**: 1天

### 任务8.1: 重构核心 `app.py`
保留核心内容（约300-400行）：
- 导入语句整理
- 应用初始化
- 全局变量设置
- `update_canvas()` 函数
- `create_arrows()` 函数
- 应用布局设置

### 任务8.2: 更新所有导入引用
```python
# 在重构后的 app.py 中添加
from callbacks.node_operations import *
from callbacks.parameter_operations import *
from callbacks.plotting_callbacks import *
from callbacks.canvas_callbacks import *
from callbacks.ui_callbacks import *
from utils.app_utils import *
```

### 验证点8.2
```bash
# 运行完整测试套件
pytest tests/ -v --tb=short > final_test_results.txt

# 比较重构前后的测试结果
diff baseline_test_results.txt final_test_results.txt
```
- [ ] 所有原有测试通过
- [ ] 所有新增测试通过
- [ ] 功能完全一致
- [ ] 性能无明显下降

### 任务8.3: 代码质量检查
```bash
# 检查代码风格和质量
flake8 callbacks/ utils/ app.py
pylint callbacks/ utils/ app.py

# 检查导入依赖
python -c "import app; print('Import successful')"
```

---

## 最终文件结构

```
ArchDash/
├── app.py (300-400行)
├── callbacks/
│   ├── __init__.py
│   ├── node_operations.py (~900行)
│   ├── parameter_operations.py (~1000行)
│   ├── plotting_callbacks.py (~800行)
│   ├── canvas_callbacks.py (~500行)
│   └── ui_callbacks.py (~700行)
├── utils/
│   ├── __init__.py
│   └── app_utils.py (~600行)
└── tests/
    ├── callbacks/
    │   ├── test_utils_functions.py
    │   ├── test_canvas_callbacks.py
    │   ├── test_parameter_operations.py
    │   ├── test_plotting_callbacks.py
    │   └── test_ui_callbacks.py
    └── [现有测试保持不变]
```

## 风险控制

### 回滚计划
- 每个阶段完成后，创建 Git 提交点
- 如果测试失败，立即回滚到上一个稳定状态
- 保留原始 `app.py` 的备份直到重构完全完成

### 测试策略
- 每个阶段完成后立即运行测试
- 重构期间不修改任何业务逻辑
- 确保导入路径和函数签名完全一致

### 质量保证
- 所有新增测试必须达到80%以上的代码覆盖率
- 重构后的代码必须通过静态分析检查
- 功能验证必须在真实浏览器环境中进行

---

## 估计总时间
**8-12个工作日** (包含测试编写和验证时间)

## 成功标准
- ✅ 所有现有测试通过率100%
- ✅ 新增测试覆盖率 > 80%
- ✅ 代码结构清晰，每个模块职责单一
- ✅ 文件大小符合要求 (~1000行/文件)
- ✅ 无性能回归
- ✅ 导入依赖关系清晰 