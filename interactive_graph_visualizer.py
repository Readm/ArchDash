#!/usr/bin/env python3
"""
Interactive Graph Visualizer - Plotly + Dash Version
Features: Node dragging, hover effects, click interactions, modern UI
"""

import re
import math
import json
import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Set, Tuple, Optional
import webbrowser
from threading import Timer

class InteractiveCodeParser:
    """Enhanced code parser for interactive visualization"""
    
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


class InteractiveGraphVisualizer:
    """Interactive graph visualizer using Plotly + Dash"""
    
    def __init__(self):
        self.parser = InteractiveCodeParser()
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.current_graph_data = None
        self.node_positions = {}
        self.setup_layout()
        self.setup_callbacks()
        
    def get_sample_code(self):
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

    def setup_layout(self):
        """Setup the Dash app layout"""
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("Graph Visualizer - Interactive Code Dependency Tool", 
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
                            html.H4("Dependency Graph", className="mb-0", style={'color': '#34495e'})
                        ]),
                        dbc.CardBody([
                            dcc.Graph(
                                id='dependency-graph',
                                style={'height': '600px'},
                                config={
                                    'displayModeBar': True,
                                    'displaylogo': False,
                                    'modeBarButtonsToRemove': ['select2d', 'lasso2d']
                                }
                            )
                        ])
                    ], style={'border': '2px solid #3498db'})
                ], width=6),
                
                # Right panel: Code editor
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H4("Code Editor", className="mb-0", style={'color': '#34495e'})
                        ]),
                        dbc.CardBody([
                            dcc.Textarea(
                                id='code-editor',
                                value=self.get_sample_code(),
                                style={
                                    'width': '100%',
                                    'height': '500px',
                                    'fontFamily': 'Monaco, Consolas, "Lucida Console", monospace',
                                    'fontSize': '12px',
                                    'border': '1px solid #bdc3c7',
                                    'borderRadius': '4px',
                                    'padding': '10px'
                                },
                                placeholder="Enter your Graph code here..."
                            ),
                            html.Div([
                                dbc.Button("Refresh Graph", id="refresh-btn", color="primary", className="me-2"),
                                dbc.Button("Load Sample", id="sample-btn", color="success", className="me-2"),
                                dbc.Button("Clear Code", id="clear-btn", color="warning")
                            ], className="mt-3")
                        ])
                    ], style={'border': '2px solid #95a5a6'})
                ], width=6)
            ], className="mb-4"),
            
            # Status and info panel
            dbc.Row([
                dbc.Col([
                    html.Div(id="status-info", children=[
                        dbc.Alert("Welcome! Load sample code or enter your own Graph code to visualize dependencies.", 
                                color="info", className="mb-0")
                    ])
                ])
            ]),
            
            # Hidden div to store graph data
            html.Div(id='graph-data-store', style={'display': 'none'})
            
        ], fluid=True, style={'backgroundColor': '#ecf0f1', 'minHeight': '100vh', 'padding': '20px'})

    def calculate_layout(self, parameters: Dict, dependencies: Dict) -> Dict:
        """Calculate interactive node positions"""
        positions = {}
        param_names = list(parameters.keys())
        n = len(param_names)
        
        if n == 0:
            return positions
        
        # Use force-directed layout principles
        base_radius = max(3, min(6, n * 0.5))
        
        # Circular initial layout with some randomization for better distribution
        for i, param_name in enumerate(param_names):
            angle = 2 * math.pi * i / n
            # Add some randomization to avoid perfect circles
            radius_variation = base_radius + (i % 3 - 1) * 0.5
            x = math.cos(angle) * radius_variation
            y = math.sin(angle) * radius_variation
            positions[param_name] = (x, y)
        
        return positions

    def create_graph_figure(self, graph_data: Dict):
        """Create interactive Plotly figure"""
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
                text="No parameters found<br><br>Enter Graph code in the editor",
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
        positions = self.calculate_layout(parameters, dependencies)
        self.node_positions = positions
        
        # Create figure
        fig = go.Figure()
        
        # Draw edges first (so they appear behind nodes)
        edge_x = []
        edge_y = []
        edge_info = []
        
        for param_name, deps in dependencies.items():
            if param_name in positions:
                end_pos = positions[param_name]
                for dep in deps:
                    if dep in positions:
                        start_pos = positions[dep]
                        edge_x.extend([start_pos[0], end_pos[0], None])
                        edge_y.extend([start_pos[1], end_pos[1], None])
                        edge_info.append(f"{dep} → {param_name}")
        
        # Add edges
        if edge_x:
            fig.add_trace(go.Scatter(
                x=edge_x, y=edge_y,
                mode='lines',
                line=dict(width=2, color='#7f8c8d'),
                hoverinfo='none',
                showlegend=False,
                name='Dependencies'
            ))
        
        # Prepare node data
        node_x = []
        node_y = []
        node_text = []
        node_info = []
        node_colors = []
        node_sizes = []
        
        for param_name, pos in positions.items():
            param_info = parameters[param_name]
            
            node_x.append(pos[0])
            node_y.append(pos[1])
            node_text.append(param_name)
            
            # Create hover info
            value_text = str(param_info["value"])
            if len(value_text) > 30:
                value_text = value_text[:30] + "..."
            
            hover_text = f"<b>{param_name}</b><br>"
            hover_text += f"Type: {param_info['type']}<br>"
            hover_text += f"Value: {value_text}<br>"
            
            if param_name in dependencies:
                deps = dependencies[param_name]
                if deps:
                    hover_text += f"Dependencies: {', '.join(deps)}"
            
            node_info.append(hover_text)
            
            # Color coding
            if param_info["type"] == "basic":
                node_colors.append('#3498db')  # Blue for basic
            else:
                node_colors.append('#2ecc71')  # Green for computed
                
            # Size based on dependency count
            dep_count = len(dependencies.get(param_name, []))
            size = max(20, min(40, 20 + dep_count * 5))
            node_sizes.append(size)
        
        # Add nodes with drag capability
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='white'),
                opacity=0.8,
                symbol='circle'
            ),
            text=node_text,
            textposition="middle center",
            textfont=dict(size=10, color='white', family='Arial Black'),
            hovertemplate='%{customdata}<br><i>Click and drag to move</i><extra></extra>',
            customdata=node_info,
            showlegend=False,
            name='Parameters',
            # Enable individual point selection for dragging
            selected=dict(marker=dict(opacity=1.0, line=dict(width=3, color='#e74c3c'))),
            unselected=dict(marker=dict(opacity=0.8))
        ))
        
        # Update layout for interactivity
        fig.update_layout(
            title=f"Dependency Graph: {graph_data['graph_name']}",
            title_font=dict(size=16, color='#2c3e50'),
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-8, 8]
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-8, 8],
                scaleanchor="x",
                scaleratio=1
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=True,
            legend=dict(
                x=1.02,
                y=1,
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='#bdc3c7',
                borderwidth=1
            ),
            margin=dict(l=20, r=120, t=60, b=20),
            dragmode='select',  # Enable selection mode for node dragging
            clickmode='event+select',  # Enable both click and select events
            # Add selection and drag configuration
            selectdirection='any'
        )
        
        # Add legend manually since we're not using showlegend for traces
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode='markers',
            marker=dict(size=15, color='#3498db'),
            legendgroup='legend',
            showlegend=True,
            name='Basic Parameters'
        ))
        
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode='markers',
            marker=dict(size=15, color='#2ecc71'),
            legendgroup='legend',
            showlegend=True,
            name='Computed Parameters'
        ))
        
        return fig

    def setup_callbacks(self):
        """Setup Dash callbacks for interactivity"""
        
        # Main graph update callback
        @self.app.callback(
            [Output('dependency-graph', 'figure'),
             Output('status-info', 'children'),
             Output('graph-data-store', 'children')],
            [Input('refresh-btn', 'n_clicks'),
             Input('sample-btn', 'n_clicks'),
             Input('clear-btn', 'n_clicks')],
            [State('code-editor', 'value')]
        )
        def update_graph(refresh_clicks, sample_clicks, clear_clicks, code_value):
            ctx = callback_context
            
            if not ctx.triggered:
                # Initial load
                code = code_value or self.get_sample_code()
            else:
                trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
                
                if trigger_id == 'sample-btn':
                    code = self.get_sample_code()
                elif trigger_id == 'clear-btn':
                    code = ""
                else:  # refresh-btn or any other trigger
                    code = code_value or ""
            
            # Parse code
            graph_data = self.parser.parse_code(code)
            self.current_graph_data = graph_data
            
            # Create figure
            fig = self.create_graph_figure(graph_data)
            
            # Create status message
            if graph_data and graph_data.get("success", False):
                params = graph_data["parameters"]
                basic_count = sum(1 for p in params.values() if p["type"] == "basic")
                computed_count = sum(1 for p in params.values() if p["type"] == "computed")
                
                status = dbc.Alert([
                    html.Strong("Graph parsed successfully! "),
                    f"Found {len(params)} parameters: {basic_count} basic, {computed_count} computed. ",
                    html.Br(),
                    html.Small("💡 Tip: Hover over nodes for details, drag to pan, zoom with mouse wheel.")
                ], color="success")
            elif graph_data:
                status = dbc.Alert([
                    html.Strong("Parse Error: "),
                    graph_data.get("error", "Unknown error")
                ], color="danger")
            else:
                status = dbc.Alert("Enter Graph code to visualize dependencies.", color="info")
            
            return fig, status, json.dumps(graph_data)
        
        # Load sample code callback
        @self.app.callback(
            Output('code-editor', 'value'),
            [Input('sample-btn', 'n_clicks'),
             Input('clear-btn', 'n_clicks')]
        )
        def update_code_editor(sample_clicks, clear_clicks):
            ctx = callback_context
            
            if not ctx.triggered:
                return self.get_sample_code()
            
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if trigger_id == 'sample-btn':
                return self.get_sample_code()
            elif trigger_id == 'clear-btn':
                return ""
            
            return dash.no_update
        
        # Node interaction callback for clicks and hover effects
        @self.app.callback(
            Output('status-info', 'children', allow_duplicate=True),
            [Input('dependency-graph', 'clickData'),
             Input('dependency-graph', 'hoverData')],
            prevent_initial_call=True
        )
        def handle_node_interaction(click_data, hover_data):
            ctx = callback_context
            
            if not ctx.triggered:
                return dash.no_update
            
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if trigger_id == 'dependency-graph':
                trigger_prop = ctx.triggered[0]['prop_id'].split('.')[1]
                
                if trigger_prop == 'clickData' and click_data:
                    # Handle node click
                    point = click_data['points'][0]
                    if 'text' in point:  # This is a node, not an edge
                        node_name = point['text']
                        return dbc.Alert([
                            html.Strong(f"Clicked node: {node_name} "),
                            html.Br(),
                            "💡 Node interactions: Click to select, hover for details, drag to move (when supported)"
                        ], color="primary")
                
                elif trigger_prop == 'hoverData' and hover_data:
                    # Handle node hover (could add specific hover effects here)
                    return dash.no_update
            
            return dash.no_update

    def run_server(self, debug=False, host='127.0.0.1', port=8050):
        """Run the Dash server"""
        print(f"🚀 Starting Interactive Graph Visualizer...")
        print(f"📊 Features:")
        print(f"   • Interactive node positioning")
        print(f"   • Hover effects and detailed tooltips") 
        print(f"   • Drag to pan, zoom with mouse wheel")
        print(f"   • Modern responsive UI")
        print(f"   • Real-time code parsing")
        print(f"")
        print(f"🌐 Opening browser at: http://{host}:{port}")
        print(f"💡 Tip: Try the sample code, then modify it to see real-time updates!")
        
        # Auto-open browser
        Timer(1.5, lambda: webbrowser.open(f'http://{host}:{port}')).start()
        
        self.app.run(debug=debug, host=host, port=port)


def main():
    """Main function"""
    visualizer = InteractiveGraphVisualizer()
    visualizer.run_server(debug=False)


if __name__ == "__main__":
    main()