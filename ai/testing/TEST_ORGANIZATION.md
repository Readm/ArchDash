# ArchDash 测试组织指南

本文档描述了 ArchDash 项目的测试组织方法和最佳实践。

## 测试目录结构

我们采用分层的测试组织结构，将不同类型的测试分类存放：

```
tests/
├── core/                    # 核心功能测试
│   ├── test_models.py      # 数据模型测试
│   └── test_file_ops.py    # 文件操作测试
│
├── features/               # 功能特性测试
│   ├── test_unlink.py     # 解链功能测试
│   └── test_layout.py     # 布局管理测试
│
├── examples/              # 示例功能测试
│   ├── test_basic.py     # 基础示例测试
│   └── test_advanced.py  # 高级示例测试
│
├── integration/          # 集成测试
│   └── test_app.py      # 应用集成测试
│
├── conftest.py          # pytest配置和共享fixture
└── run_tests.py         # 测试运行脚本
```

## 测试分类说明

### 1. 核心功能测试 (core/)
- 测试基础数据模型和核心API
- 测试文件操作和数据持久化
- 测试核心算法和计算功能
- 特点：单元测试为主，强调隔离性

### 2. 功能特性测试 (features/)
- 测试具体功能模块（如unlink功能）
- 测试用户交互功能
- 测试特定功能流程
- 特点：功能测试为主，关注用户场景

### 3. 示例功能测试 (examples/)
- 测试示例计算图
- 验证示例文档
- 测试示例用例
- 特点：端到端测试，验证文档准确性

### 4. 集成测试 (integration/)
- 测试整体应用功能
- 测试模块间交互
- 测试端到端流程
- 特点：系统测试，验证整体功能

## 测试运行方法

### 基本用法

```bash
# 运行所有测试
python tests/run_tests.py

# 运行特定类别的测试
python tests/run_tests.py --type core
python tests/run_tests.py --type features
python tests/run_tests.py --type examples
python tests/run_tests.py --type integration
```

### 高级选项

```bash
# 不显示详细输出
python tests/run_tests.py --no-verbose

# 不生成覆盖率报告
python tests/run_tests.py --no-coverage

# 禁用并行执行
python tests/run_tests.py --no-parallel

# 组合使用
python tests/run_tests.py --type core --no-coverage --no-parallel
```

## 测试编写指南

### 1. 命名规范
- 测试文件名应以 `test_` 开头
- 测试类名应以 `Test` 开头
- 测试方法名应以 `test_` 开头
- 使用描述性名称，表明测试目的

### 2. 测试结构
- 每个测试文件应专注于一个功能模块
- 使用测试类组织相关测试
- 合理使用 setup 和 teardown
- 适当添加测试文档字符串

### 3. 断言和验证
- 使用明确的断言消息
- 验证预期的状态和行为
- 测试边界条件和错误情况
- 避免测试间的依赖

### 4. 测试数据
- 使用 fixtures 管理测试数据
- 避免硬编码的测试数据
- 使用工厂方法创建测试对象
- 清理测试产生的数据

## CI/CD 集成

在 CI/CD 环境中运行测试时，系统会自动添加 `--headless` 参数：

```bash
# CI环境中的测试命令
TEST_ENV=CI python tests/run_tests.py
```

## 最佳实践

1. **测试隔离**
   - 每个测试应该是独立的
   - 避免测试间的状态共享
   - 使用适当的 mock 和 stub

2. **测试覆盖率**
   - 保持高测试覆盖率
   - 关注关键路径测试
   - 定期检查覆盖率报告

3. **测试维护**
   - 及时更新测试用例
   - 删除过时的测试
   - 重构重复的测试代码

4. **文档更新**
   - 保持测试文档的更新
   - 添加必要的注释
   - 说明测试的目的和前提条件 