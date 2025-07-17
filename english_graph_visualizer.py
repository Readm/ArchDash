#!/usr/bin/env python3
"""
Graph Visualizer - Code Dependency Graph Visualization Tool (English Version)
"""

import re
import math
import matplotlib
# Force Tkinter backend for better WSL compatibility  
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.widgets import Button, TextBox
from typing import Dict, List, Set, Tuple, Optional

class EnglishCodeParser:
    """English Code Parser for Graph structures"""
    
    def __init__(self):
        self.graph_name = ""
        self.parameters = {}
        self.dependencies = {}
        
    def parse_code(self, code: str) -> Dict:
        """Parse code and extract Graph information"""
        self.graph_name = ""
        self.parameters = {}
        self.dependencies = {}
        
        try:
            # Parse Graph creation
            graph_match = re.search(r'Graph\s*\(\s*["\']([^"\']+)["\']', code)
            if graph_match:
                self.graph_name = graph_match.group(1)
            else:
                self.graph_name = "Unknown Graph"
            
            # Parse basic parameters
            param_pattern = r'g\s*\[\s*["\']([^"\']+)["\']\s*\]\s*=\s*([^#\n]+)'
            for match in re.finditer(param_pattern, code):
                param_name = match.group(1)
                param_value = match.group(2).strip()
                self.parameters[param_name] = {
                    "type": "basic",
                    "value": param_value
                }
            
            # Parse add_computed calls
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
        """Parse add_computed function calls"""
        # Find function definitions
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
        
        # Find add_computed calls
        add_computed_pattern = r'add_computed\s*\(\s*["\']([^"\']+)["\'],\s*(\w+)'
        for match in re.finditer(add_computed_pattern, code):
            param_name = match.group(1)
            func_name = match.group(2)
            
            # Extract dependencies from function
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


class EnglishGraphVisualizer:
    """English Graph Visualizer with clean UI"""
    
    def __init__(self):
        self.parser = EnglishCodeParser()
        self.fig = None
        self.ax = None
        self.text_box = None
        self.current_graph_data = None
        
    def create_gui(self):
        """Create GUI interface"""
        # Create figure with more space between subplots
        self.fig, (self.ax, self.text_ax) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Adjust spacing between panels for better separation
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.12, wspace=0.15)
        
        # Set window title instead of figure title
        self.fig.canvas.manager.set_window_title('Graph Visualizer - Code Dependency Visualization Tool')
        
        # Left side: Graph visualization area
        self.ax.set_title('Dependency Graph', fontsize=14, fontweight='bold', pad=20)
        
        # Add visual border to graph area
        for spine in self.ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(2)
            spine.set_edgecolor('darkblue')
        
        # Right side: Code editor area
        self.text_ax.set_xlim(0, 1)
        self.text_ax.set_ylim(0, 1)
        self.text_ax.set_title('Code Editor', fontsize=14, fontweight='bold', pad=20)
        self.text_ax.axis('off')
        
        # Add background color to distinguish code area
        self.text_ax.set_facecolor('#f8f9fa')
        
        # Create text box with improved positioning
        text_box_ax = plt.axes([0.525, 0.15, 0.42, 0.75])
        text_box_ax.set_facecolor('#ffffff')
        # Add border to text box
        for spine in text_box_ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(1.5)
            spine.set_edgecolor('gray')
        
        # Create text box with proper styling
        self.text_box = TextBox(text_box_ax, '', initial=self._get_sample_code())
        # Fix cursor size by setting text properties
        self.text_box.text_disp.set_fontsize(10)
        self.text_box.cursor.set_linewidth(1)
        
        # Create refresh button
        refresh_ax = plt.axes([0.81, 0.02, 0.1, 0.04])
        refresh_button = Button(refresh_ax, 'Refresh')
        refresh_button.on_clicked(self._refresh_graph)
        
        # Create sample button
        sample_ax = plt.axes([0.7, 0.02, 0.1, 0.04])
        sample_button = Button(sample_ax, 'Sample')
        sample_button.on_clicked(self._load_sample)
        
        # Create clear button
        clear_ax = plt.axes([0.59, 0.02, 0.1, 0.04])
        clear_button = Button(clear_ax, 'Clear')
        clear_button.on_clicked(self._clear_code)
        
        # Initialize graph
        self._refresh_graph(None)
        
        # Don't use tight_layout as it conflicts with manual positioning
        plt.show()
    
    def _get_sample_code(self):
        """Get sample code"""
        return '''from core import Graph

# Create graph
g = Graph("Circuit Analysis")

# Basic parameters
g["voltage"] = 12.0
g["current"] = 2.0
g["resistance"] = 6.0
g["time"] = 1.0

# Calculation functions
def power_calculation():
    return g["voltage"] * g["current"]

def energy_calculation():
    return g["power"] * g["time"]

def efficiency_calculation():
    return g["power"] / (g["voltage"] * g["current"])

# Add computed parameters
g.add_computed("power", power_calculation, "Power calculation")
g.add_computed("energy", energy_calculation, "Energy calculation")
g.add_computed("efficiency", efficiency_calculation, "Efficiency calculation")

print(f"Power: {g['power']} W")
print(f"Energy: {g['energy']} Wh")
print(f"Efficiency: {g['efficiency']}")'''
    
    def _load_sample(self, event):
        """Load sample code"""
        self.text_box.set_val(self._get_sample_code())
        self._refresh_graph(None)
    
    def _clear_code(self, event):
        """Clear code"""
        self.text_box.set_val("")
        self._refresh_graph(None)
    
    def _refresh_graph(self, event):
        """Refresh graph"""
        code = self.text_box.text
        self.current_graph_data = self.parser.parse_code(code)
        self._draw_graph()
    
    def _draw_graph(self):
        """Draw graph"""
        self.ax.clear()
        
        if not self.current_graph_data["success"]:
            self.ax.text(0.5, 0.5, f'Error: {self.current_graph_data["error"]}', 
                        ha='center', va='center', transform=self.ax.transAxes,
                        color='red', fontsize=12)
            self.ax.set_title('Dependency Graph: Parse Error', fontsize=14, fontweight='bold', pad=20)
            
            # Maintain visual separation even on error
            for spine in self.ax.spines.values():
                spine.set_visible(True)
                spine.set_linewidth(2)
                spine.set_edgecolor('darkblue')
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            
            plt.draw()
            return
        
        parameters = self.current_graph_data["parameters"]
        dependencies = self.current_graph_data["dependencies"]
        
        if not parameters:
            self.ax.text(0.5, 0.5, 'No parameters found\n\nTip: Enter Graph code in the editor on the right', 
                        ha='center', va='center', transform=self.ax.transAxes,
                        fontsize=12, color='gray')
            self.ax.set_title('Dependency Graph: No Parameters Found', fontsize=14, fontweight='bold', pad=20)
            
            # Maintain visual separation even when empty
            for spine in self.ax.spines.values():
                spine.set_visible(True)
                spine.set_linewidth(2)
                spine.set_edgecolor('darkblue')
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            
            plt.draw()
            return
        
        # Calculate node positions
        positions = self._calculate_layout(parameters, dependencies)
        
        # Draw edges (dependencies)
        self._draw_edges(positions, dependencies)
        
        # Draw nodes
        self._draw_nodes(positions, parameters)
        
        # Set title and maintain visual separation
        graph_name = self.current_graph_data["graph_name"]
        self.ax.set_title(f'Dependency Graph: {graph_name}', fontsize=14, fontweight='bold', pad=20)
        self.ax.set_aspect('equal')
        
        # Auto-adjust axis limits based on positions
        if positions:
            xs = [pos[0] for pos in positions.values()]
            ys = [pos[1] for pos in positions.values()]
            margin = 1.0
            self.ax.set_xlim(min(xs) - margin, max(xs) + margin)
            self.ax.set_ylim(min(ys) - margin, max(ys) + margin)
        
        # Keep border visible for separation
        for spine in self.ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(2)
            spine.set_edgecolor('darkblue')
        
        # Hide ticks but keep border
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        
        # Add legend
        self._add_legend()
        
        # Add statistics
        self._add_statistics(parameters)
        
        plt.draw()
    
    def _calculate_layout(self, parameters: Dict, dependencies: Dict) -> Dict:
        """Calculate node layout with auto-sizing"""
        positions = {}
        param_names = list(parameters.keys())
        n = len(param_names)
        
        if n == 0:
            return positions
        
        # Auto-adjust radius based on number of nodes
        base_radius = max(2.5, min(4.0, n * 0.4))
        
        # Use circular layout with proper spacing
        for i, param_name in enumerate(param_names):
            angle = 2 * math.pi * i / n
            x = math.cos(angle) * base_radius
            y = math.sin(angle) * base_radius
            positions[param_name] = (x, y)
        
        return positions
    
    def _draw_edges(self, positions: Dict, dependencies: Dict):
        """Draw edges"""
        for param_name, deps in dependencies.items():
            if param_name in positions:
                end_pos = positions[param_name]
                for dep in deps:
                    if dep in positions:
                        start_pos = positions[dep]
                        
                        # Draw arrow
                        self.ax.annotate('', xy=end_pos, xytext=start_pos,
                                       arrowprops=dict(arrowstyle='->', lw=1.5, color='gray'))
    
    def _draw_nodes(self, positions: Dict, parameters: Dict):
        """Draw nodes with auto-sizing"""
        n = len(parameters)
        # Auto-adjust node size based on number of nodes
        node_radius = max(0.25, min(0.4, 3.0 / max(n, 5)))
        font_size = max(8, min(12, 60 / max(n, 5)))
        
        for param_name, pos in positions.items():
            param_info = parameters[param_name]
            
            # Choose color
            if param_info["type"] == "basic":
                color = 'lightblue'
            else:
                color = 'lightgreen'
            
            # Draw node with auto-sizing
            circle = patches.Circle(pos, node_radius, facecolor=color, edgecolor='black', linewidth=2)
            self.ax.add_patch(circle)
            
            # Add label with auto-sizing
            display_name = param_name if len(param_name) <= 10 else param_name[:8] + ".."
            self.ax.text(pos[0], pos[1], display_name, ha='center', va='center', 
                        fontsize=font_size, fontweight='bold')
            
            # Add value label with auto-sizing
            value_text = str(param_info["value"])
            if len(value_text) > 12:
                value_text = value_text[:12] + "..."
            self.ax.text(pos[0], pos[1]-node_radius*1.8, value_text, ha='center', va='top', 
                        fontsize=max(6, font_size-2), style='italic', color='darkblue')
    
    def _add_legend(self):
        """Add legend"""
        legend_elements = [
            patches.Patch(color='lightblue', label='Basic Parameters'),
            patches.Patch(color='lightgreen', label='Computed Parameters')
        ]
        self.ax.legend(handles=legend_elements, loc='upper right')
    
    def _add_statistics(self, parameters: Dict):
        """Add statistics"""
        basic_count = sum(1 for p in parameters.values() if p["type"] == "basic")
        computed_count = sum(1 for p in parameters.values() if p["type"] == "computed")
        total_count = len(parameters)
        
        info_text = f'Total: {total_count}\nBasic: {basic_count}\nComputed: {computed_count}'
        self.ax.text(0.02, 0.98, info_text, transform=self.ax.transAxes, 
                    fontsize=10, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))


def main():
    """Main function"""
    print("Starting Graph Visualizer (English Version)...")
    print("Features:")
    print("- Left: Dependency graph visualization")
    print("- Right: Code editor")
    print("- Click 'Sample' to load example code")
    print("- Click 'Refresh' to update graph")
    print("- Click 'Clear' to clear code")
    print("\nLaunching GUI...")
    
    visualizer = EnglishGraphVisualizer()
    visualizer.create_gui()


if __name__ == "__main__":
    main()