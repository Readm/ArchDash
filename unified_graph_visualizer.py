#!/usr/bin/env python3
"""
Unified Graph Visualizer - Support both online and offline modes
Usage: 
  python unified_graph_visualizer.py --mode online   # Web-based Dash app
  python unified_graph_visualizer.py --mode offline  # Tkinter + embedded browser
  python unified_graph_visualizer.py --mode window   # Tkinter + matplotlib (fallback)
"""

import re
import math
import argparse
import sys
from typing import Dict, List, Set, Tuple, Optional

# Common code parser
class UnifiedCodeParser:
    """Unified code parser for all visualization modes"""
    
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


def get_sample_code():
    """Get sample code for demonstration"""
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


# Mode 1: Online Dash Application
def run_online_mode():
    """Run online Dash web application"""
    try:
        import dash
        from dash import dcc, html, Input, Output, State, callback_context
        import dash_bootstrap_components as dbc
        import plotly.graph_objects as go
        import webbrowser
        from threading import Timer
        
        print("🌐 Starting Online Mode (Dash Web Application)...")
        
        # Import the online visualizer
        from interactive_graph_visualizer import InteractiveGraphVisualizer
        
        visualizer = InteractiveGraphVisualizer()
        visualizer.run_server(debug=False)
        
    except ImportError as e:
        print(f"❌ Online mode requires: dash, plotly, dash-bootstrap-components")
        print(f"   Install with: pip install dash plotly dash-bootstrap-components")
        print(f"   Error: {e}")
        sys.exit(1)


# Mode 2: Offline with embedded browser
def run_offline_mode():
    """Run offline mode with embedded browser in Tkinter"""
    try:
        import tkinter as tk
        from tkinter import scrolledtext, messagebox, ttk
        import plotly.graph_objects as go
        import plotly.offline as pyo
        import tempfile
        import os
        import threading
        import http.server
        import socketserver
        from urllib.parse import quote
        
        print("🖥️  Starting Offline Mode (Embedded Browser)...")
        
        class EmbeddedBrowserVisualizer:
            def __init__(self):
                self.parser = UnifiedCodeParser()
                self.root = tk.Tk()
                self.current_graph_data = None
                self.server_thread = None
                self.server_port = None
                self.setup_gui()
                
            def setup_gui(self):
                """Setup Tkinter GUI with embedded browser"""
                self.root.title("Graph Visualizer - Offline Mode")
                self.root.geometry("1400x900")
                self.root.configure(bg='#f0f0f0')
                
                # Main container
                main_frame = ttk.Frame(self.root)
                main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                # Title
                title_label = ttk.Label(main_frame, text="Graph Visualizer - Offline Mode", 
                                       font=('Arial', 16, 'bold'))
                title_label.pack(pady=(0, 10))
                
                # Create paned window
                paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
                paned.pack(fill=tk.BOTH, expand=True)
                
                # Left panel: Code editor
                left_frame = ttk.LabelFrame(paned, text="Code Editor", padding=10)
                paned.add(left_frame, weight=1)
                
                # Code editor
                self.code_text = scrolledtext.ScrolledText(
                    left_frame,
                    wrap=tk.NONE,
                    font=('Consolas', 11),
                    height=30,
                    width=50
                )
                self.code_text.pack(fill=tk.BOTH, expand=True)
                self.code_text.insert(tk.END, get_sample_code())
                
                # Button frame
                button_frame = ttk.Frame(left_frame)
                button_frame.pack(fill=tk.X, pady=(10, 0))
                
                ttk.Button(button_frame, text="Generate Graph", 
                          command=self.generate_graph).pack(side=tk.LEFT, padx=(0, 5))
                ttk.Button(button_frame, text="Load Sample", 
                          command=self.load_sample).pack(side=tk.LEFT, padx=(0, 5))
                ttk.Button(button_frame, text="Clear Code", 
                          command=self.clear_code).pack(side=tk.LEFT, padx=(0, 5))
                ttk.Button(button_frame, text="Open in Browser", 
                          command=self.open_in_browser).pack(side=tk.LEFT)
                
                # Right panel: Graph display
                right_frame = ttk.LabelFrame(paned, text="Interactive Graph", padding=10)
                paned.add(right_frame, weight=2)
                
                # Try to use embedded browser
                self.setup_graph_display(right_frame)
                
                # Status bar
                self.status_var = tk.StringVar(value="Ready - Enter code and click 'Generate Graph'")
                status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                                      relief=tk.SUNKEN, font=('Arial', 9))
                status_bar.pack(fill=tk.X, pady=(5, 0))
                
            def setup_graph_display(self, parent):
                """Setup graph display area"""
                self.graph_frame = ttk.Frame(parent)
                self.graph_frame.pack(fill=tk.BOTH, expand=True)
                
                # Try different approaches for embedded browser
                try:
                    # Method 1: Try tkinter html (usually not available)
                    from tkinter.html import HtmlFrame
                    self.html_frame = HtmlFrame(self.graph_frame)
                    self.html_frame.pack(fill=tk.BOTH, expand=True)
                    self.display_method = "tkinter_html"
                    print("✅ Using tkinter.html for embedded display")
                except ImportError:
                    try:
                        # Method 2: Try tkwebview2 (Windows only)
                        import tkwebview2
                        self.webview = tkwebview2.WebView2(self.graph_frame)
                        self.webview.pack(fill=tk.BOTH, expand=True)
                        self.display_method = "webview2"
                        print("✅ Using WebView2 for embedded display")
                    except ImportError:
                        # Method 3: Fallback to text display with browser button
                        self.setup_fallback_display()
                        
            def setup_fallback_display(self):
                """Setup fallback display when no embedded browser is available"""
                self.display_method = "fallback"
                
                # Info text
                info_frame = ttk.Frame(self.graph_frame)
                info_frame.pack(fill=tk.BOTH, expand=True)
                
                ttk.Label(info_frame, text="Graph Preview", 
                         font=('Arial', 14, 'bold')).pack(pady=(0, 10))
                
                self.info_text = scrolledtext.ScrolledText(
                    info_frame,
                    wrap=tk.WORD,
                    font=('Arial', 10),
                    height=20,
                    state=tk.DISABLED
                )
                self.info_text.pack(fill=tk.BOTH, expand=True)
                
                # Browser button
                browser_frame = ttk.Frame(info_frame)
                browser_frame.pack(fill=tk.X, pady=(10, 0))
                
                ttk.Label(browser_frame, text="💡 Interactive graph will open in your default browser").pack(side=tk.LEFT)
                
                self.update_info("Welcome to Graph Visualizer!\n\n"
                               "Features in Offline Mode:\n"
                               "• No internet connection required\n"
                               "• Interactive graphs open in browser\n" 
                               "• All Plotly features available\n"
                               "• Drag, zoom, hover interactions\n\n"
                               "Enter your Graph code and click 'Generate Graph'!")
                
                print("ℹ️  Using fallback display - graphs will open in external browser")
                
            def update_info(self, text):
                """Update info display"""
                if hasattr(self, 'info_text'):
                    self.info_text.config(state=tk.NORMAL)
                    self.info_text.delete(1.0, tk.END)
                    self.info_text.insert(tk.END, text)
                    self.info_text.config(state=tk.DISABLED)
                    
            def start_local_server(self, html_content):
                """Start a local HTTP server to serve the HTML content"""
                if self.server_thread and self.server_thread.is_alive():
                    return self.server_port
                    
                # Find an available port
                with socketserver.TCPServer(("", 0), None) as s:
                    self.server_port = s.server_address[1]
                
                # Create a custom handler that serves our HTML
                class CustomHandler(http.server.SimpleHTTPRequestHandler):
                    def __init__(self, *args, html_content=None, **kwargs):
                        self.html_content = html_content
                        super().__init__(*args, **kwargs)
                        
                    def do_GET(self):
                        if self.path == '/':
                            self.send_response(200)
                            self.send_header('Content-type', 'text/html')
                            self.end_headers()
                            self.wfile.write(self.html_content.encode())
                        else:
                            super().do_GET()
                
                # Start server in a separate thread
                def run_server():
                    with socketserver.TCPServer(("", self.server_port), 
                                               lambda *args, **kwargs: CustomHandler(*args, html_content=html_content, **kwargs)) as httpd:
                        httpd.serve_forever()
                
                self.server_thread = threading.Thread(target=run_server, daemon=True)
                self.server_thread.start()
                
                return self.server_port
                
            def calculate_layout(self, parameters: Dict, dependencies: Dict) -> Dict:
                """Calculate node positions"""
                positions = {}
                param_names = list(parameters.keys())
                n = len(param_names)
                
                if n == 0:
                    return positions
                
                # Circular layout with some variation
                base_radius = max(3, min(6, n * 0.4))
                for i, param_name in enumerate(param_names):
                    angle = 2 * math.pi * i / n
                    radius_variation = base_radius + (i % 3 - 1) * 0.3
                    x = math.cos(angle) * radius_variation
                    y = math.sin(angle) * radius_variation
                    positions[param_name] = (x, y)
                
                return positions
                
            def create_plotly_figure(self, graph_data: Dict):
                """Create Plotly figure"""
                if not graph_data or not graph_data.get("success", False):
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
                positions = self.calculate_layout(parameters, dependencies)
                
                # Create figure
                fig = go.Figure()
                
                # Add edges with arrows
                for param_name, deps in dependencies.items():
                    if param_name in positions:
                        end_pos = positions[param_name]
                        for dep in deps:
                            if dep in positions:
                                start_pos = positions[dep]
                                fig.add_annotation(
                                    x=end_pos[0], y=end_pos[1],
                                    ax=start_pos[0], ay=start_pos[1],
                                    xref='x', yref='y',
                                    axref='x', ayref='y',
                                    arrowhead=2, arrowsize=1.5, arrowwidth=2,
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
                    title=f"Interactive Graph: {graph_data['graph_name']}",
                    title_font=dict(size=18, color='#2c3e50'),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    plot_bgcolor='white',
                    paper_bgcolor='#f8f9fa',
                    showlegend=False,
                    margin=dict(l=50, r=50, t=80, b=50),
                    dragmode='pan'
                )
                
                return fig
                
            def generate_graph(self):
                """Generate and display graph"""
                try:
                    self.status_var.set("Parsing code...")
                    self.root.update()
                    
                    # Get and parse code
                    code = self.code_text.get(1.0, tk.END).strip()
                    graph_data = self.parser.parse_code(code)
                    self.current_graph_data = graph_data
                    
                    if graph_data["success"]:
                        # Create figure
                        fig = self.create_plotly_figure(graph_data)
                        
                        # Generate HTML
                        config = {
                            'displayModeBar': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
                            'toImageButtonOptions': {
                                'format': 'png',
                                'filename': 'dependency_graph',
                                'height': 800,
                                'width': 1200,
                                'scale': 1
                            }
                        }
                        
                        html_content = pyo.plot(fig, output_type='div', include_plotlyjs=True, config=config)
                        full_html = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <title>Graph Visualizer</title>
                            <style>
                                body {{
                                    margin: 0;
                                    padding: 10px;
                                    font-family: Arial, sans-serif;
                                    background-color: #f8f9fa;
                                }}
                                .header {{
                                    text-align: center;
                                    color: #2c3e50;
                                    margin-bottom: 10px;
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="header">
                                <h2>Graph Visualizer - Offline Mode</h2>
                                <p>💡 Drag to pan • Scroll to zoom • Hover for details</p>
                            </div>
                            {html_content}
                        </body>
                        </html>
                        """
                        
                        # Display based on available method
                        if self.display_method == "tkinter_html":
                            self.html_frame.load_string(full_html)
                        elif self.display_method == "webview2":
                            self.webview.navigate_to_string(full_html)
                        elif self.display_method == "server":
                            # Start local server and display in embedded browser
                            port = self.start_local_server(full_html)
                            url = f"http://localhost:{port}/"
                            # Load in embedded browser
                        else:
                            # Fallback: save to temp file and provide info
                            temp_dir = tempfile.gettempdir()
                            html_file = os.path.join(temp_dir, "graph_visualizer.html")
                            with open(html_file, 'w', encoding='utf-8') as f:
                                f.write(full_html)
                            
                            # Update info display
                            params = graph_data["parameters"]
                            basic_count = sum(1 for p in params.values() if p["type"] == "basic")
                            computed_count = sum(1 for p in params.values() if p["type"] == "computed")
                            
                            info_text = f"✅ Graph Generated Successfully!\n\n"
                            info_text += f"Graph Name: {graph_data['graph_name']}\n"
                            info_text += f"Total Parameters: {len(params)}\n"
                            info_text += f"Basic Parameters: {basic_count}\n"
                            info_text += f"Computed Parameters: {computed_count}\n\n"
                            info_text += f"📁 File: {html_file}\n\n"
                            info_text += "🎮 Interactive Features:\n"
                            info_text += "• Drag to pan the view\n"
                            info_text += "• Scroll to zoom in/out\n"
                            info_text += "• Hover over nodes for details\n"
                            info_text += "• Click toolbar buttons for options\n"
                            info_text += "• Download as PNG using camera icon\n\n"
                            
                            if dependencies := graph_data["dependencies"]:
                                info_text += "🔗 Dependencies:\n"
                                for param, deps in dependencies.items():
                                    if deps:
                                        info_text += f"• {param} ← {', '.join(deps)}\n"
                            
                            self.update_info(info_text)
                            
                            # Also open in browser
                            import webbrowser
                            webbrowser.open(f"file://{html_file}")
                        
                        self.status_var.set("Graph generated successfully!")
                        
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
                self.code_text.insert(1.0, get_sample_code())
                self.status_var.set("Sample code loaded")
                
            def clear_code(self):
                """Clear code editor"""
                self.code_text.delete(1.0, tk.END)
                self.update_info("Code cleared. Enter your Graph code and click 'Generate Graph'.")
                self.status_var.set("Code cleared")
                
            def open_in_browser(self):
                """Force open current graph in external browser"""
                if self.current_graph_data and self.current_graph_data["success"]:
                    self.generate_graph()  # This will open in browser
                else:
                    messagebox.showinfo("Info", "Please generate a graph first!")
                    
            def run(self):
                """Run the application"""
                self.root.mainloop()
        
        # Create and run the visualizer
        app = EmbeddedBrowserVisualizer()
        app.run()
        
    except ImportError as e:
        print(f"❌ Offline mode requires: tkinter, plotly")
        print(f"   Install with: pip install plotly")
        print(f"   Error: {e}")
        sys.exit(1)


# Mode 3: Window mode with matplotlib
def run_window_mode():
    """Run window mode with matplotlib (fallback)"""
    try:
        print("🖼️  Starting Window Mode (Matplotlib)...")
        
        # Import the matplotlib-based visualizer
        from english_graph_visualizer import EnglishGraphVisualizer
        
        print("Note: This mode uses matplotlib and has limited interactivity.")
        print("For full interactive features, use --mode online or --mode offline")
        
        visualizer = EnglishGraphVisualizer()
        visualizer.create_gui()
        
    except ImportError as e:
        print(f"❌ Window mode requires: matplotlib, tkinter")
        print(f"   Install with: pip install matplotlib")
        print(f"   Error: {e}")
        sys.exit(1)


def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Unified Graph Visualizer - Interactive dependency graph visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python unified_graph_visualizer.py --mode online   # Web-based application
  python unified_graph_visualizer.py --mode offline  # Desktop app with browser
  python unified_graph_visualizer.py --mode window   # Desktop app with matplotlib

Modes:
  online  : Full web application with real-time updates (requires Dash)
  offline : Desktop application with embedded/external browser (requires Plotly)
  window  : Simple desktop application with matplotlib (basic interactivity)
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['online', 'offline', 'window'],
        default='offline',
        help='Visualization mode (default: offline)'
    )
    
    args = parser.parse_args()
    
    print("🚀 Graph Visualizer - Unified Mode Selector")
    print("=" * 50)
    print(f"Selected mode: {args.mode}")
    print()
    
    if args.mode == 'online':
        run_online_mode()
    elif args.mode == 'offline':
        run_offline_mode()
    elif args.mode == 'window':
        run_window_mode()


if __name__ == "__main__":
    main()