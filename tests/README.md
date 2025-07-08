# ArchDash 测试目录结构

## 目录说明

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

1. **核心功能测试 (core/)**
   - 测试基础数据模型
   - 测试文件操作功能
   - 测试核心API

2. **功能特性测试 (features/)**
   - 测试具体功能模块
   - 测试用户交互功能
   - 测试特定功能流程

3. **示例功能测试 (examples/)**
   - 测试示例计算图
   - 测试示例用例
   - 验证示例文档

4. **集成测试 (integration/)**
   - 测试整体应用功能
   - 测试模块间交互
   - 测试端到端流程

## 运行测试

```bash
# 运行所有测试
python tests/run_tests.py

# 运行特定分类的测试
pytest tests/core/
pytest tests/features/
pytest tests/examples/
pytest tests/integration/

# 运行单个测试文件
pytest tests/core/test_models.py
``` 