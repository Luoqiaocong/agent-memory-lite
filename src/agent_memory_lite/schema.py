import time
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

ts_func = lambda: int(time.time()*1000)

FactKey = Literal["job","location","preference","allergy", "skill","name"]

class Fact(BaseModel):
    user_id: str
    fact_key: FactKey
    fact_value: str=Field(description="提取极简原子值，去掉动词或前缀（如直接填 '杭州' 而非 '居住在杭州'）；若有多个并列爱好（如旅游、跑步），请拆成多条 Fact 分别输出，不要合并。")
    confidence: float = Field(default=1.0)
    hit_count: int = Field(default=1)
    is_active: int = Field(default=1)
    previous_value: Optional[str] = Field(default=None)
    # 动态获取当前时间戳(秒)，与数据库中的 updated_at REAL 完美契合
    updated_at: float = Field(default_factory=ts_func)

class ExtractedFact(BaseModel):
    """从外部模型中提取的Fact"""
    fact_key: FactKey
    fact_value: str=Field(description="提取极简原子值，去掉动词或前缀（如直接填 '杭州' 而非 '居住在杭州'）；若有多个并列爱好（如旅游、跑步），请拆成多条 Fact 分别输出，不要合并。")
    confidence: float = Field(default=1.0)
    

class ExtractionResult(BaseModel):
    facts: List[ExtractedFact]