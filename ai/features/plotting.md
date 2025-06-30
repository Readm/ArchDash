# ArchDash 绘图功能文档

## 目录
1. [功能概述](#功能概述)
2. [参数敏感性分析](#参数敏感性分析)
3. [累计绘图功能](#累计绘图功能)
4. [技术实现](#技术实现)
5. [用户指南](#用户指南)
6. [未来规划](#未来规划)

## 功能概述

ArchDash的绘图功能主要包含两个核心部分：
1. 参数敏感性分析：分析一个参数变化对另一个参数的影响
2. 累计绘图功能：在同一图表中显示多次分析的结果

### 界面布局
```
┌─────────────────────────────────────────────────────────┐
│                     参数敏感性分析                         │
├─────────────────────────────────────────────────────────┤
│ X轴参数: [选择器] Y轴参数: [选择器]                        │
│ 起始值: [输入] 结束值: [输入] 步长: [输入]                 │
│ 系列名称: [输入框]     ☐ 累计绘图                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                    图表显示区域                           │
│                                                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 参数敏感性分析

### 核心功能
1. **参数选择**：
   - X轴参数（独立变量）选择
   - Y轴参数（依赖变量）选择
   - 范围设置（起始值、结束值、步长）

2. **分析执行**：
   - 在指定范围内改变X轴参数
   - 自动计算Y轴参数响应
   - 生成响应曲线

3. **结果展示**：
   - 交互式图表
   - 支持缩放和平移
   - 数据点显示
   - 导出功能

### 技术实现
```python
def perform_sensitivity_analysis(x_param_info, y_param_info, x_start, x_end, x_step):
    """执行参数敏感性分析
    
    Args:
        x_param_info: X轴参数信息
        y_param_info: Y轴参数信息
        x_start: 起始值
        x_end: 结束值
        x_step: 步长
    
    Returns:
        dict: 分析结果
    """
    x_node_id, x_param_name = x_param_info['value'].split('|')
    y_node_id, y_param_name = y_param_info['value'].split('|')
    
    # 获取参数对象
    x_param = graph.nodes[x_node_id].get_parameter_by_name(x_param_name)
    y_param = graph.nodes[y_node_id].get_parameter_by_name(y_param_name)
    
    # 保存原始值
    original_x_value = x_param.value
    
    try:
        x_values = []
        y_values = []
        
        # 生成X轴取值范围
        x_range = np.arange(x_start, x_end + x_step, x_step)
        
        for x_val in x_range:
            # 设置X参数值
            x_param.value = x_val
            
            # 触发Y参数重新计算
            if y_param.calculation_func:
                y_param.calculate()
            
            x_values.append(x_val)
            y_values.append(y_param.value)
        
        return {
            'x_values': x_values,
            'y_values': y_values,
            'x_label': f"{x_param_info['label']} ({x_param.unit})",
            'y_label': f"{y_param_info['label']} ({y_param.unit})",
            'success': True
        }
    
    finally:
        # 恢复原始值
        x_param.value = original_x_value
```

## 累计绘图功能

### 功能特性
1. **累计模式**：
   - 可选择是否启用累计模式
   - 在同一图表中显示多条曲线
   - 最多支持10条历史曲线

2. **系列管理**：
   - 自定义系列名称
   - 自动生成默认名称
   - 图例显示优化

3. **视觉效果**：
   - 历史曲线渐变效果
   - 当前曲线突出显示
   - 清晰的图例标识

### 数据结构
```python
trace_data = {
    'x_values': x_values,           # X轴数据点
    'y_values': y_values,           # Y轴数据点
    'x_label': x_label,             # X轴标签
    'y_label': y_label,             # Y轴标签
    'trace_name': series_name,      # 曲线名称
    'x_param': x_param,             # X轴参数标识
    'y_param': y_param,             # Y轴参数标识
    'timestamp': timestamp          # 生成时间戳
}
```

## 技术实现

### 核心组件
1. **参数选择器**：
   ```python
   def get_plotting_parameters():
       """获取所有可用于绘图的参数"""
       all_params = []
       for node_id, node in graph.nodes.items():
           for param in node.parameters:
               all_params.append({
                   'label': f"{node.name}.{param.name}",
                   'value': f"{node_id}|{param.name}",
                   'node_id': node_id,
                   'param_name': param.name
               })
       return all_params
   ```

2. **图表生成**：
   ```python
   def generate_plot(result, is_cumulative=False, cumulative_data=None):
       """生成Plotly图表"""
       fig = go.Figure()
       
       # 添加历史曲线
       if is_cumulative and cumulative_data:
           for i, trace in enumerate(cumulative_data):
               opacity = max(0.3, 1.0 - i * 0.1)
               fig.add_trace(go.Scatter(
                   x=trace['x_values'],
                   y=trace['y_values'],
                   name=f"{trace['trace_name']} (历史)",
                   opacity=opacity,
                   line=dict(width=1.5)
               ))
       
       # 添加当前曲线
       fig.add_trace(go.Scatter(
           x=result['x_values'],
           y=result['y_values'],
           name="当前",
           line=dict(width=2, color='#1f77b4')
       ))
       
       return fig
   ```

### 性能优化
1. **数据限制**：
   - 最多保存10条历史曲线
   - 自动删除最旧的数据

2. **渲染优化**：
   - 历史曲线使用较小的标记点
   - 透明度递减效果
   - 按需加载数据

## 用户指南

### 基本使用流程
1. 选择X轴和Y轴参数
2. 设置分析范围
3. （可选）启用累计模式
4. （可选）设置系列名称
5. 点击"生成图表"按钮
6. 查看和交互图表
7. 导出数据（如需要）

### 高级使用技巧
1. **参数对比**：
   - 固定X轴，更改Y轴参数
   - 观察不同参数的响应特性

2. **范围分析**：
   - 使用不同的分析范围
   - 研究参数在不同区间的行为

3. **设计优化**：
   - 记录设计迭代过程
   - 对比优化效果

## 未来规划

### 短期计划
1. **功能增强**：
   - 多Y轴参数同时分析
   - 更多图表类型支持
   - 范围预设功能

2. **用户体验**：
   - 曲线标注功能
   - 选择性删除历史曲线
   - 更多配色方案

### 长期规划
1. **高级分析**：
   - 3D参数分析
   - 统计分析功能
   - 优化算法集成

2. **系统集成**：
   - 自动报告生成
   - 数据库存储支持
   - API接口扩展 