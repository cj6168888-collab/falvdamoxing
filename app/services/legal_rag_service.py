"""
法律条文RAG服务（biz-9）
向量数据库存储法条 + 引用溯源

核心功能：
1. 向量数据库存储常用法律条文
2. 语义检索法律条文
3. 引用溯源（用户可点击跳转到法条原文）
4. 条文有效性验证
5. RAG增强生成（结合法条生成更准确的法律建议）

依赖：
- chromadb (已安装)
- sentence-transformers (已安装)
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class LawCategory(str, Enum):
    """法律分类"""
    CIVIL = "civil"              # 民法
    CRIMINAL = "criminal"        # 刑法
    ADMINISTRATIVE = "admin"    # 行政法
    COMMERCIAL = "commercial"    # 商法
    LABOR = "labor"             # 劳动法
    PROCEDURAL = "procedural"   # 程序法
    OTHER = "other"             # 其他


@dataclass
class LegalArticle:
    """
    法律条文
    """
    law_name: str              # 法律法规名称
    category: str              # 分类
    article_no: str            # 条文编号（如"第188条"）
    full_article_no: str       # 完整编号（如"民法典第188条"）
    title: str                 # 标题（如"普通诉讼时效"）
    content: str               # 全文内容
    effective_date: str        # 生效日期
    is_valid: bool            # 是否现行有效
    supersedes: str            # 替代了哪些旧法条
    keywords: List[str]        # 关键词（用于检索）
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def format_citation(self) -> str:
        """格式化引用格式"""
        return f"《{self.law_name}》{self.article_no}"


class LegalRAGService:
    """
    法律条文RAG服务（biz-9）
    
    使用向量数据库存储和检索法律条文
    支持：
    - 语义检索法律条文
    - 条文引用溯源
    - RAG增强生成
    """
    
    # 内置法条数据库（核心常用条文，fallback用）
    CORE_LAWS: List[Dict] = [
        # 民法典核心条文
        {
            "law_name": "中华人民共和国民法典",
            "category": "civil",
            "article_no": "第143条",
            "title": "民事法律行为有效条件",
            "content": "具备下列条件的民事法律行为有效：（一）行为人具有相应的民事行为能力；（二）意思表示真实；（三）不违反法律、行政法规的强制性规定，不违背公序良俗。",
            "effective_date": "2021-01-01",
            "is_valid": True,
            "supersedes": "",
            "keywords": ["民事法律行为", "有效", "行为能力", "意思表示", "公序良俗"]
        },
        {
            "law_name": "中华人民共和国民法典",
            "category": "civil",
            "article_no": "第188条",
            "title": "普通诉讼时效",
            "content": "向人民法院请求保护民事权利的诉讼时效期间为三年。法律另有规定的，依照其规定。诉讼时效期间自权利人知道或者应当知道权利受到损害以及义务人之日起计算。法律另有规定的，依照其规定。但是，从权利被侵害之日起超过二十年的，人民法院不予保护，有特殊情况的，人民法院可以根据权利人的申请决定延长。",
            "effective_date": "2021-01-01",
            "is_valid": True,
            "supersedes": "民法通则第135-141条",
            "keywords": ["诉讼时效", "三年", "时效", "权利保护", "最长保护期间"]
        },
        {
            "law_name": "中华人民共和国民法典",
            "category": "civil",
            "article_no": "第502条",
            "title": "合同生效时间",
            "content": "依法成立的合同，自成立时生效，但是法律另有规定或者当事人另有约定的除外。",
            "effective_date": "2021-01-01",
            "is_valid": True,
            "supersedes": "合同法第44条",
            "keywords": ["合同", "生效", "成立", "意思表示"]
        },
        {
            "law_name": "中华人民共和国民法典",
            "category": "civil",
            "article_no": "第577条",
            "title": "违约责任",
            "content": "当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。",
            "effective_date": "2021-01-01",
            "is_valid": True,
            "supersedes": "合同法第107条",
            "keywords": ["违约", "违约责任", "继续履行", "补救", "赔偿损失"]
        },
        {
            "law_name": "中华人民共和国民法典",
            "category": "civil",
            "article_no": "第563条",
            "title": "法定解除合同情形",
            "content": "有下列情形之一的，当事人可以解除合同：（一）因不可抗力致使不能实现合同目的；（二）在履行期限届满前，当事人一方明确表示或者以自己的行为表明不履行主要债务；（三）当事人一方迟延履行主要债务，经催告后在合理期限内仍未履行；（四）当事人一方迟延履行债务或者有其他违约行为致使不能实现合同目的；（五）法律规定的其他情形。",
            "effective_date": "2021-01-01",
            "is_valid": True,
            "supersedes": "合同法第94条",
            "keywords": ["解除合同", "法定解除", "不可抗力", "违约", "迟延履行"]
        },
        {
            "law_name": "中华人民共和国民法典",
            "category": "civil",
            "article_no": "第585条",
            "title": "违约金调整",
            "content": "当事人可以约定一方违约时应当根据违约情况向对方支付一定数额的违约金，也可以约定因违约产生的损失赔偿额的计算方法。约定的违约金低于造成的损失的，人民法院或者仲裁机构可以根据当事人的请求予以增加；约定的违约金过分高于造成的损失的，人民法院或者仲裁机构可以根据当事人的请求予以适当减少。",
            "effective_date": "2021-01-01",
            "is_valid": True,
            "supersedes": "合同法第114条",
            "keywords": ["违约金", "违约金调整", "过分高于", "适当减少"]
        },
        {
            "law_name": "中华人民共和国民法典",
            "category": "civil",
            "article_no": "第496-498条",
            "title": "格式条款",
            "content": "格式条款是当事人为了重复使用而预先拟定，并在订立合同时未与对方协商的条款。采用格式条款订立合同的，提供格式条款的一方应当遵循公平原则确定当事人之间的权利和义务，并采取合理的方式提示对方注意免除或者减轻其责任、加重对方责任、限制对方主要权利等与对方有重大利害关系的条款，按照对方的要求对该条款予以说明。提供格式条款一方不合理地免除或者减轻其责任、加重对方责任、限制对方主要权利的，该格式条款无效。对格式条款的理解发生争议的，应当按照通常理解予以解释。对格式条款有两种以上解释的，应当作出不利于提供格式条款一方的解释。",
            "effective_date": "2021-01-01",
            "is_valid": True,
            "supersedes": "合同法第39-41条",
            "keywords": ["格式条款", "格式合同", "免责条款", "不公平条款", "解释规则"]
        },
        # 民事诉讼法核心条文
        {
            "law_name": "中华人民共和国民事诉讼法",
            "category": "procedural",
            "article_no": "第67条",
            "title": "举证责任",
            "content": "当事人对自己提出的主张，有责任提供证据。当事人及其诉讼代理人因客观原因不能自行收集的证据，或者人民法院认为审理案件需要的证据，人民法院应当调查收集。",
            "effective_date": "2021-12-24",
            "is_valid": True,
            "supersedes": "",
            "keywords": ["举证责任", "谁主张谁举证", "证据", "调查收集"]
        },
        {
            "law_name": "中华人民共和国民事诉讼法",
            "category": "procedural",
            "article_no": "第68条",
            "title": "举证期限",
            "content": "当事人应当在举证期限内提供证据。当事人逾期提供证据的，人民法院应当责令其说明理由；拒不说明理由或者理由不成立的，人民法院可以根据不同情形采取不予采纳该证据、采纳该证据但予以训诫、罚款等措施。",
            "effective_date": "2021-12-24",
            "is_valid": True,
            "supersedes": "",
            "keywords": ["举证期限", "逾期举证", "证据采纳"]
        },
        {
            "law_name": "中华人民共和国民事诉讼法",
            "category": "procedural",
            "article_no": "第170条",
            "title": "上诉期限",
            "content": "上诉应当递交上诉状。上诉状的内容，应当包括当事人的姓名，法人的名称及其法定代表人的姓名或者其他组织的名称及其主要负责人的姓名；原审人民法院名称、案件的编号和案由；上诉的请求和理由。上诉状应当通过原审人民法院提出，并按照对方当事人或者代表人的人数提出副本。当事人直接向第二审人民法院上诉的，第二审人民法院应当在五日内将上诉状移交原审人民法院。原审人民法院收到上诉状，应当在五日内将上诉状副本送达对方当事人，对方当事人在收到之日起十五日内提出答辩状。被上诉人收到上诉状副本的，应当在收到之日起十五日内提出答辩状。当事人逾期未提出答辩状的，不影响第二审人民法院的审理。",
            "effective_date": "2021-12-24",
            "is_valid": True,
            "supersedes": "",
            "keywords": ["上诉期限", "上诉状", "答辩状", "15日"]
        },
        {
            "law_name": "中华人民共和国民事诉讼法",
            "category": "procedural",
            "article_no": "第246条",
            "title": "执行申请期限",
            "content": "申请执行的期间为二年，从法律文书规定履行期间的最后一日起计算；法律文书规定分期履行的，从最后一期履行期间届满之日起计算；法律文书未规定履行期间的，从法律文书生效之日起计算。",
            "effective_date": "2021-12-24",
            "is_valid": True,
            "supersedes": "",
            "keywords": ["执行申请", "申请执行", "二年", "履行期间"]
        },
        # 劳动争议调解仲裁法
        {
            "law_name": "中华人民共和国劳动争议调解仲裁法",
            "category": "labor",
            "article_no": "第27条",
            "title": "劳动仲裁时效",
            "content": "劳动争议申请仲裁的时效期间为一年，从当事人知道或者应当知道其权利被侵害之日起计算。劳动关系存续期间因拖欠劳动报酬发生争议的，劳动者申请仲裁不受本条第一款规定的仲裁时效期间的限制；但是，劳动关系终止的，应当自劳动关系终止之日起一年内提出。",
            "effective_date": "2008-05-01",
            "is_valid": True,
            "supersedes": "",
            "keywords": ["劳动仲裁", "时效", "一年", "劳动报酬", "拖欠工资"]
        },
        # 仲裁法
        {
            "law_name": "中华人民共和国仲裁法",
            "category": "procedural",
            "article_no": "第74条",
            "title": "仲裁时效",
            "content": "法律对仲裁时效有规定的，适用该规定。法律对仲裁时效没有规定的，适用诉讼时效的规定。",
            "effective_date": "2017-09-01",
            "is_valid": True,
            "supersedes": "",
            "keywords": ["仲裁时效", "诉讼时效", "适用规定"]
        },
    ]
    
    def __init__(self, persist_directory: Optional[str] = None):
        """
        初始化法律条文RAG服务
        
        Args:
            persist_directory: 向量数据库持久化目录
        """
        self.persist_directory = persist_directory
        self.embeddings = None
        self.vector_db = None
        self._initialized = False
        
        # 初始化向量数据库
        if CHROMADB_AVAILABLE and persist_directory:
            self._init_vector_db()
    
    def _init_vector_db(self):
        """初始化向量数据库"""
        if not CHROMADB_AVAILABLE:
            return
        
        try:
            self.vector_db = chromadb.Client(
                Settings(
                    persist_directory=self.persist_directory,
                    anonymized_telemetry=False
                )
            )
            # 创建或获取 collection
            self.collection = self.vector_db.get_or_create_collection(
                name="legal_articles",
                metadata={"description": "法律条文向量数据库"}
            )
            
            # 检查是否需要初始化数据
            if self.collection.count() == 0:
                self._load_core_laws()
            
            self._initialized = True
        except Exception as e:
            self._initialized = False
    
    def _load_core_laws(self):
        """加载核心法条到向量数据库"""
        if not CHROMADB_AVAILABLE or not self.vector_db:
            return
        
        # 初始化 embedding 模型
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self.embeddings = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        for law in self.CORE_LAWS:
            self._add_article(law)
    
    def _add_article(self, law: Dict):
        """添加法条到向量数据库"""
        if not CHROMADB_AVAILABLE or not self.vector_db:
            return
        
        # 构建文本用于 embedding
        text = f"{law['law_name']}{law['article_no']} {law['title']} {law['content']}"
        
        # 生成 embedding
        if self.embeddings:
            embedding = self.embeddings.encode(text).tolist()
        else:
            # fallback: 使用简单哈希
            import hashlib
            embedding = [float(ord(c)) / 255.0 for c in hashlib.md5(text.encode()).digest()[:128]]
        
        doc_id = f"{law['law_name']}_{law['article_no']}"
        
        self.collection.add(
            documents=[text],
            embeddings=[embedding],
            metadatas=[law],
            ids=[doc_id]
        )
    
    def add_article(self, law: Dict) -> bool:
        """
        添加法律条文到知识库
        
        Args:
            law: 法律条文数据
            
        Returns:
            是否添加成功
        """
        try:
            # 验证必要字段
            required = ["law_name", "article_no", "content"]
            for field in required:
                if field not in law:
                    return False
            
            # 补全字段
            law.setdefault("category", "other")
            law.setdefault("title", "")
            law.setdefault("effective_date", datetime.now().strftime("%Y-%m-%d"))
            law.setdefault("is_valid", True)
            law.setdefault("supersedes", "")
            law.setdefault("keywords", [])
            
            # 生成完整编号
            law["full_article_no"] = f"{law['law_name']}{law['article_no']}"
            
            self._add_article(law)
            return True
        except Exception:
            return False
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        law_name: Optional[str] = None,
        valid_only: bool = True
    ) -> List[Dict]:
        """
        语义检索法律条文
        
        Args:
            query: 查询文本
            top_k: 返回数量
            category: 限定分类
            law_name: 限定法律名称
            valid_only: 仅返回现行有效
            
        Returns:
            匹配的法条列表
        """
        results = []
        
        # 使用向量检索
        if self._initialized and self.embeddings:
            query_embedding = self.embeddings.encode(query).tolist()
            query_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            for i, metadata in enumerate(query_results["metadatas"][0]):
                if valid_only and not metadata.get("is_valid", True):
                    continue
                if category and metadata.get("category") != category:
                    continue
                if law_name and metadata.get("law_name") != law_name:
                    continue
                
                result = dict(metadata)
                result["similarity_score"] = query_results["distances"][0][i]
                result["rank"] = i + 1
                results.append(result)
        
        # fallback: 关键词匹配
        if not results:
            results = self._keyword_search(query, top_k, category, valid_only)
        
        return results
    
    def _keyword_search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        valid_only: bool = True
    ) -> List[Dict]:
        """关键词匹配搜索（fallback）"""
        query_keywords = query.lower().split()
        scores = {}
        
        for law in self.CORE_LAWS:
            if valid_only and not law.get("is_valid", True):
                continue
            if category and law.get("category") != category:
                continue
            
            score = 0
            law_text = f"{law['title']} {law['content']} {' '.join(law.get('keywords', []))}".lower()
            
            for kw in query_keywords:
                if kw in law_text:
                    score += 1
            
            if score > 0:
                scores[f"{law['law_name']}_{law['article_no']}"] = (score, law)
        
        # 排序并返回
        sorted_results = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)
        
        return [
            {**law, "rank": i + 1, "similarity_score": score / len(query_keywords)}
            for i, (_, (score, law)) in enumerate(sorted_results[:top_k])
        ]
    
    def cite(self, law_name: str, article_no: str) -> Optional[LegalArticle]:
        """
        获取法条引用信息
        
        Args:
            law_name: 法律名称
            article_no: 条文编号
            
        Returns:
            法条对象或None
        """
        # 精确查找
        for law in self.CORE_LAWS:
            if law["law_name"] == law_name and law["article_no"] == article_no:
                return LegalArticle(**{**law, "full_article_no": f"{law_name}{article_no}"})
        
        # 向量数据库查找
        if self._initialized:
            doc_id = f"{law_name}_{article_no}"
            try:
                result = self.collection.get(ids=[doc_id])
                if result["metadatas"]:
                    return LegalArticle(**{**result["metadatas"][0], 
                                           "full_article_no": f"{law_name}{article_no}"})
            except Exception:
                pass
        
        return None
    
    def rag_generate(
        self,
        query: str,
        context: Optional[str] = None,
        top_k: int = 5,
        user_position: str = "有利"
    ) -> Dict:
        """
        RAG增强生成
        
        Args:
            query: 用户问题
            context: 案件上下文
            top_k: 检索的法条数量
            user_position: 用户立场
            
        Returns:
            生成结果（包含引用溯源）
        """
        # 1. 检索相关法条
        retrieved_laws = self.search(query, top_k=top_k)
        
        # 2. 构建提示词
        laws_context = "\n\n".join([
            f"法条{i+1}：{law['law_name']}{law['article_no']}（{law['title']}）\n{law['content']}"
            for i, law in enumerate(retrieved_laws)
        ])
        
        # 3. 构建完整提示
        full_prompt = f"""你是一位专业的法律顾问。请根据以下检索到的法律条文回答用户问题。

【检索到的法律条文】：
{laws_context}

"""
        
        if context:
            full_prompt += f"""【案件背景】：
{context}

"""
        
        full_prompt += f"""【用户问题】：{query}

请结合法律条文进行分析，给出专业的法律建议。

注意：
1. 必须引用本文检索到的法律条文，格式为：《法律名》第X条
2. 如果法律条文与问题不相关，请明确说明
3. 对当事人有利的角度和不利角度都应分析
4. 如果涉及时效问题，必须计算具体日期"""

        # 4. 调用LLM（此处生成结构化返回，实际由LLM服务调用）
        citations = [
            {
                "law_name": law["law_name"],
                "article_no": law["article_no"],
                "title": law["title"],
                "content_preview": law["content"][:200],
                "is_valid": law.get("is_valid", True),
                "effective_date": law.get("effective_date", "")
            }
            for law in retrieved_laws
        ]
        
        return {
            "query": query,
            "retrieved_laws": retrieved_laws,
            "citations": citations,
            "prompt": full_prompt,
            "law_count": len(retrieved_laws),
            "search_method": "vector" if self._initialized else "keyword"
        }
    
    def verify_law(self, law_name: str, article_no: str) -> Dict:
        """
        验证法条是否现行有效
        
        Args:
            law_name: 法律名称
            article_no: 条文编号
            
        Returns:
            验证结果
        """
        article = self.cite(law_name, article_no)
        
        if not article:
            return {
                "is_found": False,
                "is_valid": False,
                "warning": f"《{law_name}》{article_no} 未在数据库中找到，请核实法律名称和条文编号"
            }
        
        return {
            "is_found": True,
            "is_valid": article.is_valid,
            "effective_date": article.effective_date,
            "supersedes": article.supersedes,
            "citation": article.format_citation(),
            "warning": f"⚠️ 《{article.law_name}》已失效，被{article.supersedes}替代" if article.supersedes else None
        }


# 全局实例（懒加载）
_legal_rag_service = None

def get_legal_rag_service():
    """获取LegalRAGService实例（懒加载）"""
    global _legal_rag_service
    if _legal_rag_service is None:
        _legal_rag_service = LegalRAGService(persist_directory="data/legal_knowledge")
    return _legal_rag_service

# 为了向后兼容，提供一个代理对象
class LegalRAGServiceProxy:
    """懒加载代理"""
    def __getattr__(self, name):
        return getattr(get_legal_rag_service(), name)

legal_rag_service = LegalRAGServiceProxy()
