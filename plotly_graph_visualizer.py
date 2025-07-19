#!/usr/bin/env python3
"""
Plotly Graph Visualizer - Online and Offline Modes
Usage: 
  python plotly_graph_visualizer.py --mode online   # Dash web application
  python plotly_graph_visualizer.py --mode offline  # Generate HTML file
"""

import re
import math
import argparse
import sys
import tempfile
import os
import webbrowser
from typing import Dict, List, Set, Tuple, Optional

# Common code parser
class PlotlyCodeParser:
    """Code parser for Plotly visualization"""
    
    def __init__(self):
        self.graph_name = ""
        self.parameters = {}
        self.dependencies = {}
        
    def parse_code(self, code: str) -> Dict:
        """Parse code and extract Graph information with actual execution"""
        self.graph_name = ""
        self.parameters = {}
        self.dependencies = {}
        
        try:
            # Try to execute the code and get real values
            return self._execute_and_parse(code)
        except Exception as e:
            # Fall back to static analysis if execution fails
            return self._static_parse(code, str(e))
    
    def _execute_and_parse(self, code: str) -> Dict:
        """Execute code and extract real values from Graph instance"""
        # Create a safe execution environment
        import sys
        import os
        
        # Add the current directory to path so core module can be imported
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Create execution namespace
        exec_globals = {
            '__builtins__': __builtins__,
            'Graph': None,  # Will be imported
        }
        
        # Import the Graph class
        try:
            from core.graph import Graph
            exec_globals['Graph'] = Graph
        except ImportError:
            # If can't import, fall back to static analysis
            return self._static_parse(code, "Cannot import Graph class")
        
        # Execute the code in a single namespace so functions can access variables
        exec_combined = exec_globals.copy()
        exec(code, exec_combined, exec_combined)
        
        # Find the Graph instance
        graph_instance = None
        for var_name, var_value in exec_combined.items():
            if isinstance(var_value, Graph):
                graph_instance = var_value
                break
        
        if not graph_instance:
            return self._static_parse(code, "No Graph instance found")
        
        # Extract real values from the Graph instance
        self.graph_name = graph_instance.name
        lines = code.split('\n')
        
        # Get all parameters (basic and computed)
        for param_name in graph_instance.keys():
            try:
                actual_value = graph_instance[param_name]
                
                # Determine if it's basic or computed
                if param_name in graph_instance._computed_parameters:
                    param_type = "computed"
                    # Get dependencies
                    computed_info = graph_instance.get_computed_info(param_name)
                    if computed_info:
                        self.dependencies[param_name] = computed_info.get('dependencies', [])
                else:
                    param_type = "basic"
                
                # Find line number in code
                line_num = self._find_parameter_line(code, param_name, param_type)
                
                self.parameters[param_name] = {
                    "type": param_type,
                    "value": actual_value,
                    "line_number": line_num,
                    "code_position": 0
                }
                
            except Exception as e:
                # If can't get value, use placeholder
                self.parameters[param_name] = {
                    "type": "computed",
                    "value": f"Error: {str(e)}",
                    "line_number": 1,
                    "code_position": 0
                }
        
        return {
            "graph_name": self.graph_name,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
            "success": True,
            "error": None
        }
    
    def _find_parameter_line(self, code: str, param_name: str, param_type: str) -> int:
        """Find the line number where a parameter is defined"""
        lines = code.split('\n')
        
        if param_type == "basic":
            # Look for g["param_name"] = value
            pattern = rf'g\s*\[\s*["\']({re.escape(param_name)})["\']\s*\]\s*='
            for match in re.finditer(pattern, code):
                return code[:match.start()].count('\n') + 1
        else:
            # Look for add_computed("param_name", ...)
            pattern = rf'add_computed\s*\(\s*["\']({re.escape(param_name)})["\']\s*,'
            for match in re.finditer(pattern, code):
                return code[:match.start()].count('\n') + 1
        
        return 1  # Default to line 1
    
    def _static_parse(self, code: str, error_msg: str) -> Dict:
        """Fallback static analysis when execution fails"""
        try:
            lines = code.split('\n')
            
            # Parse Graph creation
            graph_match = re.search(r'Graph\s*\(\s*["\']([^"\']+)["\']', code)
            if graph_match:
                self.graph_name = graph_match.group(1)
            else:
                self.graph_name = "Unknown Graph"
            
            # Parse basic parameters with line numbers
            param_pattern = r'g\s*\[\s*["\']([^"\']+)["\']\s*\]\s*=\s*([^#\n]+)'
            for match in re.finditer(param_pattern, code):
                param_name = match.group(1)
                param_value = match.group(2).strip()
                
                # Find line number
                line_num = code[:match.start()].count('\n') + 1
                
                try:
                    # Try to evaluate the value
                    evaluated_value = eval(param_value)
                    self.parameters[param_name] = {
                        "type": "basic",
                        "value": evaluated_value,
                        "line_number": line_num,
                        "code_position": match.start()
                    }
                except:
                    # If evaluation fails, use string representation
                    self.parameters[param_name] = {
                        "type": "basic",
                        "value": param_value,
                        "line_number": line_num,
                        "code_position": match.start()
                    }
            
            # Parse add_computed calls with line tracking
            self._parse_add_computed(code, lines)
            
            return {
                "graph_name": self.graph_name,
                "parameters": self.parameters,
                "dependencies": self.dependencies,
                "success": True,
                "error": f"Static analysis used: {error_msg}"
            }
        except Exception as e:
            return {
                "graph_name": "",
                "parameters": {},
                "dependencies": {},
                "success": False,
                "error": str(e)
            }
    
    def _parse_add_computed(self, code: str, lines: List[str]):
        """Parse add_computed function calls with line tracking"""
        # Find function definitions with line numbers
        function_defs = {}
        function_line_nums = {}
        
        current_func = None
        func_lines = []
        func_start_line = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('def '):
                if current_func:
                    function_defs[current_func] = '\n'.join(func_lines)
                func_name = stripped.split('(')[0].replace('def ', '').strip()
                current_func = func_name
                func_start_line = i + 1  # 1-based line numbering
                function_line_nums[func_name] = func_start_line
                func_lines = []
            elif current_func and (line.startswith('    ') or line.strip() == ''):
                func_lines.append(line)
            elif current_func and not line.startswith('    '):
                function_defs[current_func] = '\n'.join(func_lines)
                current_func = None
                func_lines = []
        
        if current_func:
            function_defs[current_func] = '\n'.join(func_lines)
        
        # Find add_computed calls with line numbers
        add_computed_pattern = r'add_computed\s*\(\s*["\']([^"\']+)["\']\s*,\s*(\w+)'
        for match in re.finditer(add_computed_pattern, code):
            param_name = match.group(1)
            func_name = match.group(2)
            
            # Find line number of add_computed call
            line_num = code[:match.start()].count('\n') + 1
            
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
                "value": f"computed via {func_name}()",  # Static fallback
                "line_number": line_num,
                "function_line": function_line_nums.get(func_name, line_num),
                "code_position": match.start()
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


def calculate_layout(parameters: Dict, dependencies: Dict) -> Dict:
    """Calculate node positions using columnar layout"""
    positions = {}
    
    if not parameters:
        return positions
    
    # Separate basic and computed parameters
    basic_params = []
    computed_params = []
    
    for param_name, param_info in parameters.items():
        if param_info["type"] == "basic":
            basic_params.append(param_name)
        else:
            computed_params.append(param_name)
    
    # Calculate layout parameters optimized for larger rectangles
    node_height = 1.6  # Height spacing between nodes
    column_width = 4.5  # Width spacing between columns for better spacing
    start_x = -2.5  # Starting X position
    
    # Position basic parameters in left column
    for i, param_name in enumerate(basic_params):
        x = start_x
        y = -(len(basic_params) - 1) * node_height / 2 + i * node_height
        positions[param_name] = (x, y)
    
    # Position computed parameters in right column(s)
    # If there are many computed parameters, use multiple columns
    computed_per_column = max(6, len(basic_params))  # Keep columns balanced
    
    for i, param_name in enumerate(computed_params):
        column = i // computed_per_column
        row = i % computed_per_column
        
        x = start_x + column_width * (column + 1)
        # Center the column vertically
        column_size = min(computed_per_column, len(computed_params) - column * computed_per_column)
        y = -(column_size - 1) * node_height / 2 + row * node_height
        positions[param_name] = (x, y)
    
    return positions


def create_plotly_figure(graph_data: Dict):
    """Create interactive Plotly figure"""
    import plotly.graph_objects as go
    
    if not graph_data or not graph_data.get("success", False):
        # Error state
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error: {graph_data.get('error', 'Unknown error') if graph_data else 'No data'}",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(
            title="Parse Error",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            showlegend=False
        )
        return fig
    
    parameters = graph_data["parameters"]
    dependencies = graph_data["dependencies"]
    
    if not parameters:
        # Empty state
        fig = go.Figure()
        fig.add_annotation(
            text="No parameters found<br><br>Enter Graph code to visualize dependencies",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=14, color="gray")
        )
        fig.update_layout(
            title="No Parameters Found",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            showlegend=False
        )
        return fig
    
    # Calculate positions
    positions = calculate_layout(parameters, dependencies)
    
    # Create figure
    fig = go.Figure()
    
    # Add edges with arrows from right pin to left pin
    for param_name, deps in dependencies.items():
        if param_name in positions:
            end_pos = positions[param_name]
            for dep in deps:
                if dep in positions:
                    start_pos = positions[dep]
                    
                    # Calculate pin positions
                    rect_width = 2.2
                    rect_height = 0.8
                    
                    # Start from right side pin of source node
                    start_x = start_pos[0] + rect_width/2
                    start_y = start_pos[1]
                    
                    # End at left side pin of target node
                    end_x = end_pos[0] - rect_width/2
                    end_y = end_pos[1]
                    
                    # Create Bezier curve path for smooth arrows
                    # Calculate control points for smooth curve
                    dx = end_x - start_x
                    dy = end_y - start_y
                    
                    # Control points for horizontal-leaning curves
                    control_offset = abs(dx) * 0.6  # Adjust curve strength
                    control1_x = start_x + control_offset
                    control1_y = start_y
                    control2_x = end_x - control_offset
                    control2_y = end_y
                    
                    # Create SVG path for Bezier curve
                    path = f"M {start_x},{start_y} C {control1_x},{control1_y} {control2_x},{control2_y} {end_x},{end_y}"
                    
                    # Add smooth curved arrow using SVG path
                    fig.add_shape(
                        type="path",
                        path=path,
                        line=dict(
                            color='rgba(74, 144, 226, 0.85)',
                            width=3
                        ),
                        layer="below"
                    )
                    
                    # Add arrowhead at the end
                    arrow_size = 0.15
                    arrow_angle = math.atan2(control2_y - end_y, control2_x - end_x)
                    
                    # Calculate arrowhead points
                    arrow_x1 = end_x + arrow_size * math.cos(arrow_angle + 2.8)
                    arrow_y1 = end_y + arrow_size * math.sin(arrow_angle + 2.8)
                    arrow_x2 = end_x + arrow_size * math.cos(arrow_angle - 2.8)
                    arrow_y2 = end_y + arrow_size * math.sin(arrow_angle - 2.8)
                    
                    # Add filled triangle arrowhead
                    fig.add_shape(
                        type="path",
                        path=f"M {end_x},{end_y} L {arrow_x1},{arrow_y1} L {arrow_x2},{arrow_y2} Z",
                        fillcolor='rgba(74, 144, 226, 0.85)',
                        line=dict(color='rgba(74, 144, 226, 0.85)', width=0),
                        layer="above"
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
        
        # Format text with name and value on same line, larger font
        value_str = str(param_info["value"])
        if len(value_str) > 12:  # Shorter for single line display
            value_str = value_str[:12] + "..."
        
        # Put name and value on same line with larger font
        node_text.append(f"<b>{param_name}:</b> {value_str}")
        
        # Create hover info
        value_text = str(param_info["value"])
        if len(value_text) > 40:
            value_text = value_text[:40] + "..."
        
        hover_text = f"<b>{param_name}</b><br>"
        hover_text += f"Type: {param_info['type']}<br>"
        hover_text += f"Value: {value_text}"
        
        # Add line number info
        if 'line_number' in param_info:
            hover_text += f"<br>Line: {param_info['line_number']}"
        
        if param_name in dependencies:
            deps = dependencies[param_name]
            if deps:
                hover_text += f"<br>Dependencies: {', '.join(deps)}"
        
        hover_text += f"<br><i>💡 Click to open context menu</i>"
        node_hover.append(hover_text)
        
        # Use same color for all parameters
        node_colors.append('#6c757d')
            
        # Size based on dependency count
        dep_count = len(dependencies.get(param_name, []))
        size = max(25, min(50, 25 + dep_count * 8))
        node_sizes.append(size)
    
    # Prepare custom data for double-click events
    node_custom_data = []
    for param_name, pos in positions.items():
        param_info = parameters[param_name]
        custom_data = {
            'name': param_name,
            'line_number': param_info.get('line_number', 1),
            'hover_text': node_hover[list(positions.keys()).index(param_name)]
        }
        node_custom_data.append(custom_data)
    
    # Add rectangular shapes for nodes first
    for i, (param_name, pos) in enumerate(positions.items()):
        param_info = parameters[param_name]
        
        # Optimized rectangle dimensions for better text fit
        width = 2.2
        height = 0.8
        
        # Modern gradient color with subtle depth
        fill_color = 'rgba(99, 110, 125, 0.95)'
        
        # Add modern styled rectangle with shadow effect
        fig.add_shape(
            type="rect",
            x0=pos[0] - width/2,
            y0=pos[1] - height/2,
            x1=pos[0] + width/2,
            y1=pos[1] + height/2,
            fillcolor=fill_color,
            opacity=1.0,
            line=dict(color='rgba(255, 255, 255, 0.9)', width=1.5),
            layer="below"
        )
        
        # Add pin points for visual clarity
        pin_size = 0.08
        pin_color = 'rgba(74, 144, 226, 0.9)'
        
        # Right side pin (output)
        fig.add_shape(
            type="circle",
            x0=pos[0] + width/2 - pin_size/2,
            y0=pos[1] - pin_size/2,
            x1=pos[0] + width/2 + pin_size/2,
            y1=pos[1] + pin_size/2,
            fillcolor=pin_color,
            line=dict(color='white', width=1),
            layer="above"
        )
        
        # Left side pin (input) - only for computed parameters
        if param_info["type"] == "computed":
            fig.add_shape(
                type="circle",
                x0=pos[0] - width/2 - pin_size/2,
                y0=pos[1] - pin_size/2,
                x1=pos[0] - width/2 + pin_size/2,
                y1=pos[1] + pin_size/2,
                fillcolor=pin_color,
                line=dict(color='white', width=1),
                layer="above"
            )
    
    # Add text labels inside rectangles
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='text',
        text=node_text,
        textposition="middle center",
        textfont=dict(
            size=14, 
            color='rgba(255, 255, 255, 0.95)', 
            family='SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif'
        ),
        hovertemplate='%{hovertext}<extra></extra>',
        hovertext=node_hover,
        customdata=node_custom_data,
        showlegend=False,
        name='NodeText'
    ))
    
    # Add invisible clickable areas for interaction
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        marker=dict(
            size=55,  # Adjusted to match new rectangle size
            color='rgba(0,0,0,0)',  # Transparent
            line=dict(width=0)
        ),
        hovertemplate='%{hovertext}<extra></extra>',
        hovertext=node_hover,
        customdata=node_custom_data,
        showlegend=False,
        name='ClickableAreas'
    ))
    
    # Update layout for interactivity
    fig.update_layout(
        title=f"Interactive Graph: {graph_data['graph_name']}",
        title_font=dict(size=18, color='#2c3e50'),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-5, 10]  # Adjusted for larger rectangles and spacing
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-6, 6]  # Adjusted for vertical spacing
        ),
        plot_bgcolor='rgba(250, 251, 252, 0.9)',
        paper_bgcolor='rgba(255, 255, 255, 0.98)',
        showlegend=False,
        legend=dict(
            x=1.02,
            y=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#bdc3c7',
            borderwidth=1
        ),
        margin=dict(l=20, r=120, t=80, b=50),
        dragmode='zoom'  # Allow both clicking and dragging
    )
    
    
    # Calculate statistics first
    basic_count = sum(1 for p in parameters.values() if p["type"] == "basic")
    computed_count = sum(1 for p in parameters.values() if p["type"] == "computed")
    
    
    return fig


# Mode 1: Online Dash Application
def run_online_mode():
    """Run online Dash web application"""
    try:
        import dash
        from dash import dcc, html, Input, Output, State, callback_context
        import dash_bootstrap_components as dbc
        import plotly.graph_objects as go
        from threading import Timer
        
        print("🌐 Starting Online Mode (Dash Web Application)...")
        print("📊 Features:")
        print("   • Real-time code editing")
        print("   • Interactive node dragging") 
        print("   • Hover effects and tooltips")
        print("   • Modern responsive UI")
        print("   • Auto-refresh on code changes")
        print("")
        
        # Create Dash app
        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        parser = PlotlyCodeParser()
        
        # App layout
        app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("Plotly Graph Visualizer - Online Mode", 
                           className="text-center mb-4",
                           style={'color': '#2c3e50', 'fontWeight': 'bold'})
                ])
            ]),
            
            # Main content
            dbc.Row([
                # Left panel: Graph visualization
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H4("Interactive Dependency Graph", className="mb-0", style={'color': '#34495e'})
                        ]),
                        dbc.CardBody([
                            dcc.Graph(
                                id='dependency-graph',
                                style={'height': '600px', 'borderRadius': '8px'},
                                config={
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
                            )
                        ])
                    ], style={'border': '2px solid #3498db'})
                ], width=7),
                
                # Right panel: Code editor
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H4("Code Editor", className="mb-0", style={'color': '#34495e'})
                        ]),
                        dbc.CardBody([
                            # Monaco Editor container
                            html.Div(
                                id='monaco-editor-container',
                                style={
                                    'width': '100%',
                                    'height': '500px',
                                    'border': '1px solid #bdc3c7',
                                    'borderRadius': '4px'
                                }
                            ),
                            # Hidden textarea for Dash compatibility
                            dcc.Textarea(
                                id='code-editor',
                                value=get_sample_code(),
                                style={'display': 'none'}
                            ),
                            html.Div([
                                dbc.Button("Refresh Graph", id="refresh-btn", color="primary", className="me-2"),
                                dbc.Button("Load Sample", id="sample-btn", color="success", className="me-2"),
                                dbc.Button("Clear Code", id="clear-btn", color="warning", className="me-2"),
                                dbc.Button("Save HTML", id="save-btn", color="info")
                            ], className="mt-3")
                        ])
                    ], style={'border': '2px solid #95a5a6'})
                ], width=5)
            ], className="mb-4"),
            
            # Status panel
            dbc.Row([
                dbc.Col([
                    html.Div(id="status-info", children=[
                        dbc.Alert("🚀 Online Mode: Real-time interactive visualization with full Plotly features!", 
                                color="info", className="mb-0")
                    ])
                ])
            ]),
            
            # Context menu for node actions
            html.Div([
                dbc.Card([
                    dbc.CardBody([
                        html.H6(id="menu-node-name", className="card-title mb-2"),
                        html.P(id="menu-node-info", className="card-text small mb-3"),
                        dbc.ButtonGroup([
                            dbc.Button("🔍 Jump to Code", id="jump-to-code-btn", color="primary", size="sm"),
                            dbc.Button("📋 Copy Name", id="copy-name-btn", color="secondary", size="sm"),
                            dbc.Button("❌ Close", id="close-menu-btn", color="light", size="sm")
                        ], vertical=False)
                    ])
                ], style={'width': '250px'})
            ], id='context-menu', style={
                'position': 'absolute',
                'display': 'none',
                'zIndex': 1000,
                'left': '0px',
                'top': '0px'
            }),
            
            # Hidden storage for graph data and selected node
            html.Div(id='graph-data-store', style={'display': 'none'}),
            html.Div(id='selected-node-store', style={'display': 'none'})
            
        ], fluid=True, style={'backgroundColor': '#ecf0f1', 'minHeight': '100vh', 'padding': '20px'})
        
        # Callbacks
        @app.callback(
            [Output('dependency-graph', 'figure'),
             Output('status-info', 'children'),
             Output('graph-data-store', 'children')],
            [Input('refresh-btn', 'n_clicks'),
             Input('sample-btn', 'n_clicks'),
             Input('clear-btn', 'n_clicks'),
             Input('save-btn', 'n_clicks')],
            [State('code-editor', 'value')]
        )
        def update_graph(refresh_clicks, sample_clicks, clear_clicks, save_clicks, code_value):
            ctx = callback_context
            
            if not ctx.triggered:
                code = code_value or get_sample_code()
            else:
                trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
                
                if trigger_id == 'sample-btn':
                    code = get_sample_code()
                elif trigger_id == 'clear-btn':
                    code = ""
                elif trigger_id == 'save-btn':
                    # Save current graph as HTML
                    code = code_value or ""
                    graph_data = parser.parse_code(code)
                    if graph_data["success"]:
                        fig = create_plotly_figure(graph_data)
                        import plotly.offline as pyo
                        import json
                        html_file = os.path.join(tempfile.gettempdir(), "graph_visualizer_online.html")
                        pyo.plot(fig, filename=html_file, auto_open=False)
                        return fig, dbc.Alert(f"✅ Graph saved to: {html_file}", color="success"), json.dumps(graph_data)
                    else:
                        return create_plotly_figure(graph_data), dbc.Alert("❌ Cannot save - fix parse errors first", color="danger"), json.dumps(graph_data)
                else:
                    code = code_value or ""
            
            # Parse and create figure
            graph_data = parser.parse_code(code)
            fig = create_plotly_figure(graph_data)
            
            # Status message
            if graph_data and graph_data.get("success", False):
                params = graph_data["parameters"]
                basic_count = sum(1 for p in params.values() if p["type"] == "basic")
                computed_count = sum(1 for p in params.values() if p["type"] == "computed")
                
                status = dbc.Alert([
                    html.Strong("✅ Graph updated successfully! "),
                    f"Found {len(params)} parameters: {basic_count} basic, {computed_count} computed. ",
                    html.Br(),
                    html.Small("💡 Drag to pan, scroll to zoom, hover for details, click node for context menu.")
                ], color="success")
            elif graph_data:
                status = dbc.Alert([
                    html.Strong("❌ Parse Error: "),
                    graph_data.get("error", "Unknown error")
                ], color="danger")
            else:
                status = dbc.Alert("Enter Graph code to visualize dependencies.", color="info")
            
            import json
            return fig, status, json.dumps(graph_data)
        
        # Handle sample and clear buttons with Monaco Editor
        app.clientside_callback(
            """
            function(sample_clicks, clear_clicks) {
                const ctx = window.dash_clientside.callback_context;
                
                if (!ctx.triggered || ctx.triggered.length === 0) {
                    return window.dash_clientside.no_update;
                }
                
                const trigger_id = ctx.triggered[0].prop_id.split('.')[0];
                
                if (trigger_id === 'sample-btn' && window.setMonacoValue) {
                    const sampleCode = `""" + get_sample_code().replace('`', '\\`').replace('${', '\\${') + """`;
                    window.setMonacoValue(sampleCode);
                } else if (trigger_id === 'clear-btn' && window.setMonacoValue) {
                    window.setMonacoValue('');
                }
                
                return window.dash_clientside.no_update;
            }
            """,
            Output('sample-btn', 'n_clicks'),
            [Input('sample-btn', 'n_clicks'),
             Input('clear-btn', 'n_clicks')]
        )
        
        # Handle node click to show context menu
        app.clientside_callback(
            """
            function(clickData, graphData) {
                console.log('Click callback triggered:', clickData);
                
                if (!clickData || !clickData.points || clickData.points.length === 0) {
                    // Hide menu if clicked elsewhere
                    const menu = document.getElementById('context-menu');
                    if (menu) {
                        menu.style.display = 'none';
                    }
                    return [window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update];
                }
                
                const point = clickData.points[0];
                console.log('Point data:', point);
                
                // Check if this is a clickable node (with customdata)
                if (point.customdata) {
                    const paramName = point.customdata.name || point.text;
                    const lineNumber = point.customdata.line_number || 'Unknown';
                    const graphDataParsed = JSON.parse(graphData || '{}');
                    
                    console.log('Found clickable node:', paramName, 'Line:', lineNumber);
                    
                    let paramInfo = '';
                    if (graphDataParsed.parameters && graphDataParsed.parameters[paramName]) {
                        const param = graphDataParsed.parameters[paramName];
                        paramInfo = `Type: ${param.type}\\nLine: ${lineNumber}\\nValue: ${param.value}`;
                    }
                    
                    // Show context menu at click position
                    const menu = document.getElementById('context-menu');
                    if (menu) {
                        // Position menu near click point
                        const rect = document.getElementById('dependency-graph').getBoundingClientRect();
                        const x = Math.min(point.x || 200, window.innerWidth - 300);
                        const y = Math.min(point.y || 200, window.innerHeight - 200);
                        
                        menu.style.left = (rect.left + 200) + 'px';
                        menu.style.top = (rect.top + 100) + 'px';
                        menu.style.display = 'block';
                        
                        console.log('Context menu displayed at:', menu.style.left, menu.style.top);
                    }
                    
                    return [paramName, paramInfo, JSON.stringify(point.customdata), window.dash_clientside.no_update];
                }
                
                console.log('Click was not on a node with customdata');
                return [window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update];
            }
            """,
            [Output('menu-node-name', 'children'),
             Output('menu-node-info', 'children'),
             Output('selected-node-store', 'children'),
             Output('context-menu', 'style')],
            [Input('dependency-graph', 'clickData')],
            [State('graph-data-store', 'children')]
        )
        
        # Handle jump to code button
        app.clientside_callback(
            """
            function(n_clicks, selected_node_data) {
                if (!n_clicks || !selected_node_data) {
                    return window.dash_clientside.no_update;
                }
                
                try {
                    const nodeData = JSON.parse(selected_node_data);
                    const lineNumber = nodeData.line_number || 1;
                    
                    // Use Monaco Editor API to jump to line
                    if (window.jumpToLine) {
                        window.jumpToLine(lineNumber);
                        console.log('Jumped to line ' + lineNumber);
                    }
                    
                    // Hide context menu
                    const menu = document.getElementById('context-menu');
                    if (menu) {
                        menu.style.display = 'none';
                    }
                    
                } catch (e) {
                    console.error('Error jumping to code:', e);
                }
                
                return window.dash_clientside.no_update;
            }
            """,
            Output('jump-to-code-btn', 'n_clicks'),
            [Input('jump-to-code-btn', 'n_clicks')],
            [State('selected-node-store', 'children')]
        )
        
        # Handle close menu button
        app.clientside_callback(
            """
            function(n_clicks) {
                if (n_clicks) {
                    const menu = document.getElementById('context-menu');
                    if (menu) {
                        menu.style.display = 'none';
                    }
                }
                return window.dash_clientside.no_update;
            }
            """,
            Output('close-menu-btn', 'n_clicks'),
            [Input('close-menu-btn', 'n_clicks')]
        )
        
        # Handle copy name button
        app.clientside_callback(
            """
            function(n_clicks, nodeName) {
                if (n_clicks && nodeName) {
                    // Copy to clipboard
                    navigator.clipboard.writeText(nodeName).then(function() {
                        console.log('Parameter name copied to clipboard: ' + nodeName);
                        // Could show a toast notification here
                    });
                }
                return window.dash_clientside.no_update;
            }
            """,
            Output('copy-name-btn', 'n_clicks'),
            [Input('copy-name-btn', 'n_clicks')],
            [State('menu-node-name', 'children')]
        )
        
        # Add hover effect for nodes
        app.clientside_callback(
            """
            function(hoverData) {
                // Handle hover effects on nodes
                if (hoverData && hoverData.points && hoverData.points.length > 0) {
                    const point = hoverData.points[0];
                    if (point.customdata) {
                        // Add subtle highlight effect
                        const graphDiv = document.getElementById('dependency-graph');
                        if (graphDiv) {
                            graphDiv.style.cursor = 'pointer';
                        }
                    }
                } else {
                    // Reset cursor when not hovering
                    const graphDiv = document.getElementById('dependency-graph');
                    if (graphDiv) {
                        graphDiv.style.cursor = 'default';
                    }
                }
                return window.dash_clientside.no_update;
            }
            """,
            Output('dependency-graph', 'hoverData'),
            [Input('dependency-graph', 'hoverData')]
        )
        
        # Initialize Monaco Editor
        app.clientside_callback(
            """
            function(dummy) {
                if (!window.monacoInitialized) {
                    window.monacoInitialized = true;
                    
                    // Load Monaco Editor
                    const script = document.createElement('script');
                    script.src = 'https://unpkg.com/monaco-editor@0.44.0/min/vs/loader.js';
                    script.onload = function() {
                        require.config({ paths: { vs: 'https://unpkg.com/monaco-editor@0.44.0/min/vs' } });
                        require(['vs/editor/editor.main'], function() {
                            // Create Monaco Editor
                            const sampleCode = `from core import Graph

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
print(f"Efficiency: {g['efficiency']}")`;

                            window.monacoEditor = monaco.editor.create(document.getElementById('monaco-editor-container'), {
                                value: sampleCode,
                                language: 'python',
                                theme: 'vs-dark',
                                fontSize: 12,
                                fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                                minimap: { enabled: false },
                                scrollBeyondLastLine: false,
                                automaticLayout: true,
                                wordWrap: 'on'
                            });
                            
                            // Sync with hidden textarea
                            function syncWithTextarea() {
                                const hiddenTextarea = document.getElementById('code-editor');
                                if (hiddenTextarea && window.monacoEditor) {
                                    hiddenTextarea.value = window.monacoEditor.getValue();
                                    hiddenTextarea.dispatchEvent(new Event('change', { bubbles: true }));
                                }
                            }
                            
                            window.monacoEditor.onDidChangeModelContent(syncWithTextarea);
                            
                            // Helper functions
                            window.jumpToLine = function(lineNumber) {
                                if (window.monacoEditor && lineNumber) {
                                    window.monacoEditor.revealLineInCenter(lineNumber);
                                    window.monacoEditor.setPosition({ lineNumber: lineNumber, column: 1 });
                                    window.monacoEditor.focus();
                                }
                            };
                            
                            window.setMonacoValue = function(value) {
                                if (window.monacoEditor) {
                                    window.monacoEditor.setValue(value);
                                    syncWithTextarea();
                                }
                            };
                            
                            // Initial sync
                            syncWithTextarea();
                            
                            console.log('Monaco Editor initialized with Python support');
                        });
                    };
                    document.head.appendChild(script);
                }
                return window.dash_clientside.no_update;
            }
            """,
            Output('monaco-editor-container', 'id'),
            [Input('monaco-editor-container', 'id')]
        )
        
        # Auto-open browser
        Timer(1.5, lambda: webbrowser.open('http://127.0.0.1:8054')).start()
        
        print("🌐 Opening browser at: http://127.0.0.1:8054")
        print("💡 Tip: Try editing code in real-time!")
        
        app.run(debug=False, host='127.0.0.1', port=8054)
        
    except ImportError as e:
        print(f"❌ Online mode requires: dash, plotly, dash-bootstrap-components")
        print(f"   Install with: pip install dash plotly dash-bootstrap-components")
        print(f"   Error: {e}")
        sys.exit(1)


# Mode 2: Offline HTML Generation
def run_offline_mode():
    """Run offline mode - generate HTML file"""
    try:
        import plotly.offline as pyo
        
        print("📁 Starting Offline Mode (HTML File Generation)...")
        print("📊 Features:")
        print("   • Generates standalone HTML files")
        print("   • No web server required")
        print("   • Full interactivity in browser")
        print("   • Shareable files")
        print("")
        
        parser = PlotlyCodeParser()
        
        # Get code from user
        print("Enter your Graph code (or press Enter for sample):")
        print("-" * 50)
        
        code_lines = []
        sample_used = False
        
        try:
            while True:
                line = input()
                if not line.strip() and not code_lines:
                    # Empty input on first line - use sample
                    code = get_sample_code()
                    sample_used = True
                    break
                elif not line.strip() and code_lines:
                    # Empty line after content - done
                    break
                else:
                    code_lines.append(line)
            
            if not sample_used:
                code = '\n'.join(code_lines)
                
        except KeyboardInterrupt:
            print("\n\n🔄 Using sample code...")
            code = get_sample_code()
            sample_used = True
        
        if sample_used:
            print("✅ Using sample code:")
            print("-" * 30)
            for i, line in enumerate(code.split('\n')[:10], 1):
                print(f"{i:2d}: {line}")
            if len(code.split('\n')) > 10:
                print("    ... (truncated)")
            print("-" * 30)
        
        print("\n🔄 Parsing code...")
        
        # Parse code
        graph_data = parser.parse_code(code)
        
        if not graph_data["success"]:
            print(f"❌ Parse Error: {graph_data['error']}")
            return
        
        # Create figure
        print("🎨 Creating interactive figure...")
        fig = create_plotly_figure(graph_data)
        
        # Generate HTML
        print("📝 Generating HTML file...")
        
        # Save to temp directory
        temp_dir = tempfile.gettempdir()
        html_file = os.path.join(temp_dir, "graph_visualizer_offline.html")
        
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
        
        pyo.plot(fig, filename=html_file, auto_open=True, config=config)
        
        # Print summary
        params = graph_data["parameters"]
        basic_count = sum(1 for p in params.values() if p["type"] == "basic")
        computed_count = sum(1 for p in params.values() if p["type"] == "computed")
        
        print(f"\n✅ Success! Interactive graph generated:")
        print(f"📊 Graph: {graph_data['graph_name']}")
        print(f"📈 Parameters: {len(params)} total ({basic_count} basic, {computed_count} computed)")
        print(f"📁 File: {html_file}")
        print(f"🌐 Opening in browser...")
        
        if graph_data["dependencies"]:
            print(f"\n🔗 Dependencies:")
            for param, deps in graph_data["dependencies"].items():
                if deps:
                    print(f"   • {param} ← {', '.join(deps)}")
        
        print(f"\n💡 Features in HTML file:")
        print(f"   • Drag to pan view")
        print(f"   • Scroll to zoom")
        print(f"   • Hover for node details")
        print(f"   • Toolbar for save/zoom options")
        print(f"   • Fully self-contained file")
        
    except ImportError as e:
        print(f"❌ Offline mode requires: plotly")
        print(f"   Install with: pip install plotly")
        print(f"   Error: {e}")
        sys.exit(1)


def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Plotly Graph Visualizer - Interactive dependency graph visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python plotly_graph_visualizer.py --mode online   # Web application (Dash)
  python plotly_graph_visualizer.py --mode offline  # Generate HTML file

Modes:
  online  : Web application with real-time editing (requires Dash + browser)
  offline : Generate standalone HTML file (requires only Plotly)
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['online', 'offline'],
        default='offline',
        help='Visualization mode (default: offline)'
    )
    
    args = parser.parse_args()
    
    print("🚀 Plotly Graph Visualizer")
    print("=" * 40)
    print(f"Mode: {args.mode}")
    print()
    
    if args.mode == 'online':
        run_online_mode()
    elif args.mode == 'offline':
        run_offline_mode()


if __name__ == "__main__":
    main()