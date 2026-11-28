from types import SimpleNamespace
from typing import Any, cast

import pytest
from langchain.agents.middleware import ModelRequest

from agent_memory_lite.ai.middleware import MemoryContext, build_memory_middleware
from agent_memory_lite.ai.tool import build_memory_tools
from agent_memory_lite.schema import ExtractedFact
from agent_memory_lite.service import MemoryService
@pytest.fixture
def service(tmp_path):  # tmp_path 是 pytest 白送的临时文件夹，每个测试互不干扰
    db_url = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    svc = MemoryService(db_url=db_url)
    yield svc                   # yield 之前是“准备”，把 svc 交出去给测试函数用
    svc.repo.engine.dispose()   # yield 之后是“收尾”，测试一结束自动释放数据库连接
    
    
def test_empty_memory(service:MemoryService):
    assert service.build_memory_prompt("user_101") == ""
    
def test_record_fact(service:MemoryService):
    assert service.record_fact("user_101", [ExtractedFact(fact_key="preference", fact_value="basketball")]) == "ok"
    fact = service.get_user_facts("user_101")[0]
    assert fact.fact_key == "preference"
    assert fact.fact_value == "basketball"
    assert fact.user_id == "user_101"
    
    service.record_fact("user_101", [ExtractedFact(fact_key="preference", fact_value="basketball")])
    fact = service.get_user_facts("user_101")[0]
    assert fact.hit_count == 2
    assert fact.previous_value is None
    
def test_update_fact(service:MemoryService):
    service.record_fact("user_101", [ExtractedFact(fact_key="location", fact_value="北京")])
    service.record_fact("user_101", [ExtractedFact(fact_key="location", fact_value="杭州")])
    # 注意：仓储层每次用完即关闭 Session，先前查出的旧 Fact 对象只是离线快照，不会随数据库更新而自动刷新；
    # 因此这里重新调用 get_user_facts 查库验证旧值已被停用、仅剩新值
    facts = service.get_user_facts("user_101")

    assert len(facts) == 1
    assert facts[0].fact_value == "杭州"
    assert facts[0].previous_value == "北京"

def test_replace_fact_by_id(service:MemoryService):
    service.record_fact("user_101", [ExtractedFact(fact_key="preference", fact_value="篮球")])
    old_id = service.get_user_facts("user_101")[0].id
    assert old_id is not None
    assert f"preference:篮球({old_id})" in service.build_memory_prompt("user_101")

    service.record_fact("user_101", [ExtractedFact(fact_key="preference", fact_value="跑步", replace_id=old_id)])
    facts = service.get_user_facts("user_101")

    assert len(facts) == 1
    assert facts[0].fact_value == "跑步"
    assert facts[0].previous_value == "篮球"


def test_forget_fact(service:MemoryService):
    service.record_fact("user_101", [ExtractedFact(fact_key="preference", fact_value="篮球")])

    assert service.forget_fact("user_101", "preference", "篮球") == "ok"
    assert service.get_user_facts("user_101") == []
    assert service.forget_fact("user_101", "preference", "篮球") == "not found"


def test_multi_value_and_user_isolation(service:MemoryService):
    service.record_fact(
        "user_101",
        [
            ExtractedFact(fact_key="preference", fact_value="篮球"),
            ExtractedFact(fact_key="preference", fact_value="旅游"),
        ],
    )
    service.record_fact("user_102", [ExtractedFact(fact_key="location", fact_value="杭州")])

    # next(...) 配合生成器表达式：惰性查找第一个满足条件的记录并取其 id，拿到即停（若一条都找不到会抛 StopIteration）
    basketball_id = next(
        f.id for f in service.get_user_facts("user_101") if f.fact_value == "篮球"
    )
    assert basketball_id is not None

    service.record_fact(
        "user_101",
        [ExtractedFact(fact_key="preference", fact_value="跑步", replace_id=basketball_id)],
    )

    user1_values = {f.fact_value for f in service.get_user_facts("user_101")}
    user2_values = [f.fact_value for f in service.get_user_facts("user_102")]
    assert user1_values == {"跑步", "旅游"}
    assert user2_values == ["杭州"]


def test_memory_tools(service:MemoryService):
    tools = {t.name: t for t in build_memory_tools(service)}
    get_long_memory,forget_long_memory, upsert_long_memory = tools["get_long_memory"], tools["forget_long_memory"], tools["upsert_long_memory"]

    assert get_long_memory.invoke({"user_id": "user_101"}) == ""

    # @tool 会把函数包装成 LangChain StructuredTool，需通过 .invoke(字典) 调用，顺带验证 Pydantic 入参解析
    res = upsert_long_memory.invoke(
        {
            "user_id": "user_101",
            "facts": [{"fact_key": "preference", "fact_value": "黑咖啡"}],
        }
    )
    assert res == "ok"

    prompt = get_long_memory.invoke({"user_id": "user_101"})
    assert "preference:黑咖啡(" in prompt

    assert (
        forget_long_memory.invoke(
            {"user_id": "user_101", "fact_key": "preference", "fact_value": "黑咖啡"}
        )
        == "ok"
    )
    assert get_long_memory.invoke({"user_id": "user_101"}) == ""


def test_memory_middleware(service: MemoryService):
    middleware = build_memory_middleware(service)

    def run_middleware(context: MemoryContext | None) -> str | None:
        captured: dict[str, str | None] = {}
        req = ModelRequest(
            model=cast(Any, None),
            messages=[],
            system_prompt="你是私人助手",
            runtime=cast(Any, SimpleNamespace(context=context)),
        )
        # 拦截传给下游模型的最终请求，检查 system_prompt 是否按预期注入
        middleware.wrap_model_call(
            req,
            lambda new_req: cast(Any, captured.update({"prompt": new_req.system_prompt}) or "ok"),
        )
        return captured["prompt"]

    # 1. 新用户或未传上下文时，保留原提示词不被覆盖为空
    assert run_middleware(None) == "你是私人助手"
    assert run_middleware(MemoryContext(user_id="user_101")) == "你是私人助手"

    # 2. 有记忆后，原提示词与长期记忆一起注入
    service.record_fact("user_101", [ExtractedFact(fact_key="location", fact_value="杭州")])
    injected = run_middleware(MemoryContext(user_id="user_101"))
    assert injected is not None
    assert injected.startswith("你是私人助手\n\n[已知用户长期记忆]")
    assert "location:杭州(" in injected


def test_fact_history(service: MemoryService):
    tools = {t.name: t for t in build_memory_tools(service)}
    get_history = tools["get_long_memory_history"]

    # 未记录过的键返回 not found
    assert get_history.invoke({"user_id": "user_101", "fact_key": "allergy"}) == "not found"

    # 连续迁移三次：北京 -> 杭州 -> 上海
    for city in ("北京", "杭州", "上海"):
        service.record_fact("user_101", [ExtractedFact(fact_key="location", fact_value=city)])

    history = get_history.invoke({"user_id": "user_101", "fact_key": "location"})
    assert "当前生效记忆：\n- location:上海" in history
    assert "历史记录：" in history
    assert "- location:杭州" in history
    assert "- location:北京" in history
    assert history.index("杭州") < history.index("北京")

    # 彻底遗忘当前生效记忆后，不应出现空“当前生效记忆：”标题
    assert service.forget_fact("user_101", "location", "上海") == "ok"
    after_forget = service.get_fact_history("user_101", "location")
    assert "当前生效记忆" not in after_forget
    assert "- location:上海" in after_forget


def test_semantic_search(service: MemoryService):
    vecs = {
        "preference:拿铁": [1.0, 0.0],
        "skill:Python": [0.0, 1.0],
        "想喝咖啡": [1.0, 0.0],
        "写请假条": [-1.0, 0.0],
    }
    service.embedder = lambda texts: [vecs[t] for t in texts]

    service.record_fact(
        "user_101",
        [
            ExtractedFact(fact_key="preference", fact_value="拿铁"),
            ExtractedFact(fact_key="skill", fact_value="Python"),
        ],
    )

    prompt = service.build_memory_prompt("user_101", query="想喝咖啡")
    assert "拿铁(" in prompt
    assert "Python" not in prompt
    assert service.build_memory_prompt("user_101", query="写请假条") == ""