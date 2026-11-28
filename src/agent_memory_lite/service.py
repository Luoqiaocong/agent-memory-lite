from typing import List, Optional

from .repo import FactRepository
from .db import MemoryDB
from .schema import ExtractedFact, Fact, FactKey
from collections import defaultdict

SINGLE_VALUE_KEYS={"location", "name", "job"}

        
class MemoryService:
    def __init__(self,db_url:Optional[str]=None):
        self.repo = FactRepository(MemoryDB(db_url=db_url))

    def record_fact(self, user_id: str,facts:List[ExtractedFact]) -> str:
        """转换提取结果并批量写入或替换用户长期记忆"""
        self.repo.save_facts(user_id,[(Fact(**fact.model_dump(exclude={"replace_id"}),user_id=user_id),fact.replace_id) for fact in facts], SINGLE_VALUE_KEYS)
        return "ok"

    def get_user_facts(self, user_id: str,limit:int=20):
        """查询指定用户当前的所有有效事实"""
        return self.repo.get_active_facts(user_id, limit)
    
    def build_memory_prompt(self, user_id: str, limit: int = 20)-> str:
        """按事实键分组组装可注入对话上下文的长期记忆提示词"""
        facts = self.get_user_facts(user_id,limit)
        if not facts:return ""
        grouped = defaultdict(list)  # 值是列表，当键不存在的时候，默认创建一个空列表
         
        for fact in facts:
            value = fact.fact_value+f"({fact.id})"
            if fact.previous_value:
                value += f"|之前:{fact.previous_value}"
            grouped[fact.fact_key].append(value)
            
        return "[已知用户长期记忆]\n"+"\n".join([f"{key}:{'、'.join(values)}" for key,values in grouped.items()])+"\n\n请在回答时自然运用以上背景信息，但不要刻意生硬地说出‘根据我的记忆数据库…"
        
    def forget_fact(self, user_id: str, fact_key: FactKey, fact_value: str) -> str:
        """按键值软删除指定有效记忆"""
        return "ok" if self.repo.deactivate_fact(user_id, fact_key, fact_value) else "not found"


    def get_fact_history(self, user_id: str, fact_key: FactKey, limit: int = 10) -> str:
        """查询指定事实键的当前有效记录与已变更历史轨迹"""
        facts = self.repo.get_fact_history(user_id, fact_key, limit)
        if not facts:
            return "not found"
        active_facts = [fact for fact in facts if fact.is_active]
        inactive_facts = [fact for fact in facts if not fact.is_active]
        
        sections = []
        if active_facts:
            sections.append(
                "当前生效记忆：\n" + "\n".join(f"- {f.fact_key}:{f.fact_value}" for f in active_facts)
            )
        if inactive_facts:
            sections.append(
                "历史记录：\n" + "\n".join(f"- {f.fact_key}:{f.fact_value}" for f in inactive_facts)
            )
        return "\n\n".join(sections)