import pytest
from models import CanvasLayoutManager, GridPosition

def test_layout_manager_basic_operations():
    """测试布局管理器的基本操作"""
    layout = CanvasLayoutManager(initial_cols=3, initial_rows=5)
    
    # 测试添加节点
    pos1 = layout.place_node("node1")
    assert pos1.row == 0 and pos1.col == 0
    
    pos2 = layout.place_node("node2")
    assert pos2.row == 1 and pos2.col == 0  # 在第一列的下一行
    
    # 测试指定位置放置节点
    specific_pos = GridPosition(0, 2)
    pos3 = layout.place_node("node3", specific_pos)
    assert pos3 == specific_pos
    
    print("✅ 基本操作测试通过")
    print(layout.print_layout())

def test_layout_manager_node_movements():
    """测试节点移动功能"""
    layout = CanvasLayoutManager(initial_cols=3, initial_rows=5)
    
    # 创建测试节点
    layout.place_node("nodeA", GridPosition(0, 0))
    layout.place_node("nodeB", GridPosition(1, 0))
    layout.place_node("nodeC", GridPosition(2, 0))
    
    print("初始布局:")
    print(layout.print_layout())
    
    # 测试节点上移
    success = layout.move_node_up("nodeB")
    assert success == True
    assert layout.get_node_position("nodeB") == GridPosition(0, 0)
    assert layout.get_node_position("nodeA") == GridPosition(1, 0)  # 被交换了
    
    print("nodeB上移后:")
    print(layout.print_layout())
    
    # 测试节点右移
    success = layout.move_node_right("nodeB")
    assert success == True
    assert layout.get_node_position("nodeB").col == 1
    
    print("nodeB右移后:")
    print(layout.print_layout())
    
    print("✅ 节点移动测试通过")

def test_layout_manager_column_operations():
    """测试列操作"""
    layout = CanvasLayoutManager(initial_cols=2, initial_rows=3)
    
    # 填充一些节点
    layout.place_node("n1", GridPosition(0, 0))
    layout.place_node("n2", GridPosition(1, 0))
    layout.place_node("n3", GridPosition(0, 1))
    
    # 测试获取列节点
    col0_nodes = layout.get_column_nodes(0)
    assert len(col0_nodes) == 2
    assert ("n1", 0) in col0_nodes
    assert ("n2", 1) in col0_nodes
    
    col1_nodes = layout.get_column_nodes(1)
    assert len(col1_nodes) == 1
    assert ("n3", 0) in col1_nodes
    
    print("✅ 列操作测试通过")

def test_layout_serialization():
    """测试布局序列化"""
    layout = CanvasLayoutManager(initial_cols=2, initial_rows=3)
    
    # 添加节点
    layout.place_node("node1", GridPosition(0, 0))
    layout.place_node("node2", GridPosition(1, 1))
    
    # 获取布局字典
    layout_dict = layout.get_layout_dict()
    
    # 验证结构
    assert "grid_size" in layout_dict
    assert "node_positions" in layout_dict
    assert "column_layouts" in layout_dict
    
    assert layout_dict["grid_size"]["rows"] == 3
    assert layout_dict["grid_size"]["cols"] == 2
    assert layout_dict["node_positions"]["node1"] == {"row": 0, "col": 0}
    assert layout_dict["node_positions"]["node2"] == {"row": 1, "col": 1}
    
    print("✅ 序列化测试通过")
    print("布局字典:", layout_dict)

if __name__ == "__main__":
    test_layout_manager_basic_operations()
    test_layout_manager_node_movements() 
    test_layout_manager_column_operations()
    test_layout_serialization()
    print("🎉 所有布局管理器测试通过！") 