#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试无头模式下的基本功能
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from app import graph, layout_manager

def test_headless_basic_operations(dash_duo):
    """测试无头模式下的基本操作"""
    try:
        # 清理现有状态
        graph.nodes.clear()
        layout_manager.node_positions.clear()
        layout_manager.position_nodes.clear()
        layout_manager._init_grid()
        
        # 启动应用
        dash_duo.start_server(app)
        
        # 等待页面加载
        dash_duo.wait_for_element("#canvas-container", timeout=10)
        
        # 验证初始状态
        assert len(graph.nodes) == 0, "初始状态应该没有节点"
        assert len(layout_manager.node_positions) == 0, "初始状态应该没有布局信息"
        
        # 点击添加节点按钮
        add_node_btn = dash_duo.find_element("#add-node-from-graph-button")
        add_node_btn.click()
        
        # 等待模态框出现
        WebDriverWait(dash_duo.driver, 10).until(
            EC.presence_of_element_located((By.ID, "node-add-modal"))
        )
        
        # 输入节点信息
        name_input = dash_duo.find_element("#node-add-name")
        name_input.send_keys("测试节点")
        
        desc_input = dash_duo.find_element("#node-add-description")
        desc_input.send_keys("这是一个测试节点")
        
        # 保存节点
        save_btn = dash_duo.find_element("#node-add-save")
        save_btn.click()
        
        # 等待节点出现在画布上
        WebDriverWait(dash_duo.driver, 10).until(
            lambda d: len(graph.nodes) > 0
        )
        
        # 验证节点创建结果
        assert len(graph.nodes) == 1, "应该创建了一个节点"
        assert len(layout_manager.node_positions) == 1, "应该有一个节点的布局信息"
        
        # 获取创建的节点
        node = list(graph.nodes.values())[0]
        assert node.name == "测试节点", "节点名称应该正确"
        assert node.description == "这是一个测试节点", "节点描述应该正确"
        
        print("✅ 无头模式基本操作测试通过")
        
    except Exception as e:
        pytest.fail(f"无头模式测试失败: {e}")

def test_headless_layout_operations(dash_duo):
    """测试无头模式下的布局操作"""
    try:
        # 清理现有状态
        graph.nodes.clear()
        layout_manager.node_positions.clear()
        layout_manager.position_nodes.clear()
        layout_manager._init_grid()
        
        # 启动应用
        dash_duo.start_server(app)
        
        # 等待页面加载
        dash_duo.wait_for_element("#canvas-container", timeout=10)
        
        # 创建测试节点
        for i in range(3):
            # 点击添加节点按钮
            add_node_btn = dash_duo.find_element("#add-node-from-graph-button")
            add_node_btn.click()
            
            # 等待模态框出现
            WebDriverWait(dash_duo.driver, 10).until(
                EC.presence_of_element_located((By.ID, "node-add-modal"))
            )
            
            # 输入节点信息
            name_input = dash_duo.find_element("#node-add-name")
            name_input.send_keys(f"节点{i+1}")
            
            desc_input = dash_duo.find_element("#node-add-description")
            desc_input.send_keys(f"测试节点{i+1}")
            
            # 保存节点
            save_btn = dash_duo.find_element("#node-add-save")
            save_btn.click()
            
            # 等待节点创建完成
            WebDriverWait(dash_duo.driver, 10).until(
                lambda d: len(graph.nodes) == i + 1
            )
        
        # 验证节点创建
        assert len(graph.nodes) == 3, "应该创建了3个节点"
        assert len(layout_manager.node_positions) == 3, "应该有3个节点的布局信息"
        
        # 测试列管理
        add_col_btn = dash_duo.find_element("#add-column-btn")
        initial_cols = len(layout_manager.position_nodes)
        
        # 添加列
        add_col_btn.click()
        WebDriverWait(dash_duo.driver, 10).until(
            lambda d: len(layout_manager.position_nodes) == initial_cols + 1
        )
        
        assert len(layout_manager.position_nodes) == initial_cols + 1, "应该增加了一列"
        
        print("✅ 无头模式布局操作测试通过")
        
    except Exception as e:
        pytest.fail(f"无头模式布局测试失败: {e}")

def test_headless_parameter_operations(dash_duo):
    """测试无头模式下的参数操作"""
    try:
        # 清理现有状态
        graph.nodes.clear()
        layout_manager.node_positions.clear()
        layout_manager.position_nodes.clear()
        layout_manager._init_grid()
        
        # 启动应用
        dash_duo.start_server(app)
        
        # 等待页面加载
        dash_duo.wait_for_element("#canvas-container", timeout=10)
        
        # 创建测试节点
        add_node_btn = dash_duo.find_element("#add-node-from-graph-button")
        add_node_btn.click()
        
        # 等待模态框出现
        WebDriverWait(dash_duo.driver, 10).until(
            EC.presence_of_element_located((By.ID, "node-add-modal"))
        )
        
        # 输入节点信息
        name_input = dash_duo.find_element("#node-add-name")
        name_input.send_keys("参数测试节点")
        
        desc_input = dash_duo.find_element("#node-add-description")
        desc_input.send_keys("用于测试参数操作")
        
        # 保存节点
        save_btn = dash_duo.find_element("#node-add-save")
        save_btn.click()
        
        # 等待节点创建完成
        WebDriverWait(dash_duo.driver, 10).until(
            lambda d: len(graph.nodes) == 1
        )
        
        # 获取节点ID
        node = list(graph.nodes.values())[0]
        
        # 添加参数
        add_param_btn = dash_duo.find_element(f"button[data-dash-id*='{node.id}'][id*='add-param']")
        add_param_btn.click()
        
        # 等待参数输入框出现
        WebDriverWait(dash_duo.driver, 10).until(
            lambda d: len(node.parameters) == 1
        )
        
        # 验证参数创建
        assert len(node.parameters) == 1, "应该创建了一个参数"
        
        print("✅ 无头模式参数操作测试通过")
        
    except Exception as e:
        pytest.fail(f"无头模式参数测试失败: {e}") 