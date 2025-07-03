#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T117 - 错误处理测试
从原始测试文件分离出的独立测试
"""

import os
import tempfile
from models import CalculationGraph, Node, Parameter, CanvasLayoutManager, GridPosition
import json

def test_error_handling():
    """测试错误处理"""
    print("\n🧪 测试错误处理...")
    
    # 测试加载不存在的文件
    print("📂 测试加载不存在的文件...")
    result = CalculationGraph.load_from_file("nonexistent_file.json")
    if result is not None:
        print("❌ 应该返回None但没有")
        assert False, "应该返回None但没有"
    print("✅ 正确处理不存在的文件")
    
    # 测试加载无效JSON
    print("📂 测试加载无效JSON文件...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        temp_file.write("invalid json content")
        temp_path = temp_file.name
    
    try:
        result = CalculationGraph.load_from_file(temp_path)
        if result is not None:
            print("❌ 应该返回None但没有")
            assert False, "应该返回None但没有"
        print("✅ 正确处理无效JSON文件")
    finally:
        os.unlink(temp_path)
    
    # 测试保存到无效路径
    print("💾 测试保存到无效路径...")
    graph = CalculationGraph()
    success = graph.save_to_file("/invalid/path/file.json")
    if success:
        print("❌ 应该失败但成功了")
        assert False, "应该失败但成功了"
    print("✅ 正确处理无效保存路径")
    
    print("✅ 错误处理测试通过！")
    # 使用assert代替return来表示测试通过
    assert True

if __name__ == "__main__":
    test_error_handling()
    print("✅ T117 错误处理测试通过")
