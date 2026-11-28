import os
from uuid import uuid4

from langchain.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.typing import ContextT
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from dotenv import load_dotenv

load_dotenv()

def init_model(temperature=0.5,**args):
    """初始化底层对话模型实例"""
    return init_chat_model(
        model="deepseek-v4.1-flash",
        model_provider="openai",
        base_url=os.getenv("OPENCODE_BASE_URL"),
        api_key=os.getenv("OPENCODE_API_KEY"),
        default_headers={"x-opencode-session":str(uuid4()) }, # opencode 特有请求头
        temperature=temperature,
        **args
    )

def init_agent(
    prompt: str,
    temperature: float = 0.5,
    tools: list[BaseTool]|None = None,
    checkpointer: InMemorySaver|None = None,
    context_schema:type[ContextT] | None = None,
    **args,
):
    """创建并装配工具、记忆中间件与运行时上下文的对话 Agent"""
    return create_agent(
        model=init_model(temperature),
        system_prompt=prompt,
        tools=tools or [],
        checkpointer=checkpointer,
        context_schema=context_schema,
        **args,
    )