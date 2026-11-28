from dataclasses import dataclass

from langchain.agents.middleware import ModelRequest, dynamic_prompt

from agent_memory_lite.service import MemoryService


@dataclass
class MemoryContext:
    """Agent 运行时上下文：传递 user_id 等身份信息，不混入会话状态存档"""

    user_id: str


def build_memory_middleware(service: MemoryService):
    """构建动态提示词中间件，每次模型调用前自动注入最新长期记忆"""

    @dynamic_prompt
    def personalized_prompt(request: ModelRequest[MemoryContext]) -> str:
        ctx = request.runtime.context if request.runtime else None
        user_id = ctx.user_id if ctx else None
        memory = service.build_memory_prompt(user_id) if user_id else ""
        parts = [p for p in (request.system_prompt, memory) if p]
        return "\n\n".join(parts)

    return personalized_prompt
