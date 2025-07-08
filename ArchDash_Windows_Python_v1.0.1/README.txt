# ArchDash Windows Python版本

## 简介
ArchDash是一个交互式计算图可视化工具，用于参数敏感性分析和依赖关系管理。

## 系统要求
- Windows 10或更高版本
- Python 3.8或更高版本
- 至少1GB可用磁盘空间

## 安装步骤

### 1. 安装Python（如果尚未安装）
1. 访问 https://www.python.org/downloads/
2. 下载最新的Python 3.x版本
3. 运行安装程序，**重要：勾选"Add Python to PATH"**
4. 完成安装

### 2. 安装ArchDash
1. 解压此压缩包到任意文件夹
2. 双击 `install.bat` 文件
3. 等待安装完成

### 3. 运行应用
1. 双击 `start_ArchDash.bat` 启动应用
2. 等待应用启动完成
3. 在浏览器中访问：http://127.0.0.1:8050

## 功能特性
- 🎨 交互式计算图编辑
- 📊 参数敏感性分析
- 🔄 依赖关系可视化
- 💾 图表保存/加载
- 🎯 示例图表模板

## 故障排除

### Python相关问题
- 如果提示"python不是内部或外部命令"，请重新安装Python并确保勾选"Add Python to PATH"
- 如果安装依赖失败，请尝试以管理员身份运行install.bat

### 应用相关问题
- 如果遇到端口占用，请关闭其他可能使用8050端口的程序
- 如果页面无法打开，请检查防火墙设置
- 如果应用无法启动，请检查Python版本是否为3.8或更高

### 网络问题
- 如果pip安装缓慢，可以使用国内镜像：
  ```
  pip install -r src\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
  ```

## 卸载方法
直接删除整个ArchDash文件夹即可。

## 技术支持
如果遇到问题，请检查：
1. Python版本是否正确
2. 网络连接是否正常
3. 是否有足够的磁盘空间

## 版本信息
- 版本：1.0.1
- 打包日期：2025-07-09
- Python要求：3.8+
- 架构：任何支持Python的Windows系统

## 开发者信息
本软件基于Python/Dash开发，源代码位于src目录。
