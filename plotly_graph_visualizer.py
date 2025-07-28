#!/usr/bin/env python3
"""
Plotly Graph Visualizer - Online and Offline Modes
Usage: 
  python plotly_graph_visualizer.py --mode online   # Dash web application
  python plotly_graph_visualizer.py --mode offline  # Generate HTML file
"""

import re
import math
from i18n import get_translation, get_available_languages
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
        self.groups = {}  # group_name -> {name, description, parameters: []}
        self.parameter_groups = {}  # parameter_name -> group_name
        
    def parse_code(self, code: str) -> Dict:
        """Parse code and extract Graph information with actual execution"""
        self.graph_name = ""
        self.parameters = {}
        self.dependencies = {}
        self.groups = {}
        self.parameter_groups = {}
        
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
        
        # Extract groups if the Graph instance supports them
        if hasattr(graph_instance, '_groups'):
            for group_name, group_info in graph_instance._groups.items():
                self.groups[group_name] = {
                    'name': group_name,
                    'description': group_info.get('description', group_name),
                    'parameters': []
                }
        
        if hasattr(graph_instance, '_parameter_groups'):
            self.parameter_groups = graph_instance._parameter_groups.copy()
        
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
                    "code_position": 0,
                    "group": self.parameter_groups.get(param_name, None)
                }
                
            except Exception as e:
                # If can't get value, use placeholder
                self.parameters[param_name] = {
                    "type": "computed",
                    "value": f"Error: {str(e)}",
                    "line_number": 1,
                    "code_position": 0,
                    "group": self.parameter_groups.get(param_name, None)
                }
        
        # Populate groups with their parameters
        for param_name, param_info in self.parameters.items():
            group_name = param_info.get("group")
            if group_name and group_name in self.groups:
                if param_name not in self.groups[group_name]["parameters"]:
                    self.groups[group_name]["parameters"].append(param_name)
        
        return {
            "graph_name": self.graph_name,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
            "groups": self.groups,
            "parameter_groups": self.parameter_groups,
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
                        "code_position": match.start(),
                        "group": None  # Will be filled by _parse_groups
                    }
                except:
                    # If evaluation fails, use string representation
                    self.parameters[param_name] = {
                        "type": "basic",
                        "value": param_value,
                        "line_number": line_num,
                        "code_position": match.start(),
                        "group": None  # Will be filled by _parse_groups
                    }
            
            # Parse add_computed calls with line tracking
            self._parse_add_computed(code, lines)
            
            # Parse group-related calls
            self._parse_groups(code)
            
            # Populate groups with their parameters
            for param_name, param_info in self.parameters.items():
                group_name = param_info.get("group")
                if group_name and group_name in self.groups:
                    if param_name not in self.groups[group_name]["parameters"]:
                        self.groups[group_name]["parameters"].append(param_name)
            
            return {
                "graph_name": self.graph_name,
                "parameters": self.parameters,
                "dependencies": self.dependencies,
                "groups": self.groups,
                "parameter_groups": self.parameter_groups,
                "success": True,
                "error": f"Static analysis used: {error_msg}"
            }
        except Exception as e:
            return {
                "graph_name": "",
                "parameters": {},
                "dependencies": {},
                "groups": {},
                "parameter_groups": {},
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
                "code_position": match.start(),
                "group": None  # Will be filled by _parse_groups
            }
            self.dependencies[param_name] = dependencies

    def _parse_groups(self, code: str):
        """Parse group-related function calls"""
        lines = code.split('\n')
        
        # Parse create_group calls: g.create_group("group_name", "Group Description")
        create_group_pattern = r'g\.create_group\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']*)["\']'
        for match in re.finditer(create_group_pattern, code):
            group_name = match.group(1)
            group_description = match.group(2)
            self.groups[group_name] = {
                'name': group_name,
                'description': group_description,
                'parameters': []
            }
        
        # Parse set_group calls: g.set_group("param_name", "group_name")
        set_group_pattern = r'g\.set_group\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']'
        for match in re.finditer(set_group_pattern, code):
            param_name = match.group(1)
            group_name = match.group(2)
            self.parameter_groups[param_name] = group_name
            
            # Update parameter info if it exists
            if param_name in self.parameters:
                self.parameters[param_name]["group"] = group_name


def get_sample_examples():
    """Get all available sample examples organized by category"""
    return {
        "basic": {
            "name": {"en": "📐 Basic Math", "zh": "📐 基础数学"},
            "examples": {
                "geometry": {
                    "name": {"en": "Circle Geometry", "zh": "圆形几何"},
                    "description": {"en": "Calculate circle properties", "zh": "计算圆形属性"},
                    "code": '''from core import Graph

# Circle Geometry Analysis
g = Graph("Circle Properties")

# Create parameter groups
g.create_group("inputs", "Input Parameters")
g.create_group("results", "Calculation Results")

# Basic parameters with groups
g["radius"] = 5.0      # 半径 (m)
g["pi"] = 3.14159      # 圆周率
g.set_group("radius", "inputs")
g.set_group("pi", "inputs")

# Calculation functions
def diameter_calc():
    return 2 * g["radius"]

def circumference_calc():
    return 2 * g["pi"] * g["radius"]

def area_calc():
    return g["pi"] * g["radius"] ** 2

# Add computed parameters with groups
g.add_computed("diameter", diameter_calc, "Diameter calculation")
g.add_computed("circumference", circumference_calc, "Circumference calculation") 
g.add_computed("area", area_calc, "Area calculation")
g.set_group("diameter", "results")
g.set_group("circumference", "results")
g.set_group("area", "results")

print(f"Diameter: {g['diameter']:.2f} m")
print(f"Circumference: {g['circumference']:.2f} m")
print(f"Area: {g['area']:.2f} m²")'''
                }
            }
        },
        "finance": {
            "name": {"en": "💰 Finance", "zh": "💰 金融投资"},
            "examples": {
                "investment": {
                    "name": {"en": "Investment Returns", "zh": "投资收益计算"},
                    "description": {"en": "Calculate compound interest and ROI", "zh": "计算复利和投资回报率"},
                    "code": '''from core import Graph

# Investment Analysis
g = Graph("Investment Calculator")

# Create logical parameter groups
g.create_group("inputs", "📊 Investment Inputs")
g.create_group("calculations", "🔢 Intermediate Calculations") 
g.create_group("results", "💎 Final Results")

# Basic parameters with groups
g["principal"] = 10000.0    # 本金 ($)
g["annual_rate"] = 0.08     # 年利率 (8%)
g["years"] = 5              # 投资年限
g["monthly_contribution"] = 500.0  # 月定投 ($)

# Assign inputs to group
g.set_group("principal", "inputs")
g.set_group("annual_rate", "inputs")
g.set_group("years", "inputs")
g.set_group("monthly_contribution", "inputs")

# Calculation functions
def compound_amount():
    return g["principal"] * (1 + g["annual_rate"]) ** g["years"]

def total_contributions():
    return g["monthly_contribution"] * 12 * g["years"]

def final_value():
    return g["compound_amount"] + g["total_contributions"] * 1.06  # 定投复利

def total_return():
    return g["final_value"] - g["principal"] - g["total_contributions"]

def roi_percentage():
    return (g["total_return"] / (g["principal"] + g["total_contributions"])) * 100

# Add computed parameters with groups
g.add_computed("compound_amount", compound_amount, "Compound interest on principal")
g.add_computed("total_contributions", total_contributions, "Total monthly contributions")
g.add_computed("final_value", final_value, "Final investment value")
g.add_computed("total_return", total_return, "Total profit")
g.add_computed("roi_percentage", roi_percentage, "Return on investment %")

# Assign calculated parameters to appropriate groups
g.set_group("compound_amount", "calculations")
g.set_group("total_contributions", "calculations")
g.set_group("final_value", "results")
g.set_group("total_return", "results")
g.set_group("roi_percentage", "results")

print(f"Final Value: ${g['final_value']:,.2f}")
print(f"Total Return: ${g['total_return']:,.2f}")
print(f"ROI: {g['roi_percentage']:.2f}%")'''
                }
            }
        },
        "physics": {
            "name": {"en": "⚡ Physics", "zh": "⚡ 物理工程"},
            "examples": {
                "mechanics": {
                    "name": {"en": "Projectile Motion", "zh": "抛物运动"},
                    "description": {"en": "Calculate trajectory and motion parameters", "zh": "计算轨迹和运动参数"},
                    "code": '''from core import Graph
import math

# Projectile Motion Analysis
g = Graph("Projectile Motion")

# Create parameter groups for better organization
g.create_group("launch_params", "🚀 Launch Parameters")
g.create_group("constants", "⚖️ Physical Constants")
g.create_group("velocity_components", "📐 Velocity Components")
g.create_group("motion_results", "🎯 Motion Results")

# Basic parameters
g["initial_velocity"] = 50.0    # 初始速度 (m/s)
g["launch_angle"] = 45.0        # 发射角度 (度)
g["gravity"] = 9.81             # 重力加速度 (m/s²)
g["mass"] = 2.0                 # 质量 (kg)

# Assign basic parameters to groups
g.set_group("initial_velocity", "launch_params")
g.set_group("launch_angle", "launch_params")
g.set_group("mass", "launch_params")
g.set_group("gravity", "constants")

# Calculation functions
def angle_radians():
    return g["launch_angle"] * math.pi / 180

def velocity_x():
    return g["initial_velocity"] * math.cos(g["angle_radians"])

def velocity_y():
    return g["initial_velocity"] * math.sin(g["angle_radians"])

def time_of_flight():
    return 2 * g["velocity_y"] / g["gravity"]

def max_height():
    return (g["velocity_y"] ** 2) / (2 * g["gravity"])

def range_distance():
    return g["velocity_x"] * g["time_of_flight"]

def kinetic_energy():
    return 0.5 * g["mass"] * g["initial_velocity"] ** 2

# Add computed parameters
g.add_computed("angle_radians", angle_radians, "Angle in radians")
g.add_computed("velocity_x", velocity_x, "Horizontal velocity component")
g.add_computed("velocity_y", velocity_y, "Vertical velocity component")
g.add_computed("time_of_flight", time_of_flight, "Total flight time")
g.add_computed("max_height", max_height, "Maximum height reached")
g.add_computed("range_distance", range_distance, "Horizontal range")
g.add_computed("kinetic_energy", kinetic_energy, "Initial kinetic energy")

# Assign computed parameters to logical groups
g.set_group("angle_radians", "constants")
g.set_group("velocity_x", "velocity_components")
g.set_group("velocity_y", "velocity_components")
g.set_group("time_of_flight", "motion_results")
g.set_group("max_height", "motion_results")
g.set_group("range_distance", "motion_results")
g.set_group("kinetic_energy", "motion_results")

print(f"Max Height: {g['max_height']:.2f} m")
print(f"Range: {g['range_distance']:.2f} m")
print(f"Flight Time: {g['time_of_flight']:.2f} s")'''
                },
                "circuit": {
                    "name": {"en": "Electric Circuit", "zh": "电路分析"},
                    "description": {"en": "Analyze electrical circuit parameters", "zh": "分析电路参数"},
                    "code": '''from core import Graph

# Circuit Analysis
g = Graph("Electric Circuit")

# Basic parameters
g["voltage"] = 12.0         # 电压 (V)
g["current"] = 2.0          # 电流 (A)
g["resistance"] = 6.0       # 电阻 (Ω)
g["time"] = 3600.0          # 时间 (s) - 1小时

# Calculation functions
def power_calculation():
    return g["voltage"] * g["current"]

def energy_calculation():
    return g["power"] * g["time"] / 3600  # Convert to Wh

def efficiency_calculation():
    ideal_power = g["voltage"] * g["current"]
    return (g["power"] / ideal_power) * 100

def cost_calculation():
    # Electricity cost at $0.12 per kWh
    return (g["energy"] / 1000) * 0.12

# Add computed parameters
g.add_computed("power", power_calculation, "Power consumption")
g.add_computed("energy", energy_calculation, "Energy consumed")
g.add_computed("efficiency", efficiency_calculation, "Circuit efficiency")
g.add_computed("cost", cost_calculation, "Electricity cost")

print(f"Power: {g['power']:.2f} W")
print(f"Energy: {g['energy']:.2f} Wh") 
print(f"Cost: ${g['cost']:.4f}")'''
                }
            }
        },
        "engineering": {
            "name": {"en": "🏗️ Engineering", "zh": "🏗️ 工程计算"},
            "examples": {
                "beam": {
                    "name": {"en": "Beam Analysis", "zh": "梁受力分析"},
                    "description": {"en": "Structural analysis of a simply supported beam", "zh": "简支梁结构分析"},
                    "code": '''from core import Graph

# Simply Supported Beam Analysis
g = Graph("Beam Structural Analysis")

# Basic parameters
g["length"] = 6.0           # 梁长度 (m)
g["load"] = 10000.0         # 均布荷载 (N/m)
g["elastic_modulus"] = 200000000000.0  # 弹性模量 (Pa)
g["moment_of_inertia"] = 0.0001  # 惯性矩 (m⁴)
g["material_density"] = 7850.0   # 材料密度 (kg/m³)
g["cross_section_area"] = 0.01   # 截面积 (m²)

# Calculation functions
def max_moment():
    # Maximum bending moment for uniformly distributed load
    return g["load"] * g["length"] ** 2 / 8

def max_shear():
    # Maximum shear force
    return g["load"] * g["length"] / 2

def max_deflection():
    # Maximum deflection at mid-span
    return (5 * g["load"] * g["length"] ** 4) / (384 * g["elastic_modulus"] * g["moment_of_inertia"])

def beam_weight():
    # Self weight of beam
    return g["material_density"] * g["cross_section_area"] * g["length"] * 9.81

def max_stress():
    # Maximum bending stress (assuming rectangular section)
    section_modulus = g["moment_of_inertia"] / 0.05  # assuming height = 0.1m
    return g["max_moment"] / section_modulus

def safety_factor():
    # Assuming material yield strength of 250 MPa
    yield_strength = 250000000.0
    return yield_strength / g["max_stress"]

# Add computed parameters
g.add_computed("max_moment", max_moment, "Maximum bending moment")
g.add_computed("max_shear", max_shear, "Maximum shear force")
g.add_computed("max_deflection", max_deflection, "Maximum deflection")
g.add_computed("beam_weight", beam_weight, "Beam self weight")
g.add_computed("max_stress", max_stress, "Maximum bending stress")
g.add_computed("safety_factor", safety_factor, "Safety factor")

print(f"Max Moment: {g['max_moment']:,.0f} N·m")
print(f"Max Deflection: {g['max_deflection']:.4f} m")
print(f"Safety Factor: {g['safety_factor']:.2f}")'''
                }
            }
        },
        "chemistry": {
            "name": {"en": "🧪 Chemistry", "zh": "🧪 化学计算"},
            "examples": {
                "reaction": {
                    "name": {"en": "Chemical Reaction", "zh": "化学反应"},
                    "description": {"en": "Calculate reaction rates and concentrations", "zh": "计算反应速率和浓度"},
                    "code": '''from core import Graph
import math

# Chemical Reaction Kinetics
g = Graph("Chemical Reaction Analysis")

# Basic parameters
g["initial_concentration"] = 2.0     # 初始浓度 (mol/L)
g["rate_constant"] = 0.05            # 反应速率常数 (1/s)
g["time"] = 60.0                     # 反应时间 (s)
g["temperature"] = 298.15            # 温度 (K)
g["activation_energy"] = 50000.0     # 活化能 (J/mol)
g["gas_constant"] = 8.314            # 气体常数 (J/mol·K)

# Calculation functions
def concentration_remaining():
    # First-order reaction kinetics: C = C₀ * e^(-kt)
    return g["initial_concentration"] * math.exp(-g["rate_constant"] * g["time"])

def concentration_consumed():
    return g["initial_concentration"] - g["concentration_remaining"]

def half_life():
    # Half-life for first-order reaction
    return math.log(2) / g["rate_constant"]

def reaction_rate():
    # Instantaneous reaction rate
    return g["rate_constant"] * g["concentration_remaining"]

def arrhenius_factor():
    # Temperature dependence factor
    return math.exp(-g["activation_energy"] / (g["gas_constant"] * g["temperature"]))

def percent_completion():
    return (g["concentration_consumed"] / g["initial_concentration"]) * 100

# Add computed parameters
g.add_computed("concentration_remaining", concentration_remaining, "Remaining concentration")
g.add_computed("concentration_consumed", concentration_consumed, "Consumed concentration")
g.add_computed("half_life", half_life, "Reaction half-life")
g.add_computed("reaction_rate", reaction_rate, "Current reaction rate")
g.add_computed("arrhenius_factor", arrhenius_factor, "Arrhenius temperature factor")
g.add_computed("percent_completion", percent_completion, "Reaction completion percentage")

print(f"Remaining: {g['concentration_remaining']:.3f} mol/L")
print(f"Half-life: {g['half_life']:.1f} s")
print(f"Completion: {g['percent_completion']:.1f}%")'''
                }
            }
        }
    }

def get_sample_code(category="physics", example="circuit"):
    """Get sample code by category and example name"""
    examples = get_sample_examples()
    try:
        return examples[category]["examples"][example]["code"]
    except KeyError:
        # Default fallback to circuit example
        return examples["physics"]["examples"]["circuit"]["code"]


def calculate_dependency_levels(parameters: Dict, dependencies: Dict) -> Dict:
    """Calculate dependency level for each node using topological analysis"""
    levels = {}
    
    # Identify basic parameters (level 0)
    basic_params = set()
    for param_name, param_info in parameters.items():
        if param_info["type"] == "basic":
            basic_params.add(param_name)
            levels[param_name] = 0
    
    # Build reverse dependency graph for easier traversal
    dependents = {}  # param -> [nodes that depend on it]
    for param, deps in dependencies.items():
        for dep in deps:
            if dep not in dependents:
                dependents[dep] = []
            dependents[dep].append(param)
    
    # Use BFS to assign levels
    from collections import deque
    queue = deque(basic_params)
    
    while queue:
        current_param = queue.popleft()
        current_level = levels[current_param]
        
        # Process all nodes that depend on current_param
        if current_param in dependents:
            for dependent in dependents[current_param]:
                # Calculate the maximum level requirement for this dependent
                required_level = current_level + 1
                
                # Check if all dependencies of this dependent have been processed
                all_deps_processed = True
                max_dependency_level = 0
                
                if dependent in dependencies:
                    for dep in dependencies[dependent]:
                        if dep not in levels:
                            all_deps_processed = False
                            break
                        max_dependency_level = max(max_dependency_level, levels[dep])
                
                # If all dependencies are processed, assign level
                if all_deps_processed:
                    final_level = max_dependency_level + 1
                    if dependent not in levels or levels[dependent] < final_level:
                        levels[dependent] = final_level
                        queue.append(dependent)
    
    # Handle any remaining unprocessed nodes (circular dependencies or isolated nodes)
    for param_name in parameters:
        if param_name not in levels:
            if param_name in dependencies and dependencies[param_name]:
                # Try to assign based on maximum dependency level
                max_dep_level = 0
                for dep in dependencies[param_name]:
                    if dep in levels:
                        max_dep_level = max(max_dep_level, levels[dep])
                levels[param_name] = max_dep_level + 1
            else:
                # Isolated node or no dependencies
                levels[param_name] = 0
    
    return levels

def calculate_layout(parameters: Dict, dependencies: Dict, groups: Dict = None, parameter_groups: Dict = None) -> Dict:
    """Calculate node positions using dependency-level-based columnar layout with group support"""
    positions = {}
    group_positions = {}  # Store group container positions
    
    if not parameters:
        return positions
    
    # If no groups are defined, use the original layout
    if not groups or not parameter_groups:
        return calculate_layout_original(parameters, dependencies)
    
    # Calculate dependency levels for each node
    levels = calculate_dependency_levels(parameters, dependencies)
    
    # Separate grouped and ungrouped parameters
    grouped_params = {}  # group_name -> [param_names]
    ungrouped_params = []
    
    for param_name in parameters:
        group_name = parameter_groups.get(param_name)
        if group_name and group_name in groups:
            if group_name not in grouped_params:
                grouped_params[group_name] = []
            grouped_params[group_name].append(param_name)
        else:
            ungrouped_params.append(param_name)
    
    # Group nodes by level, considering groups as single units
    level_groups = {}
    max_level = max(levels.values()) if levels else 0
    
    # Add groups to level_groups based on their parameters' levels
    for group_name, param_names in grouped_params.items():
        # Find the minimum level of all parameters in the group
        group_level = min(levels[param] for param in param_names)
        if group_level not in level_groups:
            level_groups[group_level] = []
        level_groups[group_level].append(('group', group_name, param_names))
    
    # Add ungrouped parameters
    for param_name in ungrouped_params:
        level = levels[param_name]
        if level not in level_groups:
            level_groups[level] = []
        level_groups[level].append(('param', param_name, None))
    
    # Calculate layout parameters
    node_height = 1.8  # Height spacing between individual nodes (increased to prevent overlap)
    group_padding = 0.4  # Padding inside groups
    group_margin = 0.8  # Margin between groups and individual nodes (increased)
    column_width = 5.5  # Width spacing between columns (increased for wider nodes)
    start_x = -2.5  # Starting X position
    
    # Position nodes level by level (column by column)
    for level in range(max_level + 1):
        if level not in level_groups:
            continue
            
        items_in_level = level_groups[level]
        column_x = start_x + level * column_width
        
        # Calculate total height needed for this column
        total_height = 0
        for item_type, item_name, param_names in items_in_level:
            if item_type == 'group':
                # Group height = number of parameters * node_height + padding
                group_height = len(param_names) * node_height + 2 * group_padding
                total_height += group_height + group_margin
            else:
                # Individual parameter
                total_height += node_height + group_margin
        
        # Remove the last margin
        total_height -= group_margin
        
        # Start positioning from the top
        current_y = total_height / 2
        
        for item_type, item_name, param_names in items_in_level:
            if item_type == 'group':
                # Position group parameters vertically within the group
                group_height = len(param_names) * node_height + 2 * group_padding
                group_center_y = current_y - group_height / 2
                
                # Store group position for visual rendering
                group_positions[item_name] = {
                    'x': column_x,
                    'y': group_center_y,
                    'width': 3.0,  # Will be calculated based on content
                    'height': group_height
                }
                
                # Position individual parameters within the group
                param_start_y = current_y - group_padding
                for i, param_name in enumerate(param_names):
                    param_y = param_start_y - (i + 0.5) * node_height
                    positions[param_name] = (column_x, param_y)
                
                current_y -= group_height + group_margin
            else:
                # Individual parameter
                param_y = current_y - node_height / 2
                positions[item_name] = (column_x, param_y)
                current_y -= node_height + group_margin
    
    return positions, group_positions

def calculate_layout_original(parameters: Dict, dependencies: Dict) -> Dict:
    """Original layout algorithm for backward compatibility"""
    positions = {}
    
    if not parameters:
        return positions
    
    # Calculate dependency levels for each node
    levels = calculate_dependency_levels(parameters, dependencies)
    
    # Group nodes by level
    level_groups = {}
    max_level = max(levels.values()) if levels else 0
    
    for param_name, level in levels.items():
        if level not in level_groups:
            level_groups[level] = []
        level_groups[level].append(param_name)
    
    # Calculate layout parameters
    node_height = 1.6  # Height spacing between nodes
    column_width = 4.5  # Width spacing between columns
    start_x = -2.5  # Starting X position
    
    # Position nodes level by level (column by column)
    for level in range(max_level + 1):
        if level not in level_groups:
            continue
            
        nodes_in_level = level_groups[level]
        column_x = start_x + level * column_width
        
        # Center nodes vertically in each column
        for i, param_name in enumerate(nodes_in_level):
            y = -(len(nodes_in_level) - 1) * node_height / 2 + i * node_height
            positions[param_name] = (column_x, y)
    
    return positions


def calculate_node_width(param_name: str, param_info: Dict) -> float:
    """Calculate dynamic rectangle width based on text content"""
    value_str = str(param_info["value"])
    if len(value_str) > 12:
        value_str = value_str[:12] + "..."
    
    # Calculate text content length: "param_name: value"
    text_content = f"{param_name}: {value_str}"
    text_length = len(text_content)
    
    # Dynamic width calculation: base width + character-based scaling
    base_width = 2.5
    char_width_factor = 0.08  # Adjust this for different font sizes
    calculated_width = base_width + (text_length * char_width_factor)
    return max(2.5, min(5.0, calculated_width))  # Constrain between 2.5 and 5.0

def calculate_shared_widths(parameters: Dict, groups: Dict, parameter_groups: Dict, positions: Dict) -> Dict:
    """Calculate shared widths for parameters in same group or same column"""
    widths = {}
    
    # Calculate individual widths first
    individual_widths = {}
    for param_name, param_info in parameters.items():
        individual_widths[param_name] = calculate_node_width(param_name, param_info)
    
    # Group parameters by column (same X position)
    columns = {}
    for param_name, (x, y) in positions.items():
        if x not in columns:
            columns[x] = []
        columns[x].append(param_name)
    
    # Group parameters by group
    grouped_params = {}
    for param_name, group_name in parameter_groups.items():
        if group_name not in grouped_params:
            grouped_params[group_name] = []
        grouped_params[group_name].append(param_name)
    
    # Calculate shared widths
    for param_name in parameters:
        max_width = individual_widths[param_name]
        
        # Find parameters in same group
        group_name = parameter_groups.get(param_name)
        if group_name and group_name in grouped_params:
            for group_param in grouped_params[group_name]:
                if group_param in individual_widths:
                    max_width = max(max_width, individual_widths[group_param])
        
        # Find parameters in same column
        param_x = positions[param_name][0]
        for column_param in columns.get(param_x, []):
            if column_param in individual_widths:
                max_width = max(max_width, individual_widths[column_param])
        
        widths[param_name] = max_width
    
    return widths

def get_group_colors():
    """Return a list of distinct colors for different groups"""
    return [
        'rgba(74, 144, 226, 0.95)',   # Blue
        'rgba(231, 76, 60, 0.95)',    # Red  
        'rgba(46, 204, 113, 0.95)',   # Green
        'rgba(241, 196, 15, 0.95)',   # Yellow
        'rgba(155, 89, 182, 0.95)',   # Purple
        'rgba(230, 126, 34, 0.95)',   # Orange
        'rgba(52, 152, 219, 0.95)',   # Light Blue
        'rgba(26, 188, 156, 0.95)',   # Turquoise
        'rgba(192, 57, 43, 0.95)',    # Dark Red
        'rgba(142, 68, 173, 0.95)',   # Dark Purple
    ]

def assign_group_colors(groups: Dict, parameter_groups: Dict) -> Dict:
    """Assign colors to groups and return color mapping for parameters"""
    colors = get_group_colors()
    group_color_map = {}
    param_color_map = {}
    
    # Assign colors to groups
    for i, group_name in enumerate(groups.keys()):
        group_color_map[group_name] = colors[i % len(colors)]
    
    # Assign colors to parameters based on their groups
    for param_name, group_name in parameter_groups.items():
        if group_name in group_color_map:
            param_color_map[param_name] = group_color_map[group_name]
        else:
            param_color_map[param_name] = 'rgba(99, 110, 125, 0.95)'  # Default color
    
    # Assign default color to ungrouped parameters
    return param_color_map, group_color_map

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
    
    # Calculate positions with group support
    groups = graph_data.get("groups", {})
    parameter_groups = graph_data.get("parameter_groups", {})
    
    if groups and parameter_groups:
        positions, group_positions = calculate_layout(parameters, dependencies, groups, parameter_groups)
        # Calculate shared widths and colors for grouped parameters
        shared_widths = calculate_shared_widths(parameters, groups, parameter_groups, positions)
        param_colors, group_colors = assign_group_colors(groups, parameter_groups)
    else:
        positions = calculate_layout_original(parameters, dependencies)
        group_positions = {}
        # Use individual widths and default colors for ungrouped parameters
        shared_widths = {name: calculate_node_width(name, info) for name, info in parameters.items()}
        param_colors = {name: 'rgba(99, 110, 125, 0.95)' for name in parameters}
        group_colors = {}
    
    # Create figure
    fig = go.Figure()
    
    # Add group containers first (behind everything)
    for group_name, group_pos in group_positions.items():
        group_info = groups.get(group_name, {})
        group_description = group_info.get('description', group_name)
        
        # Calculate group width based on shared width of contained parameters
        group_width = 3.5  # Base width
        for param_name in group_info.get('parameters', []):
            if param_name in shared_widths:
                param_width = shared_widths[param_name]
                group_width = max(group_width, param_width + 0.8)  # Add padding
        
        # Get group color (lighter version for background)
        group_color = group_colors.get(group_name, 'rgba(100, 150, 200, 0.6)')
        # Convert to lighter background color
        if group_color.startswith('rgba('):
            # Extract RGB values and make lighter
            rgb_part = group_color[5:-1].split(',')
            r, g, b = int(rgb_part[0]), int(rgb_part[1]), int(rgb_part[2])
            # Lighten the color for background
            bg_color = f'rgba({r}, {g}, {b}, 0.15)'
            border_color = f'rgba({r}, {g}, {b}, 0.6)'
            text_color = f'rgba({max(0, r-30)}, {max(0, g-30)}, {max(0, b-30)}, 0.9)'
        else:
            bg_color = 'rgba(220, 230, 240, 0.15)'
            border_color = 'rgba(100, 150, 200, 0.6)'
            text_color = 'rgba(70, 120, 170, 0.9)'
        
        # Draw group container rectangle
        fig.add_shape(
            type="rect",
            x0=group_pos['x'] - group_width/2,
            y0=group_pos['y'] - group_pos['height']/2,
            x1=group_pos['x'] + group_width/2,
            y1=group_pos['y'] + group_pos['height']/2,
            fillcolor=bg_color,
            line=dict(color=border_color, width=2, dash='dash'),
            layer="below"
        )
        
        # Add group title
        fig.add_annotation(
            x=group_pos['x'],
            y=group_pos['y'] + group_pos['height']/2 + 0.3,
            text=f"<b>{group_description}</b>",
            showarrow=False,
            font=dict(size=13, color=text_color),
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor=border_color,
            borderwidth=1
        )
    
    # Add edges with arrows from right pin to left pin
    for param_name, deps in dependencies.items():
        if param_name in positions:
            end_pos = positions[param_name]
            for dep in deps:
                if dep in positions:
                    start_pos = positions[dep]
                    
                    # Calculate dynamic pin positions based on shared widths
                    start_width = shared_widths.get(dep, 3.0)
                    end_width = shared_widths.get(param_name, 3.0)
                    rect_height = 0.8
                    
                    # Start from right side pin of source node
                    start_x = start_pos[0] + start_width/2
                    start_y = start_pos[1]
                    
                    # End at left side pin of target node
                    end_x = end_pos[0] - end_width/2
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
        
        # Use shared width for consistent appearance
        width = shared_widths.get(param_name, 3.0)
        height = 0.8
        
        # Get color based on group membership
        fill_color = param_colors.get(param_name, 'rgba(99, 110, 125, 0.95)')
        
        # Add modern styled rectangle with group-based colors
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
        print("   • Monaco Editor with Python syntax highlighting")
        print("   • Interactive node dragging and context menus") 
        print("   • Hover effects and detailed tooltips")
        print("   • Smart dependency-level layout")
        print("   • Bezier curve arrows and dynamic node sizing")
        print("   • Manual graph updates (auto-update disabled)")
        print("")
        
        # Create Dash app
        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        parser = PlotlyCodeParser()
        
        # App layout
        app.layout = dbc.Container([
            # Header with language selector
            dbc.Row([
                dbc.Col([
                    html.H1(id="app-title", children="Plotly Graph Visualizer - Online Mode", 
                           className="text-center mb-4",
                           style={'color': '#2c3e50', 'fontWeight': 'bold'})
                ], width=8),
                dbc.Col([
                    html.Div([
                        html.Label("🌐", className="me-2", style={'fontSize': '20px'}),
                        dcc.Dropdown(
                            id='language-selector',
                            options=[
                                {'label': f"{lang['flag']} {lang['name']}", 'value': lang['code']}
                                for lang in get_available_languages()
                            ],
                            value='en',
                            clearable=False,
                            style={'minWidth': '150px', 'fontSize': '14px'}
                        )
                    ], style={'textAlign': 'right', 'marginTop': '20px'})
                ], width=4)
            ], className="mb-3"),
            
            # Main content
            dbc.Row([
                # Left panel: Graph visualization
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H4(id="graph-title", children="Interactive Dependency Graph", className="mb-0", style={'color': '#34495e'})
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
                            html.H4(id="editor-title", children="Code Editor", className="mb-0", style={'color': '#34495e'})
                        ]),
                        dbc.CardBody([
                            # Controls at the top
                            html.Div([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Button("Refresh Graph", id="refresh-btn", color="primary", className="me-2"),
                                        dbc.Button("Clear Code", id="clear-btn", color="warning", className="me-2"),
                                        dbc.Button("Save HTML", id="save-btn", color="info")
                                    ], width=7),
                                    dbc.Col([
                                        html.Label(id="examples-label", children="📚 Examples", className="mb-1", style={'fontSize': '14px', 'fontWeight': 'bold'}),
                                        dcc.Dropdown(
                                            id='example-selector',
                                            placeholder="Select an example...",
                                            clearable=False,
                                            style={'fontSize': '13px'}
                                        )
                                    ], width=5)
                                ])
                            ], className="mb-3"),
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
                            )
                        ])
                    ], style={'border': '2px solid #95a5a6'})
                ], width=5)
            ], className="mb-4"),
            
            # Status panel
            dbc.Row([
                dbc.Col([
                    html.Div(id="status-info", children=[
                        dbc.Alert("🚀 Online Mode: Interactive visualization with Monaco Editor. Use 'Refresh Graph' button to update!", 
                                color="info", className="mb-0")
                    ])
                ])
            ]),
            
            # Real-time preview control (currently disabled)
            dcc.Interval(
                id='realtime-interval',
                interval=1000,  # Check every second
                n_intervals=0,
                disabled=True  # Disabled - manual updates only
            ),
            
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
            
            # Confirmation modal for example switching
            dbc.Modal([
                dbc.ModalHeader([
                    dbc.ModalTitle(id="confirm-modal-title", children="Overwrite Current Code?")
                ]),
                dbc.ModalBody([
                    html.P(id="confirm-modal-message", children="Loading this example will replace your current code. Are you sure you want to continue?")
                ]),
                dbc.ModalFooter([
                    dbc.Button(id="confirm-yes-btn", children="Yes, Replace Code", color="primary", className="me-2"),
                    dbc.Button(id="confirm-no-btn", children="Cancel", color="secondary")
                ])
            ], id="confirm-modal", is_open=False),
            
            # Hidden storage for graph data and selected node
            html.Div(id='graph-data-store', style={'display': 'none'}),
            html.Div(id='selected-node-store', style={'display': 'none'}),
            html.Div(id='current-code-store', style={'display': 'none'}),
            html.Div(id='pending-example-store', style={'display': 'none'}),  # Store pending example selection
            dcc.Store(id='language-store', data='en')  # Default language
            
        ], fluid=True, style={'backgroundColor': '#ecf0f1', 'minHeight': '100vh', 'padding': '20px'})
        
        # Language selector callback
        @app.callback(
            Output('language-store', 'data'),
            [Input('language-selector', 'value')]
        )
        def update_language(selected_language):
            return selected_language or 'en'
        
        # Update UI text based on language
        @app.callback(
            [Output('app-title', 'children'),
             Output('graph-title', 'children'),
             Output('editor-title', 'children'),
             Output('examples-label', 'children'),
             Output('example-selector', 'placeholder'),
             Output('refresh-btn', 'children'),
             Output('clear-btn', 'children'),
             Output('save-btn', 'children')],
            [Input('language-store', 'data')]
        )
        def update_ui_text(language):
            return (
                get_translation('app_title', language),
                get_translation('dependency_graph', language),
                get_translation('code_editor', language),
                f"📚 {get_translation('examples', language)}",
                get_translation('select_example', language),
                get_translation('refresh_graph', language),
                get_translation('clear_code', language),
                get_translation('save_html', language)
            )
        
        # Update context menu text
        @app.callback(
            [Output('jump-to-code-btn', 'children'),
             Output('copy-name-btn', 'children'),
             Output('close-menu-btn', 'children')],
            [Input('language-store', 'data')]
        )
        def update_context_menu_text(language):
            return (
                get_translation('jump_to_code', language),
                get_translation('copy_name', language),
                get_translation('close', language)
            )
        
        # Update confirmation modal text
        @app.callback(
            [Output('confirm-modal-title', 'children'),
             Output('confirm-modal-message', 'children'),
             Output('confirm-yes-btn', 'children'),
             Output('confirm-no-btn', 'children')],
            [Input('language-store', 'data')]
        )
        def update_modal_text(language):
            return (
                get_translation('confirm_example_title', language),
                get_translation('confirm_example_message', language),
                get_translation('confirm_yes', language),
                get_translation('confirm_no', language)
            )
        
        # Update example selector options based on language
        @app.callback(
            Output('example-selector', 'options'),
            [Input('language-store', 'data')]
        )
        def update_example_options(language):
            language = language or 'en'
            examples = get_sample_examples()
            options = []
            
            for category_key, category_data in examples.items():
                category_name = category_data["name"][language]
                
                for example_key, example_data in category_data["examples"].items():
                    example_name = example_data["name"][language]
                    example_desc = example_data["description"][language]
                    
                    options.append({
                        'label': f"{category_name} → {example_name}",
                        'value': f"{category_key}:{example_key}",
                        'title': example_desc  # Tooltip description
                    })
            
            return options

        # Callbacks
        @app.callback(
            [Output('dependency-graph', 'figure'),
             Output('status-info', 'children'),
             Output('graph-data-store', 'children')],
            [Input('refresh-btn', 'n_clicks'),
             Input('clear-btn', 'n_clicks'),
             Input('save-btn', 'n_clicks'),
             Input('realtime-interval', 'n_intervals'),
             Input('current-code-store', 'children')],  # Monaco Editor code
            [State('code-editor', 'value'),
             State('language-store', 'data')]
        )
        def update_graph(refresh_clicks, clear_clicks, save_clicks, realtime_intervals, monaco_code, code_value, language):
            ctx = callback_context
            
            # Initialize debouncing storage if it doesn't exist
            if not hasattr(update_graph, 'last_code'):
                update_graph.last_code = ""
                update_graph.last_update_time = 0
            
            import time
            current_time = time.time()
            
            # Initialize trigger_id to avoid UnboundLocalError
            trigger_id = 'initial'
            force_update = True
            
            if not ctx.triggered:
                code = code_value or get_sample_code()
                trigger_id = 'initial'
            else:
                trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
                force_update = trigger_id != 'realtime-interval'
                
                if trigger_id == 'clear-btn':
                    code = ""
                    # Force update for manual actions
                    update_graph.last_code = "non-empty"  # Reset to force update
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
                        return fig, dbc.Alert(f"✅ {get_translation('graph_saved', language or 'en')} {html_file}", color="success"), json.dumps(graph_data)
                    else:
                        return create_plotly_figure(graph_data), dbc.Alert(f"❌ {get_translation('cannot_save', language or 'en')}", color="danger"), json.dumps(graph_data)
                elif trigger_id == 'refresh-btn' or trigger_id == 'current-code-store':
                    # Force update for manual refresh - use Monaco Editor code directly
                    code = monaco_code or code_value or ""
                    # Force complete reset of debouncing state 
                    update_graph.last_code = None  # Force different value
                    update_graph.last_update_time = 0  # Reset time
                elif trigger_id == 'realtime-interval':
                    # Real-time update with smart debouncing (disabled)
                    code = code_value or ""
                    
                    # Smart debouncing: only update if code actually changed
                    if code == update_graph.last_code:
                        # Code hasn't changed, no need to update
                        from dash import no_update
                        return no_update, no_update, no_update
                    
                    # Additional time-based debouncing for rapid changes
                    if current_time - update_graph.last_update_time < 2.0:
                        # Too soon since last update, wait longer
                        from dash import no_update
                        return no_update, no_update, no_update
                    
                    # Code has changed and enough time passed - proceed with update
                    update_graph.last_code = code
                    update_graph.last_update_time = current_time
                else:
                    # Handle other manual updates
                    code = code_value or ""
            
            # Parse and create figure
            graph_data = parser.parse_code(code)
            fig = create_plotly_figure(graph_data)
            
            # Status message with i18n
            language = language or 'en'
            if graph_data and graph_data.get("success", False):
                params = graph_data["parameters"]
                basic_count = sum(1 for p in params.values() if p["type"] == "basic")
                computed_count = sum(1 for p in params.values() if p["type"] == "computed")
                
                status = dbc.Alert([
                    html.Strong(f"✅ {get_translation('graph_updated_success', language)} "),
                    get_translation('found_parameters', language, 
                                  count=len(params), basic=basic_count, computed=computed_count),
                    html.Br(),
                    html.Small(f"🔄 {get_translation('edit_code_hint', language)} "),
                    html.Small(f"💡 {get_translation('interaction_hints', language)}")
                ], color="success")
            elif graph_data:
                status = dbc.Alert([
                    html.Strong(f"❌ {get_translation('parse_error', language)}: "),
                    graph_data.get("error", "Unknown error")
                ], color="danger")
            else:
                status = dbc.Alert(get_translation('enter_graph_code', language), color="info")
            
            # Update last_code for future debouncing (except for refresh-btn which resets it)
            if trigger_id != 'refresh-btn':
                update_graph.last_code = code
            
            import json
            return fig, status, json.dumps(graph_data)
        
        # Handle refresh button with direct Monaco Editor access
        app.clientside_callback(
            """
            function(refresh_clicks) {
                if (refresh_clicks && window.monacoEditor) {
                    // Get current code from Monaco Editor
                    const currentCode = window.monacoEditor.getValue();
                    
                    // Store in a global variable for server access
                    window.currentMonacoCode = currentCode;
                    
                    // Force sync to hidden textarea
                    const hiddenTextarea = document.getElementById('code-editor');
                    if (hiddenTextarea) {
                        hiddenTextarea.value = currentCode;
                        hiddenTextarea.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                    
                    // Trigger a manual refresh by updating a dummy store
                    return currentCode;
                }
                return window.dash_clientside.no_update;
            }
            """,
            Output('current-code-store', 'children'),
            [Input('refresh-btn', 'n_clicks')]
        )
        
        # Handle example selection - show confirmation dialog
        @app.callback(
            [Output('confirm-modal', 'is_open'),
             Output('pending-example-store', 'children')],
            [Input('example-selector', 'value')],
            [State('confirm-modal', 'is_open')],
            prevent_initial_call=True
        )
        def show_confirmation_dialog(example_value, is_open):
            if example_value and not is_open:
                # Store the pending example selection and show modal
                return True, example_value
            return False, ""
        
        # Handle modal close and code loading
        @app.callback(
            [Output('confirm-modal', 'is_open', allow_duplicate=True),
             Output('code-editor', 'value')],
            [Input('confirm-yes-btn', 'n_clicks'),
             Input('confirm-no-btn', 'n_clicks')],
            [State('pending-example-store', 'children'),
             State('code-editor', 'value')],
            prevent_initial_call=True
        )
        def handle_modal_response(yes_clicks, no_clicks, pending_example, current_code):
            from dash import no_update
            ctx = callback_context
            if not ctx.triggered:
                return no_update, no_update
            
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if trigger_id == 'confirm-yes-btn' and pending_example:
                # User confirmed - load the example code and close modal
                try:
                    category, example = pending_example.split(':')
                    example_code = get_sample_code(category, example)
                    return False, example_code  # Close modal, load code
                except (ValueError, KeyError):
                    return False, get_sample_code()  # Close modal, load default
                    
            elif trigger_id == 'confirm-no-btn':
                # User cancelled - close modal, keep current code
                return False, no_update  # Close modal, keep current code
            
            return no_update, no_update
        
        
        # Handle dropdown reset when cancelled
        app.clientside_callback(
            """
            function(no_clicks) {
                if (no_clicks) {
                    // Reset dropdown selection when user cancels
                    return null;
                }
                return window.dash_clientside.no_update;
            }
            """,
            Output('example-selector', 'value'),
            [Input('confirm-no-btn', 'n_clicks')]
        )
        
        # Handle confirmed example loading with Monaco Editor
        app.clientside_callback(
            """
            function(code_value) {
                if (code_value && window.monacoEditor) {
                    // Get the code from Python backend via hidden textarea
                    const hiddenTextarea = document.getElementById('code-editor');
                    if (hiddenTextarea && hiddenTextarea.value !== window.monacoEditor.getValue()) {
                        // Only update if the code is different to avoid unnecessary changes
                        window.monacoEditor.setValue(hiddenTextarea.value);
                    }
                }
                return window.dash_clientside.no_update;
            }
            """,
            Output('example-selector', 'style'),
            [Input('code-editor', 'value')]
        )
        
        # Auto-refresh after example confirmation
        app.clientside_callback(
            """
            function(code_value) {
                // Check if this is from example loading (code change after confirmation)
                if (code_value && window.autoRefreshPending) {
                    window.autoRefreshPending = false;
                    
                    setTimeout(() => {
                        // Store current code for refresh
                        if (window.monacoEditor) {
                            const currentCode = window.monacoEditor.getValue();
                            window.currentMonacoCode = currentCode;
                            
                            // Force sync to hidden textarea
                            const hiddenTextarea = document.getElementById('code-editor');
                            if (hiddenTextarea) {
                                hiddenTextarea.value = currentCode;
                                hiddenTextarea.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                            
                            // Auto-click refresh button
                            const refreshBtn = document.getElementById('refresh-btn');
                            if (refreshBtn) {
                                refreshBtn.click();
                            }
                        }
                    }, 100);
                }
                return window.dash_clientside.no_update;
            }
            """,
            Output('confirm-yes-btn', 'style'),
            [Input('code-editor', 'value')]
        )
        
        # Set auto-refresh pending flag when user confirms
        app.clientside_callback(
            """
            function(yes_clicks) {
                if (yes_clicks) {
                    window.autoRefreshPending = true;
                }
                return window.dash_clientside.no_update;
            }
            """,
            Output('pending-example-store', 'style'),
            [Input('confirm-yes-btn', 'n_clicks')]
        )
        
        # Handle clear button with Monaco Editor
        app.clientside_callback(
            """
            function(clear_clicks) {
                if (clear_clicks && window.monacoEditor) {
                    window.monacoEditor.setValue('');
                }
                return window.dash_clientside.no_update;
            }
            """,
            Output('clear-btn', 'style'),
            [Input('clear-btn', 'n_clicks')]
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
                            
                            // Real-time content sync with smart change detection
                            let syncTimeout;
                            let lastContentHash = '';
                            
                            function getContentHash(content) {
                                // Simple hash function for content comparison
                                let hash = 0;
                                for (let i = 0; i < content.length; i++) {
                                    const char = content.charCodeAt(i);
                                    hash = ((hash << 5) - hash) + char;
                                    hash = hash & hash; // Convert to 32-bit integer
                                }
                                return hash.toString();
                            }
                            
                            window.monacoEditor.onDidChangeModelContent(function() {
                                // Immediate sync for Dash state
                                syncWithTextarea();
                                
                                // Check if content actually changed meaningfully
                                const currentContent = window.monacoEditor.getValue();
                                const currentHash = getContentHash(currentContent.trim());
                                
                                if (currentHash !== lastContentHash) {
                                    lastContentHash = currentHash;
                                    
                                    // Visual feedback for code changes (manual update mode)
                                    const statusElement = document.querySelector('#status-info .alert');
                                    if (statusElement && !statusElement.classList.contains('alert-warning')) {
                                        statusElement.innerHTML = '<strong>📝 Code changed - click "Refresh Graph" to update visualization</strong>';
                                        statusElement.className = statusElement.className.replace('alert-success', 'alert-warning').replace('alert-danger', 'alert-warning');
                                        
                                        clearTimeout(syncTimeout);
                                        syncTimeout = setTimeout(() => {
                                            // Reset visual feedback after delay
                                            statusElement.className = statusElement.className.replace('alert-warning', 'alert-info');
                                        }, 5000);  // Longer timeout for manual mode
                                    }
                                }
                            });
                            
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
        Timer(1.5, lambda: webbrowser.open('http://127.0.0.1:8056')).start()
        
        print("🌐 Opening browser at: http://127.0.0.1:8056")
        print("🔧 Manual update mode ENABLED!")
        print("💡 Tips:")
        print("   - Edit code in Monaco Editor with syntax highlighting")
        print("   - Click 'Refresh Graph' button to update visualization")
        print("   - Click nodes for context menu, hover for details")
        print("   - Use 'Load Sample' and 'Clear Code' for quick actions")
        
        app.run(debug=False, host='127.0.0.1', port=8056)
        
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