#!/usr/bin/env python3
"""
ArchDash API 演示 - 自动依赖追踪的计算图
"""

from core import Graph

def main():
    """主演示函数"""
    print("🚀 ArchDash API 演示")
    print("=" * 50)
    
    # 创建图
    g = Graph("处理器设计演示")
    
    print("\n📝 1. 设置基础参数")
    # 直接设置参数 - 完全扁平化语法
    g["工艺_节点"] = 7      # nm
    g["工艺_电压"] = 1.8    # V
    g["工艺_频率"] = 3.0    # GHz
    
    g["CPU_核心数"] = 8
    g["CPU_缓存"] = 32     # MB
    
    # 设置分组（可选）
    g.set_group("工艺_节点", "工艺参数")
    g.set_group("工艺_电压", "工艺参数")
    g.set_group("工艺_频率", "工艺参数")
    g.set_group("CPU_核心数", "CPU参数")
    g.set_group("CPU_缓存", "CPU参数")
    
    print("✅ 基础参数设置完成")
    
    print("\n📝 2. 定义计算函数")
    # 定义计算函数 - 自动依赖追踪
    def cpu_power():
        """CPU功耗计算"""
        voltage = g["工艺_电压"]
        cores = g["CPU_核心数"]
        return voltage ** 2 * cores * 0.5
    
    def cpu_performance():
        """CPU性能计算"""
        cores = g["CPU_核心数"]
        frequency = g["工艺_频率"]
        return cores * frequency * 8  # GFLOPS
    
    def efficiency():
        """能效比计算"""
        perf = g["CPU_性能"]
        power = g["CPU_功耗"]
        return perf / power if power > 0 else 0
    
    print("✅ 计算函数定义完成")
    
    print("\n📝 3. 添加计算参数")
    # 添加计算参数 - 自动建立依赖关系
    g.add_computed("CPU_功耗", cpu_power, "CPU功耗计算", "计算结果")
    g.add_computed("CPU_性能", cpu_performance, "CPU性能计算", "计算结果")
    g.add_computed("能效比", efficiency, "能效比计算", "计算结果")
    
    print("✅ 计算参数添加完成")
    
    print("\n📝 4. 查看结果")
    print(f"CPU功耗: {g['CPU_功耗']:.2f}W")
    print(f"CPU性能: {g['CPU_性能']:.0f}GFLOPS")
    print(f"能效比: {g['能效比']:.2f}GFLOPS/W")
    
    print("\n📝 5. 测试自动更新")
    print("🔧 升级工艺节点 7nm -> 5nm...")
    g["工艺_节点"] = 5
    g["工艺_电压"] = 1.2
    
    print(f"新的CPU功耗: {g['CPU_功耗']:.2f}W")
    print(f"新的能效比: {g['能效比']:.2f}GFLOPS/W")
    
    print("\n🚀 增加CPU核心数 8 -> 16...")
    g["CPU_核心数"] = 16
    
    print(f"新的CPU功耗: {g['CPU_功耗']:.2f}W") 
    print(f"新的CPU性能: {g['CPU_性能']:.0f}GFLOPS")
    print(f"新的能效比: {g['能效比']:.2f}GFLOPS/W")
    
    print("\n📝 6. 查看依赖关系")
    deps = ["CPU_功耗", "CPU_性能", "能效比"]
    
    for param_name in deps:
        info = g.get_computed_info(param_name)
        deps_str = ", ".join(info.get('dependencies', []))
        print(f"{param_name}: 依赖 [{deps_str}]")
    
    print("\n📝 7. 查看图结构")
    g.print_structure()
    
    print("\n✅ 演示完成！")
    print("\n🎉 ArchDash 核心特性:")
    print("• 🎯 极简语法: g['参数'] = 值")
    print("• 🔄 自动依赖: 函数内直接访问数据")
    print("• 📦 扁平结构: 无节点层级，直接参数访问")
    print("• 🏷️ 可选分组: 灵活的逻辑分组")
    print("• 🚀 高性能: 直接访问，无解析")
    print("• 💡 IDE友好: 完整代码补全")

if __name__ == "__main__":
    main()