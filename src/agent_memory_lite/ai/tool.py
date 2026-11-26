from typing import List

from langchain.tools import tool

from agent_memory_lite.service import MemoryService
from agent_memory_lite.schema import ExtractedFact, Fact


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

    return [get_long_memory,save_long_memory]

