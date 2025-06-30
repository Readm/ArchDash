#!/usr/bin/env python3
"""
测试运行脚本
提供多种测试运行模式和分类执行
"""

import os
import sys
import pytest
import argparse
from pathlib import Path

def run_tests(test_type=None, verbose=True, coverage=True, parallel=True):
    """
    运行指定类型的测试
    
    Args:
        test_type: 测试类型 ('core', 'features', 'examples', 'integration', None)
        verbose: 是否显示详细输出
        coverage: 是否生成覆盖率报告
        parallel: 是否并行执行
    """
    # 添加项目根目录到Python路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

    # 基础测试参数
    test_args = []
    
    # 根据测试类型选择测试目录
    tests_dir = Path(__file__).parent
    if test_type:
        test_path = tests_dir / test_type
        if not test_path.exists():
            print(f"错误: 测试目录 {test_path} 不存在")
            return 1
        test_args.extend([str(test_path)])
    else:
        # 运行所有测试，但排除某些目录
        test_args.extend([
            str(tests_dir),
            "--ignore=tests/__pycache__",
            "--ignore=tests/.pytest_cache"
        ])
    
    # 添加可选参数
    if verbose:
        test_args.append("-v")
    
    if coverage:
        test_args.extend([
            "--cov=./",
            "--cov-report=term-missing",
            "--cov-config=.coveragerc"
        ])
    
    if parallel:
        test_args.extend(["-n", "auto"])
    
    # 添加测试发现模式
    test_args.extend([
        "-p", "no:warnings",  # 禁用警告插件
        "--import-mode=importlib",  # 使用importlib模式导入
    ])
    
    # 如果在CI环境中运行，添加额外的参数
    if os.environ.get("TEST_ENV") == "CI":
        test_args.extend(["--headless"])

    # 打印测试命令
    print(f"\n执行测试命令: pytest {' '.join(test_args)}\n")

    # 运行测试
    return pytest.main(test_args)

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="ArchDash测试运行工具")
    parser.add_argument("--type", choices=["core", "features", "examples", "integration"],
                      help="指定要运行的测试类型")
    parser.add_argument("--no-verbose", action="store_false", dest="verbose",
                      help="不显示详细输出")
    parser.add_argument("--no-coverage", action="store_false", dest="coverage",
                      help="不生成覆盖率报告")
    parser.add_argument("--no-parallel", action="store_false", dest="parallel",
                      help="不使用并行执行")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 运行测试
    result = run_tests(
        test_type=args.type,
        verbose=args.verbose,
        coverage=args.coverage,
        parallel=args.parallel
    )
    
    # 根据测试结果设置退出码
    sys.exit(result)

if __name__ == "__main__":
    main() 