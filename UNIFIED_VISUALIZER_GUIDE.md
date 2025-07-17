# 统一图形可视化工具使用指南

## 🎯 概述

现在您有了一个**统一的图形可视化工具**，支持三种不同的运行模式，可以根据需求和环境选择最合适的方案。

## 🚀 快速开始

### 基本用法
```bash
# 查看帮助
python unified_graph_visualizer.py --help

# 使用不同模式
python unified_graph_visualizer.py --mode online   # 在线模式
python unified_graph_visualizer.py --mode offline  # 离线模式  
python unified_graph_visualizer.py --mode window   # 窗口模式
```

## 📊 三种模式详细对比

### 1. 在线模式 (`--mode online`)
**特点**: 现代Web应用，功能最完整
```bash
python unified_graph_visualizer.py --mode online
```

✅ **优势**:
- 🌐 现代化Web界面，响应式设计
- 🔄 实时代码编辑，无需点击刷新
- 🎮 完整交互功能：拖拽、缩放、悬停
- 🎨 最佳视觉效果和用户体验
- 📱 支持多设备访问

❌ **限制**:
- 需要运行Web服务器
- 依赖：`dash`, `plotly`, `dash-bootstrap-components`
- 需要浏览器访问 http://localhost:8050

**适用场景**: 开发环境，团队协作，最佳用户体验

### 2. 离线模式 (`--mode offline`)  
**特点**: 桌面应用，无需服务器
```bash
python unified_graph_visualizer.py --mode offline
```

✅ **优势**:
- 🖥️ 桌面GUI应用，无需Web服务器
- 🌐 图形在浏览器中渲染，保持完整交互性
- 📁 生成可分享的HTML文件
- 🔌 完全离线运行
- ⚡ 启动速度快

❌ **限制**:
- 图形在外部浏览器显示
- 依赖：`plotly`, `tkinter`
- 需要点击按钮生成图形

**适用场景**: 单机使用，无网络环境，文件分享

### 3. 窗口模式 (`--mode window`)
**特点**: 轻量级，最小依赖
```bash
python unified_graph_visualizer.py --mode window
```

✅ **优势**:
- 🪶 最轻量级，依赖最少
- 🖼️ 完全在窗口内显示
- 🚫 无需浏览器
- 📦 适合受限环境

❌ **限制**:
- 交互功能有限
- 视觉效果基础
- 依赖：`matplotlib`, `tkinter`

**适用场景**: 资源受限环境，快速预览，简单可视化

## 🛠️ 安装依赖

### 最小安装（窗口模式）
```bash
pip install matplotlib
```

### 离线模式
```bash
pip install matplotlib plotly
```

### 完整安装（所有模式）
```bash
pip install matplotlib plotly dash dash-bootstrap-components
```

## 🎮 功能对比表

| 功能特性 | 在线模式 | 离线模式 | 窗口模式 |
|---------|---------|---------|---------|
| 节点拖拽 | ✅ 原生支持 | ✅ 原生支持 | ❌ 不支持 |
| 悬停高亮 | ✅ 丰富效果 | ✅ 丰富效果 | ⚠️ 基础支持 |
| 缩放平移 | ✅ 流畅 | ✅ 流畅 | ⚠️ 有限 |
| 实时编辑 | ✅ 自动更新 | ❌ 需点击 | ❌ 需点击 |
| 现代UI | ✅ Bootstrap | ⚠️ 基础 | ❌ 传统 |
| 启动速度 | ⚠️ 中等 | ✅ 快速 | ✅ 最快 |
| 部署难度 | ⚠️ 需服务器 | ✅ 简单 | ✅ 最简单 |
| 网络依赖 | ⚠️ 需要 | ❌ 无需 | ❌ 无需 |
| 文件分享 | ❌ 不适合 | ✅ HTML文件 | ❌ 截图 |

## 💡 使用建议

### 选择指南
1. **追求最佳体验** → 在线模式
2. **需要离线使用** → 离线模式  
3. **环境受限/快速预览** → 窗口模式

### 典型工作流

#### 开发阶段
```bash
# 开发时使用在线模式
python unified_graph_visualizer.py --mode online
```

#### 演示分享
```bash
# 生成HTML文件分享
python unified_graph_visualizer.py --mode offline
# 生成graph_visualizer.html文件，可以发送给他人
```

#### 快速检查
```bash
# 快速验证代码
python unified_graph_visualizer.py --mode window
```

## 🔧 高级用法

### 自定义端口（在线模式）
可以修改代码中的端口设置：
```python
# 在interactive_graph_visualizer.py中修改
visualizer.run_server(debug=False, port=8051)
```

### 自定义保存路径（离线模式）
HTML文件默认保存在临时目录，可以修改保存位置。

### 批量处理
可以通过脚本调用不同模式：
```bash
#!/bin/bash
echo "生成在线版本..."
python unified_graph_visualizer.py --mode online &

echo "生成离线文件..."
python unified_graph_visualizer.py --mode offline
```

## 🎉 总结

**统一可视化工具**为您提供了完整的解决方案：

🎯 **回答您的核心问题**:
- ✅ **Plotly不一定需要Web**: 离线模式证明可以生成本地HTML
- ✅ **支持窗口内渲染**: 窗口模式完全在应用内显示
- ✅ **灵活的启动参数**: `--mode` 参数轻松切换方案

🚀 **推荐的使用策略**:
- **日常开发**: 使用在线模式获得最佳体验
- **文件分享**: 使用离线模式生成HTML文件
- **快速预览**: 使用窗口模式进行快速检查

现在您可以根据具体需求选择最合适的模式，享受完整的图形可视化功能！