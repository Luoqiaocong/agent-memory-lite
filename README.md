# agent-memory-lite

基于 `SQLModel` + `SQLite` 的轻量级 Agent 长期记忆组件，配合 LangChain / LangGraph 工具调用使用。

## 分层结构

```text
ai/tool.py   ──▶ 对接大模型工具入参（@tool 包装为 StructuredTool）
    │
service.py   ──▶ 业务编排：Prompt 组装（透出 id）、ExtractedFact -> Fact 转换
    │
repo.py      ──▶ 纯仓储层：只面向数据库 ORM 模型 Fact，负责事务与增删改查
    │
db.py        ──▶ SQLModel Engine 初始化与建表（默认 sqlite:///data/memory.db）
schema.py    ──▶ 数据模型：Fact（ORM 表）与 ExtractedFact（工具提取入参）
```

> **分层约定**：`ExtractedFact` 止步于 `service.py`，由 `service.record_fact` 拆包成 `(Fact, replace_id)` 再交给 `repo.save_facts`，保持 `repo.py` 不耦合 AI 提取 schema。

## 核心设计取舍

1. **单值覆盖 vs 多值按 ID 替换**
   - **单值键**（`SINGLE_VALUE_KEYS = {"location", "name", "job"}`）：同键新值写入时自动停用旧值并记录 `previous_value`。
   - **多值键**（如 `preference`、`skill`、`allergy`）：查询时在文本中附带记录 ID（如 `黑咖啡(3)`）；需要替换或纠错时，模型直接把该 `id` 填入 `upsert_long_memory` 的 `replace_id` 参数即可单次完成替换，无需再“先遗忘再保存”，也不依赖易出错的文本匹配或额外 LLM 后台重算。
   - **彻底遗忘**：只有无新值替代的放弃（如“戒掉咖啡了”）才调用 `forget_long_memory`。

2. **软删除与变更轨迹**
   - 替换与遗忘均采用软删除（`is_active = 0`），通过 `previous_value` 保留前任值；同一事实被再次提及时累加 `hit_count` 进行加固。

3. **SQLModel 双重模型**
   - `Fact(SQLModel, table=True)` 用于数据库建表与 ORM 查询；`ExtractedFact(SQLModel)` 不带 `table=True`，仅用于 Pydantic 校验与大模型结构化工具参数描述。

## 快速开始

```bash
# 安装依赖
uv sync

# 运行交互式对话示例（需在 .env 配置 OPENCODE_BASE_URL / OPENCODE_API_KEY）
uv run python demo.py

# 运行单元测试（基于 pytest + 临时 SQLite，不触碰 data/memory.db）
uv run pytest -v
```
