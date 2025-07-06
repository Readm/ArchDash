#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试节点创建过程的脚本
"""

import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def debug_node_creation():
    """调试节点创建流程"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🔧 开始调试节点创建流程")
        
        # 访问应用
        driver.get("http://localhost:8050")
        print("✅ 页面加载完成")
        
        # 等待页面完全加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "canvas-container"))
        )
        print("✅ 画布容器已出现")
        
        # 检查添加节点按钮
        add_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='add-node-button']")
        print(f"✅ 添加节点按钮存在: {add_button.is_displayed()}")
        
        # 点击按钮
        driver.execute_script("arguments[0].scrollIntoView(true);", add_button)
        time.sleep(0.5)
        add_button.click()
        print("✅ 添加节点按钮已点击")
        
        # 等待模态框出现
        try:
            modal = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "node-add-modal"))
            )
            print("✅ 模态框已出现")
        except Exception as e:
            print(f"❌ 模态框未出现: {e}")
            print("当前页面源码:")
            print(driver.page_source)
            return
        
        # 填写节点信息
        name_input = driver.find_element(By.ID, "node-add-name")
        name_input.clear()
        name_input.send_keys("调试节点")
        print("✅ 节点名称已填写")
        
        desc_input = driver.find_element(By.ID, "node-add-description")
        desc_input.clear()
        desc_input.send_keys("这是一个调试节点")
        print("✅ 节点描述已填写")
        
        # 保存节点
        save_btn = driver.find_element(By.ID, "node-add-save")
        save_btn.click()
        print("✅ 保存按钮已点击")
        
        # 等待模态框关闭
        WebDriverWait(driver, 10).until_not(
            EC.visibility_of_element_located((By.ID, "node-add-modal"))
        )
        print("✅ 模态框已关闭")
        
        # 等待节点出现
        time.sleep(2)
        
        # 检查节点是否存在
        nodes = driver.find_elements(By.CSS_SELECTOR, ".node-container")
        print(f"📊 找到 {len(nodes)} 个节点容器")
        
        for i, node in enumerate(nodes):
            print(f"节点 {i+1}:")
            print(f"  - 文本: {node.text}")
            print(f"  - 可见: {node.is_displayed()}")
            print(f"  - ID: {node.get_attribute('id')}")
            print(f"  - Class: {node.get_attribute('class')}")
        
        # 查找包含"调试节点"的节点
        target_nodes = [node for node in nodes if "调试节点" in node.text and node.is_displayed()]
        print(f"📊 包含'调试节点'的可见节点: {len(target_nodes)}")
        
        if target_nodes:
            print("✅ 节点创建成功!")
        else:
            print("❌ 节点创建失败!")
            print("\n完整页面源码:")
            print(driver.page_source[-2000:])  # 只打印最后2000字符
        
    except Exception as e:
        print(f"❌ 调试过程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_node_creation() 