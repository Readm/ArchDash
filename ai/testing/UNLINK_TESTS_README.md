# Unlink功能测试文档

## 概述

本文档描述了ArchDash项目中unlink功能的测试套件。unlink功能允许用户断开参数的自动计算依赖，手动设置参数值。

## 新的Unlink功能逻辑

### 1. 🔓 UI显示逻辑
- **只有**当参数同时满足以下条件时才显示🔓按钮：
  - 有计算函数 (`calculation_func`)
  - 有依赖关系 (`dependencies`)
  - 已断开连接 (`unlinked = True`)

### 2. 🔄 自动Unlink触发
- **手动修改参数值**：当用户手动修改有依赖计算的参数值时，自动设置 `unlinked = True`
- **相关性分析**：在相关性分析过程中，如果X轴参数有计算依赖，自动临时断开连接

### 3. 🔗 重新连接功能
- 点击🔓按钮：重新连接参数并重新计算（`unlinked = False`）
- 按钮消失：重新连接后，由于 `unlinked = False`，🔓按钮自动隐藏

## 测试文件结构

```
📁 测试文件
├── test_unlink_feature.py              # 原有的unlink功能测试（模型层）
├── test_enhanced_unlink_feature.py     # 增强的unlink功能测试（模型层）
├── test_unlink_ui_feature.py          # UI交互测试（Selenium）
├── run_unlink_tests.py                # 集成测试运行脚本
└── UNLINK_TESTS_README.md             # 本文档
```

## 测试覆盖范围

### 📊 模型层测试
- ✅ unlink基础功能
- ✅ 序列化/反序列化
- ✅ 手动设置值自动unlink
- ✅ 重新连接功能
- ✅ 边界情况处理
- ✅ 复杂依赖关系

### 🖥️ UI交互测试
- ✅ unlink图标显示逻辑
- ✅ 手动修改值触发auto unlink
- ✅ 点击🔓按钮重新连接
- ✅ 相关性分析UI验证
- ✅ 完整UI集成测试

## 快速开始

### 1. 安装依赖

```bash
# 基础依赖
pip install dash plotly dash-bootstrap-components

# 测试依赖
pip install pytest selenium

# 如果需要无头浏览器测试
pip install webdriver-manager
```

### 2. 运行所有测试

```bash
# 使用集成脚本运行所有测试
python run_unlink_tests.py
```

### 3. 单独运行测试

```bash
# 模型层测试
python test_enhanced_unlink_feature.py

# UI交互测试（需要浏览器）
pytest test_unlink_ui_feature.py -v

# 特定测试用例
pytest test_unlink_ui_feature.py::test_unlink_icon_display_logic -v
```

## 详细测试说明

### 📋 test_enhanced_unlink_feature.py

**核心测试：**

1. **`test_enhanced_unlink_display_logic()`**
   - 测试UI显示逻辑
   - 验证只有满足条件的参数才显示🔓按钮

2. **`test_manual_value_auto_unlink()`**
   - 测试手动修改值自动unlink
   - 验证有依赖参数自动unlink，无依赖参数不会

3. **`test_unlink_icon_click_reconnect()`**
   - 测试点击🔓按钮重新连接
   - 验证重新连接后重新计算并隐藏按钮

4. **`test_sensitivity_analysis_auto_unlink_simulation()`**
   - 模拟相关性分析的auto unlink
   - 验证分析前自动断开，分析后恢复

5. **`test_edge_cases_and_error_handling()`**
   - 边界情况和错误处理
   - 测试各种异常情况

6. **`test_unlink_with_complex_dependencies()`**
   - 复杂依赖链中的unlink
   - 测试A→B→C→D依赖链中间断开的影响

### 🖱️ test_unlink_ui_feature.py

**UI交互测试：**

1. **`test_unlink_icon_display_logic()`**
   - 浏览器中验证🔓图标显示逻辑
   - 检查DOM元素的存在/不存在

2. **`test_manual_value_change_auto_unlink()`**
   - 模拟用户在输入框中修改值
   - 验证auto unlink消息和🔓图标出现

3. **`test_unlink_icon_click_reconnect()`**
   - 模拟点击🔓图标
   - 验证重新连接消息和图标消失

4. **`test_unlink_ui_integration()`**
   - 完整的UI集成测试
   - 测试整个用户操作流程

## 运行环境要求

### 最低要求
- Python 3.8+
- 已安装的依赖包（见requirements.txt）

### UI测试额外要求
- 浏览器（Chrome/Firefox）
- Selenium WebDriver
- 图形界面（或配置无头模式）

### 推荐配置
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装所有依赖
pip install -r requirements.txt
pip install pytest selenium webdriver-manager
```

## 测试输出示例

### 成功运行输出
```
🧪 运行所有unlink功能测试
============================================================
当前目录: /path/to/ArchDash

🔍 检查测试依赖...
✅ pytest 已安装
✅ selenium 已安装
✅ dash 已安装
✅ test_enhanced_unlink_feature.py 存在
✅ test_unlink_ui_feature.py 存在

🚀 开始运行 7 个测试...

[1/7] 运行测试...
============================================================
🔄 运行增强unlink功能测试（模型层）
命令: python test_enhanced_unlink_feature.py
============================================================
🔬 测试增强的unlink显示逻辑
==================================================
1. 测试显示逻辑：
   area有依赖且unlinked=False -> 应该不显示按钮
   area显示按钮: False
   ...
✅ 所有增强unlink功能测试通过！

📊 测试总结
============================================================
✅ 模型层测试: 2/2 (100.0%)
✅ UI交互测试: 1/1 (100.0%)
✅ UI专项测试: 4/4 (100.0%)

🎉 总体测试: 7/7 (100.0%)

🎊 所有测试通过！unlink功能工作正常！
```

## 故障排除

### 常见问题

1. **Selenium找不到浏览器**
   ```bash
   pip install webdriver-manager
   ```

2. **UI测试超时**
   - 检查应用是否正常启动
   - 增加等待时间
   - 使用无头模式测试

3. **模型测试失败**
   - 检查models.py中是否有新方法
   - 确保Parameter类有set_manual_value和relink_and_calculate方法

### 调试技巧

1. **查看详细输出**
   ```bash
   pytest test_unlink_ui_feature.py -v -s
   ```

2. **只运行特定测试**
   ```bash
   pytest test_unlink_ui_feature.py::test_manual_value_change_auto_unlink -v
   ```

3. **保持浏览器打开（调试UI）**
   在测试代码中添加：
   ```python
   time.sleep(10)  # 暂停10秒观察浏览器状态
   ```

## 贡献指南

### 添加新测试

1. **模型层测试**：在`test_enhanced_unlink_feature.py`中添加
2. **UI测试**：在`test_unlink_ui_feature.py`中添加
3. **更新运行脚本**：在`run_unlink_tests.py`中添加新测试命令

### 测试命名规范
- 测试函数：`test_功能描述()`
- 测试文件：`test_模块名_功能.py`
- 描述性注释：说明测试目的和预期结果

### 最佳实践
- 每个测试独立：不依赖其他测试状态
- 清理资源：测试后重置全局状态
- 详细断言：提供清晰的错误信息
- 边界测试：包含异常和边界情况

## 更新日志

### v1.0 (2024-12-19)
- ✅ 创建增强unlink功能测试套件
- ✅ 添加UI交互测试
- ✅ 实现集成测试运行脚本
- ✅ 完善测试文档和使用说明 