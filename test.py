#!/usr/bin/env python3
"""
ArchDash API 测试 - 展示极简的使用方式
"""

from core import Graph

def test_api():
    """测试ArchDash API"""
    print("🚀 测试 ArchDash API")
    print("=" * 60)
    
    # 创建图
    g = Graph("超级简化设计")
    
    print("\n📝 1. 直接设置参数 (无需节点概念)")
    # 完全扁平 - 直接是参数，无节点层级
    g["电压"] = 1.8
    g["频率"] = 3.0
    g["核心数"] = 8
    g["工艺"] = 7
    
    print(f"设置的参数: {list(g.keys())}")
    
    print("\n📝 2. 定义计算函数 (直接访问参数)")
    def power():
        return g["电压"] ** 2 * g["核心数"] * 0.5
    
    def performance():
        return g["核心数"] * g["频率"] * 8
    
    def efficiency():
        return g["性能"] / g["功耗"] if g["功耗"] > 0 else 0
    
    def thermal():
        return 25 + g["功耗"] * 0.8  # 环境温度 + 功耗 * 热阻
    
    print("✅ 计算函数定义完成")
    
    print("\n📝 3. 添加计算参数")
    g.add_computed("功耗", power, "功耗计算")
    g.add_computed("性能", performance, "性能计算")
    g.add_computed("效率", efficiency, "效率计算")
    g.add_computed("温度", thermal, "温度计算")
    
    print("✅ 计算参数添加完成")
    
    print("\n📝 4. 查看所有参数和值")
    for param in sorted(g.keys()):
        value = g[param]
        if isinstance(value, (int, float)):
            if param == "温度":
                print(f"  {param}: {value:.1f}°C")
            elif param in ["功耗"]:
                print(f"  {param}: {value:.2f}W")
            elif param in ["性能"]:
                print(f"  {param}: {value:.0f}GFLOPS")
            elif param in ["效率"]:
                print(f"  {param}: {value:.2f}GFLOPS/W")
            else:
                print(f"  {param}: {value}")
        else:
            print(f"  {param}: {value}")
    
    print("\n📝 5. 测试链式更新")
    print("🔧 升级工艺: 7nm -> 5nm, 降低电压")
    g.update({
        "工艺": 5,
        "电压": 1.2,
        "频率": 3.5
    })
    
    print(f"新功耗: {g['功耗']:.2f}W, 新性能: {g['性能']:.0f}GFLOPS")
    print(f"新效率: {g['效率']:.2f}GFLOPS/W, 新温度: {g['温度']:.1f}°C")
    
    print("\n📝 6. 查看依赖关系")
    computed_params = ["功耗", "性能", "效率", "温度"]
    for param in computed_params:
        info = g.get_computed_info(param)
        deps = ", ".join(info.get('dependencies', []))
        print(f"  {param} <- [{deps}]")
    
    print("\n📝 7. 极简使用示例")
    print("```python")
    print("g = Graph('设计')")
    print("g['电压'] = 1.8")
    print("g['频率'] = 3.0")
    print("")
    print("def power(): return g['电压']**2 * g['频率'] * 0.5")
    print("g.add_computed('功耗', power)")
    print("")
    print("print(g['功耗'])  # 自动计算并返回结果")
    print("```")
    
    return g

def test_grouping():
    """测试分组功能"""
    print("\n" + "=" * 60)
    print("🏷️ 测试参数分组功能")
    print("=" * 60)
    
    g = Graph("分组测试")
    
    # 设置参数并分组
    g["芯片_工艺"] = 5
    g["芯片_电压"] = 1.2
    g["芯片_频率"] = 3.5
    
    g["CPU_核心数"] = 16
    g["CPU_缓存"] = 64
    g["CPU_架构"] = "x86"
    
    g["GPU_核心数"] = 2048
    g["GPU_显存"] = 16
    g["GPU_架构"] = "RDNA"
    
    # 设置分组
    for param in ["芯片_工艺", "芯片_电压", "芯片_频率"]:
        g.set_group(param, "芯片技术")
    
    for param in ["CPU_核心数", "CPU_缓存", "CPU_架构"]:
        g.set_group(param, "CPU规格")
    
    for param in ["GPU_核心数", "GPU_显存", "GPU_架构"]:
        g.set_group(param, "GPU规格")
    
    # 添加一些计算参数
    def cpu_score():
        return g["CPU_核心数"] * g["芯片_频率"] * 10
    
    def gpu_score():
        return g["GPU_核心数"] * 0.1
    
    def total_score():
        return g["CPU_评分"] + g["GPU_评分"]
    
    g.add_computed("CPU_评分", cpu_score, "CPU综合评分", "性能评分")
    g.add_computed("GPU_评分", gpu_score, "GPU综合评分", "性能评分")
    g.add_computed("总评分", total_score, "系统总评分", "性能评分")
    
    print("\n📊 按组显示参数:")
    g.print_structure()
    
    print(f"\n📈 评分结果:")
    print(f"CPU评分: {g['CPU_评分']:.0f}")
    print(f"GPU评分: {g['GPU_评分']:.0f}")
    print(f"总评分: {g['总评分']:.0f}")
    
    return g

def test_batch_operations():
    """测试批量操作"""
    print("\n" + "=" * 60)
    print("⚡ 测试批量操作")
    print("=" * 60)
    
    g = Graph("批量操作测试")
    
    # 批量设置多个参数
    initial_params = {
        "基础频率": 2.5,
        "加速频率": 3.8,
        "电压": 1.8,
        "核心数": 8,
        "线程数": 16,
        "缓存L1": 32,
        "缓存L2": 256,
        "缓存L3": 32
    }
    
    print("📝 批量设置参数...")
    g.update(initial_params)
    print(f"设置了 {len(initial_params)} 个参数")
    
    # 定义多个计算
    def base_power():
        return g["电压"] ** 2 * g["核心数"] * g["基础频率"] * 0.3
    
    def boost_power():
        return g["电压"] ** 2 * g["核心数"] * g["加速频率"] * 0.5
    
    def cache_power():
        return (g["缓存L1"] * 0.1 + g["缓存L2"] * 0.05 + g["缓存L3"] * 0.02) * g["核心数"]
    
    def total_power():
        return g["基础功耗"] + g["加速功耗"] + g["缓存功耗"]
    
    def mt_performance():
        return g["线程数"] * g["加速频率"] * 8
    
    def st_performance():
        return g["加速频率"] * 10
    
    # 批量添加计算参数
    computed_params = [
        ("基础功耗", base_power, "基础功耗计算"),
        ("加速功耗", boost_power, "加速功耗计算"),
        ("缓存功耗", cache_power, "缓存功耗计算"),
        ("总功耗", total_power, "总功耗计算"),
        ("多线程性能", mt_performance, "多线程性能"),
        ("单线程性能", st_performance, "单线程性能")
    ]
    
    print("📝 批量添加计算参数...")
    for name, func, desc in computed_params:
        g.add_computed(name, func, desc)
    
    print(f"添加了 {len(computed_params)} 个计算参数")
    
    print("\n📊 计算结果:")
    print(f"基础功耗: {g['基础功耗']:.2f}W")
    print(f"加速功耗: {g['加速功耗']:.2f}W")
    print(f"缓存功耗: {g['缓存功耗']:.2f}W")
    print(f"总功耗: {g['总功耗']:.2f}W")
    print(f"多线程性能: {g['多线程性能']:.0f}分")
    print(f"单线程性能: {g['单线程性能']:.0f}分")
    
    # 测试批量更新
    print("\n📝 批量更新测试 (更高端配置)...")
    updates = {
        "核心数": 12,
        "线程数": 24,
        "加速频率": 4.2,
        "电压": 1.6,
        "缓存L3": 48
    }
    
    g.update(updates)
    
    print("📊 更新后结果:")
    print(f"总功耗: {g['总功耗']:.2f}W")
    print(f"多线程性能: {g['多线程性能']:.0f}分")
    print(f"单线程性能: {g['单线程性能']:.0f}分")
    
    return g

def main():
    """主测试函数"""
    try:
        g1 = test_api()
        g2 = test_grouping()
        g3 = test_batch_operations()
        
        print("\n" + "="*60)
        print("✅ ArchDash API 测试完成！")
        print("="*60)
        
        print("\n🎉 ArchDash API 特点:")
        print("1. 🎯 终极简化: g['参数'] = 值")
        print("2. 🔄 自动依赖: 无需任何手动配置")
        print("3. 📦 扁平结构: 完全扁平的参数空间")
        print("4. 🏷️ 灵活分组: 可选的逻辑组织")
        print("5. ⚡ 批量操作: 高效的批量设置和更新")
        print("6. 🚀 极致性能: 最直接的访问方式")
        print("7. 💡 极致简单: 学习成本接近零")
        
        # 显示总参数统计
        total_params = len(g1.keys()) + len(g2.keys()) + len(g3.keys())
        print(f"\n📊 测试统计: 创建了3个图，总共 {total_params} 个参数")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()