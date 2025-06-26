#!/usr/bin/env python3
"""
测试运行脚本
提供多种测试运行模式
"""

import os
import sys
import pytest

def main():
    # 添加项目根目录到Python路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

    # 运行所有测试
    test_args = [
        "tests",  # 测试目录
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