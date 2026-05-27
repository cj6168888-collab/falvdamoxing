"""
增强版报告生成服务 - 解决超时问题
================================
核心特性：
1. 分段生成 - 将报告分成多个部分逐步生成
2. 缓存机制 - 避免重复生成，24小时缓存
3. 异步处理 - 后台处理长报告
4. 进度追踪 - 实时显示生成进度
5. 断点续传 - 中断后可继续生成
"""

import hashlib
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Generator
from dataclasses import dataclass, field
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor


class ReportPhase(Enum):
    """报告生成阶段"""
    PENDING = "pending"      # 等待生成
    GENERATING = "generating"  # 生成中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"        # 生成失败
    CANCELLED = "cancelled"  # 已取消


class ReportType(Enum):
    """报告类型"""
    ANALYSIS = "analysis"           # 案件分析
    STRATEGY = "strategy"           # 策略建议
    FULL_ANALYSIS = "full_analysis" # 完整对抗性分析
    EVIDENCE_REPORT = "evidence_report"  # 证据分析报告
    MILESTONE_REPORT = "milestone_report"  # 里程碑报告
    SUMMARY_REPORT = "summary_report"  # 总结报告


@dataclass
class ReportSegment:
    """报告分段"""
    segment_id: int
    title: str                    # 段落标题
    content: str = ""            # 段落内容
    status: ReportPhase = ReportPhase.PENDING
    generated_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class ReportTask:
    """报告生成任务"""
    task_id: str
    case_id: int
    report_type: ReportType
    status: ReportPhase = ReportPhase.PENDING
    
    # 分段内容
    segments: List[ReportSegment] = field(default_factory=list)
    
    # 完整内容（所有分段合并后）
    full_content: str = ""
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 进度
    progress: float = 0.0  # 0.0 - 1.0
    
    # 错误信息
    error: Optional[str] = None
    
    # 缓存信息
    cached: bool = False
    cache_expires_at: Optional[datetime] = None


class ReportCache:
    """报告缓存管理器"""
    
    def __init__(self, max_age_hours: int = 24):
        self._cache: Dict[str, ReportTask] = {}
        self.max_age_hours = max_age_hours
        self._lock = threading.Lock()
    
    def get_cache_key(self, case_id: int, report_type: str, include_context: str = "") -> str:
        """生成缓存键"""
        # 包含案件ID、报告类型和关键上下文（简化版）
        key_base = f"{case_id}_{report_type}"
        if include_context:
            # 取上下文的前100字符的哈希
            ctx_hash = hashlib.md5(include_context[:100].encode()).hexdigest()[:8]
            key_base = f"{key_base}_{ctx_hash}"
        return key_base
    
    def get(self, cache_key: str) -> Optional[ReportTask]:
        """获取缓存的报告任务"""
        with self._lock:
            task = self._cache.get(cache_key)
            if task and task.status == ReportPhase.COMPLETED:
                # 检查是否过期
                if task.cache_expires_at and datetime.now() < task.cache_expires_at:
                    task.cached = True
                    return task
                else:
                    # 过期了，删除
                    del self._cache[cache_key]
            return None
    
    def set(self, cache_key: str, task: ReportTask):
        """设置缓存"""
        with self._lock:
            task.cache_expires_at = datetime.now() + timedelta(hours=self.max_age_hours)
            self._cache[cache_key] = task
    
    def invalidate(self, case_id: int):
        """使指定案件的所有缓存失效"""
        with self._lock:
            keys_to_remove = [k for k, v in self._cache.items() 
                            if v.case_id == case_id]
            for k in keys_to_remove:
                del self._cache[k]
    
    def clear_all(self):
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()


class StreamingReportGenerator:
    """
    流式报告生成器
    
    核心设计理念：
    1. 慢即是快：宁可分段输出，也要保证完整准确
    2. 用户体验：实时显示进度，让用户知道在做什么
    3. 容错性：部分失败不影响已生成的内容
    4. 可中断：用户可以随时停止，不丢失已生成内容
    """
    
    def __init__(self, llm_service):
        self.llm = llm_service
        self.cache = ReportCache()
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._active_tasks: Dict[str, ReportTask] = {}
        self._lock = threading.Lock()
    
    def generate_report(
        self,
        case_id: int,
        report_type: ReportType,
        case_info: Dict,
        force_regenerate: bool = False,
        on_progress: Optional[Callable[[float, str], None]] = None
    ) -> str:
        """
        生成报告 - 支持缓存和分段
        
        Args:
            case_id: 案件ID
            report_type: 报告类型
            case_info: 案件信息
            force_regenerate: 是否强制重新生成
            on_progress: 进度回调函数
            
        Returns:
            完整的报告内容
        """
        # 生成缓存键
        cache_key = self.cache.get_cache_key(
            case_id, 
            report_type.value,
            str(case_info.get('description', ''))
        )
        
        # 检查缓存
        if not force_regenerate:
            cached_task = self.cache.get(cache_key)
            if cached_task:
                if on_progress:
                    on_progress(1.0, "使用缓存的报告")
                return cached_task.full_content
        
        # 获取或创建任务
        with self._lock:
            if cache_key in self._active_tasks:
                task = self._active_tasks[cache_key]
                if task.status == ReportPhase.GENERATING:
                    # 等待生成完成
                    return self._wait_for_task(task, on_progress)
            else:
                task = ReportTask(
                    task_id=cache_key,
                    case_id=case_id,
                    report_type=report_type
                )
                self._active_tasks[cache_key] = task
        
        # 开始生成
        try:
            task.status = ReportPhase.GENERATING
            task.started_at = datetime.now()
            
            # 根据报告类型选择生成方法
            if report_type == ReportType.ANALYSIS:
                self._generate_analysis_report(task, case_info, on_progress)
            elif report_type == ReportType.STRATEGY:
                self._generate_strategy_report(task, case_info, on_progress)
            elif report_type == ReportType.FULL_ANALYSIS:
                self._generate_full_analysis_report(task, case_info, on_progress)
            elif report_type == ReportType.EVIDENCE_REPORT:
                self._generate_evidence_report(task, case_info, on_progress)
            elif report_type == ReportType.MILESTONE_REPORT:
                self._generate_milestone_report(task, case_info, on_progress)
            elif report_type == ReportType.SUMMARY_REPORT:
                self._generate_summary_report(task, case_info, on_progress)
            
            # 生成完成
            task.status = ReportPhase.COMPLETED
            task.completed_at = datetime.now()
            task.progress = 1.0
            
            # 缓存结果
            self.cache.set(cache_key, task)
            
            if on_progress:
                on_progress(1.0, "报告生成完成")
            
        except Exception as e:
            task.status = ReportPhase.FAILED
            task.error = str(e)
            if on_progress:
                on_progress(task.progress, f"生成失败: {e}")
        
        finally:
            with self._lock:
                if cache_key in self._active_tasks:
                    del self._active_tasks[cache_key]
        
        return task.full_content
    
    def generate_report_async(
        self,
        case_id: int,
        report_type: ReportType,
        case_info: Dict,
        on_progress: Optional[Callable[[float, str], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        异步生成报告 - 不阻塞调用
        
        适合长报告生成，立即返回任务ID，后续通过回调获取结果
        """
        cache_key = self.cache.get_cache_key(case_id, report_type.value)
        
        # 检查缓存
        cached_task = self.cache.get(cache_key)
        if cached_task:
            if on_progress:
                on_progress(1.0, "使用缓存")
            if on_complete:
                on_complete(cached_task.full_content)
            return cached_task.full_content
        
        # 异步提交任务
        future = self._executor.submit(
            self.generate_report,
            case_id, report_type, case_info, False, on_progress
        )
        
        # 注册完成回调
        if on_complete:
            def done_callback(f):
                try:
                    result = f.result()
                    on_complete(result)
                except Exception as e:
                    on_complete(f"生成失败: {e}")
            
            future.add_done_callback(done_callback)
        
        return "报告正在后台生成，请稍候..."
    
    def _wait_for_task(self, task: ReportTask, on_progress: Optional[Callable[[float, str], None]]) -> str:
        """等待任务完成"""
        import time
        while task.status == ReportPhase.GENERATING:
            if on_progress:
                on_progress(task.progress, f"生成中... {int(task.progress * 100)}%")
            time.sleep(1)
        
        if task.status == ReportPhase.COMPLETED:
            return task.full_content
        elif task.status == ReportPhase.FAILED:
            raise Exception(task.error or "生成失败")
        else:
            raise Exception("任务状态异常")
    
    def _generate_analysis_report(
        self, 
        task: ReportTask, 
        case_info: Dict, 
        on_progress: Optional[Callable[[float, str], None]]
    ):
        """生成案件分析报告 - 分7段 - 使用证据全文"""

        segments_config = [
            ("一、案件事实", "分析案件的基本事实情况，包括时间、地点、人物、事件经过"),
            ("二、法律关系", "分析案件涉及的法律关系，明确各方的权利义务"),
            ("三、争议焦点", "识别并分析案件的争议焦点，确定核心问题"),
            ("四、证据评估", "评估现有证据的证明力，分析证据链的完整性"),
            ("五、法律依据", "引用适用的法律条款，分析法律适用问题"),
            ("六、突破口", "分析可能的突破口和有利因素"),
            ("七、策略建议", "提出具体的诉讼策略和行动建议")
        ]

        total_segments = len(segments_config)

        for i, (title, description) in enumerate(segments_config):
            if task.status == ReportPhase.CANCELLED:
                break

            current_progress = (i / total_segments) * 0.8
            task.progress = current_progress
            if on_progress:
                on_progress(current_progress, f"正在生成：{title}")

            segment = ReportSegment(
                segment_id=i + 1,
                title=title
            )
            task.segments.append(segment)

            # 基础信息
            base_info = f"""【案件基本信息】
- 案件名称：{case_info.get('title', '未知')}
- 案件类型：{case_info.get('case_type', '未知')}
- 案由：{case_info.get('cause', '未知')}
- 原告：{case_info.get('plaintiff', '未知')}
- 被告：{case_info.get('defendant', '未知')}
- 诉讼金额：{case_info.get('claim_amount', '未知')}
- 案件描述：{case_info.get('description', '暂无')}
"""
            # 证据全文（如有）
            if case_info.get('evidence_full_text'):
                base_info += f"\n【证据全文内容】\n{case_info['evidence_full_text']}\n"
            # 对抗性分析结论
            if case_info.get('adversarial_analysis'):
                base_info += f"\n【对抗性分析结论】\n{case_info['adversarial_analysis']}\n"

            prompt = f"""基于以下案件信息，请详细分析「{title}」。

{base_info}

【分析要求】
{title}
分析要点：{description}

请生成300-500字的详细分析内容，要求：
1. 事实分析要引用证据原文，不能凭空捏造
2. 法律分析要有理有据，引用具体法条
3. 策略建议要具体可操作
4. 重点突出，不要泛泛而谈"""
            
            try:
                content = self.llm.chat([
                    {"role": "system", "content": "你是一位资深法律专家，分析精准、结构清晰、用词严谨。"},
                    {"role": "user", "content": prompt}
                ], model="qwen-plus")
                
                segment.content = content
                segment.status = ReportPhase.COMPLETED
                segment.generated_at = datetime.now()
                
                # 追加到完整内容
                task.full_content += f"\n\n{title}\n{content}"
                
            except Exception as e:
                segment.status = ReportPhase.FAILED
                segment.error = str(e)
                # 继续生成下一段，不中断整个报告
        
        # 添加报告结尾
        task.full_content += f"\n\n{'='*60}\n"
        task.full_content += f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        task.full_content += f"本报告由 AI 法律助手自动生成，仅供参考\n"
    
    def _generate_strategy_report(
        self, 
        task: ReportTask, 
        case_info: Dict, 
        on_progress: Optional[Callable[[float, str], None]]
    ):
        """生成策略建议报告 - 分5段 - 使用证据全文"""

        segments_config = [
            ("一、诉讼方向", "确定诉讼策略方向，选择最优路径"),
            ("二、证据策略", "制定证据准备、举证、质证策略"),
            ("三、关键风险", "识别并评估关键风险点"),
            ("四、行动建议", "提出具体的行动建议和时间表"),
            ("五、备选方案", "准备应对不利情景的备选方案")
        ]

        total_segments = len(segments_config)

        # 证据摘要（如果有）
        evidence_section = ""
        if case_info.get('evidence_full_text'):
            evidence_section = f"\n【证据全文参考】\n{case_info['evidence_full_text']}\n"
        if case_info.get('evidence_summary'):
            evidence_section += f"\n【证据摘要】{case_info['evidence_summary']}\n"
        # 对抗性分析
        if case_info.get('adversarial_analysis'):
            evidence_section += f"\n【对抗性分析结论】\n{case_info['adversarial_analysis']}\n"

        for i, (title, description) in enumerate(segments_config):
            if task.status == ReportPhase.CANCELLED:
                break

            current_progress = (i / total_segments) * 0.8
            task.progress = current_progress
            if on_progress:
                on_progress(current_progress, f"正在生成：{title}")

            segment = ReportSegment(segment_id=i + 1, title=title)
            task.segments.append(segment)

            prompt = f"""基于以下案件信息，请制定详细的诉讼策略。

【案件信息】
- 案件名称：{case_info.get('title', '未知')}
- 案由：{case_info.get('cause', '未知')}
- 原告：{case_info.get('plaintiff', '未知')}
- 被告：{case_info.get('defendant', '未知')}
- 诉讼金额：{case_info.get('claim_amount', '未知')}
{evidence_section}

【策略要求】
{title}
{description}

请生成300-400字的策略内容，要求：
1. 策略要具体、可执行
2. 必须基于证据内容制定，不能凭空设计
3. 突出重点，给出优先级
4. 包含时间节点和行动步骤"""
            
            try:
                content = self.llm.chat([
                    {"role": "system", "content": "你是一位顶级诉讼律师，策略精准、可操作、有远见。"},
                    {"role": "user", "content": prompt}
                ], model="qwen-plus")
                
                segment.content = content
                segment.status = ReportPhase.COMPLETED
                segment.generated_at = datetime.now()
                task.full_content += f"\n\n{title}\n{content}"
                
            except Exception as e:
                segment.status = ReportPhase.FAILED
                segment.error = str(e)
    
    def _generate_full_analysis_report(
        self, 
        task: ReportTask, 
        case_info: Dict, 
        on_progress: Optional[Callable[[float, str], None]]
    ):
        """生成完整对抗性分析报告 - 分8段 - 使用证据全文和分析结论"""

        segments_config = [
            ("第一部分：我方态势评估", "SWOT分析：优势、劣势、机会、威胁。详细列出案件的事实优势、法律优势和证据优势"),
            ("第二部分：对手画像", "分析对手的可能策略、诉讼风格、证据预测和行为模式"),
            ("第三部分：证据攻防矩阵", "分析双方证据的攻守价值，识别克制关系和关键证据节点"),
            ("第四部分：案件走向预测", "预测不同情景下的可能结果，包括最优、中性、最差三种路径"),
            ("第五部分：应对策略", "制定分层应对方案，包括防御层、均衡层、进攻层"),
            ("第六部分：执行清单", "具体行动步骤和时间表，按优先级排序的任务清单"),
            ("第七部分：风险预警", "识别和监控关键风险，包括红色预警和黄色预警"),
            ("第八部分：核心结论", "总结最关键的判断、建议和最需要警惕的事项")
        ]

        total_segments = len(segments_config)

        # 构建完整基础信息
        base_info = f"""【案件基本信息】
案件名称：{case_info.get('title', '未知')}
案由：{case_info.get('cause', '未知')}
原告：{case_info.get('plaintiff', '未知')}
被告：{case_info.get('defendant', '未知')}
诉讼金额：{case_info.get('claim_amount', '未知')}
描述：{str(case_info.get('description', ''))}
"""
        # 证据全文
        if case_info.get('evidence_full_text'):
            base_info += f"\n【证据全文内容】\n{case_info['evidence_full_text']}\n"
        # 对抗性分析结论
        if case_info.get('adversarial_analysis'):
            base_info += f"\n【已有的对抗性分析结论】\n{case_info['adversarial_analysis']}\n"
        # SWOT分析
        if case_info.get('swot_analysis'):
            base_info += f"\n【SWOT分析参考】\n{case_info['swot_analysis']}\n"
        # 关键风险
        if case_info.get('key_risks'):
            base_info += f"\n【关键风险】\n{case_info['key_risks']}\n"

        # 添加对手信息
        if case_info.get('opponent_name'):
            base_info += f"\n【对手信息】\n名称：{case_info.get('opponent_name')}\n"
        if case_info.get('opponent_type'):
            base_info += f"类型：{case_info.get('opponent_type')}\n"
        if case_info.get('opponent_evidence'):
            base_info += f"对方证据：{case_info.get('opponent_evidence')}\n"

        for i, (title, description) in enumerate(segments_config):
            if task.status == ReportPhase.CANCELLED:
                break
            
            current_progress = (i / total_segments) * 0.8
            task.progress = current_progress
            if on_progress:
                on_progress(current_progress, f"正在生成：{title}")
            
            segment = ReportSegment(segment_id=i + 1, title=title)
            task.segments.append(segment)
            
            prompt = f"""基于以下案件信息，生成{title}。

{base_info}

【分析重点】
{description}

请生成400-600字的详细分析，要求：
1. 深入分析，不泛泛而谈
2. 具体可操作，不是空话套话
3. 量化分析，用数据说话
4. 预见性分析，提前布局
5. 突出重点，给出具体建议"""

            try:
                content = self.llm.chat([
                    {"role": "system", "content": "你是一位顶级诉讼策略专家，擅长对抗性思维和情景推演。分析要专业、深入、有见地。"},
                    {"role": "user", "content": prompt}
                ], model="qwen-plus")
                
                segment.content = content
                segment.status = ReportPhase.COMPLETED
                segment.generated_at = datetime.now()
                task.full_content += f"\n\n{'='*50}\n{title}\n{'='*50}\n{content}"
                
            except Exception as e:
                segment.status = ReportPhase.FAILED
                segment.error = str(e)
                # 即使单段失败，也尝试继续生成其他段
        
        # 添加报告结尾
        if task.full_content:
            task.full_content += f"\n\n{'='*60}\n"
            task.full_content += f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            task.full_content += f"本报告由 AI 法律助手自动生成，仅供参考\n"
    
    def _generate_evidence_report(
        self, 
        task: ReportTask, 
        case_info: Dict, 
        on_progress: Optional[Callable[[float, str], None]]
    ):
        """生成证据分析报告 - 分5段"""
        
        segments_config = [
            ("一、现有证据评估", "分析已有证据的类型、证明力和完整性"),
            ("二、证据缺口分析", "识别缺失的关键证据及其影响"),
            ("三、证据获取方案", "提供获取缺失证据的具体方法"),
            ("四、证据链构建", "设计完整的证据链，证明案件事实"),
            ("五、质证策略", "准备对对方证据的质证意见")
        ]
        
        total_segments = len(segments_config)
        
        for i, (title, description) in enumerate(segments_config):
            if task.status == ReportPhase.CANCELLED:
                break
            
            current_progress = (i / total_segments) * 0.8
            task.progress = current_progress
            if on_progress:
                on_progress(current_progress, f"正在生成：{title}")
            
            segment = ReportSegment(segment_id=i + 1, title=title)
            task.segments.append(segment)
            
            prompt = f"""基于以下案件信息，生成证据分析报告。

【案件信息】
- 案由：{case_info.get('cause', '未知')}
- 诉讼金额：{case_info.get('claim_amount', '未知')}
- 描述：{case_info.get('description', '')}

【分析要求】
{title}
{description}

请生成详细的证据分析内容。"""
            
            try:
                content = self.llm.chat([
                    {"role": "system", "content": "你是一位专业的诉讼证据顾问。"},
                    {"role": "user", "content": prompt}
                ], model="qwen-plus")
                
                segment.content = content
                segment.status = ReportPhase.COMPLETED
                segment.generated_at = datetime.now()
                task.full_content += f"\n\n{title}\n{content}"
                
            except Exception as e:
                segment.status = ReportPhase.FAILED
                segment.error = str(e)
    
    def _generate_milestone_report(
        self, 
        task: ReportTask, 
        case_info: Dict, 
        on_progress: Optional[Callable[[float, str], None]]
    ):
        """生成里程碑报告"""
        
        task.progress = 0.5
        if on_progress:
            on_progress(0.5, "生成里程碑计划")
        
        prompt = f"""基于以下案件信息，生成案件里程碑计划。

【案件信息】
- 案件名称：{case_info.get('title', '未知')}
- 案件类型：{case_info.get('case_type', '民事')}
- 案由：{case_info.get('cause', '未知')}
- 当前状态：{case_info.get('status', '待处理')}

请生成以下格式的里程碑计划：

## 案件时间线

### 第一阶段：准备期（预计X天）
- [ ] 任务1
- [ ] 任务2

### 第二阶段：立案期（预计X天）
- [ ] 任务1

...（根据案件类型调整）

请生成具体、可执行的时间计划。"""
        
        try:
            content = self.llm.chat([
                {"role": "system", "content": "你是一位专业的诉讼项目总监。"},
                {"role": "user", "content": prompt}
            ], model="qwen-plus")
            
            task.full_content = content
            task.progress = 1.0
            
        except Exception as e:
            task.error = str(e)
    
    def _generate_summary_report(
        self, 
        task: ReportTask, 
        case_info: Dict, 
        on_progress: Optional[Callable[[float, str], None]]
    ):
        """生成案件总结报告"""
        
        task.progress = 0.5
        if on_progress:
            on_progress(0.5, "生成案件总结")
        
        prompt = f"""请为以下案件生成一份简洁的总结报告。

【案件信息】
案件名称：{case_info.get('title', '未知')}
案件类型：{case_info.get('case_type', '未知')}
案由：{case_info.get('cause', '未知')}
原告：{case_info.get('plaintiff', '未知')}
被告：{case_info.get('defendant', '未知')}
诉讼金额：{case_info.get('claim_amount', '未知')}
状态：{case_info.get('status', '未知')}

总结要求：
1. 案件概要（100字）
2. 核心争议（50字）
3. 当前进展（50字）
4. 下一步计划（100字）

请用简洁明了的格式输出。"""
        
        try:
            content = self.llm.chat([
                {"role": "system", "content": "你是一位专业的法律顾问。"},
                {"role": "user", "content": prompt}
            ], model="qwen-plus")
            
            task.full_content = content
            task.progress = 1.0
            
        except Exception as e:
            task.error = str(e)
    
    def cancel_task(self, case_id: int, report_type: ReportType):
        """取消正在生成的任务"""
        cache_key = self.cache.get_cache_key(case_id, report_type.value)
        with self._lock:
            if cache_key in self._active_tasks:
                self._active_tasks[cache_key].status = ReportPhase.CANCELLED
    
    def invalidate_cache(self, case_id: int):
        """使指定案件的缓存失效"""
        self.cache.invalidate(case_id)
    
    def get_task_status(self, case_id: int, report_type: ReportType) -> Optional[Dict]:
        """获取任务状态"""
        cache_key = self.cache.get_cache_key(case_id, report_type.value)
        with self._lock:
            task = self._active_tasks.get(cache_key)
            if task:
                return {
                    "status": task.status.value,
                    "progress": task.progress,
                    "segments_completed": len([s for s in task.segments if s.status == ReportPhase.COMPLETED]),
                    "total_segments": len(task.segments)
                }
        return None


# 全局实例
streaming_report_generator = None

def get_streaming_report_generator(llm_service) -> StreamingReportGenerator:
    """获取流式报告生成器实例"""
    global streaming_report_generator
    if streaming_report_generator is None:
        streaming_report_generator = StreamingReportGenerator(llm_service)
    return streaming_report_generator
