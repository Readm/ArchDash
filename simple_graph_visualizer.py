#!/usr/bin/env python3
"""
简化版Graph Visualizer - 使用matplotlib进行可视化
"""

import ast
import re
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.widgets import Button, TextBox
from typing import Dict, List, Set, Tuple, Optional

class SimpleCodeParser:
    """简化的代码解析器"""
    
    def __init__(self):
        self.graph_name = ""
        self.parameters = {}
        self.dependencies = {}
        
    def parse_code(self, code: str) -> Dict:
        """解析代码，提取Graph信息"""
        self.graph_name = ""
        self.parameters = {}
        self.dependencies = {}
        
        try:
            # 解析Graph创建
            graph_match = re.search(r'Graph\s*\(\s*["\']([^"\']+)["\']', code)
            if graph_match:
                self.graph_name = graph_match.group(1)
            
            # 解析基础参数
            param_pattern = r'g\s*\[\s*["\']([^"\']+)["\']\s*\]\s*=\s*([^#\n]+)'
            for match in re.finditer(param_pattern, code):
                param_name = match.group(1)
                param_value = match.group(2).strip()
                self.parameters[param_name] = {
                    "type": "basic",
                    "value": param_value
                }
            
            # 解析add_computed调用
            self._parse_add_computed(code)
            
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
    
    def _parse_add_computed(self, code: str):
        """解析add_computed调用"""
        # 查找函数定义
        function_defs = {}
        lines = code.split('\n')
        
        current_func = None
        func_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('def '):
                if current_func:
                    function_defs[current_func] = '\n'.join(func_lines)
                func_name = stripped.split('(')[0].replace('def ', '').strip()
                current_func = func_name
                func_lines = []
            elif current_func and (line.startswith('    ') or line.strip() == ''):
                func_lines.append(line)
            elif current_func and not line.startswith('    '):
                function_defs[current_func] = '\n'.join(func_lines)
                current_func = None
                func_lines = []
        
        if current_func:
            function_defs[current_func] = '\n'.join(func_lines)
        
        # 查找add_computed调用
        add_computed_pattern = r'add_computed\s*\(\s*["\']([^"\']+)["\'],\s*(\w+)'
        for match in re.finditer(add_computed_pattern, code):
            param_name = match.group(1)
            func_name = match.group(2)
            
            # 从函数中提取依赖
            dependencies = []
            if func_name in function_defs:
                func_code = function_defs[func_name]
                dep_pattern = r'g\s*\[\s*["\']([^"\']+)["\']'
                for dep_match in re.finditer(dep_pattern, func_code):
                    dep_name = dep_match.group(1)
                    if dep_name not in dependencies:
                        dependencies.append(dep_name)
            
            self.parameters[param_name] = {
                "type": "computed",
                "value": f"computed via {func_name}()"
            }
            self.dependencies[param_name] = dependencies


class SimpleGraphVisualizer:
    """简化的图形可视化器"""
    
    def __init__(self):
        self.parser = SimpleCodeParser()
        self.fig = None
        self.ax = None
        self.text_box = None
        self.current_graph_data = None
        
    def create_gui(self):
        """创建GUI界面"""
        # 创建图形和子图
        self.fig, (self.ax, self.text_ax) = plt.subplots(1, 2, figsize=(16, 8))
        
        # 设置图形标题
        self.fig.suptitle('Graph Visualizer - 代码依赖图可视化工具', fontsize=16)
        
        # 右侧：代码编辑区域
        self.text_ax.set_xlim(0, 1)
        self.text_ax.set_ylim(0, 1)
        self.text_ax.set_title('代码编辑器')
        self.text_ax.axis('off')
        
        # 创建文本框
        text_box_ax = plt.axes([0.55, 0.1, 0.4, 0.8])
        self.text_box = TextBox(text_box_ax, '', initial=self._get_sample_code())
        
        # 创建刷新按钮
        refresh_ax = plt.axes([0.81, 0.02, 0.1, 0.04])
        refresh_button = Button(refresh_ax, 'Refresh')
        refresh_button.on_clicked(self._refresh_graph)
        
        # 创建示例按钮
        sample_ax = plt.axes([0.7, 0.02, 0.1, 0.04])
        sample_button = Button(sample_ax, 'Sample')
        sample_button.on_clicked(self._load_sample)
        
        # 初始化图形
        self._refresh_graph(None)
        
        plt.tight_layout()
        plt.show()
    
    def _get_sample_code(self):
        """获取示例代码"""
        return '''from core import Graph

# 创建图
g = Graph("电路分析")

# 基础参数
g["voltage"] = 12.0
g["current"] = 2.0
g["resistance"] = 6.0
g["time"] = 1.0

# 计算函数
def power_calculation():
    return g["voltage"] * g["current"]

def energy_calculation():
    return g["power"] * g["time"]

def efficiency_calculation():
    return g["power"] / (g["voltage"] * g["current"])

# 添加计算参数
g.add_computed("power", power_calculation, "功率计算")
g.add_computed("energy", energy_calculation, "能量计算")
g.add_computed("efficiency", efficiency_calculation, "效率计算")

print(f"功率: {g['power']} W")
print(f"能量: {g['energy']} Wh")
print(f"效率: {g['efficiency']}")'''
    
    def _load_sample(self, event):
        """加载示例代码"""
        self.text_box.set_val(self._get_sample_code())
        self._refresh_graph(None)
    
    def _refresh_graph(self, event):
        """刷新图形"""
        code = self.text_box.text
        self.current_graph_data = self.parser.parse_code(code)
        self._draw_graph()
    
    def _draw_graph(self):
        """绘制图形"""
        self.ax.clear()
        
        if not self.current_graph_data["success"]:
            self.ax.text(0.5, 0.5, f'Error: {self.current_graph_data["error"]}', 
                        ha='center', va='center', transform=self.ax.transAxes,
                        color='red', fontsize=12)
            self.ax.set_title('解析错误')
            plt.draw()
            return
        
        parameters = self.current_graph_data["parameters"]
        dependencies = self.current_graph_data["dependencies"]
        
        if not parameters:
            self.ax.text(0.5, 0.5, 'No parameters found', 
                        ha='center', va='center', transform=self.ax.transAxes)
            self.ax.set_title('没有找到参数')
            plt.draw()
            return
        
        # 创建网络图
        G = nx.DiGraph()
        
        # 添加节点
        for param_name in parameters:
            G.add_node(param_name)
        
        # 添加边
        for param_name, deps in dependencies.items():
            for dep in deps:
                if dep in parameters:
                    G.add_edge(dep, param_name)
        
        # 计算布局
        if len(G.nodes) > 0:
            pos = nx.spring_layout(G, k=3, iterations=50)
        else:
            pos = {}
        
        # 设置节点颜色
        node_colors = []
        for node in G.nodes:
            if parameters[node]["type"] == "basic":
                node_colors.append('lightblue')
            else:
                node_colors.append('lightgreen')
        
        # 绘制图形
        nx.draw_networkx_edges(G, pos, ax=self.ax, edge_color='gray', 
                             arrows=True, arrowsize=20, alpha=0.7)
        
        nx.draw_networkx_nodes(G, pos, ax=self.ax, node_color=node_colors, 
                             node_size=3000, alpha=0.8)
        
        # 绘制标签
        nx.draw_networkx_labels(G, pos, ax=self.ax, font_size=10, font_weight='bold')
        
        # 添加参数值标签
        for node, (x, y) in pos.items():
            value = parameters[node]["value"]
            self.ax.text(x, y-0.15, f'{value}', ha='center', va='top', 
                        fontsize=8, style='italic', color='darkblue')
        
        # 设置标题
        graph_name = self.current_graph_data["graph_name"]
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
        
        # 添加统计信息
        basic_count = sum(1 for p in parameters.values() if p["type"] == "basic")
        computed_count = sum(1 for p in parameters.values() if p["type"] == "computed")
        info_text = f'Basic: {basic_count}, Computed: {computed_count}'
        self.ax.text(0.02, 0.98, info_text, transform=self.ax.transAxes, 
                    fontsize=10, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.draw()


def main():
    """主函数"""
    print("启动Graph Visualizer...")
    visualizer = SimpleGraphVisualizer()
    visualizer.create_gui()


if __name__ == "__main__":
    main()