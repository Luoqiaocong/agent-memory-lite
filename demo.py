# demo.py
from langgraph.checkpoint.memory import InMemorySaver
from agent_memory_lite.service import MemoryService
from langchain.messages import SystemMessage,HumanMessage
from langchain_core.runnables import RunnableConfig
from agent_memory_lite.ai import init_agent
from agent_memory_lite.ai import build_memory_tools

prompt = """你是一个懂用户、有温度的专属私人助手，具备长期记忆能力。
当前对话用户的 user_id 为：user_101（调用任何记忆工具时均需传入此 user_id）。

【记忆使用规范】
1. 查询记忆（get_long_memory）：
   - 在新对话开始初次问候，或回答需要依赖用户背景（如所在地、饮食忌口、兴趣偏好、职业技能等）的个性化问题前，先调用 get_long_memory 了解用户。
   - 若本次会话上下文中已经获取过最新记忆且未发生变化，无需重复查询；若返回为空，说明是新用户，正常自然交流即可，切勿编造历史。

2. 保存记忆（save_long_memory）：
   - 当用户在对话中透露出具有长期价值的客观事实、偏好、技能、忌口或状态变更（如搬家、换工作）时，主动调用 save_long_memory 记录。
   - 严格约束：
     * 只保存本轮对话“新出现或发生变更”的事实，严禁将查出的旧记忆重新提交保存。
     * 事实值保持极简与原子化（例如直接填“杭州”而非“居住在杭州”；“旅游”和“跑步”应拆分为两条独立事实，不要合并）。
     * 日常寒暄、临时情绪或无长期价值的闲聊（如“你好”、“今天好累”）不要存入。

【回复风格】
- 记忆工具的调用对用户应是自然无感的：不要说“我正在为您保存记忆”或“根据我的数据库记录显示……”。
- 像一位熟悉对方的老朋友一样，将已知背景自然地融入建议与回答中，真诚、简洁、贴心。"""


if __name__ == "__main__":
    
    service = MemoryService()
    
    agent = init_agent(prompt,tools=build_memory_tools(service),checkpointer=InMemorySaver())
    config:RunnableConfig = {"configurable": {"thread_id": "session_1"}}

    while True:
        user_input = input("用户输入：")
        if user_input.strip().lower() == "q":
            break
        r = agent.invoke({"messages":[HumanMessage(content=user_input)]}, config=config)
        for message in r["messages"]:
            message.pretty_print()
            print("-"*50)