from .db import MemoryDB
from .extractor import mock_extract
import time
from .schema import FactScheama


ts_func = lambda: int(time.time()*1000)


class MemoryService:
    
    def __init__(self,db:MemoryDB):
        self.db = db
    
    def record_user_input(self,user_id:str,text:str):
        facts =  mock_extract(user_id,text)
        if not facts: # 无结构化信息
            return
        ts = ts_func()
        with self.db.conn:
            for fact in facts:
                self.db.conn.execute("insert into facts(user_id,fact_key,fact_value) values(?,?,?)")
    
    def get_user_facts(self,user_id:int):
        pass
        