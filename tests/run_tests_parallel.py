#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并行执行测试套件
使用 pytest-xdist 插件实现并行测试
优化：利用单端口多会话的优势
"""

import subprocess
import sys
import os
import time
import multiprocessing
from pathlib import Path

def get_optimal_worker_count():
    """获取最优并行进程数"""
    cpu_count = multiprocessing.cpu_count()
    
    # 考虑因素：
    # 1. CPU核心数
    # 2. 内存限制（每个Chrome实例约100-200MB）
    # 3. 单端口服务器的并发处理能力
    # 4. 为系统保留资源
    
    # 对于16核机器，可以更激进一些
    if cpu_count >= 16:
        # 16核机器可以使用更多进程
        optimal_workers = min(cpu_count, 16)
    else:
        # 保守估计：使用CPU核心数的60%
        optimal_workers = max(1, int(cpu_count * 0.6))
        # 限制最大进程数，避免资源耗尽
        optimal_workers = min(optimal_workers, 8)
    
    return optimal_workers

def run_parallel_tests(workers=None, headless=True, verbose=False):
    """
    并行执行测试
    
    Args:
        workers: 并行进程数，None表示自动检测
        headless: 是否使用无头模式
        verbose: 是否显示详细输出
    """
    if workers is None:
        workers = get_optimal_worker_count()
    
    print(f"🚀 开始并行测试执行")
    print(f"📊 并行进程数: {workers}")
    print(f"🖥️  CPU核心数: {multiprocessing.cpu_count()}")
    print(f"🌐 服务器模式: 单端口多会话（支持并发）")
    print(f"👻 无头模式: {'是' if headless else '否'}")
    print("-" * 60)
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-n", str(workers),  # 并行进程数
        "--dist=worksteal",  # 工作窃取模式，提高效率
        "--tb=short",        # 简短错误信息
        "--durations=10",    # 显示最慢的10个测试
    ]
    
    if headless:
        cmd.append("--headless")
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # 添加性能优化选项
    cmd.extend([
        "--disable-warnings",  # 禁用警告
        "--maxfail=10",        # 最多允许10个失败
        "--timeout=300",       # 单个测试超时5分钟
    ])
    
    print(f"🔧 执行命令: {' '.join(cmd)}")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # 执行测试
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("-" * 60)
        print(f"⏱️  总执行时间: {duration:.2f}秒")
        print(f"📈 平均每个测试: {duration/95:.2f}秒")  # 假设95个测试
        print(f"🚀 并行效率: {workers} 个进程")
        
        if result.returncode == 0:
            print("✅ 所有测试通过！")
        else:
            print(f"❌ 测试执行完成，退出码: {result.returncode}")
        
        return result.returncode, duration
        
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        return 1, 0
    except Exception as e:
        print(f"❌ 执行测试时出错: {e}")
        return 1, 0

def run_sequential_tests(headless=True, verbose=False):
    """顺序执行测试（用于对比）"""
    print(f"🐌 开始顺序测试执行")
    print(f"👻 无头模式: {'是' if headless else '否'}")
    print("-" * 60)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--tb=short",
        "--durations=10",
    ]
    
    if headless:
        cmd.append("--headless")
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    cmd.extend([
        "--disable-warnings",
        "--maxfail=10",
        "--timeout=300",
    ])
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("-" * 60)
        print(f"⏱️  总执行时间: {duration:.2f}秒")
        
        return result.returncode, duration
        
    except Exception as e:
        print(f"❌ 执行测试时出错: {e}")
        return 1, 0

def run_concurrent_test():
    """测试并发能力"""
    print("🧪 测试并发能力...")
    
    # 启动一个简单的并发测试
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_T101_parameter_validation.py",
        "tests/test_T102_parameter_dependencies.py", 
        "tests/test_T103_parameter_calculation.py",
        "-n", "3",
        "--tb=no",
        "-q",
        "--headless"
    ]
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start_time
    
    if result.returncode == 0:
        print(f"✅ 并发测试通过，耗时: {duration:.2f}秒")
        return True
    else:
        print(f"❌ 并发测试失败: {result.stderr}")
        return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="并行执行ArchDash测试套件")
    parser.add_argument("--workers", "-w", type=int, help="并行进程数（默认自动检测）")
    parser.add_argument("--sequential", "-s", action="store_true", help="顺序执行（用于对比）")
    parser.add_argument("--headless", action="store_true", default=True, help="使用无头模式")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--compare", "-c", action="store_true", help="对比并行和顺序执行时间")
    parser.add_argument("--test-concurrency", action="store_true", help="测试并发能力")
    
    args = parser.parse_args()
    
    # 检查是否安装了pytest-xdist
    try:
        import xdist
    except ImportError:
        print("❌ 未安装 pytest-xdist 插件")
        print("请运行: pip install pytest-xdist")
        return 1
    
    if args.test_concurrency:
        return 0 if run_concurrent_test() else 1
    
    if args.compare:
        print("🔄 对比并行和顺序执行性能")
        print("=" * 80)
        
        # 顺序执行
        print("1️⃣ 顺序执行测试...")
        seq_code, seq_time = run_sequential_tests(args.headless, args.verbose)
        
        print("\n" + "=" * 80)
        
        # 并行执行
        print("2️⃣ 并行执行测试...")
        par_code, par_time = run_parallel_tests(args.workers, args.headless, args.verbose)
        
        print("\n" + "=" * 80)
        print("📊 性能对比结果:")
        print(f"   顺序执行: {seq_time:.2f}秒")
        print(f"   并行执行: {par_time:.2f}秒")
        
        if seq_time > 0 and par_time > 0:
            speedup = seq_time / par_time
            improvement = ((seq_time - par_time) / seq_time) * 100
            print(f"   加速比: {speedup:.2f}x")
            print(f"   性能提升: {improvement:.1f}%")
        
        return 0 if seq_code == 0 and par_code == 0 else 1
    
    elif args.sequential:
        return run_sequential_tests(args.headless, args.verbose)[0]
    else:
        return run_parallel_tests(args.workers, args.headless, args.verbose)[0]

if __name__ == "__main__":
    sys.exit(main()) 