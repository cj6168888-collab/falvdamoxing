"""
案件智能分析引擎
==============
解决三大核心问题：
1. 超时问题：流式输出 + 分段生成 + 报告缓存
2. 问答质量：问题澄清 + 意图识别 + 追问机制
3. 证据管理：知识图谱 + 信度分析 + 精准索引

设计理念：
- 精准是法律AI的第一原理
- 慢即是快：宁可分段输出，也要保证完整准确
- 像资深律师一样思考：理解意图、分析证据、生成报告
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Generator
from dataclasses import dataclass, field
from enum import Enum
import asyncio


class AnalysisPhase(Enum):
    """分析阶段枚举"""
    PENDING = "待分析"
    ANALYZING = "分析中"
    COMPLETED = "已完成"
    FAILED = "失败"
    CANCELLED = "已取消"


class QuestionIntent(Enum):
    """问题意图枚举"""
    UNCLEAR = "unclear"           # 问题模糊，需要澄清
    FACT_QUERY = "fact_query"     # 事实查询
    EVIDENCE_QUERY = "evidence_query"  # 证据相关
    STRATEGY_QUERY = "strategy_query"  # 策略咨询
    RISK_QUERY = "risk_query"     # 风险评估
    PROCEDURE_QUERY = "procedure_query"  # 程序问题
    LEGAL_QUERY = "legal_query"   # 法律问题
    OPINION_REQUEST = "opinion_request"  # 意见请求


@dataclass
class ClarifyingQuestion:
    """澄清性问题"""
    question: str                    # 追问内容
    reason: str                      # 需要澄清的原因
    options: Optional[List[str]] = None  # 选项（如适用）
    key_point: str = ""            # 关键点


@dataclass
class AnalysisTask:
    """分析任务"""
    task_id: str
    case_id: int
    task_type: str                   # analysis/strategy/evidence/prediction
    status: AnalysisPhase = AnalysisPhase.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None
    progress: float = 0.0           # 0-1
    segments: List[Dict] = field(default_factory=list)  # 分段结果
    metadata: Dict = field(default_factory=dict)


@dataclass
class EvidenceNode:
    """证据节点 - 知识图谱中的节点"""
    evidence_id: str
    name: str
    evidence_type: str              # 证据类型
    credibility: float               # 信度 0-1
    credibility_factors: List[str]   # 信度影响因素
    
    # 关联属性
    proves_facts: List[str]         # 证明的事实
    related_evidence: List[str]     # 相关证据
    contradicts_evidence: List[str]  # 矛盾证据
    
    # 元数据
    source: str
    custody: str
    uploaded_at: datetime = field(default_factory=datetime.now)
    content_hash: str = ""         # 内容哈希，用于去重
    
    # 分析结果
    analysis_summary: str = ""       # AI分析摘要
    keywords: List[str] = field(default_factory=list)  # 关键词索引


@dataclass
class QuestionAnalysis:
    """问题分析结果"""
    intent: QuestionIntent
    key_entities: List[str]          # 关键实体
    ambiguity_points: List[str]      # 模糊点
    clarifying_questions: List[ClarifyingQuestion]  # 需要澄清的问题
    suggested_context: str = ""      # 建议补充的上下文
    
    @property
    def needs_clarification(self) -> bool:
        return self.intent == QuestionIntent.UNCLEAR or len(self.ambiguity_points) > 0


class CaseInsightEngine:
    """
    案件洞察引擎
    
    核心能力：
    1. 智能问答（问题澄清机制）
    2. 证据图谱（精准证据管理）
    3. 报告生成（分段流式输出）
    """
    
    def __init__(self, llm_service, rag_service=None):
        self.llm = llm_service
        self.rag = rag_service
        
        # 分析任务缓存
        self.analysis_cache: Dict[str, AnalysisTask] = {}
        
        # 证据知识图谱
        self.evidence_graph: Dict[int, List[EvidenceNode]] = {}  # case_id -> evidence nodes
        
        # 报告缓存
        self.report_cache: Dict[str, Dict] = {}
        
    # ==================== 核心能力1：智能问答 ====================
    
    async def analyze_question(self, question: str, case_info: Dict) -> QuestionAnalysis:
        """
        分析用户问题，识别意图和模糊点
        
        返回是否需要澄清，以及澄清问题
        """
        prompt = f"""分析以下法律案件相关问题：

【问题】
{question}

【案件基本信息】
案件类型：{case_info.get('case_type', '未知')}
案由：{case_info.get('cause', '未知')}
原告：{case_info.get('plaintiff', '未知')}
被告：{case_info.get('defendant', '未知')}

请进行深度分析：

1. **意图识别**：判断用户想问什么
   - 事实查询：问案件发生了什么
   - 证据相关：问证据准备、分析
   - 策略咨询：问如何应对
   - 风险评估：问风险大小
   - 程序问题：问诉讼流程
   - 法律问题：问法律规定
   - 意见请求：请求AI给出建议

2. **关键实体识别**：
   - 人物：{case_info.get('plaintiff', '')}、{case_info.get('defendant', '')}
   - 行为：提取问题中涉及的关键行为
   - 时间：提取问题中涉及的时间点
   - 金额：提取问题中涉及的金额

3. **模糊点识别**：
   - 识别问题中不清晰的地方
   - 判断是否需要补充信息

4. **澄清问题生成**：
   - 如果问题模糊，生成追问
   - 提供具体选项或引导

请以JSON格式返回：
{{
    "intent": "意图类型",
    "key_entities": ["实体1", "实体2"],
    "ambiguity_points": ["模糊点1", "模糊点2"],
    "clarifying_questions": [
        {{
            "question": "追问内容",
            "reason": "为什么需要澄清",
            "options": ["选项1", "选项2"]  // 如适用
        }}
    ]
}}"""
        
        try:
            response = self.llm.chat([
                {"role": "system", "content": "你是一位专业的法律案件分析助手，擅长精准理解用户意图。"},
                {"role": "user", "content": prompt}
            ], model="qwen-plus")
            
            # 解析响应
            result = json.loads(response)
            
            intent = QuestionIntent(result.get("intent", "UNCLEAR"))
            clarifying = [
                ClarifyingQuestion(
                    question=q.get("question", ""),
                    reason=q.get("reason", ""),
                    options=q.get("options")
                )
                for q in result.get("clarifying_questions", [])
            ]
            
            return QuestionAnalysis(
                intent=intent,
                key_entities=result.get("key_entities", []),
                ambiguity_points=result.get("ambiguity_points", []),
                clarifying_questions=clarifying
            )
        except Exception as e:
            # 解析失败时返回默认分析
            return QuestionAnalysis(
                intent=QuestionIntent.UNCLEAR,
                key_entities=[],
                ambiguity_points=["无法解析问题意图"],
                clarifying_questions=[
                    ClarifyingQuestion(
                        question="您的问题比较模糊，可以更具体地说明：\n1. 您想了解案件的事实情况？\n2. 您想知道需要准备哪些证据？\n3. 您想了解诉讼策略？",
                        reason="无法理解问题意图，需要用户澄清",
                        options=["了解案件事实", "了解证据准备", "了解诉讼策略"]
                    )
                ]
            )
    
    async def answer_with_clarification(
        self, 
        question: str, 
        case_info: Dict,
        context: str = ""
    ) -> Dict:
        """
        带澄清机制的问答
        
        返回格式：
        {
            "needs_clarification": bool,
            "clarifying_questions": [...],
            "answer": str,  // 如果不需要澄清
            "intent": str
        }
        """
        # 1. 先分析问题
        analysis = await self.analyze_question(question, case_info)
        
        # 2. 如果需要澄清，返回澄清问题
        if analysis.needs_clarification:
            return {
                "needs_clarification": True,
                "intent": analysis.intent.value,
                "key_entities": analysis.key_entities,
                "clarifying_questions": [
                    {
                        "question": cq.question,
                        "reason": cq.reason,
                        "options": cq.options
                    }
                    for cq in analysis.clarifying_questions
                ],
                "answer": None
            }
        
        # 3. 不需要澄清，直接回答
        # 构建精准的提示词
        answer_prompt = f"""基于以下案件信息，直接回答用户问题。

【案件信息】
案件名称：{case_info.get('title', '')}
案件类型：{case_info.get('case_type', '')}
案由：{case_info.get('cause', '')}
原告：{case_info.get('plaintiff', '')}
被告：{case_info.get('defendant', '')}
诉讼金额：{case_info.get('claim_amount', '')}
补充说明：{case_info.get('supplement', '')}

【相关上下文】
{context if context else '无'}

【用户问题】
{question}

【问题意图分析结果】
意图类型：{analysis.intent.value}
关键实体：{', '.join(analysis.key_entities)}

请直接、精准地回答问题。如果涉及法律判断，给出具体依据。"""
        
        answer = self.llm.chat([
            {"role": "system", "content": "你是一位资深法律顾问。请直接、精准地回答问题，简洁明了。"},
            {"role": "user", "content": answer_prompt}
        ], model="qwen-plus")
        
        return {
            "needs_clarification": False,
            "intent": analysis.intent.value,
            "key_entities": analysis.key_entities,
            "clarifying_questions": [],
            "answer": answer
        }
    
    # ==================== 核心能力2：证据知识图谱 ====================
    
    async def build_evidence_graph(self, case_id: int, evidence_list: List[Dict]) -> List[EvidenceNode]:
        """
        构建案件证据知识图谱
        
        每个证据被分析并创建节点，包括：
        - 证据基本信息
        - 信度评分及因素
        - 与其他证据的关系
        - 关键词索引
        """
        nodes = []
        
        for i, ev in enumerate(evidence_list):
            # 计算内容哈希，用于去重
            content_hash = hashlib.md5(
                f"{ev.get('name', '')}{ev.get('content', '')}".encode()
            ).hexdigest()
            
            # 分析证据信度
            credibility_analysis = await self._analyze_evidence_credibility(ev)
            
            # 提取关键词
            keywords = await self._extract_evidence_keywords(ev)
            
            # 分析证据关联
            related, contradicts = await self._analyze_evidence_relations(
                ev, evidence_list, nodes
            )
            
            node = EvidenceNode(
                evidence_id=ev.get('id', f"ev_{i}"),
                name=ev.get('name', ''),
                evidence_type=ev.get('type', '未知'),
                credibility=credibility_analysis['score'],
                credibility_factors=credibility_analysis['factors'],
                proves_facts=credibility_analysis['proves_facts'],
                related_evidence=related,
                contradicts_evidence=contradicts,
                source=ev.get('source', '未知'),
                custody=ev.get('custody', '未知'),
                content_hash=content_hash,
                keywords=keywords
            )
            
            nodes.append(node)
        
        # 存储到图谱
        self.evidence_graph[case_id] = nodes
        
        return nodes
    
    async def _analyze_evidence_credibility(self, evidence: Dict) -> Dict:
        """分析单个证据的信度"""
        prompt = f"""分析以下证据的信度 - 法律应用：证据完整性优先：

【证据名称】{evidence.get('name', '')}
【证据类型】{evidence.get('type', '')}
【证据内容】{evidence.get('content', '')}
【证据来源】{evidence.get('source', '')}
【举证方】{evidence.get('custody', '')}

请分析：
1. 证据信度评分 (0-1)
2. 影响信度的因素
3. 这个证据能证明什么事实

返回JSON格式：
{{
    "score": 0.85,
    "factors": ["因素1", "因素2"],
    "proves_facts": ["事实1", "事实2"]
}}"""
        
        try:
            response = self.llm.chat([
                {"role": "system", "content": "你是一位专业的证据审查专家。"},
                {"role": "user", "content": prompt}
            ], model="qwen-plus")
            
            result = json.loads(response)
            return {
                "score": result.get("score", 0.5),
                "factors": result.get("factors", []),
                "proves_facts": result.get("proves_facts", [])
            }
        except:
            return {"score": 0.5, "factors": [], "proves_facts": []}
    
    async def _extract_evidence_keywords(self, evidence: Dict) -> List[str]:
        """提取证据关键词用于索引"""
        text = f"{evidence.get('name', '')} {evidence.get('content', '')}"
        
        prompt = f"""从以下证据文本中提取关键词，用于精准检索：

【证据名称】{evidence.get('name', '')}
【证据内容】{evidence.get('content', '')}

请提取5-10个关键词，以JSON数组格式返回：
["关键词1", "关键词2", ...]"""
        
        try:
            response = self.llm.chat([
                {"role": "system", "content": "提取关键词。"},
                {"role": "user", "content": prompt}
            ], model="qwen-plus")
            
            return json.loads(response)
        except:
            return []
    
    async def _analyze_evidence_relations(
        self, 
        evidence: Dict, 
        all_evidence: List[Dict],
        existing_nodes: List[EvidenceNode]
    ) -> tuple:
        """分析证据与其他证据的关系"""
        # 简化处理，实际应该调用LLM分析
        related = []
        contradicts = []
        
        ev_name = evidence.get('name', '').lower()
        ev_content = evidence.get('content', '').lower()
        
        for other_ev in all_evidence:
            if other_ev == evidence:
                continue
            
            other_name = other_ev.get('name', '').lower()
            other_content = other_ev.get('content', '').lower()
            
            # 简单关键词匹配
            if any(w in other_content for w in [ev_name] if len(w) > 3):
                related.append(other_ev.get('id', ''))
            
            # 检查矛盾
            if ('否定' in ev_content and '确认' in other_content) or \
               ('未' in ev_content and '已' in other_content):
                contradicts.append(other_ev.get('id', ''))
        
        return related, contradicts
    
    async def query_evidence(
        self, 
        case_id: int, 
        query: str,
        search_type: str = "all"  # all/related/contradicts/keywords
    ) -> List[EvidenceNode]:
        """
        精准查询证据
        
        支持多种查询方式：
        - 关键词查询
        - 相关证据查询
        - 矛盾证据查询
        """
        if case_id not in self.evidence_graph:
            return []
        
        nodes = self.evidence_graph[case_id]
        query_lower = query.lower()
        
        if search_type == "keywords":
            # 关键词检索
            return [
                n for n in nodes 
                if any(query_lower in kw.lower() for kw in n.keywords)
            ]
        elif search_type == "related":
            # 相关证据
            results = []
            for n in nodes:
                if query_lower in n.name.lower() or query_lower in n.content_hash.lower():
                    results.extend([
                        nn for nn in nodes 
                        if nn.evidence_id in n.related_evidence
                    ])
            return results
        elif search_type == "contradicts":
            # 矛盾证据
            for n in nodes:
                if query_lower in n.name.lower():
                    return [
                        nn for nn in nodes 
                        if nn.evidence_id in n.contradicts_evidence
                    ]
            return []
        else:
            # 全局检索
            return [
                n for n in nodes
                if query_lower in n.name.lower() or
                   query_lower in n.evidence_type.lower() or
                   any(query_lower in kw.lower() for kw in n.keywords)
            ]
    
    def get_evidence_summary(self, case_id: int) -> Dict:
        """获取证据图谱摘要"""
        if case_id not in self.evidence_graph:
            return {}
        
        nodes = self.evidence_graph[case_id]
        
        # 按类型统计
        type_counts = {}
        total_credibility = 0
        
        for n in nodes:
            type_counts[n.evidence_type] = type_counts.get(n.evidence_type, 0) + 1
            total_credibility += n.credibility
        
        return {
            "total_count": len(nodes),
            "by_type": type_counts,
            "average_credibility": total_credibility / len(nodes) if nodes else 0,
            "high_credibility_count": len([n for n in nodes if n.credibility >= 0.8]),
            "low_credibility_count": len([n for n in nodes if n.credibility < 0.5]),
            "keywords": list(set(kw for n in nodes for kw in n.keywords))[:20]
        }
    
    # ==================== 核心能力3：报告分段生成 ====================
    
    async def generate_report_streaming(
        self,
        case_id: int,
        report_type: str,  # analysis/strategy/full_analysis
        case_info: Dict,
        on_progress: Callable[[float, str], None] = None
    ) -> Generator[str, None, None]:
        """
        流式生成报告
        
        分段输出，每段产出时触发回调
        这样即使用户中断，也能看到已生成的部分
        """
        # 检查缓存
        cache_key = self._get_cache_key(case_id, report_type)
        if cache_key in self.report_cache:
            cached = self.report_cache[cache_key]
            if not self._is_cache_expired(cached):
                yield cached['content']
                return
        
        # 创建分析任务
        task = AnalysisTask(
            task_id=cache_key,
            case_id=case_id,
            task_type=report_type
        )
        self.analysis_cache[cache_key] = task
        
        # 根据报告类型选择生成策略
        if report_type == "analysis":
            async for segment in self._generate_analysis_segments(case_info, task, on_progress):
                yield segment
        elif report_type == "strategy":
            async for segment in self._generate_strategy_segments(case_info, task, on_progress):
                yield segment
        elif report_type == "full_analysis":
            async for segment in self._generate_full_analysis_segments(case_info, task, on_progress):
                yield segment
        else:
            yield "不支持的报告类型"
    
    async def _generate_analysis_segments(
        self,
        case_info: Dict,
        task: AnalysisTask,
        on_progress: Callable
    ) -> Generator[str, None, None]:
        """分段生成案件分析"""
        sections = [
            ("一、案件事实", "分析案件的基本事实情况"),
            ("二、法律关系", "分析案件涉及的法律关系"),
            ("三、争议焦点", "识别并分析案件的争议焦点"),
            ("四、证据评估", "评估现有证据的证明力"),
            ("五、法律依据", "引用适用的法律条款"),
            ("六、突破口", "分析可能的突破口"),
            ("七、策略建议", "提出具体的诉讼策略")
        ]
        
        full_content = ""
        task.status = AnalysisPhase.ANALYZING
        
        for i, (title, desc) in enumerate(sections):
            if on_progress:
                on_progress((i / len(sections)) * 0.5, f"生成中: {title}")
            
            # 先生成提纲
            outline_prompt = f"""基于以下案件信息，为「{title}」生成详细分析内容。

【案件信息】
案件类型：{case_info.get('case_type', '')}
案由：{case_info.get('cause', '')}
原告：{case_info.get('plaintiff', '')}
被告：{case_info.get('defendant', '')}
诉讼金额：{case_info.get('claim_amount', '')}
描述：{case_info.get('description', '')}

【本节要求】
{title}
分析要点：{desc}

请生成300-500字的详细分析内容。"""
            
            section_content = self.llm.chat([
                {"role": "system", "content": "你是一位资深法律专家，分析精准、结构清晰。"},
                {"role": "user", "content": outline_prompt}
            ], model="qwen-plus")
            
            # 流式输出（这里简化处理，实际可以用更细粒度的流式）
            segment = f"\n\n{title}\n{section_content}"
            full_content += segment
            
            task.progress = (i + 1) / len(sections)
            task.segments.append({
                "title": title,
                "content": section_content,
                "progress": task.progress
            })
            
            yield segment
        
        # 缓存结果
        task.status = AnalysisPhase.COMPLETED
        task.completed_at = datetime.now()
        task.result = full_content
        task.progress = 1.0
        
        cache_key = task.task_id
        self.report_cache[cache_key] = {
            "content": full_content,
            "generated_at": datetime.now(),
            "case_id": task.case_id,
            "report_type": task.task_type
        }
    
    async def _generate_strategy_segments(
        self,
        case_info: Dict,
        task: AnalysisTask,
        on_progress: Callable
    ) -> Generator[str, None, None]:
        """分段生成策略建议"""
        sections = [
            ("一、诉讼方向", "确定诉讼策略方向"),
            ("二、证据策略", "制定证据准备策略"),
            ("三、关键风险", "识别并评估关键风险"),
            ("四、行动建议", "提出具体的行动建议")
        ]
        
        full_content = ""
        
        for i, (title, desc) in enumerate(sections):
            if on_progress:
                on_progress((i / len(sections)) * 0.5, f"生成中: {title}")
            
            prompt = f"""基于以下案件信息，生成{title}。

【案件信息】
案由：{case_info.get('cause', '')}
原告：{case_info.get('plaintiff', '')}
被告：{case_info.get('defendant', '')}
诉讼金额：{case_info.get('claim_amount', '')}

【本节要求】
{title}
{desc}

请生成300-500字的策略内容。"""
            
            section_content = self.llm.chat([
                {"role": "system", "content": "你是一位资深诉讼律师，策略精准、可操作。"},
                {"role": "user", "content": prompt}
            ], model="qwen-plus")
            
            segment = f"\n\n{title}\n{section_content}"
            full_content += segment
            
            yield segment
        
        # 缓存
        self.report_cache[task.task_id] = {
            "content": full_content,
            "generated_at": datetime.now(),
            "case_id": task.case_id,
            "report_type": task.task_type
        }
    
    async def _generate_full_analysis_segments(
        self,
        case_info: Dict,
        task: AnalysisTask,
        on_progress: Callable
    ) -> Generator[str, None, None]:
        """分段生成完整对抗性分析报告"""
        # 这是最复杂的报告，分成多个大段
        major_sections = [
            ("第一部分：我方战场态势评估", [
                ("1.1 我方优势", "SWOT分析-优势"),
                ("1.2 我方弱点", "SWOT分析-弱点")
            ]),
            ("第二部分：对手深度分析", [
                ("2.1 对手画像", "对手特征"),
                ("2.2 对手策略预测", "对手可能的策略")
            ]),
            ("第三部分：证据攻防矩阵", [
                ("3.1 我方核心证据", "证据分析"),
                ("3.2 对方可能证据", "预判对方证据")
            ]),
            ("第四部分：案件走向预测", [
                ("4.1 情景分支", "可能的情景"),
                ("4.2 转折点预警", "关键节点")
            ]),
            ("第五部分：应对策略", [
                ("5.1 总体战略", "战略定位"),
                ("5.2 分层应对", "具体方案")
            ]),
            ("第六部分：执行清单", [
                ("6.1 立即行动", "紧急任务"),
                ("6.2 短期任务", "近期计划")
            ])
        ]
        
        full_content = "# 对抗性分析报告\n"
        
        for i, (major_title, subsections) in enumerate(major_sections):
            if on_progress:
                on_progress((i / len(major_sections)) * 0.8, f"生成中: {major_title}")
            
            major_content = f"\n\n## {major_title}\n"
            
            for j, (sub_title, focus) in enumerate(subsections):
                sub_prompt = f"""基于案件信息，生成「{sub_title}」：

【案件】
{case_info.get('title', '')}
{case_info.get('description', '')}

【分析重点】
{focus}

生成200-400字分析。"""
                
                sub_content = self.llm.chat([
                    {"role": "system", "content": "你是一位顶级诉讼策略专家。"},
                    {"role": "user", "content": sub_prompt}
                ], model="qwen-plus")
                
                major_content += f"\n### {sub_title}\n{sub_content}"
                yield f"\n### {sub_title}\n{sub_content}"
            
            full_content += major_content
        
        # 缓存
        self.report_cache[task.task_id] = {
            "content": full_content,
            "generated_at": datetime.now(),
            "case_id": task.case_id,
            "report_type": task.task_type
        }
    
    def _get_cache_key(self, case_id: int, report_type: str) -> str:
        """生成缓存键"""
        return f"{case_id}_{report_type}_{datetime.now().strftime('%Y%m%d')}"
    
    def _is_cache_expired(self, cached: Dict, max_age_hours: int = 24) -> bool:
        """检查缓存是否过期"""
        if not cached.get("generated_at"):
            return True
        age = datetime.now() - cached["generated_at"]
        return age.total_seconds() > max_age_hours * 3600
    
    def invalidate_cache(self, case_id: Optional[int] = None):
        """清除缓存"""
        if case_id:
            # 只清除指定案件的缓存
            keys_to_remove = [
                k for k, v in self.report_cache.items()
                if v.get("case_id") == case_id
            ]
            for k in keys_to_remove:
                del self.report_cache[k]
        else:
            self.report_cache.clear()
