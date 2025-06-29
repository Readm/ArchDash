"""Session-based CalculationGraph manager.
每个浏览器会话（flask.session）对应一个 CalculationGraph 实例，解决多窗口数据串扰。
"""
from __future__ import annotations

import threading
import uuid
from typing import Dict

from flask import has_request_context, request
from urllib.parse import urlparse, parse_qs

from models import CalculationGraph, CanvasLayoutManager

# 线程安全锁
_lock = threading.Lock()

# sid -> CalculationGraph
SESSION_GRAPHS: Dict[str, CalculationGraph] = {}

# 默认全局计算图，用于缺少请求上下文（如启动时渲染布局等）
DEFAULT_GRAPH = CalculationGraph()
DEFAULT_GRAPH.set_layout_manager(CanvasLayoutManager(initial_cols=3, initial_rows=10))


def _get_session_id() -> str:
    """确保当前请求有唯一 sid，并返回。

    优先级：
    1. URL 查询参数 `_sid`（页面加载请求）。
    2. Referer 头中的 `_sid`（Dash 回调 POST 请求会携带 Referer）。
    3. 全新生成随机 sid。

    注意：当 sid 来自 URL 或 Referer 时 **不再写入 session['sid']**，
    以避免不同浏览器标签相互覆盖 cookie 引发的数据串扰。
    """

    if not has_request_context():
        return str(uuid.uuid4())  # 理论上不会触发，安全兜底

    # 1. 直接查询参数
    sid = request.args.get("_sid")

    # 2. Referer 中解析
    if not sid:
        ref = request.headers.get("Referer", "")
        if ref:
            try:
                qs = parse_qs(urlparse(ref).query)
                sid = qs.get("_sid", [None])[0]
            except Exception:
                sid = None

    # 3. 全新生成
    if not sid:
        sid = str(uuid.uuid4())

    # ⚠️ 无需写入 cookie
    return sid


def get_graph() -> CalculationGraph:
    """获取当前会话的 CalculationGraph；若无请求上下文则返回默认全局图。"""
    # 无活动请求时返回默认图（例如应用启动阶段）
    if not has_request_context():
        return DEFAULT_GRAPH

    # 有请求上下文，使用 session 隔离
    sid = _get_session_id()
    with _lock:
        if sid not in SESSION_GRAPHS:
            g = CalculationGraph()
            g.set_layout_manager(CanvasLayoutManager(initial_cols=3, initial_rows=10))
            SESSION_GRAPHS[sid] = g
        return SESSION_GRAPHS[sid]


def set_graph(graph: CalculationGraph) -> None:
    """显式替换当前会话的 CalculationGraph。若无请求上下文，则替换默认图。"""
    if not has_request_context():
        global DEFAULT_GRAPH
        DEFAULT_GRAPH = graph
        return

    sid = _get_session_id()
    with _lock:
        SESSION_GRAPHS[sid] = graph


class GraphProxy:
    """延迟代理，属性访问自动转发到当前 session 的 graph。"""

    __slots__ = ()

    def _target(self) -> CalculationGraph:  # noqa: D401
        return get_graph()

    def __getattr__(self, item):  # noqa: D401
        return getattr(self._target(), item)

    def __setattr__(self, key, value):  # noqa: D401
        return setattr(self._target(), key, value)

    def __repr__(self):  # noqa: D401
        return f"<GraphProxy to {repr(self._target())}>" 