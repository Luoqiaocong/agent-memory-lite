from typing import List, Dict, Any

def mock_extract(user_id: str, text: str) -> List[Dict[str, Any]]:
    """模拟大模型从文本中提取结构化事实"""
    facts = []
    if "摄影" in text:
        facts.append({"user_id": user_id, "fact_key": "preference", "fact_value": "摄影", "confidence": 0.95})
    if "美食" in text:
        facts.append({"user_id": user_id, "fact_key": "preference", "fact_value": "美食", "confidence": 0.90})
    if "住在北京" in text:
        facts.append({"user_id": user_id, "fact_key": "city", "fact_value": "北京", "confidence": 1.0})
    elif "住在上海" in text:
        facts.append({"user_id": user_id, "fact_key": "city", "fact_value": "上海", "confidence": 1.0})
    return facts