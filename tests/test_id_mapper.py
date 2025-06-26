import pytest
from src.models.id_mapper import IDMapper

def test_register_node():
    mapper = IDMapper()
    mapper.register_node("node1", "Test Node")
    assert mapper.get_node_name("node1") == "Test Node"

def test_get_dash_id():
    mapper = IDMapper()
    dash_id = mapper.get_dash_id("node1")
    assert dash_id == {"type": "node", "index": "node1"}

def test_get_html_id():
    mapper = IDMapper()
    html_id = mapper.get_html_id("node1")
    assert html_id == "node-node1"

def test_get_node_id_from_dash():
    mapper = IDMapper()
    dash_id = {"type": "node", "index": "node1"}
    node_id = mapper.get_node_id_from_dash(dash_id)
    assert node_id == "node1"

def test_update_node_name():
    mapper = IDMapper()
    mapper.register_node("node1", "Old Name")
    mapper.update_node_name("node1", "New Name")
    assert mapper.get_node_name("node1") == "New Name"

def test_get_nonexistent_node_name():
    mapper = IDMapper()
    assert mapper.get_node_name("nonexistent") == "" 