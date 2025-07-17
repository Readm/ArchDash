#!/usr/bin/env python3
"""
测试Graph Visualizer的基本功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from graph_visualizer import CodeParser

def test_parser():
    """测试代码解析器"""
    parser = CodeParser()
    
    # 测试代码
    test_code = '''
from core import Graph

# 创建图
g = Graph("测试图")

# 基础参数
g["param1"] = 10.0
g["param2"] = 20.0

# 计算函数
def calc_result():
    return g["param1"] * g["param2"]

# 添加计算参数
g.add_computed("result", calc_result, "计算结果")
'''
    
    # 解析代码
    result = parser.parse_advanced_code(test_code)
    
    print("解析结果:")
    print(f"成功: {result['success']}")
    print(f"图名: {result['graph_name']}")
    print(f"参数: {result['parameters']}")
    print(f"依赖: {result['dependencies']}")
    
    return result['success']

if __name__ == "__main__":
    print("测试Graph Visualizer...")
    if test_parser():
        print("✅ 解析器测试通过")
        print("\n现在可以运行: python graph_visualizer.py")
    else:
        print("❌ 解析器测试失败")