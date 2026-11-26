import os
from typing import Callable, Optional
from uuid import uuid4

from langchain.messages import SystemMessage,HumanMessage
from langchain.tools import BaseTool
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from dotenv import load_dotenv

load_dotenv()

def init_model(temperature=0.5,**args):
    return init_chat_model(
        model="deepseek-v4.1-flash",
        model_provider="openai",
        base_url=os.getenv("OPENCODE_BASE_URL"),
        api_key=os.getenv("OPENCODE_API_KEY"),
        default_headers={"x-opencode-session":str(uuid4()) }, # opencode 特有请求头
        temperature=temperature,
        **args
    )

def init_agent(prompt:str,temperature=0.5,tools:Optional[list[BaseTool]] = None,checkpointer:Optional[InMemorySaver]=None,**args):
    return create_agent(
        model=init_model(temperature),
        system_prompt=prompt,
        tools= tools or [],
        checkpointer=checkpointer,
        **args
)