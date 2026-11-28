from typing import List

from langchain.tools import BaseTool, tool

from agent_memory_lite.service import MemoryService
from agent_memory_lite.schema import ExtractedFact
from agent_memory_lite.types import FactKey

tools:list[BaseTool]=[]
def register(func):
     t = tool(func)
     tools.append(t)
     return t

def build_memory_tools(service:MemoryService):
    @register
    def get_long_memory(user_id: str):
        """
        获取用户的长记忆
        Args:
            user_id (str): 用户ID
        return:
            str: 用户的长记忆字符串
        """
        return service.build_memory_prompt(user_id)

    @register
    def upsert_long_memory(user_id: str, facts: List[ExtractedFact])->str:
        """
        保存可复用有价值的用户长期记忆,只保存本轮对话新出现或变更的事实，严禁重复保存历史记忆
        Args:
            user_id (str): 用户ID
            facts (List[ExtractedFact]): 用户长记忆
        return ok   
        """
        return service.record_fact(user_id,facts)

    @register
    def forget_long_memory(user_id: str, fact_key: FactKey, fact_value: str)->str:
        """
        当用户明确表示放弃某个爱好、习惯或纠正错误记忆时调用；传入的 fact_value 需与记忆库中一致，若不确定可先调用 get_long_memory 确认
        Args:
            user_id (str): 用户ID
            fact_key (FactKey): 事实键
            fact_value (str): 事实值
            
        return:
            str: 删除结果
            """
        return service.forget_fact(user_id,fact_key,fact_value)
    
    @register
    def get_long_memory_history(user_id: str, fact_key: FactKey)->str:
        """
        按时间倒序获取某类长期记忆的完整变更历史（包含当前生效和已停用/曾替换的旧记录）；仅在用户主动追问过往经历时调用
        Args:
            user_id (str): 用户ID
            fact_key (FactKey): 需要追溯历史的事实键（如 location、job、preference 等）
        return:
            str: 包含当前生效记录与过往历史轨迹的文本
        """
        return service.get_fact_history(user_id,fact_key)


    return tools

    
        
        
