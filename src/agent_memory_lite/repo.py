from typing import List, Optional, Set
from sqlmodel import Session, select, col

from .db import MemoryDB
from .schema import Fact


class FactRepository:
    """长期记忆仓储层：封装所有跨数据库通用的 ORM 增删改查操作"""

    def __init__(self, db: MemoryDB):
        """初始化仓储层并绑定数据库引擎"""
        self.engine = db.engine

    def get_active_facts(self, user_id: str, limit: int = 20) -> List[Fact]:
        """按提及频次与更新时间倒序，获取用户当前有效的 Top-K 记忆"""
        with Session(self.engine) as session:
            statement = (
                select(Fact)
                .where(Fact.user_id == user_id, Fact.is_active == 1)
                # col() 显式声明列对象，让编辑器能识别 .desc() 并提供代码提示
                .order_by(col(Fact.hit_count).desc(), col(Fact.updated_at).desc())
                .limit(limit)
            )
            return list(session.exec(statement).all())

    def save_facts(
        self,
        user_id: str,
        facts: List[Fact],
        single_value_keys: Set[str],
    ) -> None:
        """在同一事务中批量保存记忆，自动处理单值覆盖与重复加固"""
        if not facts:
            return

        with Session(self.engine) as session:
            for fact in facts:
                if fact.fact_key in single_value_keys:
                    # 停用同键下值不同的旧记忆，并记录其作为本次变更的前任值
                    prev_value = self._deactivate_conflicts(
                        session,
                        user_id,
                        fact.fact_key,
                        fact.fact_value,
                        fact.updated_at,
                    )
                    if prev_value is not None:
                        fact.previous_value = prev_value
                self._upsert_fact(session, fact)

            # 统一提交事务；若中途发生异常则自动回滚，保证整批原子性
            session.commit()

    def _deactivate_conflicts(
        self,
        session: Session,
        user_id: str,
        fact_key: str,
        new_value: str,
        updated_at: float,
    ) -> Optional[str]:
        """停用同一标量键下值不同的历史有效记忆，并返回被替换前的旧值"""
        statement = select(Fact).where(
            Fact.user_id == user_id,
            Fact.fact_key == fact_key,
            Fact.fact_value != new_value,
            Fact.is_active == 1,
        )
        old_facts = list(session.exec(statement).all())
        if not old_facts:
            return None

        for old_fact in old_facts:
            old_fact.is_active = 0
            old_fact.updated_at = updated_at
            session.add(old_fact)

        return old_facts[0].fact_value

    def _upsert_fact(self, session: Session, fact: Fact) -> None:
        """跨库通用 Upsert：存在则累加 hit_count 并刷新属性，不存在则新增"""
        statement = select(Fact).where(
            Fact.user_id == fact.user_id,
            Fact.fact_key == fact.fact_key,
            Fact.fact_value == fact.fact_value,
        )
        existing = session.exec(statement).first()

        if existing is not None:
            existing.hit_count += 1
            existing.updated_at = fact.updated_at
            existing.is_active = 1
            existing.confidence = max(existing.confidence, fact.confidence)
            # 仅当本次产生了新前任时才覆写，避免原地重复提及（previous_value 为 None）时误清空老前任
            if fact.previous_value is not None:
                existing.previous_value = fact.previous_value
            session.add(existing)
        else:
            session.add(fact)
