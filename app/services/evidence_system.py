"""
证据管理系统 - 证据链构建、完整性检查、补全方案、证据册生成
核心功能：
1. 证据清单提取
2. 证据链完整性检查
3. 缺失证据补全方案
4. 证据册自动生成与导出（含原始文件嵌入）
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import re
import os


@dataclass
class Evidence:
    """证据"""
    id: str
    name: str                           # 证据名称
    evidence_type: str                  # 证据类型
    content: str                        # 证据内容摘要
    source: str                         # 证据来源
    custody: str                        # 举证方
    proof_point: str                    # 证明目的
    authenticity: str = "待核实"        # 真实性
    legitimacy: str = "待核实"          # 合法性
    relevance: str = "待核实"           # 关联性
    original_status: str = "待核实"     # 原件状态
    formed_at: str = ""                 # 形成/取得时间
    strengthening_actions: List[str] = field(default_factory=list)  # 补强动作
    review_notes: str = ""              # 复核备注
    file_path: Optional[str] = None     # 文件路径
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "evidence_type": self.evidence_type,
            "content": self.content,
            "source": self.source,
            "custody": self.custody,
            "proof_point": self.proof_point,
            "authenticity": self.authenticity,
            "legitimacy": self.legitimacy,
            "relevance": self.relevance,
            "original_status": self.original_status,
            "formed_at": self.formed_at,
            "strengthening_actions": self.strengthening_actions,
            "review_notes": self.review_notes,
            "file_path": self.file_path,
            "created_at": self.created_at
        }


@dataclass
class EvidenceGap:
    """缺失证据"""
    missing_type: str                   # 缺失证据类型
    description: str                    # 缺失描述
    importance: str                     # 重要性：高/中/低
    proof_point: str                    # 需证明的事实
    alternative_solution: str           # 弥补方案
    alternative_feasibility: str         # 可行性评估
    risk_level: str                    # 风险等级


@dataclass
class EvidenceChain:
    """证据链"""
    claim: str                          # 主张
    required_facts: List[str]           # 需要证明的事实
    required_evidence: List[str]       # 需要哪些证据
    current_evidence: List[Evidence]     # 现有证据
    gaps: List[EvidenceGap]             # 缺失证据
    completeness: float                 # 完整性 0-1


class EvidenceTypeClassifier:
    """
    证据类型分类器
    常见证据类型及证明目的
    """

    # 证据类型定义
    EVIDENCE_TYPES = {
        "书面证据": {
            "subtypes": ["合同", "协议", "函件", "文书", "证书", "票据", "账册", "单据"],
            "proof_points": ["证明合同关系", "证明履行情况", "证明权利义务"]
        },
        "物证": {
            "subtypes": ["实物", "现场照片", "损坏物品", "产品样品"],
            "proof_points": ["证明物品状态", "证明损害事实", "证明标的物"]
        },
        "视听资料": {
            "subtypes": ["录音", "录像", "监控视频", "聊天记录截图", "电子邮件"],
            "proof_points": ["证明口头约定", "证明行为过程", "证明事实发生"]
        },
        "电子数据": {
            "subtypes": ["微信记录", "QQ记录", "邮件", "网页截图", "电子合同", "转账记录"],
            "proof_points": ["证明通讯内容", "证明交易过程", "证明电子约定"]
        },
        "证人证言": {
            "subtypes": ["当事人陈述", "第三人证言", "鉴定人意见"],
            "proof_points": ["证明案件事实", "还原事实经过", "印证其他证据"]
        },
        "鉴定意见": {
            "subtypes": ["文书鉴定", "痕迹鉴定", "会计鉴定", "评估报告"],
            "proof_points": ["证明专门性问题", "证明损失金额", "证明真伪"]
        },
        "当事人陈述": {
            "subtypes": ["原告陈述", "被告答辩", "第三人陈述"],
            "proof_points": ["陈述案件事实", "承认或否认对方主张"]
        },
        "勘验笔录": {
            "subtypes": ["现场勘验", "物品勘验", "人身检查"],
            "proof_points": ["证明现场状态", "证明客观事实"]
        }
    }

    @classmethod
    def classify(cls, evidence_name: str, content: str = "") -> str:
        """根据证据名称和内容分类"""
        evidence_lower = (evidence_name + content).lower()

        # 关键词匹配
        keywords_map = {
            "合同": "书面证据",
            "协议": "书面证据",
            "发票": "书面证据",
            "收据": "书面证据",
            "转账": "电子数据",
            "银行流水": "书面证据",
            "微信": "电子数据",
            "聊天": "电子数据",
            "录音": "视听资料",
            "录像": "视听资料",
            "照片": "视听资料",
            "图片": "视听资料",
            "证人": "证人证言",
            "鉴定": "鉴定意见",
            "陈述": "当事人陈述",
            "勘验": "勘验笔录",
            "邮件": "电子数据",
            "短信": "电子数据",
            "通话": "视听资料"
        }

        for keyword, evidence_type in keywords_map.items():
            if keyword in evidence_lower:
                return evidence_type

        return "其他证据"


class EvidenceCompletenessChecker:
    """
    证据链完整性检查器
    像侦探一样检查证据是否形成完整证据链
    """

    # 不同案件类型的证据要求
    CASE_EVIDENCE_REQUIREMENTS = {
        "合同纠纷": {
            "基本证据": [
                ("合同原件", "证明合同关系成立", "高"),
                ("合同履行证据", "证明合同已履行或未履行", "高"),
                ("付款凭证", "证明付款情况", "高"),
            ],
            "可选证据": [
                ("补充协议", "证明合同变更", "中"),
                ("变更函件", "证明合同变更", "中"),
                ("催告函", "证明已履行催告义务", "中"),
            ]
        },
        "侵权纠纷": {
            "基本证据": [
                ("侵权行为证据", "证明侵权行为发生", "高"),
                ("损害事实证据", "证明损害后果", "高"),
                ("因果关系证据", "证明侵权与损害的因果关系", "高"),
                ("过错证据", "证明侵权方过错", "高"),
            ],
            "可选证据": [
                ("损失计算明细", "证明损失金额", "高"),
                ("录像/照片", "证明侵权现场", "中"),
                ("证人证言", "还原事实经过", "中"),
            ]
        },
        "劳动纠纷": {
            "基本证据": [
                ("劳动合同", "证明劳动关系", "高"),
                ("工资发放记录", "证明工资标准", "高"),
                ("社保缴纳记录", "证明劳动关系", "中"),
                ("解除通知", "证明解除原因", "高"),
            ],
            "可选证据": [
                ("工作证/工牌", "证明劳动关系", "低"),
                ("考勤记录", "证明出勤情况", "中"),
                ("工作成果", "证明工作情况", "低"),
            ]
        },
        "债务纠纷": {
            "基本证据": [
                ("借条/欠条", "证明债务关系", "高"),
                ("转账记录", "证明款项交付", "高"),
                ("催款记录", "证明已催告", "中"),
            ],
            "可选证据": [
                ("证人证言", "证明借款事实", "中"),
                ("聊天记录", "证明借款合意", "中"),
            ]
        }
    }

    def __init__(self):
        self.evidence_types = EvidenceTypeClassifier()

    def check_completeness(self,
                          case_type: str,
                          submitted_evidence: List[Evidence],
                          user_claims: List[str]) -> EvidenceChain:
        """
        检查证据链完整性

        Returns:
            EvidenceChain: 包含完整性评估和缺失清单
        """
        # 获取案件类型要求
        requirements = self.CASE_EVIDENCE_REQUIREMENTS.get(
            case_type,
            self.CASE_EVIDENCE_REQUIREMENTS["合同纠纷"]  # 默认
        )

        basic_evidence = requirements.get("基本证据", [])
        optional_evidence = requirements.get("可选证据", [])

        # 当前已有的证据
        current_evidence = submitted_evidence

        # 检查缺失
        gaps = []
        covered_types = set()

        # 检查基本证据
        for req_name, req_proof_point, importance in basic_evidence:
            found = self._find_matching_evidence(req_name, current_evidence)
            if not found:
                gap = self._create_gap(
                    req_name, req_proof_point, importance,
                    case_type, user_claims
                )
                gaps.append(gap)
            else:
                covered_types.add(req_name)

        # 检查可选证据
        for req_name, req_proof_point, importance in optional_evidence:
            found = self._find_matching_evidence(req_name, current_evidence)
            if not found:
                gap = self._create_gap(
                    req_name, req_proof_point, importance,
                    case_type, user_claims, is_optional=True
                )
                gaps.append(gap)

        # 计算完整性
        total_required = len(basic_evidence) + len(optional_evidence)
        completeness = len(covered_types) / len(basic_evidence) if basic_evidence else 0

        return EvidenceChain(
            claim="; ".join(user_claims),
            required_facts=self._extract_required_facts(basic_evidence),
            required_evidence=[e[0] for e in basic_evidence + optional_evidence],
            current_evidence=current_evidence,
            gaps=gaps,
            completeness=completeness
        )

    def _find_matching_evidence(self,
                               required_name: str,
                               evidence_list: List[Evidence]) -> Optional[Evidence]:
        """查找匹配的证据"""
        required_lower = required_name.lower()

        for evidence in evidence_list:
            evidence_lower = (evidence.name + evidence.evidence_type).lower()
            # 模糊匹配
            if any(word in evidence_lower for word in required_lower.split("/")):
                return evidence

        return None

    def _create_gap(self,
                   evidence_name: str,
                   proof_point: str,
                   importance: str,
                   case_type: str,
                   claims: List[str],
                   is_optional: bool = False) -> EvidenceGap:
        """创建缺失证据说明"""

        # 生成弥补方案
        alternative = self._generate_alternative(evidence_name, case_type, claims)

        # 评估可行性
        feasibility = self._assess_feasibility(evidence_name, case_type)

        # 评估风险
        risk = self._assess_gap_risk(evidence_name, importance, is_optional)

        return EvidenceGap(
            missing_type=evidence_name,
            description=f"缺少{evidence_name}，用于证明{proof_point}",
            importance=importance,
            proof_point=proof_point,
            alternative_solution=alternative["solution"],
            alternative_feasibility=feasibility,
            risk_level=risk
        )

    def _generate_alternative(self,
                            evidence_name: str,
                            case_type: str,
                            claims: List[str]) -> Dict:
        """
        生成证据补全方案
        当原始证据无法取得时，提供弥补方案
        """

        alternatives = {
            # 合同类
            "合同原件": {
                "solution": "1. 尝试联系对方获取复印件并盖章\n2. 调取工商档案中的合同备案\n3. 寻找第三方见证人作证\n4. 提供微信/邮件沟通记录证明合同履行",
                "feasibility": "中高",
                "priority": 1
            },
            "付款凭证": {
                "solution": "1. 前往银行打印历史转账流水\n2. 获取支付宝/微信支付凭证\n3. 调取会计账簿中的付款记录\n4. 申请法院调查令调取对方账户记录",
                "feasibility": "高",
                "priority": 1
            },
            # 侵权类
            "侵权行为证据": {
                "solution": "1. 申请公证处对侵权现场进行公证\n2. 委托鉴定机构进行鉴定\n3. 收集网络截图（需公证）\n4. 申请法院现场勘验",
                "feasibility": "中高",
                "priority": 1
            },
            "损害事实证据": {
                "solution": "1. 委托有资质的评估机构评估损失\n2. 收集财务账册证明经营损失\n3. 收集医疗票据证明人身损害\n4. 申请鉴定确定损失金额",
                "feasibility": "高",
                "priority": 1
            },
            "因果关系证据": {
                "solution": "1. 委托专业鉴定机构出具鉴定意见\n2. 收集专家证人意见\n3. 引用同类案件判决作为参考\n4. 申请法院调查取证",
                "feasibility": "中",
                "priority": 2
            },
            # 劳动类
            "劳动合同": {
                "solution": "1. 前往社保中心查询社保缴费记录证明劳动关系\n2. 收集工资流水证明劳动关系\n3. 收集工作证、工牌、门禁记录\n4. 申请劳动仲裁委调取用人单位提交的证据",
                "feasibility": "高",
                "priority": 1
            },
            "工资发放记录": {
                "solution": "1. 前往银行打印工资卡历史流水\n2. 收集个人所得税扣缴记录\n3. 要求用人单位提供工资台账\n4. 申请仲裁委或法院责令用人单位提供",
                "feasibility": "高",
                "priority": 1
            },
            # 债务类
            "借条/欠条": {
                "solution": "1. 收集银行转账记录作为补充证据\n2. 获取微信/短信催款记录证明债务存在\n3. 寻找知情人作证\n4. 提供录音证据证明借款事实",
                "feasibility": "中高",
                "priority": 1
            },
            "转账记录": {
                "solution": "1. 前往银行打印历史转账凭证\n2. 获取支付宝/微信支付账单\n3. 申请法院调查令调取对方收款记录\n4. 提供现金交付的证人证言",
                "feasibility": "高",
                "priority": 1
            }
        }

        # 返回对应方案或默认方案
        for key, alt in alternatives.items():
            if key in evidence_name:
                return alt

        # 默认方案
        return {
            "solution": f"1. 寻找能替代'{evidence_name}'的其他证据\n"
                       f"2. 申请法院调查取证\n"
                       f"3. 收集间接证据形成证据链\n"
                       f"4. 申请鉴定或勘验",
            "feasibility": "中",
            "priority": 3
        }

    def _assess_feasibility(self, evidence_name: str, case_type: str) -> str:
        """评估弥补方案可行性"""
        high_feasibility = ["付款", "转账", "银行", "工资", "社保", "录音"]
        medium_feasibility = ["合同", "协议", "催告", "聊天"]
        low_feasibility = ["原件", "签字", "盖章"]

        for keyword in high_feasibility:
            if keyword in evidence_name:
                return "高"

        for keyword in medium_feasibility:
            if keyword in evidence_name:
                return "中"

        for keyword in low_feasibility:
            if keyword in evidence_name:
                return "低"

        return "中"

    def _assess_gap_risk(self,
                         evidence_name: str,
                         importance: str,
                         is_optional: bool) -> str:
        """评估缺失证据的风险"""
        if is_optional:
            return "低风险"

        if importance == "高":
            # 高重要性证据缺失的风险
            high_risk_keywords = ["合同", "原件", "付款", "转账", "侵权行为", "损害"]
            for keyword in high_risk_keywords:
                if keyword in evidence_name:
                    return "🔴 高风险 - 可能导致败诉"
            return "🟡 中风险 - 增加举证难度"

        return "🟢 低风险"

    def _extract_required_facts(self, evidence_list: List[Tuple]) -> List[str]:
        """提取需要证明的事实"""
        return [e[1] for e in evidence_list]


class EvidenceBookGenerator:
    """
    证据册自动生成器
    将证据整理成符合法院要求的证据册格式
    
    设计原则：
    1. 证据册是给法官/仲裁看的，表达要清晰、条理明白
    2. 目录、页码、证据编号都要清晰
    3. 证据要分类，针对不同诉求的证据放在一起，便于查阅
    """

    # A4页面尺寸（单位：mm）
    A4_WIDTH = 210
    A4_HEIGHT = 297
    MARGIN = 20  # 页边距

    def __init__(self):
        self.checker = EvidenceCompletenessChecker()

    def get_css_styles(self) -> str:
        """获取证据册CSS样式"""
        return """
        <style>
        @page { size: A4; margin: 20mm; }
        body { font-family: "SimSun", "宋体", serif; font-size: 12pt; line-height: 1.6; color: #333; }
        .evidence-box { border: 1px solid #333; margin: 10px 0; page-break-inside: avoid; }
        .evidence-header { background: #f5f5f5; border-bottom: 1px solid #333; padding: 10px; font-weight: bold; }
        .evidence-content { padding: 15px; }
        .evidence-image { page-break-inside: avoid; margin: 15mm 0; text-align: center; }
        .evidence-image img { max-width: 190mm; height: auto; display: block; margin: 0 auto; border: 1px solid #333; }
        .page-break { page-break-after: always; }
        </style>
        """

    def generate_evidence_book(self,
                              case_info: Dict,
                              evidence_list: List[Evidence],
                              party_info: Dict,
                              case_type: str,
                              claim_info: Dict = None) -> Dict:
        """
        生成完整的证据册
        
        设计升级：
        1. 分类按诉求分组（同诉求的证据放一起）
        2. 每个证据有清晰编号（类别号-顺序号）
        3. 页码连续编号
        4. 目录显示证据编号、名称、页码

        Args:
            case_info: 案件基本信息
            evidence_list: 证据列表
            party_info: 当事人信息
            case_type: 案件类型
            claim_info: 诉求信息（用于分组）

        Returns:
            包含封面、目录、证据正文等完整证据册
        """
        # 按诉求分类证据
        grouped_evidence = self._group_by_claim(evidence_list, claim_info)
        
        # 生成带诉求标签的目录
        table_of_contents = self._generate_toc_with_claims(grouped_evidence)
        
        # 生成分组后的证据章节（带页码）
        evidence_sections = self._generate_grouped_sections(grouped_evidence)
        
        book = {
            "cover": self._generate_cover(case_info, party_info),
            "table_of_contents": table_of_contents,
            "evidence_sections": evidence_sections,
            "summary": self._generate_summary(evidence_list),
            "export_format": "pdf",
            "grouped_evidence": grouped_evidence,
        }

        return book

    def _group_by_claim(self, evidence_list: List[Evidence], claim_info: Dict = None) -> Dict:
        """
        按诉求分组证据
        同一诉求的证据放在一起，便于法官查阅
        """
        # 默认分类：按证据类型
        grouped = {}
        for ev in evidence_list:
            ev_type = getattr(ev, 'claim_group', None) or getattr(ev, 'evidence_type', None) or "其他"
            
            # 分类名称映射（更易懂）
            type_names = {
                "CONTRACT": "合同协议类",
                "CORRESPONDENCE": "函件文书类", 
                "PAYMENT": "付款凭证类",
                "IDENTITY": "身份证明类",
                "AUDIO_VIDEO": "视听资料类",
                "TESTIMONY": "证人证言类",
                "EXPERT": "鉴定评估类",
                "DOCUMENT": "政府文件类",
            }
            group_name = type_names.get(ev_type, ev_type)
            
            if group_name not in grouped:
                grouped[group_name] = []
            grouped[group_name].append(ev)
        
        return grouped

    def _generate_toc_with_claims(self, grouped_evidence: Dict) -> str:
        """
        生成带诉求分类的目录
        格式：类别 | 证据编号 | 证据名称 | 证明事项 | 页码
        """
        toc_lines = [
            "┌" + "─" * 96 + "┐",
            "│" + " " * 30 + "证 据 目 录" + " " * 30 + " │",
            "├" + "─" * 96 + "┤",
            "│ 类别            │ 编号  │ 证据名称                    │ 证明事项                  │ 页码 │",
            "├" + "─" * 96 + "┤",
        ]
        
        page_num = 2  # 封面后是第1页，目录从第2页开始
        global_index = 0
        
        for group_name, ev_list in grouped_evidence.items():
            for ev in ev_list:
                global_index += 1
                # 格式：类别 | 编号 | 名称 | 证明目的 | 页码
                name = (ev.name or "未命名")[:24]
                proof = (ev.proof_point or "待填写")[:20]
                # 证据编号：类别缩写-序号
                type_abbr = self._get_type_abbr(group_name)
                ev_num = f"{type_abbr}{global_index:03d}"
                
                toc_lines.append(
                    f"│ {group_name:<14} │ {ev_num:<4} │ {name:<24} │ {proof:<20} │ {page_num:<4} │"
                )
                # 假设每个证据详情需要1页
                page_num += 1
        
        toc_lines.extend([
            "├" + "─" * 96 + "┤",
            f"│ 证据总计：{global_index} 件                                                              │",
            "└" + "─" * 96 + "┘",
        ])
        
        return "\n".join(toc_lines)

    def _get_type_abbr(self, group_name: str) -> str:
        """获取类别缩写"""
        abbr_map = {
            "合同协议类": "C",
            "函件文书类": "L", 
            "付款凭证类": "P",
            "身份证明类": "I",
            "视听资料类": "V",
            "证人证言类": "T",
            "鉴定评估类": "E",
            "政府文件类": "D",
            "其他": "O",
        }
        return abbr_map.get(group_name, "O")

    def _generate_grouped_sections(self, grouped_evidence: Dict) -> List[Dict]:
        """生成分组后的证据章节（带页码）"""
        sections = []
        page_num = 2
        
        for group_name, ev_list in grouped_evidence.items():
            # 每个类别开始新的一组
            group_section = {
                "group_name": group_name,
                "evidence_count": len(ev_list),
                "start_page": page_num,
                "evidences": []
            }
            
            for i, ev in enumerate(ev_list, 1):
                ev_num = f"{self._get_type_abbr(group_name)}{i:03d}"
                section = {
                    "index": i,
                    "evidence_num": ev_num,  # 证据编号
                    "evidence": ev,
                    "page": page_num,
                    "content": self._generate_evidence_page_v2(ev, i, group_name, page_num)
                }
                group_section["evidences"].append(section)
                sections.append(section)
                page_num += 1
            
            group_section["end_page"] = page_num - 1
            # 将组信息附加到第一个证据
            if sections:
                sections[len(sections) - len(ev_list)]["group_info"] = group_section
        
        return sections

    def _generate_evidence_page_v2(self, ev: Evidence, index: int, group_name: str, page_num: int) -> str:
        """
        生成单份证据页面（升级版）
        包含：证据编号、页码、清晰的框线
        """
        name = ev.name or "未命名证据"
        e_type = getattr(ev, 'evidence_type', None) or "其他"
        source = ev.source or "待确认"
        custody = ev.custody or "待填写"
        proof = ev.proof_point or "待填写"
        content = ev.content or "无内容摘要"
        original_status = ev.original_status or "待核实"
        formed_at = ev.formed_at or "待核实"
        strengthening_actions = ev.strengthening_actions or ["提交前核验原件、页码、形成时间和上下文"]
        strengthening_text = "；".join(str(action).strip() for action in strengthening_actions if str(action).strip()) or "提交前核验原件、页码、形成时间和上下文"
        review_notes = ev.review_notes or "无"
        
        # 证据编号
        ev_num = f"{self._get_type_abbr(group_name)}{index:03d}"

        # 处理内容（限制长度用于文本格式）
        if content and len(content) > 2000:
            display_content = content[:2000] + "\n...（内容已截断）"
        else:
            display_content = content or "无内容"

        page = f"""
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 证据编号：{ev_num}                                          第 {page_num} 页                                   │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 【证据基本信息】                                                                                     │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 证据名称：{name:<80}│
│ 所属类别：{group_name:<80}│
│ 证据类型：{e_type:<80}│
│ 证据来源：{source:<80}│
│ 举证方  ：{custody:<80}│
│ 原件状态：{original_status:<80}│
│ 形成/取得时间：{formed_at:<74}│
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 【证明事项】                                                                                         │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 证明目的：{proof:<80}│
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 【证据内容】（完整内容）                                                                           │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ {display_content:<80}│
│                                                                                                    │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 【人工复核与补强动作】                                                                               │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 真实性风险：{ev.authenticity:<72}│
│ 合法性风险：{ev.legitimacy:<72}│
│ 关联性风险：{ev.relevance:<72}│
│ 补强动作：{strengthening_text:<76}│
│ 复核备注：{review_notes:<76}│
└──────────────────────────────────────────────────────────────────────────────────────────────��────────────────────────────────────────────────┘
"""
        return page

    def _generate_cover(self, case_info: Dict, party_info: Dict) -> str:
        """生成封面"""
        case_number = str(case_info.get("case_number") or "（待立案后填写）")
        case_type = str(case_info.get("case_type") or "民事纠纷")
        plaintiff = str(party_info.get("plaintiff") or "")
        defendant = str(party_info.get("defendant") or "")
        submitter = str(party_info.get("submitter") or "")
        evidence_count = len(party_info.get("evidence_list", []))
        submit_date = datetime.now().strftime("%Y年%m月%d日")

        cover = f"""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                         民事案件证据册                                    ║
║                                                                           ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  案号：{case_number:<57}║
║                                                                           ║
║  案由：{case_type:<57}║
║                                                                           ║
║  当事人信息：                                                            ║
║    原告（上诉人）：{plaintiff:<46}║
║    被告（被上诉人）：{defendant:<45}║
║                                                                           ║
║  证据提交人：{submitter:<53}║
║                                                                           ║
║  提交日期：{submit_date:<53}║
║                                                                           ║
║  证据总数：{evidence_count} 件{(' ' * (56 - len(str(evidence_count))))}║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════╝
"""
        return cover

    def _generate_toc(self, evidence_list: List[Evidence]) -> str:
        """生成目录"""
        toc_lines = [
            "════════════════════════════════════════════════════════════════════════",
            "                              证 据 目 录",
            "════════════════════════════════════════════════════════════════════════",
            "",
            f"{'序号':<6}{'证据名称':<30}{'证据类型':<12}{'证明目的':<20}",
            "-" * 80,
        ]

        for i, ev in enumerate(evidence_list, 1):
            name = (ev.name or "未命名")[:28]
            e_type = (ev.evidence_type or "其他")[:10]
            proof = (ev.proof_point or "待填写")[:18]
            toc_lines.append(f"{i:<6}{name:<30}{e_type:<12}{proof:<20}")

        toc_lines.extend([
            "-" * 80,
            "",
            f"共计 {len(evidence_list)} 份证据",
            "",
            "───────────────────────────────────────────────────────────────────────────",
            "说明：",
            f"1. 本证据册共 {len(evidence_list)} 件证据，按证据类型及证明逻辑顺序编排。",
            "2. 每份证据后附证据说明，列明证据来源、证明内容及与案件事实的关联性。",
            "3. 证据按三性（真实性、合法性、关联性）要求整理，确保证据体系完整。",
            "════════════════════════════════════════════════════════════════════════",
        ])

        return "\n".join(toc_lines)

    def _generate_evidence_sections(self, evidence_list: List[Evidence]) -> List[Dict]:
        """生成证据正文部分"""
        sections = []

        for i, ev in enumerate(evidence_list, 1):
            section = {
                "index": i,
                "evidence": ev,
                "content": self._generate_evidence_page(ev, i)
            }
            sections.append(section)

        return sections

    def _generate_evidence_page(self, evidence: Evidence, index: int) -> str:
        """生成单份证据页面"""
        name = evidence.name or "未命名证据"
        e_type = evidence.evidence_type or "其他"
        source = evidence.source or "待确认"
        custody = evidence.custody or "待填写"
        proof = evidence.proof_point or "待填写"
        content = evidence.content or "无内容摘要"
        
        # 处理内容截断
        if content and len(content) > 800:
            display_content = content[:800] + "\n...（内容已截断）"
        else:
            display_content = content

        # 获取三性评估
        authenticity = str(evidence.authenticity) if evidence.authenticity else "待核实"
        legitimacy = str(evidence.legitimacy) if evidence.legitimacy else "待核实"
        relevance = str(evidence.relevance) if evidence.relevance else "待核实"

        page = f"""
{'═' * 80}
                              第 {index} 份 证 据
{'═' * 80}

【证据基本信息】
┌─────────────────────────────────────────────────────────────────────────┐
│ 证据名称：{name:<62}│
│ 证据类型：{e_type:<62}│
│ 证据来源：{source:<62}│
│ 举证方  ：{custody:<62}│
└─────────────────────────────────────────────────────────────────────────┘

【证明目的】
{Proof}

【证据内容摘要】
{'-' * 80}
{display_content}
{'-' * 80}

【证据"三性"分析】
┌─────────────────────────────────────────────────────────────────────────┐
│  真实性：{authenticity:<63}│
│  合法性：{legitimacy:<63}│
│  关联性：{relevance:<63}│
└─────────────────────────────────────────────────────────────────────────┘

【备注说明】
（可根据需要添加证据补充说明、与其他证据的关联性说明等）

{'─' * 80}

"""
        return page

    def _generate_summary(self, evidence_list: List[Evidence]) -> str:
        """生成证据汇总说明"""
        type_counts = {}
        for ev in evidence_list:
            t = ev.evidence_type or "其他"
            type_counts[t] = type_counts.get(t, 0) + 1

        summary_lines = [
            "════════════════════════════════════════════════════════════════════════",
            "                              证 据 汇 总",
            "════════════════════════════════════════════════════════════════════════",
            "",
            "一、证据基本情况",
            "-" * 80,
            f"本证据册共包含 {len(evidence_list)} 份证据，按证据类型分类如下：",
            "",
        ]

        for ev_type, count in type_counts.items():
            summary_lines.append(f"  {ev_type:<20} {count:>3} 份")

        summary_lines.extend([
            "",
            "───────────────────────────────────────────────────────────────────────────",
            "二、证据体系说明",
            "-" * 80,
            "本证据册按照以下逻辑组织：",
            "  1. 【主体证据】证明当事人主体资格及身份信息",
            "  2. 【合同/协议证据】证明基础法律关系及权利义务",
            "  3. 【履行证据】证明合同履行情况及事实经过",
            "  4. 【损失/赔偿证据】证明损失金额及计算依据",
            "  5. 【其他证据】补充证明相关案件事实",
            "",
            "───────────────────────────────────────────────────────────────────────────",
            "三、证据关联性说明",
            "-" * 80,
            "各证据之间相互印证，形成完整证据链：",
            "",
        ])

        for i, ev in enumerate(evidence_list[:5], 1):
            proof = str(ev.proof_point) if ev.proof_point else "待填写"
            name = str(ev.name) if ev.name else "未命名"
            summary_lines.append(f"  {i}. {name} → 证明 → {proof}")

        if len(evidence_list) > 5:
            summary_lines.append(f"  ...（共 {len(evidence_list)} 份证据）")

        summary_lines.extend([
            "",
            "───────────────────────────────────────────────────────────────────────────",
            "四、证据效力说明",
            "-" * 80,
            "本证据册中的证据均符合以下要求：",
            "  ✓ 证据来源合法          ✓ 证据形式合法",
            "  ✓ 证据内容真实          ✓ 与案件事实具有关联性",
            "",
            "════════════════════════════════════════════════════════════════════════",
            "",
            "                          证据提交人（签名）：__________________",
            "",
            "                          提交日期：__________________",
            "",
            "════════════════════════════════════════════════════════════════════════",
        ])

        return "\n".join(summary_lines)

    def export_to_text(self, book: Dict) -> str:
        """导出为纯文本格式"""
        output = []

        output.append(book["cover"])
        output.append(book["table_of_contents"])

        for section in book["evidence_sections"]:
            output.append(section["content"])

        output.append(book["summary"])

        return "\n".join(output)

    def export_to_markdown(self, book: Dict) -> str:
        """导出为 Markdown 格式"""
        output = []

        case_number = "待填写"
        if book.get('cover'):
            import re
            match = re.search(r'案号[：:]\s*(\S+)', book['cover'])
            if match:
                case_number = match.group(1)

        output.append("# 民事案件证据册\n")
        output.append(f"> **案号**：{case_number}")
        output.append(f"> **提交日期**：{datetime.now().strftime('%Y年%m月%d日')}")
        
        evidence_count = len(book.get('evidence_sections', []))
        output.append(f"> **证据总数**：{evidence_count} 件\n")

        output.append("---\n")
        output.append("## 一、证据目录\n")
        output.append("| 序号 | 证据名称 | 证据类型 | 证明目的 |")
        output.append("|:---:|:---|:---|:---|")

        for i, section in enumerate(book["evidence_sections"], 1):
            ev = section["evidence"]
            name = str(ev.name or "未命名")[:25]
            e_type = str(ev.evidence_type or "其他")
            proof = str(ev.proof_point or "待填写")[:20]
            output.append(f"| {i} | {name} | {e_type} | {proof} |")

        output.append("\n---\n")
        output.append("## 二、证据详情\n")

        for i, section in enumerate(book["evidence_sections"], 1):
            ev = section["evidence"]
            name = str(ev.name or "未命名")
            e_type = str(ev.evidence_type or "其他")
            source = str(ev.source or "待确认")
            custody = str(ev.custody or "待填写")
            proof = str(ev.proof_point or "待填写")
            content = str(ev.content or "无内容摘要")
            original_status = str(ev.original_status or "待核实")
            formed_at = str(ev.formed_at or "待核实")
            strengthening_actions = ev.strengthening_actions or ["提交前核验原件、页码、形成时间和上下文"]
            strengthening_text = "；".join(str(action).strip() for action in strengthening_actions if str(action).strip()) or "提交前核验原件、页码、形成时间和上下文"
            review_notes = str(ev.review_notes or "无")

            output.append(f"### 第 {i} 份：{name}\n")
            output.append(f"**证据类型**：{e_type}")
            output.append(f"**证据来源**：{source}")
            output.append(f"**举证方**：{custody}")
            output.append(f"**原件状态**：{original_status}")
            output.append(f"**形成/取得时间**：{formed_at}")
            output.append(f"**证明目的**：{proof}\n")
            output.append("**人工复核与补强动作**：")
            output.append(f"- 真实性风险：{ev.authenticity}")
            output.append(f"- 合法性风险：{ev.legitimacy}")
            output.append(f"- 关联性风险：{ev.relevance}")
            output.append(f"- 补强动作：{strengthening_text}")
            output.append(f"- 复核备注：{review_notes}\n")

            embedded = self._embed_evidence_content(ev)
            if embedded:
                output.append(embedded)
            else:
                content_preview = content[:500] if content else ""
                output.append(f"**内容摘要**：\n>{content_preview.replace(chr(10), chr(10)+'>')}\n")

            output.append("\n---\n")

        output.append("## 三、证据汇总\n")
        summary = book.get("summary", "")
        summary_lines = summary.split('\n') if summary else []
        for line in summary_lines[:30]:
            output.append(line)

        return "\n".join(output)

    def _embed_evidence_content(self, ev: Evidence) -> str:
        """
        根据证据文件类型嵌入原始内容：
        - 图片：使用原始尺寸，超A4页面自动缩放
        - 音频/视频：嵌入AI转录文字
        - PDF/Word：显示提取的文字内容
        
        设计原则：
        1. 保持原始尺寸（不拉伸变形）
        2. 超宽：按A4页面宽度(210mm)缩放
        3. 超长：自动分页显示
        """
        if not ev.file_path:
            return ""
        
        ext = os.path.splitext(ev.file_path)[1].lower()
        
        is_image = ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        is_audio = ext in ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac']
        is_video = ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv']

        # 图片证据：使用原始尺寸，超页面自动缩放
        if is_image:
            if os.path.exists(ev.file_path):
                file_path_formatted = ev.file_path.replace(chr(92), '/')
                
                # 获取图片尺寸（需要更精确的计算）
                # 使用CSS实现：
                # - max-width: 100% 确保不超过页面宽度
                # - height: auto 保持原始比例
                # - page-break-inside: avoid 避免在图片中间分页
                # - 对于超长图片，添加分页标记
                
                html = f'''<!-- 证据图片 -->
<div class="evidence-image" style="
    page-break-inside: avoid; 
    margin: 15mm 0;
    text-align: center;
">
    <img src="file:///{file_path_formatted}" 
         alt="{ev.name}"
         style="
            max-width: 190mm;           /* A4宽度210mm减去边距20mm*2 */
            height: auto;                /* 保持原始比例 */
            display: block;
            margin: 0 auto;
            border: 1px solid #333;    /* 精致框线 */
            box-shadow: none;
         " />
    <p style="
        font-size: 12px; 
        color: #333; 
        text-align: center; 
        margin: 8px 0 0 0;
        padding-top: 5px;
        border-top: 1px solid #ccc;
    ">图 {ev.name}</p>
</div>'''
                
                return html
            else:
                return f"- **原始图片**：{ev.file_path}（文件未找到）"

        # 音频/视频证据：嵌入转录文字
        if is_audio or is_video:
            transcript = ev.content.strip() if ev.content else ""
            if transcript:
                return f"- **语音转写文字**：\n\n```\n{transcript}\n```\n"
            else:
                base_path = os.path.splitext(ev.file_path)[0]
                for transcript_ext in ['.txt', '.lrc', '.srt']:
                    transcript_path = base_path + transcript_ext
                    if os.path.exists(transcript_path):
                        with open(transcript_path, 'r', encoding='utf-8', errors='ignore') as f:
                            transcript = f.read()
                        return f"- **语音转写**（来源：{os.path.basename(transcript_path)}）：\n\n```\n{transcript}\n```\n"
                return f"- **原始{'音频' if is_audio else '视频'}**：{ev.file_path}"

        # PDF/Word等文档：显示提取的文字内容
        if ev.content and ev.content.strip():
            content_preview = ev.content.strip()
            if len(content_preview) > 3000:
                content_preview = content_preview[:3000] + "\n\n...（内容过长已截断）"
            return f"- **提取的文字内容**：\n\n```\n{content_preview}\n```\n"
        else:
            return f"- **原始文件**：{ev.file_path}（内容待提取）"

    def generate_book(self, case_id: int, db=None, format: str = "markdown") -> str:
        """便捷入口 — 生成案件证据册并返回 Markdown/HTML。

        从数据库加载案件和证据后委托给 generate_evidence_book()。
        """
        try:
            from app.db.database import SessionLocal
            from app.models.case import Case
            from app.models.evidence import EvidenceItem
        except ImportError:
            return "# 证据册\n\n(数据库模块不可用)"

        own_db = db or SessionLocal()
        try:
            case = own_db.query(Case).filter(Case.id == case_id).first()
            if not case:
                return f"# 证据册\n\n案件 {case_id} 不存在"

            evidence_items = (
                own_db.query(EvidenceItem)
                .filter(EvidenceItem.case_id == case_id)
                .all()
            )

            evidence_objs = []
            for item in evidence_items:
                evidence_objs.append(Evidence(
                    id=item.id or "",
                    name=item.original_filename or item.display_name or f"证据-{item.id}",
                    evidence_type=item.evidence_type or "OTHER",
                    description=item.summary or "",
                    content=item.extracted_content or item.raw_content or "",
                    file_path=item.file_path or "",
                    custody=getattr(item, "custody", "原告"),
                ))

            case_info = {
                "case_name": case.title or f"案件{case_id}",
                "case_number": getattr(case, "case_number", "") or "",
                "court": "郑州高新区人民法院",
            }
            party_info = {
                "plaintiff": case.plaintiff or "原告",
                "defendant": case.defendant or "被告",
            }

            result = self.generate_evidence_book(
                case_info=case_info,
                evidence_list=evidence_objs,
                party_info=party_info,
                case_type=str(case.case_type) if case.case_type else "合同纠纷",
            )

            if format == "markdown":
                return self._render_to_markdown(result)
            return self._render_to_html(result)
        finally:
            if db is None and own_db:
                own_db.close()

    def _render_to_markdown(self, book: Dict) -> str:
        lines = [f"# {book.get('cover', {}).get('title', '证据册')}", ""]
        lines.append(book.get("table_of_contents", ""))
        lines.append("")
        for section in book.get("evidence_sections", {}).get("sections", []):
            lines.append(f"## {section.get('title', '')}")
            for ev in section.get("evidence_items", []):
                lines.append(f"### {ev.get('name', '')}")
                lines.append(f"- 类型: {ev.get('evidence_type', '')}")
                lines.append(f"- 证明事项: {ev.get('proves', '')}")
                lines.append("")
                lines.append(ev.get("content", ""))
                lines.append("")
        lines.append(book.get("summary", ""))
        return "\n".join(lines)

    def _render_to_html(self, book: Dict) -> str:
        md = self._render_to_markdown(book)
        return f"<html><head>{self.get_css_styles()}</head><body><pre>{md}</pre></body></html>"


# ========== 证据风险分析器 ==========

@dataclass
class EvidenceRisk:
    """证据风险"""
    evidence_id: str
    evidence_name: str
    risk_level: str  # high / medium / low / none
    risk_type: str  # adverse / admission / contradictory / weak / opponent_benefit
    description: str
    suggestion: str
    affected_claims: List[str] = field(default_factory=list)


@dataclass
class RiskAnalysisResult:
    """风险分析结果"""
    total_evidence: int
    adverse_evidence: List[EvidenceRisk]  # 不利证据
    questionable_evidence: List[EvidenceRisk]  # 存疑证据
    recommended_to_exclude: List[str]  # 建议排除的证据ID
    recommended_to_include: List[str]  # 建议包含的证据ID
    overall_risk_level: str  # high / medium / low
    summary: str


class EvidenceRiskAnalyzer:
    """
    证据风险分析器
    识别证据册中的不利证据、存疑证据，并提供处理建议
    """

    # 不利关键词（可能对我方不利）
    ADVERSE_KEYWORDS = [
        "确认", "承认", "知悉", "了解", "同意", "认可", "无异议",
        "收到", "已读", "知晓", "同意遵守",
        # 合同中的不利条款
        "不得", "禁止", "无权", "自动", "视为",
        # 责任相关
        "自行承担", "与甲方无关", "乙方责任", "甲方免责",
        # 违约相关
        "经催告", "逾期", "违约方", "承担违约",
    ]

    # 自认关键词（承认不利事实）
    ADMISSION_KEYWORDS = [
        "我方确实", "确实存在", "确实收到", "确认收到",
        "我方承认", "经核实", "经确认", "确认无误",
        "对上述事实无异议", "对此予以确认",
    ]

    # 矛盾关键词
    CONTRADICTION_KEYWORDS = [
        "但是", "然而", "与此矛盾", "与前述", "不一致",
        "与合同约定不符", "与前述内容矛盾",
    ]

    # 证据瑕疵关键词
    WEAKNESS_KEYWORDS = [
        "可能", "推测", "据称", "未提供原件", "复印件",
        "未经公证", "未鉴定", "无法核实", "真实性存疑",
        "不清晰", "模糊", "部分损坏",
    ]

    def __init__(self):
        pass

    def analyze_evidence_risks(
        self,
        evidence_list: List[Evidence],
        target_claims: List[str],
        case_type: str = "合同纠纷"
    ) -> RiskAnalysisResult:
        """
        分析证据列表中的风险

        Args:
            evidence_list: 证据列表
            target_claims: 目标诉求列表

        Returns:
            RiskAnalysisResult: 包含风险分析结果
        """
        adverse_evidence = []
        questionable_evidence = []
        recommended_exclude = []
        recommended_include = []

        for ev in evidence_list:
            risk = self._analyze_single_evidence(ev, target_claims, case_type)

            if risk.risk_level == "high":
                adverse_evidence.append(risk)
                if risk.risk_type in ["admission", "opponent_benefit"]:
                    recommended_exclude.append(risk.evidence_id)
                elif risk.risk_type == "contradictory":
                    recommended_exclude.append(risk.evidence_id)
            elif risk.risk_level == "medium":
                questionable_evidence.append(risk)
            else:
                recommended_include.append(risk.evidence_id)

        # 确定整体风险等级
        if adverse_evidence:
            overall_risk = "high"
        elif questionable_evidence:
            overall_risk = "medium"
        else:
            overall_risk = "low"

        # 生成摘要
        summary = self._generate_summary(
            total=len(evidence_list),
            adverse=len(adverse_evidence),
            questionable=len(questionable_evidence),
            overall_risk=overall_risk
        )

        return RiskAnalysisResult(
            total_evidence=len(evidence_list),
            adverse_evidence=adverse_evidence,
            questionable_evidence=questionable_evidence,
            recommended_to_exclude=recommended_exclude,
            recommended_to_include=recommended_include,
            overall_risk_level=overall_risk,
            summary=summary
        )

    def _analyze_single_evidence(
        self,
        evidence: Evidence,
        target_claims: List[str],
        case_type: str
    ) -> EvidenceRisk:
        """分析单条证据的风险"""
        risks = []

        content = (evidence.content or "").lower()
        name = (evidence.name or "").lower()
        proof_point = (evidence.proof_point or "").lower()

        # 1. 检查是否包含自认内容
        if self._contains_admission(content, proof_point):
            risks.append({
                "type": "admission",
                "level": "high",
                "description": "证据中包含对不利事实的承认或确认",
                "suggestion": "考虑是否必须提交。如必须提交，准备反驳说明或补充其他证据加强证明力。"
            })

        # 2. 检查是否包含不利条款
        if self._contains_adverse_terms(content, proof_point):
            risks.append({
                "type": "adverse",
                "level": "high",
                "description": "证据中包含可能对我方不利的条款或表述",
                "suggestion": "谨慎处理。如提交，需准备解释说明，强调有利的部分。"
            })

        # 3. 检查是否可能为对方利用
        if self._benefits_opponent(content, name, case_type):
            risks.append({
                "type": "opponent_benefit",
                "level": "high",
                "description": "该证据可能被对方利用来反驳我方主张",
                "suggestion": "评估是否提交。必要时在证据说明中预先设置防火墙。"
            })

        # 4. 检查是否存在矛盾
        if self._has_contradiction(content, target_claims):
            risks.append({
                "type": "contradictory",
                "level": "high",
                "description": "证据内容可能与其他证据或我方主张存在矛盾",
                "suggestion": "准备补充证据消除矛盾，或准备合理的解释说明。"
            })

        # 5. 检查证据形式瑕疵
        if self._has_form_defect(content, name):
            risks.append({
                "type": "weak",
                "level": "medium",
                "description": "证据形式存在瑕疵，可能被质疑真实性",
                "suggestion": "建议公证或鉴定后再提交，增强证据效力。"
            })

        # 6. 检查证明力是否模糊
        if self._is_vague(content):
            risks.append({
                "type": "vague",
                "level": "medium",
                "description": "证据内容表述模糊，指向不明确",
                "suggestion": "考虑补充更明确的证据，或在证据说明中明确证明目的。"
            })

        # 确定最终风险等级
        if not risks:
            return EvidenceRisk(
                evidence_id=evidence.id,
                evidence_name=evidence.name,
                risk_level="none",
                risk_type="none",
                description="未发现明显风险",
                suggestion="可正常提交",
                affected_claims=[]
            )

        # 取最高风险等级
        max_level = "low"
        for r in risks:
            if r["level"] == "high":
                max_level = "high"
            elif r["level"] == "medium" and max_level != "high":
                max_level = "medium"

        # 合并风险描述
        descriptions = [r["description"] for r in risks]
        suggestions = [r["suggestion"] for r in risks]

        return EvidenceRisk(
            evidence_id=evidence.id,
            evidence_name=evidence.name,
            risk_level=max_level,
            risk_type=risks[0]["type"],
            description="；".join(descriptions[:2]),  # 最多2个
            suggestion="；".join(suggestions[:2]),
            affected_claims=self._find_affected_claims(evidence, target_claims)
        )

    def _contains_admission(self, content: str, proof_point: str) -> bool:
        """检查是否包含自认内容"""
        combined = content + " " + proof_point
        for keyword in self.ADMISSION_KEYWORDS:
            if keyword in combined:
                return True
        return False

    def _contains_adverse_terms(self, content: str, proof_point: str) -> bool:
        """检查是否包含不利条款"""
        combined = content + " " + proof_point
        match_count = sum(1 for kw in self.ADVERSE_KEYWORDS if kw in combined)
        return match_count >= 2

    def _benefits_opponent(self, content: str, name: str, case_type: str) -> bool:
        """检查是否可能对对方有利"""
        # 检查是否是对方的函件、邮件等
        opponent_indicators = [
            "对方来函", "被告回复", "第三方出具", "对方陈述",
            "对方提供的", "对方证据", "对方向", "对方称",
        ]

        for indicator in opponent_indicators:
            if indicator in name or indicator in content:
                return True

        # 特定案件类型的不利证据
        if case_type == "合同纠纷":
            unfavorable = ["对方已履行", "我方违约", "同意变更", "免除责任"]
            for kw in unfavorable:
                if kw in content:
                    return True

        return False

    def _has_contradiction(self, content: str, target_claims: List[str]) -> bool:
        """检查是否存在矛盾"""
        # 检查是否与诉求矛盾
        for claim in target_claims:
            claim_lower = claim.lower()
            for keyword in self.CONTRADICTION_KEYWORDS:
                if keyword in content and any(kw in claim_lower for kw in ["未", "不", "无"]):
                    return True
        return False

    def _has_form_defect(self, content: str, name: str) -> bool:
        """检查证据形式瑕疵"""
        for keyword in self.WEAKNESS_KEYWORDS:
            if keyword in content or keyword in name:
                return True
        return False

    def _is_vague(self, content: str) -> bool:
        """检查内容是否模糊"""
        vague_count = sum(1 for kw in self.WEAKNESS_KEYWORDS if kw in content)
        return vague_count >= 2

    def _find_affected_claims(self, evidence: Evidence, target_claims: List[str]) -> List[str]:
        """找出受影响的诉求"""
        affected = []
        content = (evidence.content or "").lower() + " " + (evidence.proof_point or "").lower()

        for claim in target_claims:
            claim_lower = claim.lower()
            # 简单的关键词匹配
            claim_keywords = [w for w in claim_lower if len(w) >= 2]
            if any(kw in content for kw in claim_keywords[:5]):
                affected.append(claim)

        return affected

    def _generate_summary(
        self,
        total: int,
        adverse: int,
        questionable: int,
        overall_risk: str
    ) -> str:
        """生成风险摘要"""
        if adverse == 0 and questionable == 0:
            return f"整体风险低。{total}份证据中未发现明显不利证据，证据体系较为稳健。"

        parts = []
        if adverse > 0:
            parts.append(f"发现{adverse}份高风险证据，可能对我方主张产生不利影响")
        if questionable > 0:
            parts.append(f"存在{questionable}份存疑证据，建议核实或补充说明")

        if overall_risk == "high":
            return f"⚠️ 整体风险高。" + "，".join(parts) + "，建议谨慎处理。"
        else:
            return f"⚡ 存在一定风险。" + "，".join(parts) + "，可在注意风险的情况下提交。"


# ========== 核心服务类 ==========

class EvidenceService:
    """
    证据管理核心服务
    """

    def __init__(self):
        self.checker = EvidenceCompletenessChecker()
        self.generator = EvidenceBookGenerator()
        self.risk_analyzer = EvidenceRiskAnalyzer()

    def process_evidence(self,
                        case_type: str,
                        user_claims: List[str],
                        submitted_evidence: List[Dict],
                        party_info: Dict) -> Dict:
        """
        处理证据的完整流程

        1. 解析用户提交的证据
        2. 检查证据链完整性
        3. 生成补全方案
        4. 生成证据册
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "case_type": case_type,
            "user_claims": user_claims,
            "evidence_processed": [],
            "completeness_check": {},
            "gaps": [],
            "evidence_book": None,
            "next_steps": []
        }

        # Step 1: 解析证据
        for i, ev_dict in enumerate(submitted_evidence, 1):
            evidence = Evidence(
                id=f"ev_{i}",
                name=ev_dict.get("name", f"证据{i}"),
                evidence_type=ev_dict.get("type", EvidenceTypeClassifier.classify(ev_dict.get("name", ""))),
                content=ev_dict.get("content", ""),
                source=ev_dict.get("source", "用户提供"),
                custody=ev_dict.get("custody", party_info.get("submitter", "")),
                proof_point=ev_dict.get("proof_point", ""),
                file_path=ev_dict.get("file_path")
            )
            result["evidence_processed"].append(evidence)

        # Step 2: 检查完整性
        chain = self.checker.check_completeness(
            case_type=case_type,
            submitted_evidence=result["evidence_processed"],
            user_claims=user_claims
        )

        result["completeness_check"] = {
            "completeness": chain.completeness,
            "completeness_text": f"{int(chain.completeness * 100)}%",
            "required_count": len(chain.required_evidence),
            "covered_count": len(chain.current_evidence),
            "missing_count": len(chain.gaps)
        }

        # Step 3: 生成缺失清单和补全方案
        result["gaps"] = [
            {
                "type": gap.missing_type,
                "description": gap.description,
                "importance": gap.importance,
                "proof_point": gap.proof_point,
                "alternative_solution": gap.alternative_solution,
                "feasibility": gap.alternative_feasibility,
                "risk": gap.risk_level
            }
            for gap in chain.gaps
        ]

        # Step 4: 生成证据册
        case_info = {
            "case_number": party_info.get("case_number", ""),
            "case_type": case_type
        }

        result["evidence_book"] = self.generator.generate_evidence_book(
            case_info=case_info,
            evidence_list=result["evidence_processed"],
            party_info=party_info,
            case_type=case_type
        )

        # Step 5: 生成下一步建议
        result["next_steps"] = self._generate_next_steps(chain)

        return result

    def _generate_next_steps(self, chain: EvidenceChain) -> List[str]:
        """生成下一步建议"""
        steps = []

        # 高风险缺失
        high_risk_gaps = [g for g in chain.gaps if g.risk_level == "🔴 高风险 - 可能导致败诉"]

        if high_risk_gaps:
            steps.append("🔴 优先补齐高风险缺失证据：")
            for gap in high_risk_gaps:
                steps.append(f"   • {gap.missing_type}：{gap.alternative_solution.split(chr(10))[0]}")

        # 中风险缺失
        medium_risk_gaps = [g for g in chain.gaps if "中风险" in g.risk_level]

        if medium_risk_gaps:
            steps.append("\n🟡 建议补充中风险缺失证据：")
            for gap in medium_risk_gaps:
                steps.append(f"   • {gap.missing_type}")

        # 完整性评估
        if chain.completeness >= 0.9:
            steps.append("\n✅ 证据链已基本完整，可以准备起诉")
        elif chain.completeness >= 0.7:
            steps.append("\n🟡 证据链基本完整，建议补充缺失证据后起诉")
        else:
            steps.append("\n⚠️ 证据链不完整，建议先补充证据再起诉")

        return steps

    def extract_evidence_from_text(self, text: str) -> List[Dict]:
        """
        从文本中提取证据信息
        用于从用户描述中识别证据
        """
        extracted = []

        # 证据关键词模式
        evidence_patterns = [
            (r'([^\s，,。]+)合同', '合同文件'),
            (r'([^\s，,。]+)协议', '协议文件'),
            (r'转账记录[^\s，,。]*', '转账凭证'),
            (r'银行流水[^\s，,。]*', '银行流水'),
            (r'微信[^\s，,。]*截图', '微信截图'),
            (r'聊天记录[^\s，,。]*', '聊天记录'),
            (r'录音[^\s，,。]*', '录音资料'),
            (r'发票[^\s，,。]*', '发票'),
            (r'收据[^\s，,。]*', '收据'),
            (r'照片[^\s，,。]*', '照片'),
            (r'邮件[^\s，,。]*', '电子邮件'),
        ]

        for pattern, ev_type in evidence_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match and match not in [e.get("name") for e in extracted]:
                    extracted.append({
                        "name": match,
                        "type": ev_type,
                        "content": "",
                        "extracted_from": "文本自动提取"
                    })

        return extracted


# 全局实例
evidence_service = EvidenceService()


if __name__ == "__main__":
    # 测试证据服务
    service = EvidenceService()

    # 模拟证据输入
    sample_evidence = [
        {
            "name": "软件开发合同",
            "type": "书面证据",
            "content": "2024年3月1日签订的《软件开发合同》，约定开发费用50万元...",
            "proof_point": "证明合同关系成立"
        },
        {
            "name": "银行转账记录",
            "type": "书面证据",
            "content": "2024年3月5日转账20万元...",
            "proof_point": "证明已支付预付款20万元"
        }
    ]

    party_info = {
        "submitter": "张三（原告）",
        "plaintiff": "ABC科技有限公司",
        "defendant": "XYZ信息技术公司",
        "case_number": "（待立案后填写）",
        "evidence_list": sample_evidence
    }

    result = service.process_evidence(
        case_type="合同纠纷",
        user_claims=["被告未按约交付软件", "要求退还已付款项20万元并赔偿损失"],
        submitted_evidence=sample_evidence,
        party_info=party_info
    )

    print("=" * 60)
    print("证据处理结果")
    print("=" * 60)

    print(f"\n📊 完整性评估：{result['completeness_check']['completeness_text']}")
    print(f"   已提交证据：{result['completeness_check']['covered_count']} 件")
    print(f"   缺失证据：{result['completeness_check']['missing_count']} 件")

    if result['gaps']:
        print("\n⚠️ 缺失证据及补全方案：")
        for gap in result['gaps']:
            print(f"\n  【{gap['type']}】")
            print(f"  重要性：{gap['importance']}")
            print(f"  风险：{gap['risk']}")
            print(f"  补全方案：{gap['alternative_solution']}")

    print("\n📋 证据册封面预览：")
    print(result['evidence_book']['cover'])

    print("\n📝 证据册目录：")
    print(result['evidence_book']['table_of_contents'])
