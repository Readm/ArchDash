#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T108 - 缺失依赖测试
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

def test_missing_dependency():
    """测试缺失依赖的情况"""
    # 创建参数
    param1 = Parameter("param1", None, "V", description="测试参数1")
    param2 = Parameter("param2", 0.0, "A", description="测试参数2", 
                      calculation_func="result = dependencies[0].value * 2")
    
    # 设置依赖关系
    param2.add_dependency(param1)
    
    # 测试缺失依赖值的情况
    with pytest.raises(ValueError, match="依赖参数 param1 的值缺失"):
        param2.calculate()

if __name__ == "__main__":
    test_missing_dependency()
    print("✅ T108 缺失依赖测试通过")
