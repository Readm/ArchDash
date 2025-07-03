from utils import clean_state, wait_for_page_load, create_node, wait_for_element, wait_for_clickable, wait_for_node_count
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T516 - 测试
从原始测试文件分离出的独立测试
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
import time

def test_single_node_creation(selenium, flask_app):
    """测试创建单个节点"""
    try:
        print("\n========== 开始单节点创建测试 ==========")
        
        print("\n第1步：清理应用状态")
        clean_state(selenium)  # 使用默认的全局导入
        time.sleep(2)  # 等待清理完成
        
        print("\n第2步：创建测试节点")
        create_node(selenium, "TestNode", "测试节点")
        time.sleep(2)  # 等待节点创建完成
        
        print("\n第3步：分析页面内容")
        page_source = selenium.page_source
        print("\n当前页面HTML:")
        print(page_source)
        
        print("\n尝试查找所有可能的节点相关元素:")
        # 尝试各种选择器
        selectors = [
            "[data-dash-id*='node']",  # Dash节点标识
            '[data-testid="node-container"]',         # 节点容器类
            ".node-entrance",          # 节点入场动画类
            "[id^='node-']",          # 以node-开头的ID
            ".node-container",        # 节点容器类
            "[class*='node']",        # 包含node的类名
        ]
        
        for selector in selectors:
            try:
                elements = selenium.find_elements(By.CSS_SELECTOR, selector)
                print(f"选择器 '{selector}' 找到 {len(elements)} 个元素")
                if elements:
                    for i, elem in enumerate(elements[:3]):  # 只显示前3个
                        print(f"  元素 {i+1}: {elem.get_attribute('outerHTML')[:200]}...")
            except Exception as e:
                print(f"选择器 '{selector}' 出错: {e}")
        
        print("\n第4步：验证节点创建")
        # 等待节点出现
        time.sleep(3)
        
        # 检查节点数量
        node_count = get_node_count(selenium)
        print(f"当前节点数量: {node_count}")
        
        # 检查页面是否包含节点相关信息
        page_text = selenium.page_source
        if "TestNode" in page_text:
            print("✅ 页面包含节点名称")
        else:
            print("❌ 页面不包含节点名称")
            
        if "测试节点" in page_text:
            print("✅ 页面包含节点描述")
        else:
            print("❌ 页面不包含节点描述")
        
        # 基本断言
        assert node_count >= 1, f"期望至少1个节点，实际找到 {node_count} 个"
        assert "TestNode" in page_text, "页面应该包含节点名称"
        assert "测试节点" in page_text, "页面应该包含节点描述"
        
        print("✅ 单节点创建测试通过")
        
    except Exception as e:
        print(f"❌ 单节点创建测试失败: {e}")
        # 保存页面截图和源码用于调试
        try:
            selenium.save_screenshot(f"test_failure_{int(time.time())}.png")
            with open(f"test_failure_{int(time.time())}.html", "w", encoding="utf-8") as f:
                f.write(selenium.page_source)
        except:
            pass
        raise

if __name__ == "__main__":
    test_single_node_creation()
    print("✅ T516 测试通过")
