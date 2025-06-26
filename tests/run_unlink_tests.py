#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行所有unlink功能测试的集成脚本
包括：
1. 模型层测试（原有和增强功能）
2. UI交互测试（Selenium）
"""

import os
import sys
import pytest

def main():
    # 添加项目根目录到Python路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

    # 运行所有unlink相关的测试
    test_args = [
        "tests/features/test_unlink_ui_feature.py",
        "tests/features/test_enhanced_unlink_feature.py",
        "tests/features/test_unlink_feature.py",
        "-v",     # 详细输出
        "--cov=./",  # 覆盖率报告
        "-n", "auto"  # 并行执行
    ]
    
    # 如果在CI环境中运行，添加额外的参数
    if os.environ.get("TEST_ENV") == "CI":
        test_args.extend(["--headless"])

    pytest.main(test_args)

if __name__ == "__main__":
    main() 