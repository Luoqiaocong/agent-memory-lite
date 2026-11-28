from typing import List, Optional, Set, Tuple
from sqlmodel import Session, select, col

from .utils import ts_func

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
        facts: List[Tuple[Fact, Optional[int]]],
        single_value_keys: Set[str],
    ) -> None:
        """在同一事务中批量保存记忆，自动处理单值覆盖、按 ID 替换与重复加固"""
        if not facts:
            return

        with Session(self.engine) as session:
            for fact, replace_id in facts:
                if fact.fact_key in single_value_keys:
                    # 单值键（如居住地/职业）只保留一条最新值，直接按 key 自动停用不同值的旧记忆；
                    # 用 if/elif 与 replace_id 互斥，避免同一条单值记录被重复停用或互相覆盖 previous_value
                    prev_value = self._deactivate_conflicts(
                        session,
                        user_id,
                        fact.fact_key,
                        fact.fact_value,
                        fact.updated_at,
                    )
                elif replace_id is not None:
                    # 多值键（如爱好/忌口）不能靠 key 覆盖全部，仅在模型明确指定 replace_id 时精准替换指定旧记录
                    prev_value = self._deactivate_by_id(session, user_id, replace_id, fact)
                else:
                    prev_value = None

                # 统一由外层回填前任值，保持 _deactivate_* 方法只负责“停用旧记录并返回旧值”的单一职责
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
        # 防御性编程：正常情况下单值键只应有一条有效记忆，但若因并发或历史脏数据出现多条，
        # 用 all() 一次性全部停用，避免 first() 只删一条后留下残留的活跃脏数据
        old_facts = list(session.exec(statement).all())
        if not old_facts:
            return None

        for old_fact in old_facts:
            old_fact.is_active = 0
            old_fact.updated_at = updated_at
            session.add(old_fact)

        return old_facts[0].fact_value

    def _deactivate_by_id(
        self,
        session: Session,
        user_id: str,
        fact_id: int,
        new_fact: Fact,
    ) -> Optional[str]:
        """按 ID 停用同键旧记忆并返回旧值，用于多值键的精准替换"""
        old_fact = session.get(Fact, fact_id)

        # 模型传参可能产生幻觉或基于过期上下文，统一拦截四类脏 ID：
        # 1. old_fact is None：ID 不存在（模型编造或记错了数字）
        # 2. user_id 不一致：防止越权停用其他用户的记忆
        # 3. is_active != 1：该记忆已被遗忘或替换过，避免重复停用或把过时记录当作前任
        # 4. fact_key 不一致：防止跨类别误传 ID 时把无关字段写进 previous_value（如出现“拿铁|之前:杭州”）
        if (
            old_fact is None
            or old_fact.user_id != user_id
            or old_fact.is_active != 1
            or old_fact.fact_key != new_fact.fact_key
        ):
            return None

        # 解决“模型重复提及时误传同值 replace_id”的问题（如库里已有 黑咖啡(3)，模型仍带 replace_id=3 写 黑咖啡）：
        # 不拦截的话会先停用旧条，随后 _upsert_fact 又因同键同值捞出并重新激活它，导致出现“黑咖啡|之前:黑咖啡”
        if old_fact.fact_value == new_fact.fact_value:
            return None

        # 复用新记忆的时间戳，保证同一次替换中旧记录停用与新记录生效时间严格对齐
        old_fact.is_active = 0
        old_fact.updated_at = new_fact.updated_at
        session.add(old_fact)
        return old_fact.fact_value

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
    
    def deactivate_fact(self, user_id: str, fact_key: str, fact_value: str) -> bool:
        """停用指定的单条有效记忆（软删除）"""
        with Session(self.engine) as session:
            statement = select(Fact).where(
                Fact.user_id == user_id,
                Fact.fact_key == fact_key,
                Fact.fact_value == fact_value,
                Fact.is_active == 1,
            )
            fact = session.exec(statement).first()
            if not fact:
                return False

            fact.is_active = 0
            fact.updated_at = ts_func()
            session.add(fact)
            session.commit()
            return True

    def get_fact_history(self, user_id: str, fact_key: str, limit: int = 10) -> List[Fact]:
        """按时间倒序查询指定事实键的全部历史记录（含已停用记忆）"""
        with Session(self.engine) as session:
            statement = select(Fact).where(
                Fact.user_id == user_id,
                Fact.fact_key == fact_key,
            ).order_by(col(Fact.updated_at).desc(),col(Fact.id).desc()).limit(limit)
            
            return list(session.exec(statement).all())