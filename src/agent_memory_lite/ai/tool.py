from typing import List

from langchain.tools import tool

from agent_memory_lite.service import MemoryService
from agent_memory_lite.schema import ExtractedFact, Fact
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
    def save_long_memory(user_id: str, facts: List[ExtractedFact])->str:
        """
        保存可复用有价值的用户长期记忆,只保存本轮对话新出现或变更的事实，严禁重复保存历史记忆
        Args:
            user_id (str): 用户ID
            facts (List[ExtractedFact]): 用户长记忆
        return ok   
        """
        return service.record_fact(user_id,[Fact(**fact.model_dump(),user_id=user_id) for fact in facts])

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

    return [get_long_memory,save_long_memory,forget_long_memory]

