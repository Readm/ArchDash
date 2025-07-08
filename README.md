# ArchDash - 架构计算图可视化工具

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行应用
```bash
python app.py
```

访问 http://127.0.0.1:8050 查看应用

## 📋 核心功能

- **节点管理**: 创建、编辑、删除计算节点
- **参数系统**: 支持参数依赖关系和自动计算
- **可视化布局**: 自动网格布局和交互式界面
- **计算引擎**: 实时参数计算和依赖更新
- **数据持久化**: 图结构的保存和加载

## 📁 文件结构

```
ArchDash/
├── app.py              # 主应用文件
├── layout.py           # UI布局定义
├── models.py           # 数据模型
├── session_graph.py    # 图会话管理
├── examples.py         # 示例数据
├── assets/             # 静态资源
│   ├── modern_style.css
│   └── tab-sid.js
└── callbacks/          # 回调函数
    └── __init__.py
```

## 🛠️ 系统要求

- Python 3.8+
- Dash 2.0+
- 现代浏览器 (Chrome, Firefox, Safari, Edge)

## 📝 版本信息

- **版本**: Release v1.0
- **构建日期**: 2025-07-07
- **功能亮点**: 参数编辑窗口自动重置测试结果