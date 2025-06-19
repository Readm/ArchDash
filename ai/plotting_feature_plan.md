# ArchDash 参数敏感性分析绘图功能实施计划

## 功能概述

在ArchDash应用的最右侧添加一个参数敏感性分析绘图区域，用于可视化参数之间的关系。用户可以选择一个独立参数作为X轴，一个依赖参数作为Y轴，观察当X轴参数在指定范围内变化时，Y轴参数的响应曲线。

## 功能需求

### 核心功能
1. **参数选择**：选择X轴参数（独立变量）和Y轴参数（依赖变量）
2. **范围设置**：设置X轴参数的变化范围（起始值、结束值、步长）
3. **实时绘图**：基于参数关系生成响应曲线
4. **交互式图表**：支持缩放、平移、数据点显示等

### 高级功能
1. **多曲线对比**：同时绘制多个Y参数的响应曲线
2. **参数导出**：导出绘图数据为CSV或JSON
3. **图表导出**：导出图表为PNG或SVG

## 技术架构

### 前端UI组件
```
绘图区域布局：
┌─────────────────────────────────────┐
│            参数敏感性分析              │
├─────────────────────────────────────┤
│ X轴参数: [选择器] Y轴参数: [选择器]    │
│ 起始值: [输入] 结束值: [输入]        │
│ 步长: [输入] [绘图按钮] [清除按钮]    │
├─────────────────────────────────────┤
│                                   │
│          图表显示区域                │
│                                   │
│                                   │
└─────────────────────────────────────┘
```

### 依赖库
- **Plotly**: 用于交互式图表绘制
- **NumPy**: 用于数值计算和数组操作
- **Pandas**: 用于数据处理（可选）

### 数据流程
1. 用户选择X轴和Y轴参数
2. 设置X轴参数的变化范围
3. 系统在范围内逐步改变X轴参数值
4. 触发依赖计算，获取对应的Y轴参数值
5. 收集所有数据点，生成图表

## 实施步骤

### 第一阶段：基础UI框架
1. **布局调整**
   - 将当前画布容器从12列调整为8列
   - 新增4列宽的绘图区域容器
   - 确保响应式设计

2. **绘图区域组件**
   ```python
   # 绘图区域基础结构
   plotting_area = dbc.Col([
       html.H5("参数敏感性分析", className="text-center mb-3"),
       
       # 参数选择区域
       dbc.Card([
           dbc.CardBody([
               dbc.Row([
                   dbc.Col([
                       dbc.Label("X轴参数:"),
                       dcc.Dropdown(id="x-param-selector", placeholder="选择X轴参数")
                   ], width=6),
                   dbc.Col([
                       dbc.Label("Y轴参数:"),
                       dcc.Dropdown(id="y-param-selector", placeholder="选择Y轴参数")
                   ], width=6),
               ], className="mb-3"),
               
               dbc.Row([
                   dbc.Col([
                       dbc.Label("起始值:"),
                       dbc.Input(id="x-start-value", type="number", value=0)
                   ], width=4),
                   dbc.Col([
                       dbc.Label("结束值:"),
                       dbc.Input(id="x-end-value", type="number", value=100)
                   ], width=4),
                   dbc.Col([
                       dbc.Label("步长:"),
                       dbc.Input(id="x-step-value", type="number", value=1)
                   ], width=4),
               ], className="mb-3"),
               
               dbc.Row([
                   dbc.Col([
                       dbc.ButtonGroup([
                           dbc.Button("🔄 生成图表", id="generate-plot-btn", color="primary"),
                           dbc.Button("🗑️ 清除", id="clear-plot-btn", color="secondary"),
                           dbc.Button("📊 导出数据", id="export-plot-data-btn", color="info")
                       ])
                   ])
               ])
           ])
       ], className="mb-3"),
       
       # 图表显示区域
       dbc.Card([
           dbc.CardBody([
               dcc.Graph(
                   id="sensitivity-plot",
                   style={"height": "400px"},
                   config={
                       'displayModeBar': True,
                       'modeBarButtonsToRemove': ['pan2d', 'lasso2d']
                   }
               )
           ])
       ])
   ], width=4)
   ```

### 第二阶段：参数选择逻辑
1. **参数收集函数**
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
                   'param_name': param.name,
                   'param_obj': param,
                   'current_value': param.value,
                   'unit': param.unit
               })
       return all_params
   ```

2. **动态更新下拉选择器**
   ```python
   @callback(
       Output("x-param-selector", "options"),
       Output("y-param-selector", "options"),
       Input("canvas-container", "children"),
       prevent_initial_call=True
   )
   def update_param_selectors(canvas_children):
       params = get_plotting_parameters()
       return params, params
   ```

### 第三阶段：敏感性分析核心算法
1. **参数扫描函数**
   ```python
   def perform_sensitivity_analysis(x_param_info, y_param_info, x_start, x_end, x_step):
       """执行参数敏感性分析"""
       x_node_id, x_param_name = x_param_info['value'].split('|')
       y_node_id, y_param_name = y_param_info['value'].split('|')
       
       # 获取参数对象
       x_param = graph.nodes[x_node_id].get_parameter_by_name(x_param_name)
       y_param = graph.nodes[y_node_id].get_parameter_by_name(y_param_name)
       
       # 保存原始值
       original_x_value = x_param.value
       
       x_values = []
       y_values = []
       
       try:
           # 生成X轴取值范围
           x_range = np.arange(x_start, x_end + x_step, x_step)
           
           for x_val in x_range:
               # 设置X参数值
               if hasattr(graph, 'set_parameter_value'):
                   graph.set_parameter_value(x_param, x_val)
               else:
                   x_param.value = x_val
                   
               # 如果Y参数有计算函数，触发重新计算
               if y_param.calculation_func:
                   try:
                       y_param.calculate()
                   except Exception as e:
                       print(f"计算错误 (X={x_val}): {e}")
                       continue
               
               x_values.append(x_val)
               y_values.append(y_param.value)
           
           return {
               'x_values': x_values,
               'y_values': y_values,
               'x_label': f"{x_param_info['label']} ({x_param.unit})",
               'y_label': f"{y_param_info['label']} ({y_param.unit})",
               'success': True,
               'message': f"成功生成 {len(x_values)} 个数据点"
           }
           
       except Exception as e:
           return {
               'success': False,
               'message': f"分析失败: {str(e)}"
           }
       finally:
           # 恢复原始值
           if hasattr(graph, 'set_parameter_value'):
               graph.set_parameter_value(x_param, original_x_value)
           else:
               x_param.value = original_x_value
   ```

### 第四阶段：图表绘制
1. **Plotly图表生成**
   ```python
   @callback(
       Output("sensitivity-plot", "figure"),
       Output("output-result", "children", allow_duplicate=True),
       Input("generate-plot-btn", "n_clicks"),
       State("x-param-selector", "value"),
       State("y-param-selector", "value"),
       State("x-start-value", "value"),
       State("x-end-value", "value"),
       State("x-step-value", "value"),
       prevent_initial_call=True
   )
   def generate_sensitivity_plot(n_clicks, x_param, y_param, x_start, x_end, x_step):
       if not n_clicks or not x_param or not y_param:
           return {}, "请选择参数并点击生成图表"
       
       # 获取参数信息
       all_params = get_plotting_parameters()
       x_param_info = next((p for p in all_params if p['value'] == x_param), None)
       y_param_info = next((p for p in all_params if p['value'] == y_param), None)
       
       if not x_param_info or not y_param_info:
           return {}, "参数选择错误"
       
       # 执行敏感性分析
       result = perform_sensitivity_analysis(
           x_param_info, y_param_info, 
           x_start or 0, x_end or 100, x_step or 1
       )
       
       if not result['success']:
           return {}, result['message']
       
       # 创建Plotly图表
       import plotly.graph_objects as go
       
       fig = go.Figure()
       
       fig.add_trace(go.Scatter(
           x=result['x_values'],
           y=result['y_values'],
           mode='lines+markers',
           name=f"{y_param_info['label']}",
           line=dict(width=2),
           marker=dict(size=6)
       ))
       
       fig.update_layout(
           title=f"参数敏感性分析: {result['y_label']} vs {result['x_label']}",
           xaxis_title=result['x_label'],
           yaxis_title=result['y_label'],
           hovermode='x unified',
           template="plotly_white",
           showlegend=True
       )
       
       return fig, result['message']
   ```

### 第五阶段：高级功能
1. **多曲线绘制**
   - 支持选择多个Y轴参数
   - 在同一图表中显示多条曲线
   - 不同颜色区分不同参数

2. **数据导出功能**
   ```python
   @callback(
       Output("download-plot-data", "data"),
       Input("export-plot-data-btn", "n_clicks"),
       State("sensitivity-plot", "figure"),
       prevent_initial_call=True
   )
   def export_plot_data(n_clicks, figure):
       if not n_clicks or not figure:
           raise dash.exceptions.PreventUpdate
       
       # 提取图表数据并导出为CSV
       # ... 实现数据导出逻辑
   ```

## 技术挑战与解决方案

### 1. 参数依赖计算
**挑战**: 改变X轴参数值时，需要正确触发依赖链的重新计算
**解决方案**: 
- 利用现有的`graph.set_parameter_value()`方法
- 确保所有依赖参数都能正确更新

### 2. 性能优化
**挑战**: 大范围参数扫描可能导致性能问题
**解决方案**:
- 限制最大数据点数量（如1000个点）
- 添加进度指示器
- 支持异步计算（如果需要）

### 3. 参数类型兼容
**挑战**: 不同类型的参数值（数值、字符串）的处理
**解决方案**:
- 只允许数值类型参数作为X轴
- 添加参数类型检查和验证

### 4. 错误处理
**挑战**: 计算过程中可能出现各种错误
**解决方案**:
- 完善的异常捕获和错误信息显示
- 提供计算失败时的回退机制

## 用户体验设计

### 界面交互流程
1. 用户在左侧创建节点和参数，建立依赖关系
2. 在右侧绘图区域选择要分析的参数
3. 设置X轴参数的变化范围
4. 点击"生成图表"按钮
5. 查看生成的敏感性分析图表
6. 可选：导出数据或调整参数重新绘制

### 视觉设计
- 采用Bootstrap主题保持一致性
- 绘图区域使用卡片布局，清晰分割功能区域
- 图表使用Plotly默认的现代化样式
- 添加适当的加载动画和状态提示

## 实施时间估算

1. **第一阶段 (UI框架)**: 1-2天
2. **第二阶段 (参数选择)**: 1天
3. **第三阶段 (核心算法)**: 2-3天
4. **第四阶段 (图表绘制)**: 1-2天
5. **第五阶段 (高级功能)**: 2-3天
6. **测试和优化**: 1-2天

**总计**: 8-13天

## 后续扩展计划

1. **3D参数分析**: 支持两个独立参数的3D曲面分析
2. **参数优化**: 集成优化算法，寻找最优参数组合
3. **不确定性分析**: 基于参数置信度的蒙特卡洛分析
4. **批量分析**: 支持多组参数的批量敏感性分析 