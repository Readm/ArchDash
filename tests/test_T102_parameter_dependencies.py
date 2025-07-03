#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T102 - 参数依赖关系测试
从原始测试文件分离出的独立测试
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from app import app, graph, layout_manager
import pytest
from models import Parameter, Node, CalculationGraph
import json
import math

def test_parameter_dependencies():
    """测试参数依赖关系"""
    # 创建参数
    param1 = Parameter("param1", 2.0, "V", description="Test parameter 1")
    param2 = Parameter("param2", 3, "A", description="Test parameter 2")
    
    # 测试添加有效依赖
    param1.add_dependency(param2)
    assert param2 in param1.dependencies
    
    # 测试添加无效类型依赖
    with pytest.raises(TypeError):
        param1.add_dependency("invalid")
    
    # 测试添加自身作为依赖
    with pytest.raises(ValueError):
        param1.add_dependency(param1)
    
    # 测试重复添加依赖
    param1.add_dependency(param2)  # 应该不会抛出异常
    assert param1.dependencies.count(param2) == 1

if __name__ == "__main__":
    test_parameter_dependencies()
    print("✅ T102 参数依赖关系测试通过")
