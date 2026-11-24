from typing import Annotated

from pydantic import BaseModel,Field
from datetime import datetime

class FactScheama(BaseModel):
    user_id: str    
    fact_key: str
    fact_value: str
    confidence:float
    hit_count:int
    is_active:Annotated[int, Field(default=1)]
    previous_value:Annotated[str, Field(default=None)] 
    updated_at:Annotated[datetime, Field(default=datetime.now())]
   