from __future__ import annotations
from typing import List, Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import String, UniqueConstraint
from .types import FactKey
from .utils import ts_func

# SQLModel 基于 SQLAlchemy 和 Pydantic：
# - 带 table=True（如 Fact）既可建表做 ORM，也具备校验能力；字段若用 Literal 等 Python 类型，需加 sa_type 指定数据库列类型
# - 不带 table=True（如 ExtractedFact）则作为纯 Pydantic 数据模型，用于工具入参/结构化输出校验（Field 也继承自 Pydantic）

class Fact(SQLModel, table=True): 
    # SQLModel 基类的 __tablename__ 类型注解是 @declared_attr 描述符，子类直接赋值为字符串字面量时
    # Pylance 会报类型覆盖不兼容（误报），加 # type: ignore 屏蔽静态检查告警，不影响运行
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
    replace_id: Optional[int] = Field(default=None, description="仅当需要替换/纠正某条已有旧记忆时填写对应的 id；纯粹新增时留空")
    

class ExtractionResult(SQLModel):
    facts: List[ExtractedFact]