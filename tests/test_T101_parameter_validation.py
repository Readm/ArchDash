#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T101 - 参数验证测试
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

def test_parameter_validation():
    """测试参数验证"""
    # 测试有效参数
    param1 = Parameter("param1", 10.0, "V", description="测试参数1")
    assert param1.validate()
    
    param2 = Parameter("param2", "test", "A", description="测试参数2")
    assert param2.validate()
    
    # 测试无效参数
    param3 = Parameter("param3", None, "W", description="测试参数3")
    assert not param3.validate()
    
    param4 = Parameter("param4", "", "W", description="测试参数4")
    assert not param4.validate()

if __name__ == "__main__":
    test_parameter_validation()
    print("✅ T101 参数验证测试通过")
