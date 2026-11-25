# demo.py
from src.agent_memory_lite.db import MemoryDB
from src.agent_memory_lite.service import MemoryService


querys = [
    "我平时业余时间很喜欢摄影，也特别爱探索各种美食，目前住在北京。",
    "最近工作调动，我现在住在上海。"
]


if __name__ == "__main__":
    db = MemoryDB()
    service = MemoryService(db)

    # print("--- 正在记录记忆 ---")
    # for q in querys:
    #     facts = service.record_user_input("user_101", q)
    #     print(f"  {q} ->成功存入 {len(facts)}条事实")

    # print("\n--- 查库验证 ---")
    # rows = service.get_user_facts("user_101")
    # for r in rows:
    #     print(f"  [{r['fact_key']}] -> {r['fact_value']} (提取频次: {r['hit_count']})")
        
    prompt = service.build_memory_prompt("user_101")
    print(prompt)