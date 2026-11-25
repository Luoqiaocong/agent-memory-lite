import time
from typing import Optional
from pydantic import BaseModel, Field

ts_func = lambda: int(time.time()*1000)


class FactSchema(BaseModel):
    user_id: str
    fact_key: str
    fact_value: str
    confidence: float = Field(default=1.0)
    hit_count: int = Field(default=1)
    is_active: int = Field(default=1)
    previous_value: Optional[str] = Field(default=None)
    # 动态获取当前时间戳(秒)，与数据库中的 updated_at REAL 完美契合
    updated_at: float = Field(default_factory=ts_func)
