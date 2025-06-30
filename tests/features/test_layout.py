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

def test_layout_manager_add_remove_columns():
    """测试添加和删除列功能"""
    layout = CanvasLayoutManager(initial_cols=2, initial_rows=3)
    initial_cols = layout.cols
    
    print(f"初始列数: {initial_cols}")
    print("初始布局:")
    print(layout.print_layout())
    
    # 测试添加列
    layout.add_column()
    assert layout.cols == initial_cols + 1
    print(f"添加列后列数: {layout.cols}")
    
    # 测试删除空列（应该成功）
    success = layout.remove_column()
    assert success == True
    assert layout.cols == initial_cols
    print(f"删除空列后列数: {layout.cols}")
    
    # 在最后一列放置一个节点
    layout.add_column()  # 先添加一列
    layout.place_node("test_node", GridPosition(0, layout.cols - 1))  # 放在最后一列
    
    print("在最后一列放置节点后:")
    print(layout.print_layout())
    
    # 尝试删除非空的最后一列（应该失败）
    success = layout.remove_column()
    assert success == False
    print(f"尝试删除非空列后列数: {layout.cols} (应该没有变化)")
    
    # 移除节点后再尝试删除列
    layout.remove_node("test_node")
    success = layout.remove_column()
    assert success == True
    print(f"删除节点后再删除列，当前列数: {layout.cols}")
    
    print("✅ 添加和删除列测试通过")

def test_layout_manager_remove_column_edge_cases():
    """测试删除列的边界情况"""
    # 测试只有一列时不能删除
    layout = CanvasLayoutManager(initial_cols=1, initial_rows=3)
    
    success = layout.remove_column()
    assert success == False
    assert layout.cols == 1
    print("✅ 正确阻止删除最后一列")
    
    # 测试多列情况下删除到只剩一列
    layout = CanvasLayoutManager(initial_cols=3, initial_rows=3)
    initial_cols = layout.cols
    
    # 删除所有空列直到只剩一列
    deleted_count = 0
    while layout.cols > 1:
        success = layout.remove_column()
        if success:
            deleted_count += 1
        else:
            break
    
    assert layout.cols == 1
    assert deleted_count == initial_cols - 1
    print(f"✅ 成功删除了 {deleted_count} 个空列，剩余 {layout.cols} 列")
    
    # 确认现在不能再删除
    success = layout.remove_column()
    assert success == False
    assert layout.cols == 1
    
    print("✅ 删除列边界情况测试通过")

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
    test_layout_manager_add_remove_columns()
    test_layout_manager_remove_column_edge_cases()
    test_layout_serialization()
    print("🎉 所有布局管理器测试通过！") 