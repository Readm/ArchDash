# Plotly图形可视化工具

## 🎯 功能概述

纯Plotly实现的交互式图形可视化工具，支持两种模式：
- **在线模式**: Dash Web应用，实时编辑
- **离线模式**: 生成HTML文件，无需服务器

## 🚀 快速使用

### 安装依赖

```bash
# 基础安装（离线模式）
pip install plotly

# 完整安装（两种模式）
pip install plotly dash dash-bootstrap-components
```

### 运行命令

```bash
# 离线模式 - 生成HTML文件
python plotly_graph_visualizer.py --mode offline

# 在线模式 - Web应用
python plotly_graph_visualizer.py --mode online
```

## 📊 两种模式对比

### 在线模式 (`--mode online`)
✅ **优势**:
- 🌐 现代Web UI，实时编辑
- 🔄 代码修改即时更新图形
- 🎮 完整交互：拖拽、缩放、悬停
- 💾 可保存HTML文件
- 📱 多设备访问

❌ **要求**:
- 需要运行Web服务器
- 依赖：`dash`, `plotly`, `dash-bootstrap-components`
- 访问：http://localhost:8050

### 离线模式 (`--mode offline`)
✅ **优势**:
- 📁 生成独立HTML文件
- 🚫 无需Web服务器
- 🎮 保持完整交互性
- 📤 文件可直接分享
- ⚡ 启动即用

❌ **限制**:
- 需要手动输入代码
- 依赖：仅需`plotly`

## 🎮 交互功能

两种模式都支持：
- **节点拖拽**: 直接拖动节点位置
- **悬停高亮**: 鼠标悬停显示详细信息
- **缩放平移**: 鼠标滚轮缩放，拖拽平移
- **工具栏**: 保存图片、重置视图等
- **颜色编码**: 蓝色=基础参数，绿色=计算参数

## 💡 使用场景

### 日常开发
```bash
# 快速验证代码
python plotly_graph_visualizer.py --mode offline
```

### 演示分享
```bash
# 生成可分享的HTML文件
python plotly_graph_visualizer.py --mode offline
# 将生成的HTML文件发送给他人
```

### 实时协作
```bash
# 启动Web应用供团队使用
python plotly_graph_visualizer.py --mode online
```

## 📝 代码示例

### 基础用法
```python
from core import Graph

g = Graph("示例")
g["输入"] = 10
g["输出"] = 20

def 计算():
    return g["输入"] + g["输出"]

g.add_computed("结果", 计算, "求和")
```

### 复杂依赖
```python
# 多层依赖关系
def 中间值():
    return g["A"] * g["B"]

def 最终结果():
    return g["中间"] + g["C"]

g.add_computed("中间", 中间值, "中间计算")
g.add_computed("最终", 最终结果, "最终结果")
```

## 🔧 输出文件

### 在线模式
- 实时Web界面：http://localhost:8050
- 可选保存HTML文件

### 离线模式  
- 自动生成：`/tmp/graph_visualizer_offline.html`
- 包含完整交互功能
- 可直接在浏览器打开

## 🎉 总结

**完美回答您的需求**:
- ✅ **仅使用Plotly**: 没有matplotlib依赖
- ✅ **两种模式**: 在线Web应用 + 离线HTML生成
- ✅ **完整交互**: 节点拖拽、悬停、缩放等所有功能
- ✅ **启动参数**: `--mode online/offline` 灵活切换
- ✅ **无需服务器**: 离线模式生成独立HTML文件

现在您可以根据需要选择合适的模式，享受完整的Plotly交互体验！