# 🎨 ArchDash

[![PyPI version](https://badge.fury.io/py/archdash.svg)](https://badge.fury.io/py/archdash)
[![Python Version](https://img.shields.io/pypi/pyversions/archdash.svg)](https://pypi.org/project/archdash/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://pepy.tech/badge/archdash)](https://pepy.tech/project/archdash)

ArchDash 是一个强大的架构计算工具，用于构建和分析复杂的计算图。通过直观的 Web 界面，您可以轻松创建节点、设置参数、建立依赖关系，并进行参数敏感性分析。

![系统界面预览](https://raw.githubusercontent.com/Readm/ArchDash/release/screenshot.png)

## ✨ 主要功能

- 🏗️ **可视化计算图构建** - 通过拖拽创建节点和参数
- 🔗 **智能依赖管理** - 自动检测和防止循环依赖
- ⚡ **实时计算更新** - 参数变化时自动重新计算依赖项
- 📊 **参数敏感性分析** - 可视化参数对结果的影响
- 🎯 **累计绘图模式** - 对比多个分析结果
- 💾 **数据导出功能** - 支持计算图和分析数据导出
- 🌙 **深色/浅色主题** - 优雅的用户界面设计
- 📝 **Python 代码编辑** - 内置代码编辑器支持复杂计算

## 🚀 快速开始

### 方式一：从 PyPI 安装（推荐）

```bash
# 创建虚拟环境（可选但推荐）
python -m venv archdash-env
source archdash-env/bin/activate  # Linux/macOS
# 或 archdash-env\Scripts\activate  # Windows

# 安装 ArchDash
pip install archdash

# 启动应用
archdash

# 指定端口启动
archdash --port 8080

# 调试模式启动
archdash --debug
```

### 方式二：从源码安装

```bash
# 克隆仓库
git clone https://github.com/Readm/ArchDash.git
cd ArchDash

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行应用
python app.py
```

### 访问应用

无论使用哪种安装方式，应用启动后都可以通过浏览器访问：
- 默认地址：http://localhost:8050
- 自定义端口：http://localhost:YOUR_PORT

### ⚠️ 环境要求

- **Python**: 3.8 或更高版本
- **操作系统**: Windows, macOS, Linux
- **浏览器**: Chrome, Firefox, Safari, Edge（推荐使用现代浏览器）

### 💡 安装提示

1. **虚拟环境**: 强烈建议使用虚拟环境以避免依赖冲突
2. **网络**: 首次安装需要下载约 50MB 的依赖包
3. **权限**: 某些系统可能需要管理员权限安装包
4. **防火墙**: 确保所选端口未被防火墙阻止

## 🛠️ 技术栈

- **后端**: Python 3.8+, Flask
- **前端**: Dash, Bootstrap
- **数据处理**: Pandas, NumPy
- **可视化**: Plotly
- **代码编辑**: Ace Editor
- **测试**: Pytest

## 📖 使用指南

### 1. 创建节点
- 点击左上角 ➕ 按钮创建新节点
- 双击节点编辑名称和描述

### 2. 添加参数
- 使用节点标题栏的 ➕ 按钮添加参数
- 双击参数进入详细编辑模式

### 3. 建立依赖关系
- 在参数编辑面板中选择依赖参数
- 编写计算函数（支持 Python 语法）
- 系统自动检测循环依赖

### 4. 敏感性分析
- 选择 X 轴和 Y 轴参数
- 设置扫描范围和步长
- 生成可视化分析图表

### 5. 数据导出
- 保存完整计算图为 JSON 文件
- 导出敏感性分析数据为 CSV 文件

## 🎯 示例应用

ArchDash 适用于多种场景：

- **架构设计评估** - 评估不同架构参数对性能的影响
- **多核 SoC 分析** - 分析处理器核心数、频率等参数关系
- **系统优化** - 通过参数扫描找到最优配置
- **教学演示** - 可视化展示复杂系统的参数依赖关系

点击应用内的 🎯 按钮可以加载一个多核SoC示例，快速了解系统功能。

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 📝 开发

### 本地开发设置

```bash
# 克隆仓库
git clone https://github.com/Readm/ArchDash.git
cd ArchDash

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -r requirements.txt
pip install -e .

# 运行测试
pytest

# 启动开发服务器
python app.py --debug
```

### 虚拟环境管理

```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 停用虚拟环境
deactivate

# 删除虚拟环境（如需重新创建）
rm -rf venv  # Linux/macOS
rmdir /s venv  # Windows
```

### 项目结构

```
ArchDash/
├── archdash/           # 主包目录
│   ├── __init__.py
│   ├── app.py         # 主应用文件
│   ├── models.py      # 数据模型
│   ├── layout.py      # UI 布局
│   ├── constants.py   # 常量定义
│   └── assets/        # 静态资源
├── tests/             # 测试文件
├── requirements.txt   # 依赖列表
├── setup.py          # 包配置
└── README.md         # 项目说明
```

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [Dash](https://dash.plotly.com/) - 强大的 Python Web 框架
- [Plotly](https://plotly.com/) - 优秀的数据可视化库
- [Bootstrap](https://getbootstrap.com/) - 现代化的 CSS 框架

## 📞 联系

- 项目主页: [https://github.com/Readm/ArchDash](https://github.com/Readm/ArchDash)
- PyPI 页面: [https://pypi.org/project/archdash/](https://pypi.org/project/archdash/)
- 问题报告: [https://github.com/Readm/ArchDash/issues](https://github.com/Readm/ArchDash/issues)

---

⭐ 如果这个项目对您有帮助，请给我们一个星标！
