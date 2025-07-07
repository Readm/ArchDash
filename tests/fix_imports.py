#!/usr/bin/env python3
"""
修复批量生成测试文件的导入问题
"""

import os

# 需要修复的文件列表
files_to_fix = [
    'test_T511_recently_updated_params_tracking.py',
    'test_T512_duplicate_node_name_prevention.py',
    'test_T513_empty_node_name_validation.py',
    'test_T514_column_management.py',
    'test_T515_remove_column_functionality.py',
    'test_T518_headless_layout_operations.py',
    'test_T519_headless_parameter_operations.py'
]

# 标准导入
standard_imports = '''import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
from app import app, graph, layout_manager

'''

def fix_file_imports(file_path):
    """修复单个文件的导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # 找到第一个函数定义的位置
        function_start = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('def '):
                function_start = i
                break
        
        # 保留utils导入和注释
        header_lines = []
        for i in range(function_start):
            line = lines[i]
            if line.startswith('from utils') or line.startswith('#') or line.strip() == '':
                header_lines.append(line)
        
        # 组合新内容
        new_content = '\n'.join(header_lines) + '\n'
        new_content += standard_imports
        new_content += '\n'.join(lines[function_start:])
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 修复导入: {os.path.basename(file_path)}")
        
    except Exception as e:
        print(f"❌ 修复失败 {file_path}: {e}")

# 执行修复
if __name__ == "__main__":
    test_dir = "/home/readm/ArchDash/tests"
    
    for file_name in files_to_fix:
        file_path = os.path.join(test_dir, file_name)
        if os.path.exists(file_path):
            fix_file_imports(file_path)
        else:
            print(f"⚠️ 文件不存在: {file_path}")
    
    print("\n🎉 导入修复完成!")