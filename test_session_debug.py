#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试会话管理问题的脚本
"""

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_session_management():
    """测试会话管理问题"""
    
    print("🔬 开始测试会话管理问题")
    
    # 设置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 1. 首先访问主页，建立会话
        print("📍 Step 1: 访问主页")
        driver.get("http://localhost:8050")
        
        # 检查是否有会话标识符
        current_url = driver.current_url
        print(f"🔗 当前URL: {current_url}")
        
        # 等待页面加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "canvas-container"))
        )
        
        # 检查是否显示空状态
        canvas = driver.find_element(By.ID, "canvas-container")
        print(f"🎨 Canvas内容: {canvas.get_attribute('innerHTML')[:200]}...")
        
        # 2. 手动添加sid参数到URL
        print("📍 Step 2: 添加会话标识符")
        import uuid
        sid = str(uuid.uuid4())
        
        # 重新访问带有sid的URL
        driver.get(f"http://localhost:8050?_sid={sid}")
        print(f"🔗 新URL: {driver.current_url}")
        
        # 等待页面加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "canvas-container"))
        )
        
        # 3. 尝试创建节点
        print("📍 Step 3: 尝试创建节点")
        
        # 点击添加节点按钮
        add_node_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "add-node-from-graph-button"))
        )
        add_node_btn.click()
        
        # 等待模态框出现
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "node-add-modal"))
        )
        
        # 填写节点信息
        name_input = driver.find_element(By.ID, "node-add-name")
        name_input.clear()
        name_input.send_keys("测试节点")
        
        # 填写描述
        desc_input = driver.find_element(By.ID, "node-add-description")
        desc_input.clear()
        desc_input.send_keys("这是一个测试节点")
        
        # 点击保存
        save_btn = driver.find_element(By.ID, "node-add-save")
        save_btn.click()
        
        # 等待模态框关闭
        WebDriverWait(driver, 10).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".modal.show"))
        )
        
        # 4. 检查节点是否创建成功
        print("📍 Step 4: 检查节点是否创建成功")
        
        # 等待一段时间让回调执行
        time.sleep(2)
        
        # 重新获取canvas内容
        canvas = driver.find_element(By.ID, "canvas-container")
        canvas_html = canvas.get_attribute('innerHTML')
        print(f"🎨 创建后Canvas内容: {canvas_html[:500]}...")
        
        # 检查是否有节点容器
        nodes = driver.find_elements(By.CSS_SELECTOR, ".node-container")
        print(f"🎯 找到节点数量: {len(nodes)}")
        
        # 5. 使用不同的会话ID重新访问
        print("📍 Step 5: 使用不同会话ID重新访问")
        new_sid = str(uuid.uuid4())
        driver.get(f"http://localhost:8050?_sid={new_sid}")
        
        # 等待页面加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "canvas-container"))
        )
        
        # 检查节点是否还在
        nodes_after = driver.find_elements(By.CSS_SELECTOR, ".node-container")
        print(f"🎯 使用新会话ID后的节点数量: {len(nodes_after)}")
        
        # 6. 使用原始会话ID再次访问
        print("📍 Step 6: 使用原始会话ID再次访问")
        driver.get(f"http://localhost:8050?_sid={sid}")
        
        # 等待页面加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "canvas-container"))
        )
        
        # 检查节点是否还在
        nodes_original = driver.find_elements(By.CSS_SELECTOR, ".node-container")
        print(f"🎯 使用原始会话ID后的节点数量: {len(nodes_original)}")
        
        print("✅ 会话管理测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    test_session_management() 