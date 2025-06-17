#!/usr/bin/env python3
"""
测试运行脚本
提供多种测试运行模式
"""

import os
import sys
import subprocess
import argparse

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"📝 执行命令: {cmd}")
    print('='*60)
    
    result = subprocess.run(cmd, shell=True, capture_output=False)
    
    if result.returncode == 0:
        print(f"✅ {description} - 成功完成")
    else:
        print(f"❌ {description} - 执行失败 (退出码: {result.returncode})")
    
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description='运行测试的便捷脚本')
    parser.add_argument('--mode', choices=['headless', 'headed', 'demo'], 
                       default='headless', help='测试模式')
    parser.add_argument('--file', help='指定测试文件')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 构建pytest命令
    cmd_parts = ['pytest']
    
    # 添加无头模式选项（使用dash-testing内置支持）
    if args.mode == 'headless':
        cmd_parts.append('--headless')
        print("🎭 设置为无头模式（后台运行，不显示浏览器）")
    elif args.mode == 'headed':
        print("🖥️  设置为有头模式（显示浏览器窗口）")
    
    if args.verbose:
        cmd_parts.append('-v')
    
    # 添加测试文件
    if args.file:
        cmd_parts.append(args.file)
    elif args.mode == 'demo':
        cmd_parts.append('test_headless_demo.py')
    else:
        # 默认运行所有测试
        cmd_parts.extend(['test_app.py', 'test_models.py', 'test_file_operations.py'])
    
    # 添加输出选项
    cmd_parts.extend(['-s', '--tb=short'])
    
    cmd = ' '.join(cmd_parts)
    
    # 显示配置信息
    print(f"\n📋 测试配置:")
    print(f"   模式: {args.mode}")
    print(f"   无头模式: {'是' if args.mode == 'headless' else '否'}")
    print(f"   详细输出: {args.verbose}")
    if args.file:
        print(f"   测试文件: {args.file}")
    
    # 运行测试
    success = run_command(cmd, f"{args.mode.upper()} 模式测试")
    
    if success:
        print(f"\n🎉 测试完成！")
    else:
        print(f"\n💥 测试过程中出现错误")
        sys.exit(1)

if __name__ == '__main__':
    main() 