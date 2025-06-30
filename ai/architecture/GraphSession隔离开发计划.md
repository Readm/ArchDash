# 会话级 CalculationGraph 隔离 – 开发任务清单

> 目标：将现有全局 `graph` 改造为「每个浏览器会话独享」的实例，互不串数据。

---

## 1. Session 体系设计

- [ ] 采用 Flask 原生 `session` 生成 `sid`；若需要跨进程，建议引入 `Flask-Session + Redis`。
- [ ] 编写 `get_session_id()`：检测 `session["sid"]`，若不存在则生成 `uuid4()` 并写入 cookie。
- [ ] 在 `ai` 层统一维护 `SESSION_GRAPHS: dict[str, CalculationGraph]`。
- [ ] 编写 `get_graph()`：
  1. 调用 `get_session_id()` 取 `sid`。
  2. 若 `sid` 不在 `SESSION_GRAPHS`，创建新的 `CalculationGraph` 并初始化 `CanvasLayoutManager`。
  3. 返回对应实例。

## 2. app.py 改造

- [ ] **删除** 顶层全局 `graph`、`graph.set_layout_manager(...)` 相关初始化。
- [ ] 在文件顶部 `from ai.session_graph import get_graph`（或其它命名）。
- [ ] 全局搜索 ` graph.` → 在每个 **回调** 或 **业务函数** 的开头插入：
  ```python
  graph = get_graph()
  ```
  并删掉之前对全局变量的依赖。
- [ ] 对 `auto_remove_empty_last_column()`、`ensure_minimum_columns()` 等辅助函数：内部第一行 `graph = get_graph()`。
- [ ] 检查所有 `global graph` 声明，全部移除。

## 3. models.py 兼容

- [ ] **无需改动**：`CalculationGraph` 内部状态已经自洽，只是引用方式变化。
- [ ] 确认 `CalculationGraph.from_dict` / `to_dict` 不依赖全局变量。

## 4. 内存与过期策略

- [ ] 简易版本：`SESSION_GRAPHS` 存在进程内存，不做清理。
- [ ] 生产版：
  - [ ] 引入 `redis-py`，使用 `Flask-Session` 配置 Redis 存储。
  - [ ] `SESSION_GRAPHS` 换成 Redis Hash 或 Pickle 序列化。
  - [ ] 设置 TTL（如 2 小时），后台周期性清理。

## 5. 并发 & 线程安全

- [ ] 若部署方式为 Gunicorn 多进程，进程内字典无法共享，必须启用 Redis 方案。
- [ ] 若仅单进程开发环境，可先跳过。

## 6. 单元测试

- [ ] 编写 `tests/test_session_graph.py`：
  - [ ] 模拟两个不同 `sid`，确保 `get_graph()` 返回不同对象。
  - [ ] 同一 `sid` 多次调用，返回同一对象（`id()` 相同）。

## 7. 文档与 README 更新

- [ ] 在 `README.md` 添加「会话隔离」说明。
- [ ] 描述如何开启 Redis 以及相关环境变量：`REDIS_URL`、`SESSION_TYPE=redis` 等。

---

完成以上步骤后即可实现每个会话独立的计算图，彻底解决多窗口数据混淆的问题。 