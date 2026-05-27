"""
法律知识库向量化脚本
将法条、司法解释、判例等数据向量化后存入 ChromaDB
"""
import os
import sys
import json
import sqlite3
import hashlib
from typing import List, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.config import settings

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def get_db_path():
    db_url = settings.database_url
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        if db_path.startswith("./"):
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), db_path[2:])
    else:
        db_path = db_url
    if not os.path.exists(db_path):
        db_path = "legal_system.db"
    return db_path


def get_embedding_service():
    """获取 embedding 服务，优先本地 sentence-transformers，备选 DashScope"""
    try:
        from sentence_transformers import SentenceTransformer
        model_name = "shibing624/text2vec-base-chinese"
        print(f"[Embedding] 尝试加载本地模型: {model_name}")
        model = SentenceTransformer(model_name, trust_remote_code=True)
        print("[Embedding] 本地模型加载成功")
        return model, "local"
    except Exception as e:
        print(f"[Embedding] 本地模型不可用: {e}")
        print("[Embedding] 使用 DashScope API 进行向量化")
        return None, "dashscope"


def embed_with_local(model, texts: List[str]) -> List[List[float]]:
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def embed_with_dashscope(texts: List[str]) -> List[List[float]]:
    try:
        from dashscope import TextEmbedding
        from app.config import settings

        all_embeddings = []
        batch_size = 25
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = TextEmbedding.call(
                model=TextEmbedding.Models.text_embedding_v1,
                input=batch
            )
            if response.status_code == 200:
                for item in response.output["embeddings"]:
                    all_embeddings.append(item["embedding"])
            else:
                all_embeddings.extend([[0.0] * 1536 for _ in batch])
        return all_embeddings
    except Exception as e:
        print(f"[Embedding] DashScope 错误: {e}")
        return [[0.0] * 1536 for _ in texts]


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if end < len(text):
            last_newline = chunk.rfind("\n")
            if last_newline > chunk_size * 0.5:
                end = start + last_newline + 1
                chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        start = end - overlap
        if start <= 0:
            start = end

    return chunks


def vectorize_legal_articles(model, model_type: str, limit_laws: int = 50):
    """向量化法条（按重要性排序，限制数量）"""
    import chromadb

    print("\n--- 向量化法条 ---")
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取已有向量数，支持断点续传
    chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_directory)
    try:
        collection = chroma_client.get_collection("legal_articles_vec")
        existing_ids = set(collection.get(include=[])["ids"])
        print(f"  已有 {len(existing_ids)} 个向量")
    except:
        collection = chroma_client.get_or_create_collection(
            name="legal_articles_vec",
            metadata={"description": "法条向量检索"}
        )
        existing_ids = set()

    # 按法律统计文章数，优先向量化重要法律
    cursor.execute("""
        SELECT law_name, COUNT(*) as cnt FROM legal_articles 
        GROUP BY law_name ORDER BY cnt DESC LIMIT ?
    """, (limit_laws,))
    top_laws = [row[0] for row in cursor.fetchall()]
    print(f"  将向量化 Top {len(top_laws)} 部法律")

    placeholders = ",".join("?" for _ in top_laws)
    cursor.execute(f"SELECT id, law_name, article_number, title, content, chapter, category FROM legal_articles WHERE law_name IN ({placeholders})", top_laws)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("  [SKIP] 无法条数据")
        return 0

    # 过滤已向量化的
    rows = [r for r in rows if f"art_{r[0]}_0" not in existing_ids]
    print(f"  待向量化 {len(rows)} 条法条")

    if not rows:
        print("  [SKIP] 全部已向量化")
        return len(existing_ids)

    batch_size = 200
    total_vectorized = 0

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        ids = []
        documents = []
        metadatas = []

        for row in batch:
            art_id, law_name, art_num, title, content, chapter, category = row
            text = f"{law_name} {art_num}"
            if title:
                text += f" {title}"
            text += f"\n{content}"

            # 法条通常不超过500字，不分块
            ids.append(f"art_{art_id}_0")
            documents.append(text[:2000])  # 截断过长内容
            metadatas.append({
                "law_name": law_name,
                "article_number": art_num,
                "title": title or "",
                "chapter": chapter or "",
                "category": category or "",
                "type": "legal_article",
            })

        if not ids:
            continue

        if model_type == "local":
            embeddings = embed_with_local(model, documents)
        else:
            embeddings = embed_with_dashscope(documents)

        collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
        total_vectorized += len(ids)
        print(f"  已处理 {min(i + batch_size, len(rows))}/{len(rows)} 条")

    print(f"  [OK] 新增向量化: {total_vectorized} 个")
    return collection.count()


def vectorize_judicial_interpretations(model, model_type: str):
    """向量化司法解释"""
    import chromadb

    print("\n--- 向量化司法解释 ---")
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, doc_number, content FROM judicial_interpretations")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("  [SKIP] 无司法解释数据")
        return 0

    print(f"  共 {len(rows)} 部司法解释")

    chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_directory)
    collection = chroma_client.get_or_create_collection(
        name="judicial_interp_vec",
        metadata={"description": "司法解释向量检索"}
    )

    total_vectorized = 0

    for row in rows:
        interp_id, title, doc_number, content = row
        chunks = chunk_text(f"{title}\n{doc_number}\n{content}")

        ids = [f"interp_{interp_id}_{j}" for j in range(len(chunks))]
        metadatas = [
            {
                "title": title,
                "doc_number": doc_number or "",
                "type": "judicial_interpretation",
            }
            for _ in chunks
        ]

        if model_type == "local":
            embeddings = embed_with_local(model, chunks)
        else:
            embeddings = embed_with_dashscope(chunks)

        collection.upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
        total_vectorized += len(ids)

    print(f"  [OK] 向量化完成: {total_vectorized} 个向量")
    return total_vectorized


def vectorize_guiding_cases(model, model_type: str):
    """向量化指导性案例"""
    import chromadb

    print("\n--- 向量化指导性案例 ---")
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, case_number, title, court, case_type, summary, full_text, keywords FROM guiding_cases")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("  [SKIP] 无指导性案例数据")
        return 0

    print(f"  共 {len(rows)} 个案例")

    chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_directory)
    collection = chroma_client.get_or_create_collection(
        name="guiding_cases_vec",
        metadata={"description": "指导性案例向量检索"}
    )

    total_vectorized = 0

    for row in rows:
        case_id, case_number, title, court, case_type, summary, full_text, keywords = row
        text = f"{case_number} {title}\n法院: {court}\n"
        if summary:
            text += f"裁判要点: {summary}\n"
        if keywords:
            try:
                kw_list = json.loads(keywords) if isinstance(keywords, str) else keywords
                text += f"关键词: {', '.join(kw_list)}\n"
            except json.JSONDecodeError:
                pass
        text += full_text

        chunks = chunk_text(text, chunk_size=800)

        ids = [f"case_{case_id}_{j}" for j in range(len(chunks))]
        metadatas = [
            {
                "case_number": case_number,
                "title": title,
                "court": court or "",
                "case_type": case_type or "",
                "type": "guiding_case",
            }
            for _ in chunks
        ]

        if model_type == "local":
            embeddings = embed_with_local(model, chunks)
        else:
            embeddings = embed_with_dashscope(chunks)

        collection.upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
        total_vectorized += len(ids)

    print(f"  [OK] 向量化完成: {total_vectorized} 个向量")
    return total_vectorized


def run_vectorization():
    print("=" * 60)
    print("法律知识库向量化")
    print("=" * 60)

    model, model_type = get_embedding_service()

    stats = {}

    # 法条：向量化 Top 50 部法律（覆盖最常用法律）
    stats["legal_articles"] = vectorize_legal_articles(model, model_type, limit_laws=50)
    stats["judicial_interpretations"] = vectorize_judicial_interpretations(model, model_type)
    stats["guiding_cases"] = vectorize_guiding_cases(model, model_type)

    print(f"\n{'=' * 60}")
    print("[RESULT] 向量化统计:")
    for k, v in stats.items():
        print(f"  {k}: {v} 个向量")
    print(f"  总计: {sum(stats.values())} 个向量")


if __name__ == "__main__":
    run_vectorization()
