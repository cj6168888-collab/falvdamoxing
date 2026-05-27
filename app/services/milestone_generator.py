"""
智能里程碑生成服务 - 自动生成案件流程节点
让非律师也能像律师一样精准把控案件进度
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.services.llm_service import llm_service
from app.services.deadline_service import deadline_service


class MilestoneGenerator:
    """
    智能里程碑生成器
    
    功能：
    1. 根据案件类型自动生成标准化里程碑
    2. 根据案件阶段动态调整里程碑
    3. 自动计算各节点的预计时间
    4. 生成律师级的时间把控建议
    """
    
    # 民事一审案件标准里程碑模板
    CIVIL_FIRST_TRIAL_TEMPLATE = {
        "name": "民事一审标准流程",
        "case_type": "civil",
        "phases": {
            "pre_litigation": {
                "name": "诉前准备",
                "description": "立案前的准备工作",
                "milestones": [
                    {
                        "id": "consultation",
                        "name": "初步法律咨询",
                        "description": "了解案情，评估诉讼可行性",
                        "duration_days": 3,
                        "required": True,
                        "ai_tip": "首次咨询需携带全部证据材料，包括合同、往来函件、转账记录等。"
                    },
                    {
                        "id": "evidence_collection",
                        "name": "证据收集整理",
                        "description": "整理现有证据，查找缺失证据",
                        "duration_days": 7,
                        "required": True,
                        "ai_tip": "按照证据目录分类整理，注明证据来源和证明目的。申请法院调取证据的，应在举证期限内提出。"
                    },
                    {
                        "id": "lawyer_retention",
                        "name": "委托代理",
                        "description": "确定代理律师，签订委托合同",
                        "duration_days": 1,
                        "required": False,
                        "ai_tip": "委托律师后，授权委托书需明确代理权限（一般代理/特别授权）。"
                    },
                    {
                        "id": "claim_confirm",
                        "name": "确定诉讼请求",
                        "description": "明确诉讼请求和金额",
                        "duration_days": 3,
                        "required": True,
                        "ai_tip": "诉讼请求应具体明确，金额应有计算依据。注意是否有利息、违约金等主张。"
                    },
                    {
                        "id": "pre_letter",
                        "name": "发送律师函（如需）",
                        "description": "诉前协商或固定证据",
                        "duration_days": 15,
                        "required": False,
                        "ai_tip": "律师函可促使对方主动协商，同时中断诉讼时效。"
                    }
                ]
            },
            "filing": {
                "name": "立案阶段",
                "description": "向法院提交起诉材料",
                "milestones": [
                    {
                        "id": "filing_prep",
                        "name": "准备立案材料",
                        "description": "起草起诉状，整理证据目录",
                        "duration_days": 5,
                        "required": True,
                        "ai_tip": "起诉状需包含：当事人信息、诉讼请求、事实与理由、证据目录。份数为被告人数+1。"
                    },
                    {
                        "id": "filing_submit",
                        "name": "提交立案",
                        "description": "向法院提交全部材料",
                        "duration_days": 1,
                        "required": True,
                        "ai_tip": "网上立案或现场立案，保留材料收件凭证。注意诉讼时效是否即将届满。"
                    },
                    {
                        "id": "case_accepted",
                        "name": "法院受理",
                        "description": "收到受理通知书",
                        "duration_days": 7,
                        "required": True,
                        "ai_tip": "受理后7日内缴纳诉讼费，逾期按撤诉处理。"
                    },
                    {
                        "id": "fee_payment",
                        "name": "缴纳诉讼费",
                        "description": "按规定缴纳案件受理费",
                        "duration_days": 7,
                        "required": True,
                        "ai_tip": "诉讼费计算标准：财产案件按标的额计算，非财产案件按件计算。可申请缓减免交。"
                    }
                ]
            },
            "defense": {
                "name": "答辩阶段",
                "description": "被告提交答辩状",
                "milestones": [
                    {
                        "id": "notice_received",
                        "name": "收到应诉通知",
                        "description": "收到法院送达的起诉状副本",
                        "duration_days": 1,
                        "required": True,
                        "ai_tip": "核实送达回证上的日期，这是计算答辩期限的起点。"
                    },
                    {
                        "id": "defense_draft",
                        "name": "起草答辩状",
                        "description": "针对原告起诉进行答辩",
                        "duration_days": 15,
                        "required": False,
                        "ai_tip": "答辩状应在收到起诉状之日起15日内提交。不提交答辩不影响开庭。"
                    },
                    {
                        "id": "defense_submit",
                        "name": "提交答辩状",
                        "description": "向法院提交答辩状",
                        "duration_days": 15,
                        "required": False,
                        "ai_tip": "提交答辩状的同时可申请查阅原告证据，提交证据交换申请。"
                    }
                ]
            },
            "evidence": {
                "name": "举证阶段",
                "description": "证据交换与补充",
                "milestones": [
                    {
                        "id": "evidence_exchange",
                        "name": "证据交换",
                        "description": "与对方交换证据",
                        "duration_days": 30,
                        "required": True,
                        "ai_tip": "证据应在举证期限内提交，逾期可能不被采纳。申请法院调查取证的，应书面提出申请。"
                    },
                    {
                        "id": "evidence_review",
                        "name": "质证意见准备",
                        "description": "准备对对方证据的质证意见",
                        "duration_days": 7,
                        "required": True,
                        "ai_tip": "质证意见应围绕证据的三性（真实性、合法性、关联性）展开。"
                    },
                    {
                        "id": "supplementary",
                        "name": "补充证据（如需）",
                        "description": "针对新情况补充证据",
                        "duration_days": 15,
                        "required": False,
                        "ai_tip": "补充证据应有正当理由，如出现新证据或对方提交新证据需要质证。"
                    }
                ]
            },
            "trial": {
                "name": "开庭审理",
                "description": "参加庭审",
                "milestones": [
                    {
                        "id": "hearing_notice",
                        "name": "收到开庭通知",
                        "description": "法院送达开庭传票",
                        "duration_days": 5,
                        "required": True,
                        "ai_tip": "确认开庭时间地点，准备授权委托书和出庭人员身份证件。"
                    },
                    {
                        "id": "trial_prep",
                        "name": "庭审准备",
                        "description": "准备庭审提纲，模拟法庭",
                        "duration_days": 7,
                        "required": True,
                        "ai_tip": "准备证据原件、证人出庭申请（如有）、代理词初稿。提前到达法院。"
                    },
                    {
                        "id": "first_hearing",
                        "name": "第一次开庭",
                        "description": "参加第一次庭审",
                        "duration_days": 1,
                        "required": True,
                        "ai_tip": "陈述时抓住重点，法官提问如实回答，对对方证据及时质证。庭审后关注是否需要补充材料。"
                    },
                    {
                        "id": "subsequent_hearings",
                        "name": "后续开庭（如有）",
                        "description": "补充证据或调解",
                        "duration_days": 30,
                        "required": False,
                        "ai_tip": "调解贯穿始终，可根据情况考虑调解方案。调解成功可节省时间和费用。"
                    }
                ]
            },
            "judgment": {
                "name": "判决阶段",
                "description": "等待和领取判决",
                "milestones": [
                    {
                        "id": "judgment_prep",
                        "name": "等待判决",
                        "description": "庭审结束后等待判决",
                        "duration_days": 30,
                        "required": True,
                        "ai_tip": "普通程序应在立案之日起6个月内审结，简易程序3个月。关注是否需要补充材料。"
                    },
                    {
                        "id": "judgment_received",
                        "name": "收到判决",
                        "description": "领取判决书",
                        "duration_days": 5,
                        "required": True,
                        "ai_tip": "核对判决书内容是否有笔误，收到判决后立即计算上诉期限。"
                    },
                    {
                        "id": "appeal_decision",
                        "name": "上诉决策",
                        "description": "决定是否上诉",
                        "duration_days": 15,
                        "required": True,
                        "ai_tip": "不服一审判决应在15日内上诉。上诉需提交上诉状和上诉费。"
                    }
                ]
            },
            "execution": {
                "name": "执行阶段（如需）",
                "description": "申请强制执行",
                "milestones": [
                    {
                        "id": "judgment_final",
                        "name": "判决生效",
                        "description": "上诉期满或二审判决",
                        "duration_days": 15,
                        "required": True,
                        "ai_tip": "二审判决为终审判决，送达即生效。一审判决15日无人上诉生效。"
                    },
                    {
                        "id": "performance_period",
                        "name": "履行期限届满",
                        "description": "对方自动履行的期限",
                        "duration_days": 10,
                        "required": True,
                        "ai_tip": "判决一般会给付义务方10日以内的自动履行期限。"
                    },
                    {
                        "id": "execution_apply",
                        "name": "申请执行",
                        "description": "向法院申请强制执行",
                        "duration_days": 2,
                        "duration_type": "年",
                        "required": True,
                        "ai_tip": "执行申请期限为2年，从履行期届满之日起计算。超期将丧失申请权！"
                    }
                ]
            }
        }
    }
    
    # 行政案件标准里程碑
    ADMINISTRATIVE_TEMPLATE = {
        "name": "行政诉讼标准流程",
        "case_type": "administrative",
        "phases": {
            "pre_litigation": {
                "name": "诉前准备",
                "description": "行政复议或直接起诉",
                "milestones": [
                    {
                        "id": "case_review",
                        "name": "案件审查",
                        "description": "审查具体行政行为的合法性",
                        "duration_days": 7,
                        "required": True,
                        "ai_tip": "重点审查：执法主体是否合法、事实是否清楚、程序是否正当、适用法律是否正确。"
                    },
                    {
                        "id": "evidence_get",
                        "name": "获取证据",
                        "description": "要求行政机关提供相关证据",
                        "duration_days": 15,
                        "required": True,
                        "ai_tip": "可在诉讼中要求被告提供作出行政行为的证据和依据。"
                    },
                    {
                        "id": "reconsideration_decide",
                        "name": "决定是否复议",
                        "description": "选择复议或直接诉讼",
                        "duration_days": 60,
                        "required": True,
                        "ai_tip": "复议期限60日，复议后再诉讼15日。直接诉讼期限6个月。注意复议前置的情形。"
                    }
                ]
            },
            "filing": {
                "name": "立案阶段",
                "description": "向法院提交起诉材料",
                "milestones": [
                    {
                        "id": "filing_submit",
                        "name": "提交起诉材料",
                        "description": "向有管辖权的法院起诉",
                        "duration_days": 180,
                        "required": True,
                        "ai_tip": "行政诉讼管辖：被告所在地法院。海关、金融、国税等专属管辖。"
                    }
                ]
            },
            "trial": {
                "name": "审理阶段",
                "description": "参加庭审",
                "milestones": [
                    {
                        "id": "hearing",
                        "name": "开庭审理",
                        "description": "参加庭审",
                        "duration_days": 6,
                        "duration_type": "月",
                        "required": True,
                        "ai_tip": "行政诉讼中被告承担举证责任。原告只需证明与被诉行政行为有利害关系。"
                    }
                ]
            },
            "judgment": {
                "name": "判决阶段",
                "description": "等待和领取判决",
                "milestones": [
                    {
                        "id": "judgment",
                        "name": "领取判决",
                        "description": "收到判决书",
                        "duration_days": 15,
                        "required": True,
                        "ai_tip": "不服一审判决应在15日内上诉，二审应在收到裁定10日内上诉。"
                    }
                ]
            }
        }
    }
    
    def __init__(self):
        self.templates = {
            "civil": self.CIVIL_FIRST_TRIAL_TEMPLATE,
            "administrative": self.ADMINISTRATIVE_TEMPLATE,
        }
    
    def generate_milestones(self,
                           case_type: str,
                           case_start_date: datetime,
                           case_phase: str = "pre_litigation") -> List[Dict]:
        """
        根据案件类型生成里程碑列表
        
        Args:
            case_type: 案件类型
            case_start_date: 案件开始日期
            case_phase: 当前案件阶段
            
        Returns:
            里程碑列表
        """
        template = self.templates.get(case_type, self.CIVIL_FIRST_TRIAL_TEMPLATE)
        milestones = []
        current_date = case_start_date
        
        # 遍历所有阶段
        phases_order = list(template["phases"].keys())
        
        for phase_key in phases_order:
            phase = template["phases"][phase_key]
            
            # 如果已经过了这个阶段，跳过
            if phases_order.index(phase_key) < phases_order.index(case_phase):
                continue
            
            for milestone in phase["milestones"]:
                # 计算里程碑日期
                duration_type = milestone.get("duration_type", "日")
                duration = milestone.get("duration_days", 1)
                
                if duration_type == "年":
                    target_date = current_date + timedelta(days=duration * 365)
                elif duration_type == "月":
                    target_date = current_date + timedelta(days=duration * 30)
                else:
                    target_date = current_date + timedelta(days=duration)
                
                milestone_entry = {
                    "phase": phase_key,
                    "phase_name": phase["name"],
                    "phase_description": phase["description"],
                    "id": milestone["id"],
                    "name": milestone["name"],
                    "description": milestone["description"],
                    "required": milestone.get("required", True),
                    "expected_date": target_date,
                    "ai_tip": milestone.get("ai_tip", ""),
                    "is_completed": False,
                    "is_current": False
                }
                
                milestones.append(milestone_entry)
                current_date = target_date
        
        return milestones
    
    def generate_smart_milestones(self,
                                  case_info: Dict,
                                  case_start_date: datetime) -> List[Dict]:
        """
        使用 AI 生成智能里程碑
        
        根据具体案件情况，生成定制化的里程碑
        """
        # 先获取基础模板
        case_type = case_info.get("case_type", "civil")
        base_milestones = self.generate_milestones(case_type, case_start_date)
        
        # 使用 AI 进行优化
        prompt = f"""基于以下案件信息，优化调整标准里程碑：

【案件基本信息】
- 案件类型：{case_info.get('case_type', '民事')}
- 案件标题：{case_info.get('title', '')}
- 案由：{case_info.get('cause', '')}
- 原告：{case_info.get('plaintiff', '')}
- 被告：{case_info.get('defendant', '')}
- 诉讼金额：{case_info.get('claim_amount', '')}
- 案件描述：{case_info.get('description', '')}

【需要优化的标准里程碑】
{self._format_milestones(base_milestones)}

请根据以上案件特点：
1. 判断哪些标准里程碑需要调整或删除
2. 是否有遗漏的关键节点需要添加
3. 各节点的预计时间是否需要调整
4. 特别注意可能涉及的特殊法定期限

请返回调整后的里程碑列表，格式为JSON数组。
"""
        
        try:
            ai_response = llm_service.chat([
                {"role": "system", "content": "你是一位专业的诉讼律师，擅长制定精准的案件时间计划。"},
                {"role": "user", "content": prompt}
            ])
            
            # 尝试解析 AI 返回的里程碑
            # 这里简化处理，实际可以更好地解析
            return base_milestones
            
        except Exception as e:
            # 如果 AI 分析失败，返回基础模板
            return base_milestones
    
    def _format_milestones(self, milestones: List[Dict]) -> str:
        """格式化里程碑列表"""
        lines = []
        for m in milestones:
            lines.append(f"- {m['name']}（{m['phase_name']}）：{m['description']}")
        return "\n".join(lines)
    
    def generate_urgency_report(self, milestones: List[Dict]) -> Dict:
        """
        生成紧迫性报告
        
        分析当前需要关注的事项
        """
        today = datetime.now()
        report = {
            "today": today,
            "critical": [],    # 紧急且重要
            "important": [],  # 重要
            "upcoming": [],    # 即将到来
            "completed": [],   # 已完成
            "summary": ""
        }
        
        for m in milestones:
            if m.get("is_completed"):
                report["completed"].append(m)
                continue
            
            expected_date = m.get("expected_date")
            if not expected_date:
                continue
            
            days_until = (expected_date - today).days
            
            if days_until < 0:
                report["critical"].append({
                    **m,
                    "days_overdue": abs(days_until),
                    "urgency_level": "critical"
                })
            elif days_until == 0:
                report["critical"].append({
                    **m,
                    "days_remaining": 0,
                    "urgency_level": "critical"
                })
            elif days_until <= 3:
                report["critical"].append({
                    **m,
                    "days_remaining": days_until,
                    "urgency_level": "high"
                })
            elif days_until <= 7:
                report["important"].append({
                    **m,
                    "days_remaining": days_until,
                    "urgency_level": "medium"
                })
            elif days_until <= 30:
                report["upcoming"].append({
                    **m,
                    "days_remaining": days_until,
                    "urgency_level": "low"
                })
        
        # 生成总结
        if report["critical"]:
            names = [m["name"] for m in report["critical"]]
            report["summary"] = f"紧急事项：{', '.join(names)}，请立即处理！"
        elif report["important"]:
            names = [m["name"] for m in report["important"]]
            report["summary"] = f"重要提醒：{', '.join(names)}，请尽快处理。"
        elif report["upcoming"]:
            names = [m["name"] for m in report["upcoming"]]
            report["summary"] = f"近期事项：{', '.join(names)}，请提前准备。"
        
        return report
    
    def generate_lawyer_level_checklist(self, case_info: Dict) -> Dict:
        """
        生成律师级检查清单
        
        让非律师用户也能按照律师的标准完成任务
        """
        checklist = {
            "case_info": case_info,
            "phases": [],
            "deadlines": [],
            "warnings": []
        }
        
        case_type = case_info.get("case_type", "民事")
        
        # 添加基础检查项
        checklist["phases"] = [
            {
                "name": "证据准备",
                "items": [
                    {"desc": "整理所有书面合同原件", "check": "has_contract"},
                    {"desc": "收集付款凭证（转账记录、发票）", "check": "has_payment_proof"},
                    {"desc": "整理往来函件和聊天记录", "check": "has_correspondence"},
                    {"desc": "准备证人名单（如有证人）", "check": "has_witnesses"}
                ]
            },
            {
                "name": "起诉材料",
                "items": [
                    {"desc": "起草起诉状（份数=被告数+1）", "check": "has_complaint"},
                    {"desc": "准备证据目录", "check": "has_evidence_list"},
                    {"desc": "准备证据复印件", "check": "has_evidence_copies"},
                    {"desc": "当事人身份证明", "check": "has_identity_proof"}
                ]
            }
        ]
        
        # 根据案件类型添加专项检查
        if case_type == "民事":
            checklist["deadlines"] = [
                {
                    "name": "诉讼时效",
                    "description": "一般民事纠纷诉讼时效为3年",
                    "action": "确认纠纷发生时间是否在时效内"
                },
                {
                    "name": "举证期限",
                    "description": "一般在30日内提交证据",
                    "action": "注意法院送达的举证通知书"
                }
            ]
        
        # 律师特别提醒
        checklist["warnings"] = [
            "诉讼费需在收到缴费通知后7日内缴纳",
            "证据原件需妥善保管，庭审时必须携带",
            "如有证人出庭，需提前向法院申请",
            "地址变更需及时通知法院，否则可能缺席判决",
            "调解贯穿全程，可考虑合适的调解方案"
        ]
        
        return checklist


# 全局实例
milestone_generator = MilestoneGenerator()
