"""
RAG 工具 — Query Rewrite
将用户的自然语言需求改写为适合向量检索的关键词
"""
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

SYSTEM_PROMPT = """你是一个旅行搜索查询改写助手。用户会用口语描述他们的旅行需求。
你需要将其改写为 1-2 句话的精简搜索查询，用于在旅行攻略库中检索相关片段。

规则：
1. 提取核心目的地、偏好（自然/人文/美食等）、节奏（轻松/紧凑）
2. 如果用户提到了具体景点，保留景点名
3. 用空格分隔关键词，中英文均可
4. 只输出改写后的查询文本，不要输出任何解释

示例：
输入："我想去大理，在洱海边骑骑车，吃点当地小吃，不要太赶"
输出：大理 洱海 骑行 美食 慢旅行 休闲

输入："成都3天，主要想看熊猫和吃火锅，预算3000"
输出：成都 大熊猫基地 火锅 3天 行程"""  # noqa: E501


def rewrite_query_with_llm(user_input: str) -> str:
    """
    使用 LLM 改写用户查询。
    返回改写的查询文本，失败时返回原输入。
    """
    try:
        llm = ChatOpenAI(
            model=LLM_MODEL,
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            temperature=0.3,
            max_tokens=200,
        )
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_input),
        ]
        resp = llm.invoke(messages)
        result = resp.content.strip()
        # 去掉可能的引号
        result = result.strip('"\'').strip()
        return result if result else user_input
    except Exception:
        return user_input  # 失败时返回原输入


def build_destination_query(
    destination: str,
    preferences: str = "",
    pace: str = "",
    special_notes: str = "",
) -> str:
    """
    构建检索查询。
    优先使用 LLM 改写，失败回退到规则拼接。

    返回: 检索查询字符串
    """
    # 拼装用户意图描述
    parts = [f"我想去{destination}旅游"]
    if preferences:
        parts.append(f"偏好：{preferences}")
    if pace:
        parts.append(f"节奏：{pace}")
    if special_notes:
        parts.append(f"备注：{special_notes}")
    user_input = "，".join(parts)

    # 尝试 LLM 改写
    rewritten = rewrite_query_with_llm(user_input)
    if rewritten and rewritten != user_input:
        return rewritten

    # 规则回退：直接拼接关键词
    keywords = [destination]
    if preferences:
        keywords.append(preferences)
    if pace:
        keywords.append(pace)
    return " ".join(keywords)
