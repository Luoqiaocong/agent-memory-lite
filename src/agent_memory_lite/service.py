from typing import List, Dict, Any, Optional
from .db import MemoryDB
from .schema import Fact
from collections import defaultdict

SINGLE_VALUE_KEYS={"location", "name", "job"}

select_sql = """
select * from facts where user_id = ? and fact_key = ? and is_active = 1 and fact_value != ?
"""
update_sql = """
update facts set is_active=0, updated_at = ? where user_id = ? and fact_key = ? and is_active = 1  

"""

upsert_sql = """
            INSERT INTO facts (
                user_id, fact_key, fact_value, confidence, hit_count, is_active, previous_value, updated_at
            ) VALUES (
                :user_id, :fact_key, :fact_value, :confidence, :hit_count, :is_active, :previous_value, :updated_at
            ) ON CONFLICT(user_id, fact_key, fact_value) DO UPDATE SET hit_count = facts.hit_count + 1, updated_at = excluded.updated_at,is_active = 1,confidence = MAX(facts.confidence, excluded.confidence),previous_value = COALESCE(excluded.previous_value, facts.previous_value)
        """
        
        
class MemoryService:
    def __init__(self, db: MemoryDB):
        self.db = db

    def record_fact(self, user_id: str,facts:List[Fact]) -> str:
        """
        写入骨架（只做纯新增）
        """
        # 4. 批量执行写入 (事务内提交)
        with self.db.conn:
            for fact in facts:
                if fact.fact_key in SINGLE_VALUE_KEYS:
                    user_facts = self._find_active_conflict(user_id,fact.fact_key,fact.fact_value)
                    if user_facts:
                        self.db.conn.execute(update_sql, (fact.updated_at,user_id, fact.fact_key))
                        fact.previous_value = user_facts["fact_value"]
                self.db.conn.execute(upsert_sql, fact.model_dump())
        return "ok"

    def get_user_facts(self, user_id: str,limit:int=20):
        """查询指定用户当前的所有有效事实"""
        cursor = self.db.conn.execute(
            """
            SELECT id, user_id, fact_key, fact_value, confidence, hit_count, is_active, previous_value, updated_at
            FROM facts
            WHERE user_id = ? AND is_active = 1 order by hit_count desc ,updated_at desc limit ?
            """,
            (user_id,limit)
        )
        return cursor.fetchall()
    
    
    def _find_active_conflict(self, user_id: str,fact_key: str,fact_value: str):
        cursor = self.db.conn.execute(select_sql,(user_id, fact_key,fact_value))
        return cursor.fetchone()
    
    def build_memory_prompt(self, user_id: str, limit: int = 20)-> str:
        facts = self.get_user_facts(user_id,limit)
        if not facts:return ""
        grouped = defaultdict(list)
        
        
        for fact in facts:
            value = fact["fact_value"]
            if fact["previous_value"]:
                value += f"|之前:{fact['previous_value']}"
            grouped[fact["fact_key"]].append(value)
            
        return "[已知用户长期记忆]\n"+"\n".join([f"{key}:{'、'.join(values)}" for key,values in grouped.items()])+"\n\n请在回答时自然运用以上背景信息，但不要刻意生硬地说出‘根据我的记忆数据库…"
        
        

