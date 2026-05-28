"""
统一法律知识库检索服务
整合原有的 legal_rag_service 与新的法律知识库（法条、司法解释、判例）
"""
import os
import sys
import json
import sqlite3
from typing import List, Dict, Optional, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.config import settings


class UnifiedLegalSearchService:
    """
    统一法律知识库检索服务
    同时检索三个向量库：法条、司法解释、指导性案例
    """

    def __init__(self):
        self._chroma_client = None
        self._collections = {}
        self._db_path = None

    def _get_chroma(self):
        if self._chroma_client is None:
            import chromadb
            self._chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_directory)
        return self._chroma_client

    def _get_collection(self, name):
        if name not in self._collections:
            try:
                self._collections[name] = self._get_chroma().get_collection(name)
            except Exception:
                self._collections[name] = None
        return self._collections[name]

    def _get_db(self):
        if self._db_path is None:
            db_url = settings.database_url
            if db_url.startswith("sqlite:///"):
                self._db_path = db_url.replace("sqlite:///", "")
                if self._db_path.startswith("./"):
                    self._db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), self._db_path[2:])
            else:
                self._db_path = db_url
            if not os.path.exists(self._db_path):
                self._db_path = "legal_system.db"
        return self._db_path

    def search_all(self, query: str, top_k: int = 5, case_type: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        同时检索法条、司法解释、判例
        返回结构化结果
        """
        results = {
            "legal_articles": self.search_legal_articles(query, top_k),
            "judicial_interpretations": self.search_judicial_interpretations(query, top_k),
            "guiding_cases": self.search_guiding_cases(query, top_k, case_type),
        }
        return results

    def search_legal_articles(self, query: str, top_k: int = 5) -> List[Dict]:
        """检索法条"""
        col = self._get_collection("legal_articles_vec")
        if not col:
            return []

        try:
            results = col.query(query_texts=[query], n_results=top_k, include=["documents", "metadatas", "distances"])
            return self._format_results(results, "legal_article")
        except Exception:
            return []

    def search_judicial_interpretations(self, query: str, top_k: int = 5) -> List[Dict]:
        """检索司法解释"""
        col = self._get_collection("judicial_interp_vec")
        if not col:
            return []

        try:
            results = col.query(query_texts=[query], n_results=top_k, include=["documents", "metadatas", "distances"])
            return self._format_results(results, "judicial_interpretation")
        except Exception:
            return []

    def search_guiding_cases(self, query: str, top_k: int = 5, case_type: Optional[str] = None) -> List[Dict]:
        """检索指导性案例"""
        col = self._get_collection("guiding_cases_vec")
        if not col:
            return []

        try:
            where_filter = None
            if case_type:
                where_filter = {"case_type": case_type}

            results = col.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            return self._format_results(results, "guiding_case")
        except Exception:
            return []

    def _format_results(self, chroma_results: Dict, result_type: str) -> List[Dict]:
        """格式化 ChromaDB 搜索结果"""
        formatted = []
        if not chroma_results or not chroma_results.get("ids") or not chroma_results["ids"][0]:
            return formatted

        for i, doc_id in enumerate(chroma_results["ids"][0]):
            metadata = chroma_results["metadatas"][0][i] if chroma_results.get("metadatas") else {}
            distance = chroma_results["distances"][0][i] if chroma_results.get("distances") else 0
            similarity = 1 - distance

            result = {
                "id": doc_id,
                "content": chroma_results["documents"][0][i] if chroma_results.get("documents") else "",
                "type": result_type,
                "similarity": round(similarity, 4),
                "metadata": metadata,
            }

            # 添加类型特定字段
            if result_type == "legal_article":
                result["citation"] = f"《{metadata.get('law_name', '')}》{metadata.get('article_number', '')}"
                result["law_name"] = metadata.get("law_name", "")
                result["article_number"] = metadata.get("article_number", "")
            elif result_type == "judicial_interpretation":
                result["title"] = metadata.get("title", "")
                result["doc_number"] = metadata.get("doc_number", "")
                result["citation"] = f"{metadata.get('title', '')} ({metadata.get('doc_number', '')})"
            elif result_type == "guiding_case":
                result["case_number"] = metadata.get("case_number", "")
                result["title"] = metadata.get("title", "")
                result["court"] = metadata.get("court", "")
                result["case_type"] = metadata.get("case_type", "")
                result["citation"] = f"{metadata.get('case_number', '')} {metadata.get('title', '')}"

            formatted.append(result)

        return formatted

    def get_law_by_citation(self, law_name: str, article_number: str) -> Optional[Dict]:
        """通过引用获取法条原文"""
        db_path = self._get_db()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM legal_articles WHERE law_name = ? AND article_number = ?",
            (law_name, article_number)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def get_case_by_number(self, case_number: str) -> Optional[Dict]:
        """通过案号获取案例"""
        db_path = self._get_db()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM guiding_cases WHERE case_number = ?", (case_number,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None


# 单例
_unified_search = None

def get_unified_legal_search():
    global _unified_search
    if _unified_search is None:
        _unified_search = UnifiedLegalSearchService()
    return _unified_search
