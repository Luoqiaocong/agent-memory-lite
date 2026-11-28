import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """懒加载并复用 OpenAI 兼容客户端，避免导入阶段因未配置密钥报错"""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.getenv("SILICONFLOW_API_KEY"),
            base_url=os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"),
        )
    return _client


def embed_texts(texts: list[str], model: str = "BAAI/bge-m3") -> list[list[float]]:
    """调用硅基流动接口批量生成文本向量"""
    if not texts:
        return []
    resp = _get_client().embeddings.create(model=model, input=texts)
    return [item.embedding for item in resp.data]


if __name__ == "__main__":
    from agent_memory_lite.utils import cosine_similarity

    t1, t2 = embed_texts(["你好", "你好吗？"])
    print(cosine_similarity(t1, t2))
