#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行所有unlink功能测试的集成脚本
包括：
1. 模型层测试（原有和增强功能）
2. UI交互测试（Selenium）
"""

import subprocess
import sys
import os

def run_command(command, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"命令: {command}")
    print('='*60)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ 警告信息:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - 成功")
            return True
        else:
            print(f"❌ {description} - 失败 (退出码: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ 运行命令时出错: {e}")
        return False

def main():
    """主函数"""
    print("🧪 运行所有unlink功能测试")
    print("=" * 60)
    
    # 检查当前目录
    current_dir = os.getcwd()
    print(f"当前目录: {current_dir}")
    
    # 测试列表
    tests = [
        {
            "command": "python test_unlink_feature.py",
            "description": "运行原有unlink功能测试（模型层）",
            "type": "model"
        },
        {
            "command": "python test_enhanced_unlink_feature.py", 
            "description": "运行增强unlink功能测试（模型层）",
            "type": "model"
        },
        {
            "command": "pytest test_unlink_ui_feature.py -v",
            "description": "运行unlink UI交互测试（需要Selenium）",
            "type": "ui"
        },
        {
            "command": "pytest test_unlink_ui_feature.py::test_unlink_icon_display_logic -v",
            "description": "运行unlink图标显示逻辑测试",
            "type": "ui_specific"
        },
        {
            "command": "pytest test_unlink_ui_feature.py::test_manual_value_change_auto_unlink -v",
            "description": "运行手动修改值自动unlink测试",
            "type": "ui_specific"
        },
        {
            "command": "pytest test_unlink_ui_feature.py::test_unlink_icon_click_reconnect -v",
            "description": "运行点击🔓按钮重新连接测试",
            "type": "ui_specific"
        },
        {
            "command": "pytest test_unlink_ui_feature.py::test_unlink_ui_integration -v",
            "description": "运行unlink完整UI集成测试",
            "type": "ui_specific"
        }
    ]
    
    # 运行结果统计
    results = {
        "model": {"success": 0, "total": 0},
        "ui": {"success": 0, "total": 0},
        "ui_specific": {"success": 0, "total": 0}
    }
    
    # 检查依赖
    print("\n🔍 检查测试依赖...")
    
    # 检查pytest
    try:
        subprocess.run(["pytest", "--version"], capture_output=True, check=True)
        print("✅ pytest 已安装")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pytest 未安装，请运行: pip install pytest")
        print("⚠️ UI测试将被跳过")
    
    # 检查Selenium
    try:
        import selenium
        print("✅ selenium 已安装")
    except ImportError:
        print("❌ selenium 未安装，请运行: pip install selenium")
        print("⚠️ UI测试将被跳过")
    
    # 检查dash
    try:
        import dash
        print("✅ dash 已安装")
    except ImportError:
        print("❌ dash 未安装，请运行: pip install dash")
    
    # 检查测试文件
    test_files = [
        "test_unlink_feature.py",
        "test_enhanced_unlink_feature.py", 
        "test_unlink_ui_feature.py",
        "models.py",
        "app.py"
    ]
    
    missing_files = []
    for file in test_files:
        if os.path.exists(file):
            print(f"✅ {file} 存在")
        else:
            print(f"❌ {file} 不存在")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️ 缺少文件: {', '.join(missing_files)}")
        print("请确保在正确的目录中运行测试")
    
    # 运行测试
    print(f"\n🚀 开始运行 {len(tests)} 个测试...")
    
    for i, test in enumerate(tests, 1):
        print(f"\n[{i}/{len(tests)}] 运行测试...")
        
        # 检查是否跳过UI测试
        if test["type"] in ["ui", "ui_specific"]:
            try:
                import selenium
                import pytest
            except ImportError:
                print(f"⏭️ 跳过 {test['description']} - 缺少依赖")
                continue
        
        success = run_command(test["command"], test["description"])
        
        # 更新统计
        test_type = test["type"]
        results[test_type]["total"] += 1
        if success:
            results[test_type]["success"] += 1
    
    # 显示测试总结
    print(f"\n{'='*60}")
    print("📊 测试总结")
    print('='*60)
    
    total_success = 0
    total_tests = 0
    
    for test_type, stats in results.items():
        if stats["total"] > 0:
            success_rate = (stats["success"] / stats["total"]) * 100
            status = "✅" if stats["success"] == stats["total"] else "⚠️"
            
            type_names = {
                "model": "模型层测试",
                "ui": "UI交互测试", 
                "ui_specific": "UI专项测试"
            }
            
            print(f"{status} {type_names[test_type]}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
            total_success += stats["success"]
            total_tests += stats["total"]
    
    if total_tests > 0:
        overall_rate = (total_success / total_tests) * 100
        overall_status = "🎉" if total_success == total_tests else "⚠️"
        print(f"\n{overall_status} 总体测试: {total_success}/{total_tests} ({overall_rate:.1f}%)")
        
        if total_success == total_tests:
            print("\n🎊 所有测试通过！unlink功能工作正常！")
        else:
            print(f"\n📝 有 {total_tests - total_success} 个测试失败，请检查上述输出")
    else:
        print("\n⚠️ 没有运行任何测试")
    
    # 提供使用指南
    print(f"\n{'='*60}")
    print("📖 使用指南")
    print('='*60)
    print("单独运行测试：")
    print("  模型层测试: python test_enhanced_unlink_feature.py")
    print("  UI交互测试: pytest test_unlink_ui_feature.py -v")
    print("  特定测试:   pytest test_unlink_ui_feature.py::test_unlink_icon_display_logic -v")
    print("")
    print("测试覆盖范围：")
    print("  ✓ unlink图标显示逻辑（只有unlinked=True且有依赖时显示）")
    print("  ✓ 手动修改值自动unlink")
    print("  ✓ 点击🔓按钮重新连接")
    print("  ✓ 相关性分析自动unlink")
    print("  ✓ 边界情况和错误处理")
    print("  ✓ 复杂依赖关系中的unlink")
    print("  ✓ 完整UI集成测试")

if __name__ == "__main__":
    main() 