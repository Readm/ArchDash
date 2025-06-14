import pytest
from dash import html
from app import app, id_mapper
from selenium.webdriver.common.by import By

def test_add_node(dash_duo):
    dash_duo.start_server(app, debug=False)

    # Check title
    assert dash_duo.find_element("h1").text == "ArchDash"

    # Input node name
    input_box = dash_duo.find_element("#node-name")
    input_box.send_keys("TestNode")

    # Click add node button
    add_btn = dash_duo.find_element("#add-node-button")
    add_btn.click()

    # Print actual content, help debug
    print("Actual output:", dash_duo.find_element("#output-result").text)

    # Check if new node appears in canvas
    dash_duo.wait_for_contains_text("#output-result", "节点 TestNode 已添加", timeout=5)

    # Print all element IDs on the page for debugging
    print("All element IDs on the page:", dash_duo.driver.find_elements(By.CSS_SELECTOR, "*[id]"))

    # Get the first node's id
    node_id = list(id_mapper._node_mapping.keys())[0]
    node_html_id = id_mapper.get_html_id(node_id)
    print("Generated node_html_id:", node_html_id)  # 打印生成的 node_html_id
    node = dash_duo.find_element(f"#{node_html_id}")
    assert node is not None
    assert "TestNode" in node.text

    # Print any errors from the Dash app
    errors = dash_duo.get_logs()
    if errors:
        print("Dash app errors:", errors)

    # 获取第一个节点的 ID
    node_id = list(id_mapper._node_mapping.keys())[0]
    node = dash_duo.find_element(id_mapper.get_html_id(node_id))
    node.click()
    dash_duo.wait_for_element("#context-menu", timeout=5)

    # 选择左移
    dash_duo.click("#move-left")
    dash_duo.wait_for_text_to_equal("#output-result", "节点 TestNode 已左移", timeout=2)

    # 选择右移
    node = dash_duo.find_element(id_mapper.get_html_id(node_id))
    node.click()
    dash_duo.wait_for_element("#context-menu", timeout=5)
    dash_duo.click("#move-right")
    dash_duo.wait_for_text_to_equal("#output-result", "节点 TestNode 已右移", timeout=2)

    # 添加参数
    node = dash_duo.find_element(id_mapper.get_html_id(node_id))
    node.click()
    dash_duo.wait_for_element("#context-menu", timeout=5)
    dash_duo.click("#add-parameter")
    dash_duo.wait_for_text_to_equal("#output-result", "已为节点 TestNode 添加参数", timeout=2) 