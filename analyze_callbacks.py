#!/usr/bin/env python3
"""
Analyze all callbacks in app.py to understand their structure and relationships
"""
import re
import ast

def extract_callbacks_info(file_path):
    """Extract callback information from app.py"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all callback decorators and their functions
    callback_pattern = r'@callback\((.*?)\)\s*def\s+(\w+)\((.*?)\):'
    callbacks = []
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if line.strip().startswith('@callback'):
            # Extract callback decorator and function
            callback_start = i
            
            # Find the end of the decorator (could be multi-line)
            decorator_lines = []
            j = i
            paren_count = 0
            in_decorator = False
            
            while j < len(lines):
                current_line = lines[j].strip()
                if current_line.startswith('@callback'):
                    in_decorator = True
                
                if in_decorator:
                    decorator_lines.append(current_line)
                    paren_count += current_line.count('(') - current_line.count(')')
                    
                    if paren_count == 0 and current_line.endswith(')'):
                        break
                j += 1
            
            # Find function definition
            func_line_idx = j + 1
            while func_line_idx < len(lines) and not lines[func_line_idx].strip().startswith('def'):
                func_line_idx += 1
            
            if func_line_idx < len(lines):
                func_line = lines[func_line_idx].strip()
                func_match = re.match(r'def\s+(\w+)\((.*?)\):', func_line)
                if func_match:
                    func_name = func_match.group(1)
                    func_params = func_match.group(2)
                    
                    # Extract outputs and inputs from decorator
                    decorator_text = ' '.join(decorator_lines)
                    
                    # Extract outputs
                    output_pattern = r'Output\((.*?)\)'
                    outputs = re.findall(output_pattern, decorator_text)
                    
                    # Extract inputs
                    input_pattern = r'Input\((.*?)\)'
                    inputs = re.findall(input_pattern, decorator_text)
                    
                    # Extract states
                    state_pattern = r'State\((.*?)\)'
                    states = re.findall(state_pattern, decorator_text)
                    
                    callbacks.append({
                        'line': callback_start + 1,
                        'name': func_name,
                        'params': func_params,
                        'outputs': outputs,
                        'inputs': inputs,
                        'states': states,
                        'decorator': decorator_text
                    })
    
    return callbacks

def analyze_callback_relationships(callbacks):
    """Analyze relationships between callbacks"""
    relationships = []
    
    # Create a mapping of component IDs to callbacks
    component_to_callbacks = {}
    
    for callback in callbacks:
        # Track what components this callback outputs to
        for output in callback['outputs']:
            # Extract component ID from output
            match = re.search(r'"([^"]+)"', output)
            if match:
                comp_id = match.group(1)
                if comp_id not in component_to_callbacks:
                    component_to_callbacks[comp_id] = {'outputs_to': [], 'inputs_from': []}
                component_to_callbacks[comp_id]['outputs_to'].append(callback['name'])
        
        # Track what components this callback inputs from
        for input_item in callback['inputs']:
            match = re.search(r'"([^"]+)"', input_item)
            if match:
                comp_id = match.group(1)
                if comp_id not in component_to_callbacks:
                    component_to_callbacks[comp_id] = {'outputs_to': [], 'inputs_from': []}
                component_to_callbacks[comp_id]['inputs_from'].append(callback['name'])
    
    return component_to_callbacks

def main():
    file_path = '/home/readm/ArchDash/app.py'
    callbacks = extract_callbacks_info(file_path)
    
    print("=== CALLBACK ANALYSIS REPORT ===")
    print(f"Total callbacks found: {len(callbacks)}")
    print()
    
    # Group callbacks by functionality
    ui_callbacks = []
    data_callbacks = []
    modal_callbacks = []
    file_callbacks = []
    plot_callbacks = []
    
    for cb in callbacks:
        name = cb['name'].lower()
        if 'modal' in name:
            modal_callbacks.append(cb)
        elif 'file' in name or 'load' in name or 'save' in name:
            file_callbacks.append(cb)
        elif 'plot' in name or 'chart' in name or 'graph' in name:
            plot_callbacks.append(cb)
        elif 'update' in name or 'data' in name:
            data_callbacks.append(cb)
        else:
            ui_callbacks.append(cb)
    
    print("=== CALLBACK CATEGORIES ===")
    print(f"UI/Interaction callbacks: {len(ui_callbacks)}")
    print(f"Data/Update callbacks: {len(data_callbacks)}")
    print(f"Modal callbacks: {len(modal_callbacks)}")
    print(f"File operation callbacks: {len(file_callbacks)}")
    print(f"Plot/Chart callbacks: {len(plot_callbacks)}")
    print()
    
    print("=== DETAILED CALLBACK LIST ===")
    for i, cb in enumerate(callbacks, 1):
        print(f"{i}. {cb['name']} (line {cb['line']})")
        print(f"   Outputs: {len(cb['outputs'])} | Inputs: {len(cb['inputs'])} | States: {len(cb['states'])}")
        
        # Show key outputs and inputs
        if cb['outputs']:
            key_outputs = [o.split(',')[0].strip() for o in cb['outputs'][:3]]
            print(f"   Key outputs: {', '.join(key_outputs)}")
        
        if cb['inputs']:
            key_inputs = [i.split(',')[0].strip() for i in cb['inputs'][:3]]
            print(f"   Key inputs: {', '.join(key_inputs)}")
        
        print()
    
    # Analyze relationships
    relationships = analyze_callback_relationships(callbacks)
    
    print("=== COMPONENT RELATIONSHIPS ===")
    shared_components = {k: v for k, v in relationships.items() 
                        if len(v['outputs_to']) > 0 and len(v['inputs_from']) > 0}
    
    print(f"Components with both input and output connections: {len(shared_components)}")
    for comp_id, info in shared_components.items():
        print(f"  {comp_id}:")
        print(f"    Outputs to: {', '.join(info['outputs_to'])}")
        print(f"    Inputs from: {', '.join(info['inputs_from'])}")
    
    print()
    
    # Find potential issues
    print("=== POTENTIAL ISSUES ===")
    
    # Look for callbacks with many outputs (potential performance issue)
    heavy_callbacks = [cb for cb in callbacks if len(cb['outputs']) > 5]
    if heavy_callbacks:
        print("Callbacks with many outputs (>5):")
        for cb in heavy_callbacks:
            print(f"  {cb['name']}: {len(cb['outputs'])} outputs")
    
    # Look for callbacks with many inputs (complex dependencies)
    complex_callbacks = [cb for cb in callbacks if len(cb['inputs']) > 8]
    if complex_callbacks:
        print("Callbacks with many inputs (>8):")
        for cb in complex_callbacks:
            print(f"  {cb['name']}: {len(cb['inputs'])} inputs")
    
    # Look for duplicate callback names
    names = [cb['name'] for cb in callbacks]
    duplicates = [name for name in set(names) if names.count(name) > 1]
    if duplicates:
        print(f"Duplicate callback names: {duplicates}")
    
    print()
    return callbacks

if __name__ == "__main__":
    main()