"""
RAG 检索器
完整链路：向量召回 → 噪声过滤 → Cross-encoder Rerank → 返回 top-k
"""
import re
import httpx
from app.config import LLM_API_KEY, RERANK_MODEL
from app.rag.vector_db import search_guide_chunks

# DashScope Rerank API
RERANK_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"

# 噪声关键词（出现则降权）
NOISE_PATTERNS = [
    r"拍照巨出片",
    r"一定要来\S*地方",
    r"这些地方",
    r"必打卡",
    r"超级",
    r"绝美",
    r"美哭了",
]


def _is_noise_chunk(content: str) -> bool:
    """判断是否为低信息量噪声片段"""
    # 太短 = 噪声
    if len(content) < 150:
        return True
    # 大量无意义感叹词
    noise_score = sum(len(re.findall(p, content)) for p in NOISE_PATTERNS)
    return noise_score >= 3


def _filter_noise(chunks: list[dict]) -> list[dict]:
    """过滤噪声片段"""
    return [c for c in chunks if not _is_noise_chunk(c["content"])]


def _rerank_with_dashscope(query: str, chunks: list[dict]) -> list[dict]:
    """
    调用 DashScope qwen3-rerank 做语义重排序。
    返回按相关性从高到低排序的 chunks。
    """
    if not chunks:
        return chunks

    documents = [c["content"] for c in chunks]

    try:
        resp = httpx.post(
            RERANK_API_URL,
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": RERANK_MODEL,
                "input": {
                    "query": query,
                    "documents": documents,
                },
                "parameters": {
                    "top_n": min(len(documents), 6),
                },
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        # 按 rerank 分数重新排序
        results = data.get("output", {}).get("results", [])
        if results:
            reranked = []
            for r in sorted(results, key=lambda x: x.get("relevance_score", 0), reverse=True):
                idx = r["index"]
                chunks[idx]["rerank_score"] = round(r["relevance_score"], 4)
                reranked.append(chunks[idx])
            return reranked
    except Exception:
        pass

    # Rerank 失败，返回原顺序
    return chunks


def _rule_rerank(query: str, chunks: list[dict], destination: str = "") -> list[dict]:
    """
    规则级打分排序（Rerank API 失败时的回退方案）
    """
    for c in chunks:
        score = c.get("score", 0)
        # 标题匹配加分
        title = c.get("title", "")
        content = c.get("content", "")
        for word in query.split():
            if word in title:
                score += 0.3
            if word in content:
                score += 0.1
        # 目的地匹配加分
        if destination and destination in title:
            score += 0.2
        c["rule_score"] = round(score, 4)

    return sorted(chunks, key=lambda x: x.get("rule_score", 0), reverse=True)


def retrieve_travel_guide(
    query: str,
    destination: str = "",
    top_k: int = 3,
) -> list[dict]:
    """
    RAG 检索主入口。

    流程：
    1. ChromaDB 向量召回 top-6
    2. 噪声过滤
    3. Cross-encoder Rerank（失败回退规则打分）
    4. 返回 top_k 条

    返回: [{"title", "content", "source", "score"}, ...]
    """
    # ① 向量召回
    chunks = search_guide_chunks(query, top_k=6)
    if not chunks:
        return []

    # ② 噪声过滤
    chunks = _filter_noise(chunks)
    if not chunks:
        return []

    # ③ Rerank
    chunks = _rerank_with_dashscope(query, chunks)
    if not any(c.get("rerank_score") for c in chunks):
        # Rerank API 失败，用规则打分
        chunks = _rule_rerank(query, chunks, destination)

    # ④ 截取 top_k
    return chunks[:top_k]


def format_context_for_llm(chunks: list[dict]) -> str:
    """将检索结果格式化为 LLM 可用的上下文"""
    lines = []
    for i, c in enumerate(chunks, 1):
        lines.append(f"[参考资料 {i}] 来源：{c.get('source','')} | 标题：{c.get('title','')}")
        lines.append(c.get("content", ""))
        lines.append("---")
    return "\n".join(lines)
