from typing import List

from langchain.tools import tool

from agent_memory_lite.service import MemoryService
from agent_memory_lite.schema import ExtractedFact
from agent_memory_lite.types import FactKey

def build_memory_tools(service:MemoryService):
    @tool
    def get_long_memory(user_id: str):
        """
        获取用户的长记忆
        Args:
            user_id (str): 用户ID
        return:
            str: 用户的长记忆字符串
        """
        return service.build_memory_prompt(user_id)


    @tool
    def upsert_long_memory(user_id: str, facts: List[ExtractedFact])->str:
        """
        保存可复用有价值的用户长期记忆,只保存本轮对话新出现或变更的事实，严禁重复保存历史记忆
        Args:
            user_id (str): 用户ID
            facts (List[ExtractedFact]): 用户长记忆
        return ok   
        """
        return service.record_fact(user_id,facts)

    @tool
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

    # 当前工具较少，显式返回最直观；若后续工具增多不想每次手动维护列表，可改用“局部注册装饰器”自动收集：
    #   tools = []
    #   def register(func): t = tool(func); tools.append(t); return t
    # 各工具函数改挂 @register，最后直接 return tools 即可
    return [get_long_memory,upsert_long_memory,forget_long_memory]

    
        
        
