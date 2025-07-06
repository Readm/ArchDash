# ArchDash 测试标记策略

## 概述
本文档解释了为什么某些组件不能使用 `data-testid` 属性，以及我们的测试标记策略。

## 组件兼容性问题

### 不支持 `data-testid` 的组件
以下 Dash Bootstrap Components 不支持 `data-testid` 属性：

1. **`dbc.DropdownMenuItem`** - 使用 `id` 属性定位
2. **`dbc.Button`** - 使用 `id` 属性定位  
3. **`dbc.Modal`** - 使用 `id` 属性定位
4. **`dbc.Input`/`dbc.Textarea`** - 使用 `id` 属性定位
5. **`dbc.DropdownMenu`** - 使用 `id` 属性定位
6. **`dcc.Upload`** - 使用 `id` 属性定位

### 支持 `data-testid` 的组件
以下组件支持 `data-testid` 属性：

1. **`html.Button`** ✅ - 主要交互按钮
2. **`html.Div`** ✅ - 容器和状态指示器
3. **`html.Span`** ✅ - 节点名称和参数标识
4. **`html.Table`** ✅ - 参数表格
5. **`dcc.Input`** ✅ - 参数输入框
6. **`dcc.Dropdown`** ✅ - 下拉选择器

## 当前的测试标记实现

### 1. 节点元素测试标记
```python
# 节点容器
**{"data-testid": f"node-{node_id}", "data-node-name": node_name}

# 节点名称
**{"data-testid": f"node-name-{node_id}"}

# 添加参数按钮（html.Button）
**{"data-testid": f"add-param-btn-{node_id}"}
```

### 2. 参数测试标记
```python
# 参数行
**{"data-testid": f"param-row-{node_id}-{param_idx}"}

# 参数名输入框（dcc.Input）
**{"data-testid": f"param-name-input-{node_id}-{param_idx}"}

# 参数值输入框（dcc.Input）
**{"data-testid": f"param-value-input-{node_id}-{param_idx}"}

# 参数单位显示（html.Span）
**{"data-testid": f"param-unit-{node_id}-{param_idx}"}

# Pin点（html.Div）
**{"data-testid": f"param-pin-{node_id}-{param_idx}"}
```

### 3. 页面状态标记
```python
# 画布容器
**{"data-testid": "canvas-container"}

# 画布状态（空状态/有节点）
**{"data-testid": "canvas-with-arrows", "data-state": "with-nodes", "data-ready": "true"}

# 空状态提示
**{"data-testid": "empty-state", "data-state": "empty", "data-ready": "true"}
```

### 4. 主要按钮测试标记
```python
# 顶部工具栏按钮（html.Button）
**{"data-testid": "add-node-button"}
**{"data-testid": "load-file-button"}
**{"data-testid": "save-file-button"}
**{"data-testid": "load-example-button"}
**{"data-testid": "theme-toggle-button"}
```

## 不支持组件的测试策略

### 1. 使用 ID 属性定位
```python
# 下拉菜单项
selenium.find_element(By.ID, "add-column-btn")
selenium.find_element(By.ID, "remove-column-btn")

# 模态框
selenium.find_element(By.ID, "param-edit-modal")
selenium.find_element(By.ID, "node-edit-modal")
```

### 2. 使用复合选择器
```python
# 节点菜单项（通过类型和节点ID）
selenium.find_element(By.CSS_SELECTOR, "[data-type='edit-node'][data-node='node_1']")
selenium.find_element(By.CSS_SELECTOR, "[data-type='delete-node'][data-node='node_1']")
```

### 3. 使用父容器定位
```python
# 在特定节点内查找元素
node = selenium.find_element(By.CSS_SELECTOR, f"[data-testid='node-{node_id}']")
menu_btn = node.find_element(By.CSS_SELECTOR, ".dropdown-toggle")
```

## 测试工具函数

### 安全元素获取
```python
def get_parameter_input_safe(selenium, testid, timeout=10):
    """使用data-testid安全获取参数输入框"""
    element = selenium.find_element(By.CSS_SELECTOR, f"[data-testid='{testid}']")
    return element

def click_button_by_testid(selenium, testid, timeout=10):
    """通过data-testid安全点击按钮"""
    WebDriverWait(selenium, timeout).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='{testid}']"))
    )
    
def get_node_element_by_testid(selenium, node_id):
    """通过data-testid获取节点元素"""
    node = selenium.find_element(By.CSS_SELECTOR, f"[data-testid='node-{node_id}']")
    return node
```

### 状态等待函数
```python
def wait_for_canvas_ready(selenium, timeout=30):
    """等待画布准备就绪"""
    WebDriverWait(selenium, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='canvas-with-arrows'][data-ready='true']"))
    )

def wait_for_empty_state(selenium, timeout=30):
    """等待空状态显示"""
    WebDriverWait(selenium, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='empty-state'][data-ready='true']"))
    )
```

## 为什么需要移除某些测试标记

1. **组件兼容性** - 某些组件不支持 `data-testid` 属性，会导致应用程序无法启动
2. **版本限制** - Dash Bootstrap Components 版本限制了可用的属性
3. **测试稳定性** - 使用不支持的属性会导致测试失败

## 总结

- ✅ **保留支持的测试标记** - 所有 `html.*` 和 `dcc.*` 组件
- ❌ **移除不支持的测试标记** - 所有 `dbc.*` 组件的 `data-testid`
- 🔄 **使用替代策略** - ID 属性和复合选择器
- 📋 **完善测试工具** - 提供安全的元素获取函数

这种策略确保了：
1. 应用程序能够正常启动
2. 测试用例能够稳定运行
3. 测试标记覆盖了所有重要的交互元素 