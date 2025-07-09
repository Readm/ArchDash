#!/usr/bin/env python3
"""
测试画布事件驱动机制
"""
import sys
sys.path.append('.')

def test_canvas_events():
    """测试画布事件机制"""
    print("🔧 测试画布事件驱动机制")
    print("=" * 50)
    
    # 测试1：导入检查
    try:
        from app import app, create_canvas_event, add_canvas_event
        print("✅ 1. 模块导入成功")
    except Exception as e:
        print(f"❌ 1. 模块导入失败: {e}")
        return
    
    # 测试2：事件创建
    try:
        test_event = create_canvas_event("test_event", {"message": "test"})
        expected_keys = {"type", "timestamp", "data"}
        if set(test_event.keys()) == expected_keys:
            print("✅ 2. 事件创建成功")
        else:
            print(f"❌ 2. 事件结构错误: {test_event.keys()}")
    except Exception as e:
        print(f"❌ 2. 事件创建失败: {e}")
    
    # 测试3：事件队列管理
    try:
        events = []
        for i in range(12):  # 超过10个事件
            event = create_canvas_event(f"event_{i}", {"index": i})
            events = add_canvas_event(events, event)
        
        if len(events) == 10:  # 应该只保留最近10个
            print("✅ 3. 事件队列管理正常")
        else:
            print(f"❌ 3. 事件队列大小错误: {len(events)}")
    except Exception as e:
        print(f"❌ 3. 事件队列管理失败: {e}")
    
    # 测试4：callback注册检查
    try:
        callbacks = app.callback_map
        print(f"✅ 4. 应用有 {len(callbacks)} 个callback")
        
        # 检查是否有canvas-container相关的callback
        canvas_callbacks = [key for key in callbacks.keys() if "canvas-container" in key]
        if canvas_callbacks:
            print(f"✅ 4. 发现 {len(canvas_callbacks)} 个canvas相关callback")
        else:
            print("❌ 4. 没有发现canvas相关callback")
            
    except Exception as e:
        print(f"❌ 4. callback检查失败: {e}")
    
    # 测试5：启动应用（不运行服务器）
    try:
        app.layout = app.layout  # 触发布局设置
        print("✅ 5. 应用布局设置成功")
    except Exception as e:
        print(f"❌ 5. 应用布局设置失败: {e}")
    
    print("=" * 50)
    print("🎯 测试建议:")
    print("- 如果所有测试通过，可以启动应用: python3 app.py")
    print("- 然后在浏览器中测试节点移动功能")
    print("- 观察控制台是否有错误信息")

if __name__ == "__main__":
    test_canvas_events()