#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T520 - 测试
从原始测试文件分离出的独立测试
"""

import pytest
from flask import Flask, request
from session_graph import get_graph, SESSION_GRAPHS

def test_graph_isolation_by_sid():
    app = create_app()

    # 第一次请求，sid=A
    with app.test_request_context('/?_sid=A'):
        g1 = get_graph()
        # 在 g1 中记录一个字段，便于后续断言
        g1.test_attr = 'graph_A'

    # 第二次请求，sid=B
    with app.test_request_context('/?_sid=B'):
        g2 = get_graph()
        g2.test_attr = 'graph_B'

    # 第三次请求，sid=A，再次获取
    with app.test_request_context('/?_sid=A'):
        g1_again = get_graph()

    # 断言：同一 sid 获得同一实例
    assert g1 is g1_again, "同一 _sid 应获得同一 CalculationGraph 实例"
    # 断言：不同 sid 获得不同实例
    assert g1 is not g2, "不同 _sid 应获得不同 CalculationGraph 实例"
    # 断言：实例中的自定义属性不互相覆盖
    assert getattr(g1_again, 'test_attr', None) == 'graph_A'
    assert getattr(g2, 'test_attr', None) == 'graph_B'

    # 可选：确保 SESSION_GRAPHS 字典中恰好包含两个 sid
    assert set(SESSION_GRAPHS.keys()) >= {'A', 'B'}

if __name__ == "__main__":
    test_graph_isolation_by_sid()
    print("✅ T520 测试通过")
