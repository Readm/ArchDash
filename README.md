# ArchDash - Interactive Graph Visualizer

一个强大的Python图形参数可视化和代码编辑系统，提供实时的参数依赖关系可视化和专业的代码编辑体验。

## 🌟 主要功能

### 🎯 交互式图形可视化
- **矩形节点布局**: 基础参数和计算参数分列显示
- **实时依赖关系**: 清晰显示参数间的依赖箭头
- **点击交互**: 点击节点弹出上下文菜单
- **一键跳转**: 从图形直接跳转到对应代码行

### 💻 专业代码编辑
- **Monaco Editor**: VS Code同款编辑器核心
- **Python语法高亮**: 完整的Python语法着色支持
- **智能自动补全**: Graph API专用代码提示
- **实时同步**: 代码修改后图形自动更新

### 🔄 实时更新系统
- **参数计算**: 支持基础参数和计算参数
- **依赖追踪**: 自动解析函数依赖关系
- **即时反馈**: 代码变更立即反映在图形中

## 🚀 快速开始

### 安装依赖
```bash
pip install dash plotly dash-bootstrap-components
```

### 启动应用
```bash
python plotly_graph_visualizer.py --mode online
```

### 访问应用
打开浏览器访问: http://127.0.0.1:8053

## 📖 使用指南

### 基本操作
1. **编写代码**: 在Monaco Editor中编写Graph代码
2. **查看图形**: 左侧面板实时显示参数依赖关系
3. **节点交互**: 点击节点查看详细信息和操作菜单
4. **代码跳转**: 使用"Jump to Code"直接定位到代码行

### 代码示例
```python
from core import Graph

# 创建图形
g = Graph("Circuit Analysis")

# 基础参数
g["voltage"] = 12.0
g["current"] = 2.0
g["resistance"] = 6.0

# 计算函数
def power_calculation():
    return g["voltage"] * g["current"]

# 添加计算参数
g.add_computed("power", power_calculation, "Power calculation")
```

### 功能特点
- 🔵 **基础参数**: 左列显示，蓝色背景
- 🟫 **计算参数**: 右列显示，灰色背景
- 🎯 **上下文菜单**: 单击节点显示操作选项
- 📍 **精确定位**: 一键跳转到代码对应行
- 🔄 **实时更新**: 代码修改即时反映

## 🛠️ 技术栈

- **Python 3.8+**: 核心运行环境
- **Dash**: Web应用框架
- **Plotly**: 交互式图形可视化
- **Monaco Editor**: 专业代码编辑器
- **Bootstrap**: 现代UI设计

## 📁 项目结构

```
ArchDash/
├── plotly_graph_visualizer.py  # 主应用文件
├── core/                       # 核心Graph类
│   ├── __init__.py
│   └── graph.py
├── assets/                     # 静态资源
│   ├── modern_style.css
│   └── tab-sid.js
├── tests/                      # 测试文件
└── README.md                   # 项目说明
```

## 🎮 交互说明

### 图形操作
- **拖拽**: 平移视图
- **滚轮**: 缩放图形
- **点击节点**: 显示上下文菜单
- **悬停**: 查看参数详细信息

### 菜单选项
- **🔍 Jump to Code**: 跳转到代码对应行
- **📋 Copy Name**: 复制参数名称
- **❌ Close**: 关闭菜单

### 代码编辑
- **语法高亮**: 自动Python语法着色
- **自动补全**: Graph API智能提示
- **错误检查**: 实时语法错误提示
- **快捷键**: 支持VS Code标准快捷键

## 🔧 开发模式

支持两种运行模式:

1. **在线模式** (推荐): 
   ```bash
   python plotly_graph_visualizer.py --mode online
   ```
   
2. **离线模式**:
   ```bash
   python plotly_graph_visualizer.py --mode offline
   ```

## 🧪 运行测试

```bash
# 运行核心测试
pytest tests/new_graph_tests/

# 运行所有测试
pytest tests/
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**🎯 现在就开始体验专业级的图形参数可视化！**