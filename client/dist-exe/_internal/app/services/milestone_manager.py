"""
增强版里程碑生成服务 - 智能去重与增量更新
==============================================
核心特性：
1. 智能去重 - 相同里程碑不会重复添加
2. 增量更新 - 只更新新增或变化的内容
3. 案件感知 - 根据案件类型和阶段定制里程碑
4. 状态追踪 - 追踪里程碑完成状态
5. 自动生成 - 根据案件动态生成里程碑

设计理念：
- 里程碑是行动计划，不是静态模板
- 重复是效率的敌人
- 增量更新比全量更新更高效
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class MilestoneStatus(Enum):
    """里程碑状态"""
    PENDING = "pending"          # 待执行
    IN_PROGRESS = "in_progress" # 执行中
    COMPLETED = "completed"      # 已完成
    SKIPPED = "skipped"         # 已跳过
    OVERDUE = "overdue"         # 已逾期


class MilestonePhase(Enum):
    """里程碑阶段"""
    PRE_LITIGATION = "pre_litigation"   # 诉前准备
    FILING = "filing"                   # 立案阶段
    DEFENSE = "defense"                 # 答辩阶段
    EVIDENCE = "evidence"               # 举证阶段
    TRIAL = "trial"                     # 开庭阶段
    JUDGMENT = "judgment"                # 判决阶段
    APPEAL = "appeal"                   # 上诉阶段
    EXECUTION = "execution"             # 执行阶段


@dataclass
class Milestone:
    """里程碑"""
    milestone_id: str                 # 唯一ID
    phase: str                       # 阶段
    name: str                       # 名称
    description: str                  # 描述
    
    # 时间信息
    expected_date: Optional[datetime] = None
    due_days: int = 0                 # 距开始的天数
    duration_days: int = 1            # 持续天数
    
    # 状态
    status: MilestoneStatus = MilestoneStatus.PENDING
    completed_at: Optional[datetime] = None
    
    # 属性
    required: bool = True            # 是否必须完成
    priority: int = 1                 # 优先级 1-5
    is_milestone: bool = True        # 是否是关键节点
    
    # AI建议
    ai_tip: str = ""                 # AI律师提示
    checklist: List[str] = field(default_factory=list)  # 执行清单
    
    # 去重
    content_hash: str = ""            # 内容哈希
    keyword_hash: str = ""            # 关键词哈希
    
    # 元数据
    source: str = "system"           # 来源：system/custom
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.content_hash:
            self.content_hash = self._generate_hash()
        if not self.keyword_hash:
            self.keyword_hash = self._generate_keyword_hash()
    
    def _generate_hash(self) -> str:
        """生成内容哈希用于去重"""
        content = f"{self.phase}|{self.name}|{self.description[:50]}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _generate_keyword_hash(self) -> str:
        """生成关键词哈希"""
        keywords = "|".join(sorted([
            self.phase,
            self.name.replace(" ", ""),
            self.description[:20]
        ]))
        return hashlib.md5(keywords.encode()).hexdigest()[:12]
    
    def to_dict(self) -> dict:
        return {
            "milestone_id": self.milestone_id,
            "phase": self.phase,
            "phase_name": self.get_phase_name(),
            "name": self.name,
            "description": self.description,
            "expected_date": self.expected_date.isoformat() if self.expected_date else None,
            "due_days": self.due_days,
            "duration_days": self.duration_days,
            "status": self.status.value,
            "required": self.required,
            "priority": self.priority,
            "ai_tip": self.ai_tip,
            "checklist": self.checklist,
            "content_hash": self.content_hash,
            "is_overdue": self.is_overdue()
        }
    
    def get_phase_name(self) -> str:
        """获取阶段中文名"""
        names = {
            "pre_litigation": "诉前准备",
            "filing": "立案阶段",
            "defense": "答辩阶段",
            "evidence": "举证阶段",
            "trial": "开庭阶段",
            "judgment": "判决阶段",
            "appeal": "上诉阶段",
            "execution": "执行阶段"
        }
        return names.get(self.phase, self.phase)
    
    def is_overdue(self) -> bool:
        """是否已逾期"""
        if not self.expected_date:
            return False
        if self.status == MilestoneStatus.COMPLETED:
            return False
        return datetime.now() > self.expected_date


@dataclass
class MilestoneSet:
    """里程碑集合"""
    case_id: int
    
    # 里程碑列表
    milestones: List[Milestone] = field(default_factory=list)
    
    # 哈希索引（用于去重）
    hash_index: Dict[str, str] = field(default_factory=dict)  # hash -> milestone_id
    
    # 状态统计
    total_count: int = 0
    completed_count: int = 0
    overdue_count: int = 0
    
    # 当前阶段
    current_phase: str = "pre_litigation"
    
    # 元数据
    created_at: str = ""
    updated_at: str = ""
    version: int = 1
    
    def add(self, milestone: Milestone) -> Dict:
        """添加里程碑（带去重）"""
        # 检查是否重复
        if milestone.content_hash in self.hash_index:
            existing_id = self.hash_index[milestone.content_hash]
            return {
                "status": "duplicate",
                "milestone_id": existing_id,
                "message": f"里程碑 '{milestone.name}' 已存在，跳过添加"
            }
        
        # 检查关键词哈希重复（更宽松的去重）
        if milestone.keyword_hash in [m.keyword_hash for m in self.milestones]:
            return {
                "status": "similar",
                "message": f"发现相似里程碑 '{milestone.name}'，请确认是否添加"
            }
        
        # 添加到列表
        milestone.milestone_id = f"m_{len(self.milestones) + 1}"
        self.milestones.append(milestone)
        
        # 更新索引
        self.hash_index[milestone.content_hash] = milestone.milestone_id
        
        # 更新统计
        self._update_stats()
        
        return {
            "status": "added",
            "milestone_id": milestone.milestone_id,
            "message": f"里程碑 '{milestone.name}' 已添加"
        }
    
    def add_batch(self, milestones: List[Milestone]) -> Dict:
        """批量添加里程碑"""
        results = {
            "added": [],
            "duplicates": [],
            "similar": [],
            "total": len(milestones)
        }
        
        for milestone in milestones:
            result = self.add(milestone)
            if result["status"] == "added":
                results["added"].append(result["milestone_id"])
            elif result["status"] == "duplicate":
                results["duplicates"].append(result.get("milestone_id", "unknown"))
            else:
                results["similar"].append(result.get("message", ""))
        
        return results
    
    def remove(self, milestone_id: str) -> bool:
        """移除里程碑"""
        for i, m in enumerate(self.milestones):
            if m.milestone_id == milestone_id:
                # 清理索引
                if m.content_hash in self.hash_index:
                    del self.hash_index[m.content_hash]
                
                self.milestones.pop(i)
                self._update_stats()
                return True
        return False
    
    def update_status(self, milestone_id: str, status: MilestoneStatus) -> bool:
        """更新里程碑状态"""
        for m in self.milestones:
            if m.milestone_id == milestone_id:
                m.status = status
                if status == MilestoneStatus.COMPLETED:
                    m.completed_at = datetime.now()
                m.updated_at = datetime.now()
                self._update_stats()
                return True
        return False
    
    def _update_stats(self):
        """更新统计"""
        self.total_count = len(self.milestones)
        self.completed_count = sum(
            1 for m in self.milestones 
            if m.status == MilestoneStatus.COMPLETED
        )
        self.overdue_count = sum(
            1 for m in self.milestones 
            if m.is_overdue()
        )
        self.updated_at = datetime.now().isoformat()
        self.version += 1
    
    def get_by_phase(self, phase: str) -> List[Milestone]:
        """按阶段获取里程碑"""
        return [m for m in self.milestones if m.phase == phase]
    
    def get_pending(self) -> List[Milestone]:
        """获取待完成的里程碑"""
        return [m for m in self.milestones 
                if m.status != MilestoneStatus.COMPLETED]
    
    def get_overdue(self) -> List[Milestone]:
        """获取逾期里程碑"""
        return [m for m in self.milestones if m.is_overdue()]
    
    def calculate_dates(self, start_date: datetime):
        """计算所有里程碑的预计日期"""
        current_date = start_date
        
        for milestone in self.milestones:
            # 根据距开始的天数计算
            if milestone.due_days > 0:
                milestone.expected_date = start_date + timedelta(days=milestone.due_days)
            else:
                milestone.expected_date = current_date + timedelta(days=1)
            
            # 更新当前日期
            current_date = milestone.expected_date


class MilestoneGenerator:
    """
    里程碑生成器
    
    核心功能：
    1. 根据案件类型生成标准化里程碑
    2. 根据案件阶段动态调整
    3. 智能去重，避免重复
    4. 增量更新，只添加新的
    """
    
    def __init__(self, llm_service=None):
        self.llm = llm_service
        
        # 里程碑模板
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """加载里程碑模板"""
        return {
            "民事一审": {
                "pre_litigation": [
                    {
                        "name": "初步法律咨询",
                        "description": "了解案情，评估诉讼可行性",
                        "duration_days": 3,
                        "priority": 1,
                        "required": True,
                        "ai_tip": "首次咨询需携带全部证据材料",
                        "checklist": ["整理证据材料", "梳理案件经过", "明确诉讼目标"]
                    },
                    {
                        "name": "证据收集整理",
                        "description": "整理现有证据，查找缺失证据",
                        "duration_days": 7,
                        "priority": 1,
                        "required": True,
                        "ai_tip": "按证据目录分类整理，注明来源",
                        "checklist": ["分类整理证据", "标注证明目的", "查找缺失证据"]
                    },
                    {
                        "name": "确定诉讼请求",
                        "description": "明确诉讼请求和金额",
                        "duration_days": 3,
                        "priority": 1,
                        "required": True,
                        "ai_tip": "金额应有计算依据",
                        "checklist": ["确定请求项目", "计算具体金额", "准备计算依据"]
                    }
                ],
                "filing": [
                    {
                        "name": "准备立案材料",
                        "description": "起草起诉状，整理证据目录",
                        "duration_days": 5,
                        "priority": 1,
                        "required": True,
                        "ai_tip": "起诉状份数=被告数+1",
                        "checklist": ["起草起诉状", "整理证据目录", "准备身份证明"]
                    },
                    {
                        "name": "提交立案",
                        "description": "向法院提交全部材料",
                        "duration_days": 1,
                        "priority": 1,
                        "required": True,
                        "ai_tip": "网上立案或现场立案",
                        "checklist": ["在线提交材料", "保存收件凭证"]
                    },
                    {
                        "name": "缴纳诉讼费",
                        "description": "按规定缴纳案件受理费",
                        "duration_days": 7,
                        "priority": 1,
                        "required": True,
                        "ai_tip": "逾期按撤诉处理",
                        "checklist": ["计算诉讼费", "按时缴纳"]
                    }
                ],
                "defense": [
                    {
                        "name": "起草答辩状",
                        "description": "针对原告起诉进行答辩",
                        "duration_days": 15,
                        "priority": 2,
                        "required": False,
                        "ai_tip": "答辩期15日内",
                        "checklist": ["分析起诉状", "收集答辩材料", "起草答辩状"]
                    }
                ],
                "evidence": [
                    {
                        "name": "证据交换",
                        "description": "与对方交换证据",
                        "duration_days": 30,
                        "priority": 1,
                        "required": True,
                        "ai_tip": "逾期证据可能不被采纳",
                        "checklist": ["整理己方证据", "准备质证意见", "申请法院调取"]
                    },
                    {
                        "name": "质证意见准备",
                        "description": "准备对对方证据的质证意见",
                        "duration_days": 7,
                        "priority": 2,
                        "required": True,
                        "ai_tip": "围绕三性展开",
                        "checklist": ["分析对方证据", "准备质证要点", "形成书面意见"]
                    }
                ],
                "trial": [
                    {
                        "name": "庭审准备",
                        "description": "准备庭审提纲，模拟法庭",
                        "duration_days": 7,
                        "priority": 1,
                        "required": True,
                        "ai_tip": "提前到达法院",
                        "checklist": ["准备证据原件", "准备代理词", "准备证人出庭"]
                    },
                    {
                        "name": "第一次开庭",
                        "description": "参加第一次庭审",
                        "duration_days": 1,
                        "priority": 1,
                        "required": True,
                        "ai_tip": "抓住重点，如实回答",
                        "checklist": ["携带证件", "携带证据原件", "按提纲发言"]
                    }
                ],
                "judgment": [
                    {
                        "name": "等待判决",
                        "description": "庭审结束后等待判决",
                        "duration_days": 30,
                        "priority": 1,
                        "required": True,
                        "ai_tip": "普通程序6个月内审结",
                        "checklist": ["关注审理进度", "准备上诉材料"]
                    },
                    {
                        "name": "收到判决",
                        "description": "领取判决书",
                        "duration_days": 5,
                        "priority": 1,
                        "required": True,
                        "ai_tip": "立即计算上诉期限",
                        "checklist": ["核对判决内容", "评估是否上诉"]
                    },
                    {
                        "name": "上诉决策",
                        "description": "决定是否上诉",
                        "duration_days": 15,
                        "priority": 1,
                        "required": True,
                        "ai_tip": "不服判决15日内上诉",
                        "checklist": ["分析上诉理由", "准备上诉状", "缴纳上诉费"]
                    }
                ],
                "execution": [
                    {
                        "name": "判决生效",
                        "description": "上诉期满或二审判决",
                        "duration_days": 15,
                        "priority": 1,
                        "required": True,
                        "ai_tip": "一审判决15日上诉期满生效",
                        "checklist": ["确认判决生效", "准备执行申请"]
                    },
                    {
                        "name": "申请执行",
                        "description": "向法院申请强制执行",
                        "duration_days": 2,
                        "duration_type": "年",
                        "priority": 1,
                        "required": True,
                        "ai_tip": "执行申请期限2年！",
                        "checklist": ["准备执行申请", "提供财产线索", "申请财产保全"]
                    }
                ]
            },
            "劳动纠纷": {
                "pre_litigation": [
                    {"name": "收集劳动关系证据", "duration_days": 7, "priority": 1},
                    {"name": "劳动仲裁申请", "duration_days": 1, "priority": 1}
                ]
            }
        }
    
    def generate_milestones(
        self,
        case_id: int,
        case_type: str,
        case_start_date: datetime = None,
        existing_milestones: List[Milestone] = None
    ) -> MilestoneSet:
        """
        生成里程碑
        
        Args:
            case_id: 案件ID
            case_type: 案件类型
            case_start_date: 案件开始日期
            existing_milestones: 已有的里程碑列表（用于去重）
        """
        start_date = case_start_date or datetime.now()
        
        # 创建里程碑集
        milestone_set = MilestoneSet(
            case_id=case_id,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # 添加已有里程碑（用于去重）
        if existing_milestones:
            for m in existing_milestones:
                milestone_set.hash_index[m.content_hash] = m.milestone_id
                milestone_set.milestones.append(m)
        
        # 获取模板
        template = self.templates.get(case_type, self.templates.get("民事一审"))
        
        # 按阶段生成里程碑
        current_date = start_date
        milestone_num = len(milestone_set.milestones)
        
        for phase, phase_milestones in template.items():
            for m_template in phase_milestones:
                # 计算日期
                if milestone_num > 0:
                    current_date = start_date + timedelta(days=sum(
                        m.duration_days for m in milestone_set.milestones[-3:]
                    ))
                
                # 创建里程碑
                milestone = Milestone(
                    milestone_id=f"m_{milestone_num + 1}",
                    phase=phase,
                    name=m_template["name"],
                    description=m_template.get("description", ""),
                    due_days=(current_date - start_date).days,
                    duration_days=m_template.get("duration_days", 1),
                    priority=m_template.get("priority", 3),
                    required=m_template.get("required", False),
                    ai_tip=m_template.get("ai_tip", ""),
                    checklist=m_template.get("checklist", []),
                    expected_date=current_date,
                    source="system"
                )
                
                # 添加（会自动去重）
                milestone_set.add(milestone)
                milestone_num += 1
        
        # 计算所有日期
        milestone_set.calculate_dates(start_date)
        milestone_set._update_stats()
        
        return milestone_set
    
    def generate_incremental(
        self,
        case_id: int,
        case_type: str,
        current_phase: str,
        existing_milestones: List[Milestone]
    ) -> List[Milestone]:
        """
        增量生成里程碑
        
        只生成当前阶段及后续阶段的里程碑，避免重复
        """
        start_date = datetime.now()
        milestones = []
        
        # 找出已有的阶段
        existing_phases = set(m.phase for m in existing_milestones)
        
        # 获取模板
        template = self.templates.get(case_type, self.templates.get("民事一审"))
        
        # 只处理当前阶段及后续
        phase_order = ["pre_litigation", "filing", "defense", "evidence", 
                      "trial", "judgment", "appeal", "execution"]
        
        current_idx = phase_order.index(current_phase) if current_phase in phase_order else 0
        
        for phase in phase_order[current_idx:]:
            if phase not in template:
                continue
            
            # 检查是否已有该阶段里程碑
            if phase in existing_phases:
                # 已有该阶段，检查是否有新增
                phase_milestones = [m for m in existing_milestones if m.phase == phase]
                continue
            
            # 生成该阶段里程碑
            for m_template in template[phase]:
                milestone = Milestone(
                    milestone_id=f"new_{len(milestones) + 1}",
                    phase=phase,
                    name=m_template["name"],
                    description=m_template.get("description", ""),
                    duration_days=m_template.get("duration_days", 1),
                    priority=m_template.get("priority", 3),
                    required=m_template.get("required", False),
                    ai_tip=m_template.get("ai_tip", ""),
                    checklist=m_template.get("checklist", []),
                    source="system"
                )
                milestones.append(milestone)
        
        return milestones
    
    def sync_milestones(
        self,
        case_id: int,
        case_type: str,
        existing_milestones: List[Milestone],
        new_milestones: List[Milestone]
    ) -> Dict:
        """
        同步里程碑
        
        比对现有和新的里程碑，添加缺失的，标记重复的
        """
        # 创建现有哈希集合
        existing_hashes = set(m.content_hash for m in existing_milestones)
        
        results = {
            "added": [],
            "skipped": [],
            "total_existing": len(existing_milestones),
            "total_new": len(new_milestones)
        }
        
        for milestone in new_milestones:
            if milestone.content_hash in existing_hashes:
                results["skipped"].append({
                    "name": milestone.name,
                    "reason": "已存在",
                    "hash": milestone.content_hash
                })
            else:
                results["added"].append(milestone)
        
        return results
    
    def update_milestone_from_case(
        self,
        milestone: Milestone,
        case_info: Dict
    ) -> Milestone:
        """
        根据案件信息更新里程碑
        
        比如根据诉讼金额调整提示
        """
        # 根据案件类型定制AI提示
        case_type = case_info.get('case_type', '')
        claim_amount = case_info.get('claim_amount', '')
        
        if case_type == "劳动纠纷" and "工资" in milestone.name:
            milestone.ai_tip += "注意工资计算标准"
        
        if claim_amount and "诉讼费" in milestone.name:
            # 添加诉讼费计算提示
            try:
                amount = float(''.join(filter(str.isdigit, claim_amount)))
                fee = min(amount * 0.01, 50000) if amount > 10000 else 10
                milestone.ai_tip += f"预估诉讼费约{fee}元"
            except:
                pass
        
        return milestone
    
    def generate_urgency_report(
        self, 
        milestones: List[Milestone]
    ) -> Dict:
        """生成紧迫性报告"""
        today = datetime.now()
        
        report = {
            "generated_at": today.isoformat(),
            "summary": {
                "total": len(milestones),
                "pending": 0,
                "completed": 0,
                "overdue": 0,
                "upcoming_7d": 0
            },
            "critical": [],   # 紧急重要
            "important": [],  # 重要
            "upcoming": [],   # 即将到来
            "completed": [],  # 已完成
            "overdue": []    # 已逾期
        }
        
        for m in milestones:
            if m.status == MilestoneStatus.COMPLETED:
                report["summary"]["completed"] += 1
                report["completed"].append(m.to_dict())
                continue
            
            report["summary"]["pending"] += 1
            
            if not m.expected_date:
                continue
            
            days_until = (m.expected_date - today).days
            
            if days_until < 0:
                report["summary"]["overdue"] += 1
                report["overdue"].append({
                    **m.to_dict(),
                    "days_overdue": abs(days_until)
                })
            elif days_until <= 3:
                report["summary"]["upcoming_7d"] += 1
                if m.priority <= 2:
                    report["critical"].append({
                        **m.to_dict(),
                        "days_remaining": days_until
                    })
            elif days_until <= 7:
                report["summary"]["upcoming_7d"] += 1
                if m.priority <= 2:
                    report["important"].append({
                        **m.to_dict(),
                        "days_remaining": days_until
                    })
        
        return report


# 全局实例
milestone_generator = MilestoneGenerator()

def get_milestone_generator(llm_service=None) -> MilestoneGenerator:
    """获取里程碑生成器实例"""
    global milestone_generator
    if milestone_generator is None:
        milestone_generator = MilestoneGenerator(llm_service)
    elif llm_service and milestone_generator.llm is None:
        milestone_generator.llm = llm_service
    return milestone_generator
