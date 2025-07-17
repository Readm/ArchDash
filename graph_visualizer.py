#!/usr/bin/env python3
"""
Graph Visualizer - 可视化代码依赖图工具
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.scrolledtext as scrolledtext
import ast
import re
import sys
import os
from typing import Dict, List, Set, Tuple, Optional
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

# 添加core目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

class CodeParser:
    """代码解析器，提取Graph定义和依赖关系"""
    
    def __init__(self):
        self.graph_name = ""
        self.parameters = {}  # {param_name: {"type": "basic/computed", "value": any, "line": int}}
        self.dependencies = {}  # {param_name: [dependency_list]}
        self.code_lines = []
        
    def parse_code(self, code: str) -> Dict:
        """解析代码，提取Graph信息"""
        self.graph_name = ""
        self.parameters = {}
        self.dependencies = {}
        self.code_lines = code.split('\n')
        
        try:
            tree = ast.parse(code)
            self._analyze_ast(tree)
            return {
                "graph_name": self.graph_name,
                "parameters": self.parameters,
                "dependencies": self.dependencies,
                "success": True,
                "error": None
            }
        except Exception as e:
            return {
                "graph_name": "",
                "parameters": {},
                "dependencies": {},
                "success": False,
                "error": str(e)
            }
    
    def _analyze_ast(self, tree: ast.AST):
        """分析AST树"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                self._analyze_call(node)
            elif isinstance(node, ast.Assign):
                self._analyze_assignment(node)
    
    def _analyze_call(self, node: ast.Call):
        """分析函数调用"""
        if (isinstance(node.func, ast.Name) and 
            node.func.id == "Graph" and 
            len(node.args) > 0):
            # Graph("name") 调用
            if isinstance(node.args[0], ast.Constant):
                self.graph_name = node.args[0].value
    
    def _analyze_assignment(self, node: ast.Assign):
        """分析赋值语句"""
        if len(node.targets) == 1:
            target = node.targets[0]
            
            if isinstance(target, ast.Name):
                # g = Graph("name")
                if isinstance(node.value, ast.Call):
                    self._analyze_graph_creation(target.id, node.value, node.lineno)
                    
            elif isinstance(target, ast.Subscript):
                # g["param"] = value
                if isinstance(target.value, ast.Name):
                    self._analyze_parameter_assignment(target, node.value, node.lineno)
    
    def _analyze_graph_creation(self, var_name: str, call_node: ast.Call, line_no: int):
        """分析Graph创建"""
        if (isinstance(call_node.func, ast.Name) and 
            call_node.func.id == "Graph" and 
            len(call_node.args) > 0):
            if isinstance(call_node.args[0], ast.Constant):
                self.graph_name = call_node.args[0].value
    
    def _analyze_parameter_assignment(self, target: ast.Subscript, value: ast.AST, line_no: int):
        """分析参数赋值"""
        if isinstance(target.slice, ast.Constant):
            param_name = target.slice.value
            param_value = self._extract_value(value)
            
            self.parameters[param_name] = {
                "type": "basic",
                "value": param_value,
                "line": line_no
            }
    
    def _extract_value(self, node: ast.AST) -> str:
        """提取值的字符串表示"""
        if isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.BinOp):
            return f"{self._extract_value(node.left)} {self._extract_op(node.op)} {self._extract_value(node.right)}"
        else:
            return "<复杂表达式>"
    
    def _extract_op(self, op: ast.AST) -> str:
        """提取操作符"""
        if isinstance(op, ast.Add):
            return "+"
        elif isinstance(op, ast.Sub):
            return "-"
        elif isinstance(op, ast.Mult):
            return "*"
        elif isinstance(op, ast.Div):
            return "/"
        else:
            return "?"
    
    def parse_advanced_code(self, code: str) -> Dict:
        """高级代码解析，包括add_computed调用"""
        result = self.parse_code(code)
        if not result["success"]:
            return result
        
        # 使用正则表达式解析add_computed调用
        self._parse_add_computed_calls(code)
        
        result["parameters"] = self.parameters
        result["dependencies"] = self.dependencies
        return result
    
    def _parse_add_computed_calls(self, code: str):
        """解析add_computed调用"""
        lines = code.split('\n')
        
        # 查找函数定义
        function_defs = {}
        current_func = None
        func_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('def '):
                if current_func:
                    function_defs[current_func] = func_lines
                # 提取函数名
                func_name = stripped.split('(')[0].replace('def ', '').strip()
                current_func = func_name
                func_lines = []
            elif current_func and (line.startswith('    ') or line.strip() == ''):
                func_lines.append(line)
            elif current_func and not line.startswith('    '):
                function_defs[current_func] = func_lines
                current_func = None
                func_lines = []
        
        if current_func:
            function_defs[current_func] = func_lines
        
        # 查找add_computed调用
        add_computed_pattern = r'(\w+)\.add_computed\s*\(\s*["\']([^"\']+)["\']'
        for i, line in enumerate(lines):
            match = re.search(add_computed_pattern, line)
            if match:
                graph_var = match.group(1)
                param_name = match.group(2)
                
                # 查找函数引用
                func_ref_pattern = rf'add_computed\s*\(\s*["\'][^"\']+["\'],\s*(\w+)'
                func_match = re.search(func_ref_pattern, line)
                if func_match:
                    func_name = func_match.group(1)
                    dependencies = self._extract_dependencies_from_function(func_name, function_defs)
                    
                    self.parameters[param_name] = {
                        "type": "computed",
                        "value": f"computed via {func_name}()",
                        "line": i + 1
                    }
                    self.dependencies[param_name] = dependencies
    
    def _extract_dependencies_from_function(self, func_name: str, function_defs: Dict) -> List[str]:
        """从函数定义中提取依赖关系"""
        if func_name not in function_defs:
            return []
        
        dependencies = []
        func_code = '\n'.join(function_defs[func_name])
        
        # 使用正则表达式查找g["param_name"]模式
        param_pattern = r'g\s*\[\s*["\']([^"\']+)["\']'
        matches = re.findall(param_pattern, func_code)
        
        for match in matches:
            if match not in dependencies:
                dependencies.append(match)
        
        return dependencies


class GraphVisualizer:
    """图形可视化器"""
    
    def __init__(self, canvas_frame):
        self.canvas_frame = canvas_frame
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.graph = nx.DiGraph()
        self.pos = {}
        self.node_colors = {}
        self.line_mapping = {}  # {node_name: line_number}
        
        # 绑定点击事件
        self.canvas.mpl_connect('button_press_event', self._on_click)
        self.click_callback = None
    
    def set_click_callback(self, callback):
        """设置节点点击回调"""
        self.click_callback = callback
    
    def visualize_graph(self, graph_data: Dict):
        """可视化图形"""
        self.graph.clear()
        self.node_colors.clear()
        self.line_mapping.clear()
        
        if not graph_data["success"]:
            self._show_error(graph_data["error"])
            return
        
        parameters = graph_data["parameters"]
        dependencies = graph_data["dependencies"]
        
        # 添加节点
        for param_name, param_info in parameters.items():
            self.graph.add_node(param_name)
            self.line_mapping[param_name] = param_info["line"]
            
            # 设置节点颜色
            if param_info["type"] == "basic":
                self.node_colors[param_name] = 'lightblue'
            else:
                self.node_colors[param_name] = 'lightgreen'
        
        # 添加边
        for param_name, deps in dependencies.items():
            for dep in deps:
                if dep in parameters:
                    self.graph.add_edge(dep, param_name)
        
        # 绘制图形
        self._draw_graph(graph_data["graph_name"])
    
    def _draw_graph(self, graph_name: str):
        """绘制图形"""
        self.ax.clear()
        
        if len(self.graph.nodes) == 0:
            self.ax.text(0.5, 0.5, 'No parameters found', 
                        ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            return
        
        # 计算布局
        if len(self.graph.nodes) > 0:
            try:
                self.pos = nx.spring_layout(self.graph, k=3, iterations=50)
            except:
                # 如果spring_layout失败，使用简单的圆形布局
                self.pos = nx.circular_layout(self.graph)
        
        # 绘制边
        nx.draw_networkx_edges(self.graph, self.pos, ax=self.ax, 
                             edge_color='gray', arrows=True, arrowsize=20)
        
        # 绘制节点
        node_colors = [self.node_colors.get(node, 'lightgray') for node in self.graph.nodes]
        nx.draw_networkx_nodes(self.graph, self.pos, ax=self.ax,
                             node_color=node_colors, node_size=2000, alpha=0.8)
        
        # 绘制标签
        nx.draw_networkx_labels(self.graph, self.pos, ax=self.ax, 
                              font_size=10, font_weight='bold')
        
        # 设置标题
        self.ax.set_title(f'Graph: {graph_name}', fontsize=14, fontweight='bold')
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        
        # 添加图例
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightblue', 
                      markersize=10, label='Basic Parameters'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgreen', 
                      markersize=10, label='Computed Parameters')
        ]
        self.ax.legend(handles=legend_elements, loc='upper right')
        
        self.canvas.draw()
    
    def _show_error(self, error_msg: str):
        """显示错误信息"""
        self.ax.clear()
        self.ax.text(0.5, 0.5, f'Error: {error_msg}', 
                    ha='center', va='center', transform=self.ax.transAxes,
                    color='red', fontsize=12)
        self.canvas.draw()
    
    def _on_click(self, event):
        """处理点击事件"""
        if event.inaxes != self.ax or not self.pos:
            return
        
        # 查找最近的节点
        clicked_node = None
        min_distance = float('inf')
        
        for node, (x, y) in self.pos.items():
            distance = np.sqrt((event.xdata - x)**2 + (event.ydata - y)**2)
            if distance < 0.1 and distance < min_distance:  # 0.1是点击阈值
                min_distance = distance
                clicked_node = node
        
        if clicked_node and self.click_callback:
            line_no = self.line_mapping.get(clicked_node, 1)
            self.click_callback(clicked_node, line_no)


class GraphVisualizerApp:
    """主应用程序"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Graph Visualizer - 代码依赖图可视化工具")
        self.root.geometry("1400x800")
        
        self.parser = CodeParser()
        self.current_file = None
        
        self._create_widgets()
        self._load_sample_code()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建菜单
        self._create_menu()
        
        # 创建工具栏
        self._create_toolbar(main_frame)
        
        # 创建主要的分割视图
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 左侧：图形显示区域
        left_frame = ttk.LabelFrame(paned_window, text="依赖关系图", padding=5)
        paned_window.add(left_frame, weight=1)
        
        # 右侧：代码编辑区域
        right_frame = ttk.LabelFrame(paned_window, text="代码编辑器", padding=5)
        paned_window.add(right_frame, weight=1)
        
        # 创建图形可视化器
        self.visualizer = GraphVisualizer(left_frame)
        self.visualizer.set_click_callback(self._on_node_click)
        
        # 创建代码编辑器
        self._create_code_editor(right_frame)
        
        # 创建状态栏
        self._create_status_bar()
    
    def _create_menu(self):
        """创建菜单"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建", command=self._new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="打开", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="保存", command=self._save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="刷新图表", command=self._refresh_graph, accelerator="F5")
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self._show_about)
        
        # 绑定快捷键
        self.root.bind('<Control-n>', lambda e: self._new_file())
        self.root.bind('<Control-o>', lambda e: self._open_file())
        self.root.bind('<Control-s>', lambda e: self._save_file())
        self.root.bind('<F5>', lambda e: self._refresh_graph())
    
    def _create_toolbar(self, parent):
        """创建工具栏"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(toolbar, text="新建", command=self._new_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="打开", command=self._open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="保存", command=self._save_file).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        ttk.Button(toolbar, text="刷新图表", command=self._refresh_graph).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="示例代码", command=self._load_sample_code).pack(side=tk.LEFT, padx=2)
    
    def _create_code_editor(self, parent):
        """创建代码编辑器"""
        editor_frame = ttk.Frame(parent)
        editor_frame.pack(fill=tk.BOTH, expand=True)
        
        # 代码编辑器
        self.code_editor = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.NONE,
            font=('Consolas', 11),
            insertbackground='black',
            selectbackground='lightblue'
        )
        self.code_editor.pack(fill=tk.BOTH, expand=True)
        
        # 添加行号显示
        self._add_line_numbers()
        
        # 绑定内容变化事件
        self.code_editor.bind('<KeyRelease>', self._on_code_change)
        self.code_editor.bind('<Button-1>', self._on_code_change)
    
    def _add_line_numbers(self):
        """添加行号显示"""
        # 这里可以添加行号功能，为了简化demo暂时跳过
        pass
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _new_file(self):
        """新建文件"""
        if messagebox.askyesno("新建文件", "是否清空当前代码？"):
            self.code_editor.delete('1.0', tk.END)
            self.current_file = None
            self._update_status("新建文件")
    
    def _open_file(self):
        """打开文件"""
        file_path = filedialog.askopenfilename(
            title="打开Python文件",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.code_editor.delete('1.0', tk.END)
                self.code_editor.insert('1.0', content)
                self.current_file = file_path
                self._update_status(f"已打开: {file_path}")
                self._refresh_graph()
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件: {e}")
    
    def _save_file(self):
        """保存文件"""
        if not self.current_file:
            file_path = filedialog.asksaveasfilename(
                title="保存Python文件",
                defaultextension=".py",
                filetypes=[("Python files", "*.py"), ("All files", "*.*")]
            )
            if not file_path:
                return
            self.current_file = file_path
        
        try:
            content = self.code_editor.get('1.0', tk.END)
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(content)
            self._update_status(f"已保存: {self.current_file}")
        except Exception as e:
            messagebox.showerror("错误", f"无法保存文件: {e}")
    
    def _refresh_graph(self):
        """刷新图表"""
        code = self.code_editor.get('1.0', tk.END)
        graph_data = self.parser.parse_advanced_code(code)
        self.visualizer.visualize_graph(graph_data)
        
        if graph_data["success"]:
            param_count = len(graph_data["parameters"])
            self._update_status(f"图表已刷新 - 发现 {param_count} 个参数")
        else:
            self._update_status(f"解析错误: {graph_data['error']}")
    
    def _load_sample_code(self):
        """加载示例代码"""
        sample_code = '''# Graph Visualizer 示例代码
from core import Graph

# 创建图
g = Graph("电路分析")

# 基础参数
g["voltage"] = 12.0
g["current"] = 2.0
g["resistance"] = 6.0

# 计算函数
def power_calculation():
    return g["voltage"] * g["current"]

def energy_calculation():
    return g["power"] * g["time"]

def efficiency_calculation():
    return g["power"] / (g["voltage"] * g["current"])

# 添加时间参数
g["time"] = 1.0

# 添加计算参数
g.add_computed("power", power_calculation, "功率计算")
g.add_computed("energy", energy_calculation, "能量计算")
g.add_computed("efficiency", efficiency_calculation, "效率计算")

# 验证结果
print(f"功率: {g['power']} W")
print(f"能量: {g['energy']} Wh")
print(f"效率: {g['efficiency']}")
'''
        
        self.code_editor.delete('1.0', tk.END)
        self.code_editor.insert('1.0', sample_code)
        self._refresh_graph()
        self._update_status("已加载示例代码")
    
    def _on_code_change(self, event=None):
        """代码变化时的处理"""
        # 可以在这里添加实时解析功能
        pass
    
    def _on_node_click(self, node_name: str, line_no: int):
        """节点点击处理"""
        # 跳转到对应代码行
        self.code_editor.mark_set(tk.INSERT, f"{line_no}.0")
        self.code_editor.see(tk.INSERT)
        
        # 高亮显示该行
        self.code_editor.tag_remove("highlight", "1.0", tk.END)
        self.code_editor.tag_add("highlight", f"{line_no}.0", f"{line_no}.end")
        self.code_editor.tag_config("highlight", background="yellow")
        
        self._update_status(f"跳转到参数 '{node_name}' (第 {line_no} 行)")
    
    def _show_about(self):
        """显示关于信息"""
        messagebox.showinfo("关于", 
            "Graph Visualizer v1.0\n\n"
            "代码依赖图可视化工具\n"
            "可视化Python代码中的Graph参数依赖关系\n\n"
            "功能特点:\n"
            "• 实时解析代码中的Graph定义\n"
            "• 可视化参数依赖关系\n"
            "• 点击节点跳转到对应代码\n"
            "• 支持代码编辑和实时刷新")
    
    def _update_status(self, message: str):
        """更新状态栏"""
        self.status_bar.config(text=message)
        self.root.after(3000, lambda: self.status_bar.config(text="就绪"))


def main():
    """主函数"""
    root = tk.Tk()
    app = GraphVisualizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()