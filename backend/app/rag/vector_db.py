"""
ChromaDB 向量库操作
- 加载攻略文档并分块
- 向量化并入库
- 向量检索
"""
import hashlib
import re
import time
from pathlib import Path
import httpx
import chromadb
from app.config import (
    BACKEND_DIR, CHROMA_DB_DIR, CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL, LLM_API_KEY,
)

# DashScope 文本 embedding 专用端点（不走 OpenAI 兼容模式）
EMBEDDING_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"


def _embed_texts(texts: list[str]) -> list[list[float]]:
    """
    调用 DashScope text-embedding API，将文本转为向量。
    自动分批，每批最多 25 条（API 限制）。
    """
    all_vectors = []
    batch_size = 10

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        payload = {
            "model": EMBEDDING_MODEL,
            "input": {"texts": batch},
        }
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        }

        resp = httpx.post(EMBEDDING_API_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # 按 text_index 排序后提取 embedding
        embeddings = data["output"]["embeddings"]
        embeddings.sort(key=lambda e: e["text_index"])
        all_vectors.extend([e["embedding"] for e in embeddings])

        # API 限速：每秒不超过一定请求数
        time.sleep(0.1)

    return all_vectors


def _embed_single(text: str) -> list[float]:
    """将单条文本转为向量"""
    return _embed_texts([text])[0]


def load_guide_chunks(data_dir: Path | None = None) -> list[dict]:
    """
    加载 data/ 目录下所有 .md 攻略文件，按 ##/### 标题分块。
    返回: [{"source": "dali_guide.md", "title": "大理古城", "content": "...", "id": "..."}]
    """
    if data_dir is None:
        data_dir = BACKEND_DIR / "data"

    chunks = []
    for md_file in sorted(data_dir.glob("*.md")):
        source = md_file.name
        text = md_file.read_text(encoding="utf-8")
        # 按 ## 或 ### 标题分块
        sections = re.split(r'\n(?=## )', text)

        for section in sections:
            section = section.strip()
            if not section:
                continue
            # 提取标题（第一行 ## xx）
            title_match = re.match(r'^#+\s*(.+?)$', section.split('\n')[0])
            title = title_match.group(1) if title_match else section[:50]

            # 生成稳定 ID（基于内容哈希）
            chunk_id = hashlib.md5(section.encode()).hexdigest()[:16]
            chunks.append({
                "source": source,
                "title": title.strip(),
                "content": section,
                "id": f"{source.replace('.md','')}_{chunk_id}",
            })

    return chunks


def get_or_create_collection():
    """获取或创建 ChromaDB collection"""
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    return client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)


def ingest_guide_chunks_to_chroma(data_dir: Path | None = None):
    """
    将攻略文档分块 → 向量化 → 写入 ChromaDB
    已有数据会先清空再重新写入
    """
    chunks = load_guide_chunks(data_dir)
    print(f"加载 {len(chunks)} 个攻略片段")

    collection = get_or_create_collection()

    # 提取文本、ID、元数据
    texts = [c["content"] for c in chunks]
    ids = [c["id"] for c in chunks]
    metadatas = [{"source": c["source"], "title": c["title"]} for c in chunks]

    # 先清空已有数据
    try:
        existing = collection.get()
        if existing.get("ids"):
            collection.delete(ids=existing["ids"])
            print(f"清空旧数据 {len(existing['ids'])} 条")
    except Exception:
        pass

    # 批量向量化并写入
    print("正在向量化...")
    vectors = _embed_texts(texts)
    collection.add(
        ids=ids,
        embeddings=vectors,
        documents=texts,
        metadatas=metadatas,
    )
    print(f"向量入库完成！共 {len(texts)} 条")


def search_guide_chunks(query: str, top_k: int = 6) -> list[dict]:
    """
    向量检索：根据 query 返回最相似的 top_k 个攻略片段。
    返回: [{"id", "source", "title", "content", "score"}, ...]
    """
    collection = get_or_create_collection()

    # 将 query 向量化
    query_vector = _embed_single(query)

    # ChromaDB 向量检索
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    if results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 0
            chunks.append({
                "id": doc_id,
                "source": meta.get("source", ""),
                "title": meta.get("title", ""),
                "content": results["documents"][0][i] if results["documents"] else "",
                "score": round(1.0 / (1.0 + distance), 4),  # 距离转相似度
            })

    return chunks


if __name__ == "__main__":
    # 直接运行此文件 = 入库
    ingest_guide_chunks_to_chroma()
