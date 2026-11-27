from __future__ import annotations
import time
from typing import List, Literal, Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import String, UniqueConstraint
from .types import FactKey
from .utils import ts_func



class Fact(SQLModel, table=True): 
    __tablename__ = "facts" # type: ignore
    __table_args__ = (
        UniqueConstraint("user_id", "fact_key", "fact_value", name="uq_user_fact"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    fact_key: FactKey = Field(sa_type=String, index=True)
    fact_value: str = Field(
        description="提取极简原子值，去掉动词或前缀（如直接填 '杭州' 而非 '居住在杭州'）；若有多个并列爱好（如旅游、跑步），请拆成多条 Fact 分别输出，不要合并。"
    )
    confidence: float = Field(default=1.0)
    hit_count: int = Field(default=1)
    is_active: int = Field(default=1, index=True)
    previous_value: Optional[str] = Field(default=None)
    # 动态获取当前时间戳(毫秒)，与数据库中的 updated_at Float/REAL 完美契合
    updated_at: float = Field(default_factory=ts_func)

class ExtractedFact(SQLModel):
    """从外部模型中提取的Fact"""
    fact_key: FactKey
    fact_value: str=Field(description="提取极简原子值，去掉动词或前缀（如直接填 '杭州' 而非 '居住在杭州'）；若有多个并列爱好（如旅游、跑步），请拆成多条 Fact 分别输出，不要合并。")
    confidence: float = Field(default=1.0)
    

class ExtractionResult(SQLModel):
    facts: List[ExtractedFact]