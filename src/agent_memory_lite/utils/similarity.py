import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """计算两个向量的余弦相似度（范围 [-1, 1]，越接近 1 越相似）"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return round(dot / (norm_a * norm_b), 4)
