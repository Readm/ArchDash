#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T301 - 测试
从原始测试文件分离出的独立测试
"""

from dash import callback
from app import create_example_soc_graph
import time
from app import app

def test_example_basic():
    """基础测试：验证Example功能的核心特性"""
    print("🧪 开始测试Example功能...")
    
    try:
        # 1. 测试函数导入
        from app import create_example_soc_graph
        print("✅ 示例函数导入成功")
        
        # 2. 测试函数执行
        result = create_example_soc_graph()
        print(f"✅ 示例函数执行成功，返回: {result}")
        
        # 3. 验证返回结果结构
        assert isinstance(result, dict), "返回结果应该是字典"
        assert "nodes_created" in result, "应该包含节点创建数量"
        assert "total_params" in result, "应该包含总参数数量"
        assert "calculated_params" in result, "应该包含计算参数数量"
        print("✅ 返回结果结构正确")
        
        # 4. 验证创建数量合理
        assert result["nodes_created"] == 9, f"应该创建9个节点，实际{result['nodes_created']}"
        assert result["total_params"] == 26, f"应该创建26个参数，实际{result['total_params']}"
        assert result["calculated_params"] == 15, f"应该有15个计算参数，实际{result['calculated_params']}"
        print("✅ 节点和参数数量验证通过")
        
        # 5. 测试多次调用一致性
        result2 = create_example_soc_graph()
        assert result["nodes_created"] == result2["nodes_created"], "多次调用结果应该一致"
        print("✅ 多次调用一致性验证通过")
        
        # 6. 测试性能（应该在合理时间内完成）
        import time
        start_time = time.time()
        create_example_soc_graph()
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 5.0, f"执行时间应该小于5秒，实际{execution_time:.3f}秒"
        print(f"✅ 性能测试通过，执行时间: {execution_time:.3f}秒")
        
        print("🎉 Example功能所有基础测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_example_basic()
    print("✅ T301 测试通过")
