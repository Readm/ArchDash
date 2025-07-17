#!/usr/bin/env python3
"""
Offline Interactive Graph Visualizer - Plotly Offline Version
No web server needed - opens directly in browser like a local HTML file
"""

import re
import math
import plotly.graph_objects as go
import plotly.offline as pyo
from plotly.subplots import make_subplots
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
from typing import Dict, List, Set, Tuple, Optional
import tempfile
import os
import webbrowser
import threading
import http.server
import socketserver
from urllib.parse import urlparse
import socket

try:
    import tkinter.html as tkhtml  # Not available in standard tkinter
except ImportError:
    tkhtml = None

try:
    from tkinter import Frame
    import webview  # pywebview for embedded browser
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False

class OfflineCodeParser:
    """Code parser for offline visualization"""
    
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
        add_computed_pattern = r'add_computed\s*\(\s*["\']([^"\']+)["\']\s*,\s*(\w+)'
        for match in re.finditer(add_computed_pattern, code):
            param_name = match.group(1)
            func_name = match.group(2)
            
            # Extract dependencies from function
            dependencies = []
            if func_name in function_defs:
                func_code = function_defs[func_name]
                dep_pattern = r'g\s*\[\s*["\']([^"\']+)["\']\s*\]'
                for dep_match in re.finditer(dep_pattern, func_code):
                    dep_name = dep_match.group(1)
                    if dep_name not in dependencies:
                        dependencies.append(dep_name)
            
            self.parameters[param_name] = {
                "type": "computed",
                "value": f"computed via {func_name}()"
            }
            self.dependencies[param_name] = dependencies


class OfflineGraphVisualizer:
    """Offline graph visualizer with Tkinter GUI + Plotly offline rendering"""
    
    def __init__(self):
        self.parser = OfflineCodeParser()
        self.root = tk.Tk()
        self.current_graph_data = None
        self.setup_gui()
        
    def get_sample_code(self):
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

    def setup_gui(self):
        """Setup Tkinter GUI"""
        self.root.title("Offline Interactive Graph Visualizer")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Offline Interactive Graph Visualizer", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Create paned window for split layout
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left frame: Code editor
        left_frame = ttk.LabelFrame(paned, text="Code Editor", padding=10)
        paned.add(left_frame, weight=1)
        
        # Code text area
        self.code_text = scrolledtext.ScrolledText(
            left_frame,
            wrap=tk.NONE,
            font=('Consolas', 11),
            height=25,
            width=60
        )
        self.code_text.pack(fill=tk.BOTH, expand=True)
        self.code_text.insert(tk.END, self.get_sample_code())
        
        # Button frame
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Generate Graph", 
                  command=self.generate_graph).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Load Sample", 
                  command=self.load_sample).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear Code", 
                  command=self.clear_code).pack(side=tk.LEFT)
        
        # Right frame: Info and controls
        right_frame = ttk.LabelFrame(paned, text="Graph Information", padding=10)
        paned.add(right_frame, weight=1)
        
        # Info text area
        self.info_text = scrolledtext.ScrolledText(
            right_frame,
            wrap=tk.WORD,
            font=('Arial', 10),
            height=15,
            state=tk.DISABLED
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # Graph options frame
        options_frame = ttk.LabelFrame(right_frame, text="Graph Options", padding=5)
        options_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Layout options
        ttk.Label(options_frame, text="Layout:").grid(row=0, column=0, sticky=tk.W)
        self.layout_var = tk.StringVar(value="circular")
        layout_combo = ttk.Combobox(options_frame, textvariable=self.layout_var,
                                   values=["circular", "spring", "hierarchical"])
        layout_combo.grid(row=0, column=1, padx=(5, 0), sticky=tk.W)
        
        # Auto-open option
        self.auto_open_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Auto-open in browser",
                       variable=self.auto_open_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Enter code and click 'Generate Graph'")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, font=('Arial', 9))
        status_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Initial info
        self.update_info("Welcome to Offline Interactive Graph Visualizer!\n\n"
                        "Features:\n"
                        "• No web server needed\n"
                        "• Interactive Plotly graphs\n"
                        "• Opens directly in browser\n"
                        "• Drag nodes, zoom, pan\n"
                        "• Hover for details\n\n"
                        "Click 'Generate Graph' to create visualization!")

    def update_info(self, text):
        """Update info text area"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, text)
        self.info_text.config(state=tk.DISABLED)

    def calculate_layout(self, parameters: Dict, dependencies: Dict, layout_type: str = "circular") -> Dict:
        """Calculate node positions based on layout type"""
        positions = {}
        param_names = list(parameters.keys())
        n = len(param_names)
        
        if n == 0:
            return positions
        
        if layout_type == "circular":
            # Circular layout
            base_radius = max(3, min(6, n * 0.4))
            for i, param_name in enumerate(param_names):
                angle = 2 * math.pi * i / n
                x = math.cos(angle) * base_radius
                y = math.sin(angle) * base_radius
                positions[param_name] = (x, y)
                
        elif layout_type == "spring":
            # Simple spring-like layout with some randomization
            base_radius = max(2, min(5, n * 0.3))
            for i, param_name in enumerate(param_names):
                angle = 2 * math.pi * i / n + (i % 3 - 1) * 0.2
                radius = base_radius + (i % 4 - 2) * 0.5
                x = math.cos(angle) * radius
                y = math.sin(angle) * radius
                positions[param_name] = (x, y)
                
        elif layout_type == "hierarchical":
            # Simple hierarchical layout
            levels = {}
            for param_name in param_names:
                if param_name in dependencies:
                    levels[param_name] = max([levels.get(dep, 0) for dep in dependencies[param_name]], default=0) + 1
                else:
                    levels[param_name] = 0
            
            # Group by levels
            level_groups = {}
            for param_name, level in levels.items():
                if level not in level_groups:
                    level_groups[level] = []
                level_groups[level].append(param_name)
            
            # Position nodes
            for level, nodes in level_groups.items():
                y = -level * 2  # Vertical spacing
                for i, param_name in enumerate(nodes):
                    x = (i - len(nodes)/2) * 2  # Horizontal spacing
                    positions[param_name] = (x, y)
        
        return positions

    def create_interactive_figure(self, graph_data: Dict):
        """Create interactive Plotly figure"""
        if not graph_data or not graph_data.get("success", False):
            # Error figure
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error: {graph_data.get('error', 'Unknown error') if graph_data else 'No data'}",
                x=0.5, y=0.5,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=16, color="red")
            )
            fig.update_layout(title="Parse Error")
            return fig
        
        parameters = graph_data["parameters"]
        dependencies = graph_data["dependencies"]
        
        if not parameters:
            # Empty figure
            fig = go.Figure()
            fig.add_annotation(
                text="No parameters found<br><br>Enter Graph code and click 'Generate Graph'",
                x=0.5, y=0.5,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=14, color="gray")
            )
            fig.update_layout(title="No Parameters Found")
            return fig
        
        # Calculate positions
        layout_type = self.layout_var.get()
        positions = self.calculate_layout(parameters, dependencies, layout_type)
        
        # Create figure
        fig = go.Figure()
        
        # Add edges
        edge_x = []
        edge_y = []
        for param_name, deps in dependencies.items():
            if param_name in positions:
                end_pos = positions[param_name]
                for dep in deps:
                    if dep in positions:
                        start_pos = positions[dep]
                        # Add arrow line
                        fig.add_annotation(
                            x=end_pos[0], y=end_pos[1],
                            ax=start_pos[0], ay=start_pos[1],
                            xref='x', yref='y',
                            axref='x', ayref='y',
                            arrowhead=2, arrowsize=1, arrowwidth=2,
                            arrowcolor='#7f8c8d'
                        )
        
        # Prepare node data
        node_x = []
        node_y = []
        node_text = []
        node_hover = []
        node_colors = []
        node_sizes = []
        
        for param_name, pos in positions.items():
            param_info = parameters[param_name]
            
            node_x.append(pos[0])
            node_y.append(pos[1])
            node_text.append(param_name)
            
            # Create hover info
            value_text = str(param_info["value"])
            if len(value_text) > 40:
                value_text = value_text[:40] + "..."
            
            hover_text = f"<b>{param_name}</b><br>"
            hover_text += f"Type: {param_info['type']}<br>"
            hover_text += f"Value: {value_text}"
            
            if param_name in dependencies:
                deps = dependencies[param_name]
                if deps:
                    hover_text += f"<br>Dependencies: {', '.join(deps)}"
            
            node_hover.append(hover_text)
            
            # Color and size
            if param_info["type"] == "basic":
                node_colors.append('#3498db')
            else:
                node_colors.append('#2ecc71')
                
            dep_count = len(dependencies.get(param_name, []))
            size = max(25, min(50, 25 + dep_count * 8))
            node_sizes.append(size)
        
        # Add nodes
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='white'),
                opacity=0.9
            ),
            text=node_text,
            textposition="middle center",
            textfont=dict(size=12, color='white', family='Arial Black'),
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=node_hover,
            name='Parameters'
        ))
        
        # Update layout
        fig.update_layout(
            title=f"Interactive Graph: {graph_data['graph_name']} ({layout_type.title()} Layout)",
            title_font=dict(size=18, color='#2c3e50'),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            paper_bgcolor='#f8f9fa',
            showlegend=False,
            margin=dict(l=50, r=50, t=80, b=50),
            dragmode='pan',
            annotations=[
                dict(
                    text=f"📊 {len(parameters)} total parameters<br>"
                         f"🔵 {sum(1 for p in parameters.values() if p['type'] == 'basic')} basic<br>"
                         f"🟢 {sum(1 for p in parameters.values() if p['type'] == 'computed')} computed<br><br>"
                         f"💡 Drag to pan • Scroll to zoom • Hover for details",
                    x=0.02, y=0.98,
                    xref="paper", yref="paper",
                    showarrow=False,
                    font=dict(size=10),
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="#bdc3c7",
                    borderwidth=1
                )
            ]
        )
        
        return fig

    def generate_graph(self):
        """Generate and display interactive graph"""
        try:
            self.status_var.set("Parsing code...")
            self.root.update()
            
            # Get code
            code = self.code_text.get(1.0, tk.END).strip()
            
            # Parse code
            graph_data = self.parser.parse_code(code)
            self.current_graph_data = graph_data
            
            if graph_data["success"]:
                # Create figure
                fig = self.create_interactive_figure(graph_data)
                
                # Generate HTML file
                temp_dir = tempfile.gettempdir()
                html_file = os.path.join(temp_dir, "graph_visualizer.html")
                
                # Configure Plotly offline
                config = {
                    'displayModeBar': True,
                    'displaylogo': False,
                    'toImageButtonOptions': {
                        'format': 'png',
                        'filename': 'dependency_graph',
                        'height': 800,
                        'width': 1200,
                        'scale': 1
                    }
                }
                
                pyo.plot(fig, filename=html_file, auto_open=self.auto_open_var.get(), config=config)
                
                # Update info
                params = graph_data["parameters"]
                basic_count = sum(1 for p in params.values() if p["type"] == "basic")
                computed_count = sum(1 for p in params.values() if p["type"] == "computed")
                
                info_text = f"✅ Graph Generated Successfully!\n\n"
                info_text += f"Graph Name: {graph_data['graph_name']}\n"
                info_text += f"Total Parameters: {len(params)}\n"
                info_text += f"Basic Parameters: {basic_count}\n"
                info_text += f"Computed Parameters: {computed_count}\n"
                info_text += f"Layout: {self.layout_var.get().title()}\n\n"
                info_text += f"File saved to: {html_file}\n\n"
                info_text += "Interactive Features:\n"
                info_text += "• Drag to pan the view\n"
                info_text += "• Scroll to zoom in/out\n"
                info_text += "• Hover over nodes for details\n"
                info_text += "• Use toolbar for additional options\n"
                info_text += "• Download as PNG using camera icon\n\n"
                
                if dependencies := graph_data["dependencies"]:
                    info_text += "Dependencies:\n"
                    for param, deps in dependencies.items():
                        if deps:
                            info_text += f"• {param} ← {', '.join(deps)}\n"
                
                self.update_info(info_text)
                self.status_var.set(f"Graph generated successfully! Saved to {os.path.basename(html_file)}")
                
            else:
                error_msg = f"❌ Parse Error!\n\n{graph_data['error']}\n\nPlease check your code syntax."
                self.update_info(error_msg)
                self.status_var.set("Parse error - check code syntax")
                
        except Exception as e:
            error_msg = f"❌ Error generating graph!\n\n{str(e)}"
            self.update_info(error_msg)
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to generate graph:\n{str(e)}")

    def load_sample(self):
        """Load sample code"""
        self.code_text.delete(1.0, tk.END)
        self.code_text.insert(1.0, self.get_sample_code())
        self.status_var.set("Sample code loaded")

    def clear_code(self):
        """Clear code editor"""
        self.code_text.delete(1.0, tk.END)
        self.update_info("Code cleared. Enter your Graph code and click 'Generate Graph'.")
        self.status_var.set("Code cleared")

    def run(self):
        """Run the application"""
        print("🚀 Starting Offline Interactive Graph Visualizer...")
        print("📊 Features:")
        print("   • No web server required")
        print("   • Interactive Plotly graphs") 
        print("   • Opens directly in browser")
        print("   • Drag, zoom, hover interactions")
        print("   • Multiple layout options")
        print("\n💡 Use the GUI to enter code and generate interactive graphs!")
        
        self.root.mainloop()


def main():
    """Main function"""
    app = OfflineGraphVisualizer()
    app.run()


if __name__ == "__main__":
    main()