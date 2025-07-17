#!/usr/bin/env python3
"""
测试依赖关系图功能
"""

from core import Graph

def test_dependency_graph():
    """测试依赖关系图获取功能"""
    print("🚀 测试依赖关系图功能")
    print("=" * 60)
    
    # 创建一个复杂的依赖关系图
    g = Graph("依赖关系测试")
    
    # 设置基础参数
    g["电压"] = 1.8
    g["频率"] = 3.0
    g["核心数"] = 8
    g["温度"] = 25
    
    print("\n📝 1. 设置基础参数")
    print(f"基础参数: {[p for p in g.keys() if p not in g._computed_parameters]}")
    
    # 定义复杂的依赖关系
    def power():
        return g["电压"] ** 2 * g["核心数"] * 0.5
    
    def performance():
        return g["核心数"] * g["频率"] * 8
    
    def efficiency():
        return g["性能"] / g["功耗"] if g["功耗"] > 0 else 0
    
    def thermal():
        return g["温度"] + g["功耗"] * 0.8
    
    def cooling_needed():
        return max(0, g["芯片温度"] - 65)  # 超过65°C需要散热
    
    def total_score():
        return g["性能"] * 0.5 + g["效率"] * 100 - g["散热需求"] * 10
    
    print("\n📝 2. 添加计算参数")
    g.add_computed("功耗", power, "功耗计算")
    g.add_computed("性能", performance, "性能计算")
    g.add_computed("效率", efficiency, "效率计算")
    g.add_computed("芯片温度", thermal, "芯片温度计算")
    g.add_computed("散热需求", cooling_needed, "散热需求计算")
    g.add_computed("综合评分", total_score, "综合评分计算")
    
    print(f"计算参数: {list(g._computed_parameters.keys())}")
    
    print("\n📝 3. 获取依赖关系图")
    dep_graph = g.get_dependency_graph()
    print("正向依赖关系图 (被依赖参数 -> 依赖它的参数):")
    for param, dependents in dep_graph.items():
        if dependents:
            print(f"  {param} -> {dependents}")
    
    print("\n📝 4. 获取反向依赖关系图")
    reverse_dep_graph = g.get_reverse_dependency_graph()
    print("反向依赖关系图 (参数 -> 它依赖的参数):")
    for param, dependencies in reverse_dep_graph.items():
        if dependencies:
            print(f"  {param} <- {dependencies}")
    
    print("\n📝 5. 获取依赖链")
    complex_params = ["效率", "综合评分", "散热需求"]
    for param in complex_params:
        chain = g.get_dependency_chain(param)
        print(f"  {param} 的依赖链: {' -> '.join(chain)}")
    
    print("\n📝 6. 获取依赖者链")
    base_params = ["电压", "核心数", "功耗"]
    for param in base_params:
        dependents_chain = g.get_dependents_chain(param)
        print(f"  {param} 的依赖者链: {' -> '.join(dependents_chain)}")
    
    return g

def test_dependency_refresh():
    """测试依赖关系刷新功能"""
    print("\n" + "=" * 60)
    print("🔄 测试依赖关系刷新功能")
    print("=" * 60)
    
    g = Graph("刷新测试")
    
    # 设置基础参数
    g["基础值"] = 10
    g["乘数"] = 2
    g["加数"] = 5
    
    # 创建多级依赖
    def level1():
        return g["基础值"] * g["乘数"]
    
    def level2():
        return g["一级结果"] + g["加数"]
    
    def level3():
        return g["二级结果"] * 1.5
    
    def combined():
        return g["一级结果"] + g["二级结果"] + g["三级结果"]
    
    g.add_computed("一级结果", level1, "一级计算")
    g.add_computed("二级结果", level2, "二级计算")
    g.add_computed("三级结果", level3, "三级计算")
    g.add_computed("综合结果", combined, "综合计算")
    
    print("\n📝 1. 初始值")
    print(f"基础值: {g['基础值']}")
    print(f"一级结果: {g['一级结果']}")
    print(f"二级结果: {g['二级结果']}")
    print(f"三级结果: {g['三级结果']}")
    print(f"综合结果: {g['综合结果']}")
    
    print("\n📝 2. 修改基础值并观察自动刷新")
    g["基础值"] = 20
    print(f"修改基础值到 {g['基础值']}")
    print(f"一级结果: {g['一级结果']} (应该是 40)")
    print(f"二级结果: {g['二级结果']} (应该是 45)")
    print(f"三级结果: {g['三级结果']} (应该是 67.5)")
    print(f"综合结果: {g['综合结果']} (应该是 152.5)")
    
    print("\n📝 3. 测试手动刷新单个参数的依赖者")
    g["乘数"] = 3
    print(f"修改乘数到 {g['乘数']}")
    print("刷新前:")
    print(f"  一级结果: {g['一级结果']}")
    
    # 手动刷新
    g.refresh_dependents("乘数")
    print("刷新后:")
    print(f"  一级结果: {g['一级结果']} (应该是 60)")
    print(f"  二级结果: {g['二级结果']} (应该是 65)")
    print(f"  三级结果: {g['三级结果']} (应该是 97.5)")
    print(f"  综合结果: {g['综合结果']} (应该是 222.5)")
    
    print("\n📝 4. 测试全图刷新")
    g["基础值"] = 5
    g["乘数"] = 4
    g["加数"] = 10
    print("修改多个参数后，刷新全图:")
    g.refresh_all_computed()
    print(f"  一级结果: {g['一级结果']} (应该是 20)")
    print(f"  二级结果: {g['二级结果']} (应该是 30)")
    print(f"  三级结果: {g['三级结果']} (应该是 45)")
    print(f"  综合结果: {g['综合结果']} (应该是 95)")
    
    return g

def test_complex_dependency_scenarios():
    """测试复杂依赖场景"""
    print("\n" + "=" * 60)
    print("🌐 测试复杂依赖场景")
    print("=" * 60)
    
    g = Graph("复杂依赖测试")
    
    # 设置一个CPU设计的复杂依赖网络
    g["工艺_节点"] = 7
    g["工艺_电压"] = 1.8
    g["工艺_频率"] = 3.0
    g["CPU_核心数"] = 8
    g["CPU_缓存"] = 32
    g["GPU_核心数"] = 1024
    g["内存_容量"] = 32
    g["内存_频率"] = 3200
    
    # 功耗计算
    def cpu_power():
        return g["工艺_电压"] ** 2 * g["CPU_核心数"] * g["工艺_频率"] * 0.3
    
    def gpu_power():
        return g["GPU_核心数"] * g["工艺_电压"] * 0.001
    
    def memory_power():
        return g["内存_容量"] * g["内存_频率"] * 0.0001
    
    def total_power():
        return g["CPU_功耗"] + g["GPU_功耗"] + g["内存_功耗"] + 10  # 10W基础功耗
    
    # 性能计算
    def cpu_performance():
        return g["CPU_核心数"] * g["工艺_频率"] * g["CPU_缓存"] * 0.1
    
    def gpu_performance():
        return g["GPU_核心数"] * g["工艺_频率"] * 0.01
    
    def memory_bandwidth():
        return g["内存_容量"] * g["内存_频率"] * 0.01
    
    def total_performance():
        return g["CPU_性能"] + g["GPU_性能"] + g["内存_带宽"] * 0.1
    
    # 效率和温度
    def efficiency():
        return g["总性能"] / g["总功耗"] if g["总功耗"] > 0 else 0
    
    def temperature():
        return 25 + g["总功耗"] * 0.5
    
    def thermal_throttling():
        return max(0, g["芯片温度"] - 80) * 0.01  # 超过80°C降频
    
    def effective_performance():
        return g["总性能"] * (1 - g["降频系数"])
    
    # 添加所有计算参数
    computations = [
        ("CPU_功耗", cpu_power, "CPU功耗计算"),
        ("GPU_功耗", gpu_power, "GPU功耗计算"),
        ("内存_功耗", memory_power, "内存功耗计算"),
        ("总功耗", total_power, "总功耗计算"),
        ("CPU_性能", cpu_performance, "CPU性能计算"),
        ("GPU_性能", gpu_performance, "GPU性能计算"),
        ("内存_带宽", memory_bandwidth, "内存带宽计算"),
        ("总性能", total_performance, "总性能计算"),
        ("能效比", efficiency, "能效比计算"),
        ("芯片温度", temperature, "芯片温度计算"),
        ("降频系数", thermal_throttling, "降频系数计算"),
        ("有效性能", effective_performance, "有效性能计算")
    ]
    
    print("\n📝 1. 构建复杂依赖网络")
    for name, func, desc in computations:
        g.add_computed(name, func, desc)
    
    print(f"创建了 {len(computations)} 个计算参数")
    
    print("\n📝 2. 分析依赖关系")
    dep_graph = g.get_dependency_graph()
    print("关键参数的依赖者:")
    key_params = ["工艺_电压", "工艺_频率", "CPU_核心数", "总功耗"]
    for param in key_params:
        if param in dep_graph:
            dependents = dep_graph[param]
            print(f"  {param} -> {dependents}")
    
    print("\n📝 3. 查看深度依赖链")
    deep_params = ["能效比", "有效性能", "降频系数"]
    for param in deep_params:
        chain = g.get_dependency_chain(param)
        print(f"  {param} 的完整依赖链: {' -> '.join(chain)}")
    
    print("\n📝 4. 初始性能评估")
    print(f"总功耗: {g['总功耗']:.2f}W")
    print(f"总性能: {g['总性能']:.2f}")
    print(f"芯片温度: {g['芯片温度']:.1f}°C")
    print(f"降频系数: {g['降频系数']:.3f}")
    print(f"有效性能: {g['有效性能']:.2f}")
    print(f"能效比: {g['能效比']:.3f}")
    
    print("\n📝 5. 测试工艺升级的影响")
    g["工艺_节点"] = 5
    g["工艺_电压"] = 1.2
    g["工艺_频率"] = 3.5
    
    print("升级到5nm工艺后:")
    print(f"总功耗: {g['总功耗']:.2f}W")
    print(f"总性能: {g['总性能']:.2f}")
    print(f"芯片温度: {g['芯片温度']:.1f}°C")
    print(f"降频系数: {g['降频系数']:.3f}")
    print(f"有效性能: {g['有效性能']:.2f}")
    print(f"能效比: {g['能效比']:.3f}")
    
    print("\n📝 6. 依赖关系图可视化")
    print("参数依赖关系图:")
    reverse_deps = g.get_reverse_dependency_graph()
    for param in ["有效性能", "能效比", "降频系数"]:
        deps = reverse_deps.get(param, [])
        if deps:
            print(f"  {param} <- {deps}")
    
    return g

def main():
    """主测试函数"""
    try:
        g1 = test_dependency_graph()
        g2 = test_dependency_refresh()
        g3 = test_complex_dependency_scenarios()
        
        print("\n" + "="*60)
        print("✅ 依赖关系图功能测试完成！")
        print("="*60)
        
        print("\n🎉 已实现的功能:")
        print("1. 📊 get_dependency_graph() - 获取正向依赖关系图")
        print("2. 🔄 get_reverse_dependency_graph() - 获取反向依赖关系图")
        print("3. 🔗 get_dependency_chain() - 获取完整依赖链")
        print("4. 📈 get_dependents_chain() - 获取依赖者链")
        print("5. 🔄 refresh_all_computed() - 刷新所有计算参数")
        print("6. 🎯 refresh_dependents() - 刷新指定参数的依赖者")
        print("7. ⚡ 自动依赖更新 - 参数修改时自动刷新依赖者")
        
        # 显示统计信息
        total_params = sum(len(g.keys()) for g in [g1, g2, g3])
        total_computed = sum(len(g._computed_parameters) for g in [g1, g2, g3])
        print(f"\n📊 测试统计:")
        print(f"  创建了 3 个图，总共 {total_params} 个参数")
        print(f"  其中计算参数 {total_computed} 个")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()