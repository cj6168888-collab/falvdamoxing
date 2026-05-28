"""
资深律师思维引擎
让AI像经验丰富的律师一样分析案件
"""
import json
import uuid
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.evidence import EvidenceItem, EvidenceRelationship, EvidenceFact
from app.models.case import Case, CaseThread, Party
from app.db.database import SessionLocal


class SeniorLawyerEngine:
    """
    资深律师思维引擎
    模拟经验丰富律师的思维方式，提供深度案件分析
    """

    # 法律要件库 (按案件类型)
    LEGAL_REQUIREMENTS = {
        'CONTRACT_DISPUTE': {
            '合同成立': {
                '要件': ['要约', '承诺', '意思表示一致'],
                '证据要求': ['合同文本', '磋商记录', '履行行为'],
                '常见问题': ['合同是否签字盖章', '是否超期未表示异议']
            },
            '合同效力': {
                '要件': ['主体适格', '意思表示真实', '内容合法'],
                '证据要求': ['主体证明', '行为能力证明', '合法性依据'],
                '常见问题': ['是否欺诈胁迫', '是否重大误解', '是否显失公平']
            },
            '合同履行': {
                '要件': ['履行行为', '履行期限', '履行地点', '履行方式'],
                '证据要求': ['履行凭证', '验收记录', '变更协议'],
                '常见问题': ['是否按约履行', '是否存在瑕疵履行', '是否有拒绝履行']
            },
            '违约责任': {
                '要件': ['违约行为', '损害事实', '因果关系', '过错'],
                '证据要求': ['违约事实证据', '损失计算依据', '过错证明'],
                '常见问题': ['违约金是否过高', '损失如何计算', '是否可以减轻责任']
            }
        },
        'TORT_DISPUTE': {
            '侵权构成': {
                '要件': ['行为', '过错', '损害', '因果关系'],
                '证据要求': ['侵权行为证据', '损害结果证明', '因果关系鉴定'],
                '常见问题': ['行为是否违法', '过错程度', '损害范围']
            },
            '责任主体': {
                '要件': ['直接责任人', '替代责任人', '连带责任人'],
                '证据要求': ['身份关系证明', '责任依据'],
                '常见问题': ['是否多个责任主体', '责任如何分配']
            }
        },
        'LABOR_DISPUTE': {
            '劳动关系': {
                '要件': ['主体资格', '管理从属', '业务组成'],
                '证据要求': ['劳动合同', '考勤记录', '工资流水'],
                '常见问题': ['是否存在劳动关系', '是否非全日制', '是否劳务派遣']
            },
            '劳动报酬': {
                '要件': ['劳动付出', '报酬约定', '未付事实'],
                '证据要求': ['工资记录', '加班证据', '提成约定'],
                '常见问题': ['工资标准', '加班费计算', '奖金提成']
            },
            '解除终止': {
                '要件': ['解除事由', '通知程序', '经济补偿'],
                '证据要求': ['解除通知', '违纪证据', '补偿计算依据'],
                '常见问题': ['是否违法解除', '是否提前通知', '补偿金计算']
            }
        },
        'GENERIC': {
            '基本事实': {
                '要件': ['时间', '地点', '人物', '行为', '结果'],
                '证据要求': ['时间证明', '地点证明', '身份证明', '行为证据', '结果证据'],
                '常见问题': ['事实是否清楚', '关键要素是否缺失']
            },
            '法律关系': {
                '要件': ['主体', '客体', '内容', '变动'],
                '证据要求': ['主体资格', '关系依据', '内容约定', '变动证明'],
                '常见问题': ['法律关系性质', '权利义务内容']
            },
            '争议焦点': {
                '要件': ['主张', '抗辩', '举证', '质证'],
                '证据要求': ['主张依据', '抗辩理由', '证据清单', '质证意见'],
                '常见问题': ['争议点归纳', '举证责任分配']
            }
        }
    }

    # 问题严重程度
    SEVERITY_LEVELS = {
        'critical': {'name': '严重', 'icon': '🔴', 'color': '#f5222d'},
        'important': {'name': '重要', 'icon': '🟡', 'color': '#faad14'},
        'normal': {'name': '一般', 'icon': '🔵', 'color': '#1890ff'},
        'info': {'name': '提示', 'icon': 'ℹ️', 'color': '#52c41a'}
    }

    def __init__(self, llm_service=None):
        self.llm = llm_service

    def _get_db(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()

    # ==================== 主入口 ====================

    def analyze_case(self, case_id: int, analysis_level: str = 'standard') -> dict:
        """
        全面案件分析

        Args:
            case_id: 案件ID
            analysis_level: 分析深度 (quick/standard/deep)

        Returns:
            完整分析报告
        """
        db = self._get_db()
        try:
            # 1. 获取案件信息
            case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                return {'status': 'error', 'message': '案件不存在'}

            # 2. 案件理解
            case_understanding = self._understand_case(db, case)

            # 3. 证据盘点
            evidence_inventory = self._inventory_evidence(db, case_id)

            # 4. 要件核对
            requirements_check = self._check_legal_requirements(
                db, case, case_understanding, evidence_inventory
            )

            # 5. 问题发现
            issues = self._discover_issues(
                db, case, requirements_check, evidence_inventory
            )

            # 6. 风险评估
            risk_assessment = self._assess_risks(
                case, issues, evidence_inventory
            )

            # 7. 生成建议
            recommendations = self._generate_recommendations(
                issues, requirements_check, risk_assessment
            )

            return {
                'status': 'success',
                'case_understanding': case_understanding,
                'evidence_inventory': evidence_inventory,
                'requirements_check': requirements_check,
                'issues': issues,
                'risk_assessment': risk_assessment,
                'recommendations': recommendations,
                'summary': self._generate_summary(
                    case_understanding, issues, recommendations
                )
            }

        except Exception as e:
            return {'status': 'error', 'message': str(e)}
        finally:
            db.close()

    # ==================== 案件理解 ====================

    def _understand_case(self, db: Session, case: Case) -> dict:
        """
        案件理解 - 识别案件类型、争议焦点
        """
        # 获取当事人
        parties = db.query(Party).filter(Party.case_id == case.id).all()

        # 获取线索
        threads = db.query(CaseThread).filter(CaseThread.case_id == case.id).all()

        # 分析案件类型
        case_category = self._classify_case_type(case)

        # 提取关键信息
        understanding = {
            'case_id': case.id,
            'case_number': case.case_number,
            'title': case.title,
            'case_type': case_category,
            'cause': case.cause,
            'description': case.description,
            'claim_amount': case.claim_amount,
            'plaintiff': case.plaintiff,
            'defendant': case.defendant,
            'parties': [{'name': p.name, 'role': p.role.value if hasattr(p.role, 'value') else str(p.role)}
                       for p in parties],
            'threads': [{'name': t.name, 'status': t.status.value if hasattr(t.status, 'value') else str(t.status)}
                       for t in threads],
            'core_disputes': self._identify_core_disputes(case, threads),
            'key_facts': self._extract_key_facts(case),
            'timeline': self._build_timeline(case),
            'uncertain_aspects': self._identify_uncertain_aspects(case, threads)
        }

        return understanding

    def _classify_case_type(self, case: Case) -> dict:
        """分类案件类型"""
        cause = (case.cause or '').lower()
        description = (case.description or '').lower()

        combined_text = cause + ' ' + description

        # 关键词匹配
        if any(kw in combined_text for kw in ['合同', '协议', '违约', '解除', '转让']):
            category = 'CONTRACT_DISPUTE'
            category_name = '合同纠纷'
        elif any(kw in combined_text for kw in ['侵权', '伤害', '损害', '赔偿']):
            category = 'TORT_DISPUTE'
            category_name = '侵权纠纷'
        elif any(kw in combined_text for kw in ['劳动', '工资', '解除', '加班', '工伤']):
            category = 'LABOR_DISPUTE'
            category_name = '劳动纠纷'
        else:
            category = 'GENERIC'
            category_name = '一般民事'

        return {
            'category': category,
            'category_name': category_name,
            'subcategory': self._classify_subcategory(combined_text)
        }

    def _classify_subcategory(self, text: str) -> str:
        """子分类"""
        subcategories = {
            '买卖合同': ['买卖', '购买', '销售', '货物'],
            '借款合同': ['借款', '贷款', '还款', '利息', '欠款'],
            '租赁合同': ['租赁', '租金', '出租', '承租'],
            '服务合同': ['服务', '委托', '中介', '居间'],
            '劳动合同': ['劳动', '工资', '社保', '工伤'],
            '婚姻家庭': ['婚姻', '离婚', '抚养', '继承']
        }

        for subcategory, keywords in subcategories.items():
            if any(kw in text for kw in keywords):
                return subcategory

        return '其他'

    def _identify_core_disputes(self, case: Case, threads: List) -> List[str]:
        """识别核心争议"""
        disputes = []

        # 从案由推断
        cause = case.cause or ''
        if '欠款' in cause or '借款' in cause:
            disputes.append('是否存在借款关系')
        if '违约' in cause:
            disputes.append('是否存在违约行为')
        if '解除' in cause:
            disputes.append('是否符合解除条件')

        # 从线索获取
        for thread in threads:
            if thread.description:
                disputes.append(thread.description[:50])

        return list(set(disputes))[:5]

    def _extract_key_facts(self, case: Case) -> List[str]:
        """提取关键事实"""
        facts = []

        if case.description:
            facts.append(case.description)

        if case.claim_amount:
            facts.append(f"诉讼金额：{case.claim_amount}")

        return facts

    def _build_timeline(self, case: Case) -> List[dict]:
        """构建时间线"""
        timeline = []

        if case.filed_date:
            timeline.append({
                'date': case.filed_date,
                'event': '立案',
                'importance': 'high'
            })

        if case.trial_date:
            timeline.append({
                'date': case.trial_date,
                'event': '开庭',
                'importance': 'high'
            })

        return timeline

    def _identify_uncertain_aspects(self, case: Case, threads: List) -> List[str]:
        """识别不确定方面"""
        uncertain = []

        if not case.description:
            uncertain.append('案件事实描述不完整')

        if not case.plaintiff:
            uncertain.append('原告信息缺失')

        if not case.defendant:
            uncertain.append('被告信息缺失')

        if not threads:
            uncertain.append('案件线索未梳理')

        return uncertain

    # ==================== 证据盘点 ====================

    def _inventory_evidence(self, db: Session, case_id: int) -> dict:
        """
        证据全面盘点
        """
        evidence_list = db.query(EvidenceItem).filter(
            EvidenceItem.case_id == case_id,
            EvidenceItem.is_current == True
        ).all()

        # 分类统计
        by_type = {}
        by_source = {}
        by_credibility = {'high': [], 'medium': [], 'low': []}

        total_credibility = 0

        for ev in evidence_list:
            # 按类型
            ev_type = ev.evidence_type
            if ev_type not in by_type:
                by_type[ev_type] = []
            by_type[ev_type].append(self._evidence_summary(ev))

            # 按来源
            source = ev.source_party
            if source not in by_source:
                by_source[source] = 0
            by_source[source] += 1

            # 按信度
            cs = ev.credibility_score
            if cs >= 70:
                by_credibility['high'].append(ev.id)
            elif cs >= 40:
                by_credibility['medium'].append(ev.id)
            else:
                by_credibility['low'].append(ev.id)

            total_credibility += cs

        # 证据与要件对应
        evidence_mapping = self._map_evidence_to_requirements(evidence_list)

        return {
            'total': len(evidence_list),
            'by_type': {
                'counts': {k: len(v) for k, v in by_type.items()},
                'details': by_type
            },
            'by_source': by_source,
            'by_credibility': {
                'counts': {k: len(v) for k, v in by_credibility.items()},
                'ids': by_credibility
            },
            'avg_credibility': total_credibility / len(evidence_list) if evidence_list else 0,
            'evidence_mapping': evidence_mapping,
            'strongest_evidence': self._find_strongest_evidence(evidence_list),
            'weakest_evidence': self._find_weakest_evidence(evidence_list)
        }

    def _evidence_summary(self, ev: EvidenceItem) -> dict:
        """
        证据摘要 - 法律应用专用。

        资深分析接口面向“分析结果”展示，不应把证据全文原样混入输出。
        否则用户上传的草稿、AI分析稿、未核验类案会被下游误当成系统结论。
        """
        text = ev.extracted_content or ev.raw_content or ev.summary or ''
        return {
            'id': ev.id,
            'name': ev.display_name or ev.original_filename or '未命名证据',
            'type': ev.evidence_type,
            'summary': self._trim_text(ev.summary or text, 1200),
            'content_excerpt': self._trim_text(text, 1200),
            'unverified_legal_reference_warning': self._has_unverified_case_reference(text),
            'credibility': ev.credibility_score,
            'proves_facts': [f.get('fact', '') for f in (ev.proves_facts or [])]
        }

    def _trim_text(self, text: str, limit: int) -> str:
        """限制接口输出体积，保留足够人工核对的摘录。"""
        text = (text or '').strip()
        if len(text) <= limit:
            return text
        return text[:limit] + f"\n（内容较长，已截取前{limit}字；完整内容请在证据详情中核对。）"

    def _has_unverified_case_reference(self, text: str) -> bool:
        """标记证据/材料中出现的具体案号，提示不得当作已核验类案。"""
        if not text:
            return False
        return bool(re.search(r"（20\d{2}）[^\s，。；：、\n]{2,40}号|指导案例\d+号|典型案例[-\d]+", text))

    def _map_evidence_to_requirements(self, evidence_list: List) -> dict:
        """将证据映射到法律要件"""
        mapping = {}

        for ev in evidence_list:
            proves = ev.proves_facts or []
            for pf in proves:
                fact = pf.get('fact', '')
                if fact:
                    if fact not in mapping:
                        mapping[fact] = []
                    mapping[fact].append({
                        'evidence_id': ev.id,
                        'credibility': ev.credibility_score,
                        'type': ev.evidence_type
                    })

        return mapping

    def _find_strongest_evidence(self, evidence_list: List) -> dict:
        """找最强证据"""
        if not evidence_list:
            return None

        strongest = max(evidence_list, key=lambda x: x.credibility_score)
        return self._evidence_summary(strongest)

    def _find_weakest_evidence(self, evidence_list: List) -> dict:
        """找最弱证据"""
        if not evidence_list:
            return None

        weakest = min(evidence_list, key=lambda x: x.credibility_score)
        return self._evidence_summary(weakest)

    # ==================== 要件核对 ====================

    def _check_legal_requirements(
        self,
        db: Session,
        case: Case,
        case_understanding: dict,
        evidence_inventory: dict
    ) -> dict:
        """
        法律要件逐一核对
        """
        category = case_understanding['case_type']['category']
        requirements = self.LEGAL_REQUIREMENTS.get(
            category, self.LEGAL_REQUIREMENTS['GENERIC']
        )

        check_results = []
        total_gaps = []

        for req_name, req_detail in requirements.items():
            result = {
                'requirement': req_name,
                'elements': req_detail['要件'],
                'evidence_required': req_detail['证据要求'],
                'common_issues': req_detail.get('常见问题', []),
                'status': 'pending',
                'covered_elements': [],
                'missing_elements': [],
                'evidence_coverage': [],
                'gaps': [],
                'suggestions': []
            }

            # 检查每个要件
            for element in req_detail['要件']:
                # 在证据映射中查找
                evidence_map = evidence_inventory.get('evidence_mapping', {})

                # 简单匹配
                found = False
                for fact, evidence_list in evidence_map.items():
                    if element in fact:
                        result['covered_elements'].append({
                            'element': element,
                            'evidence': evidence_list
                        })
                        found = True
                        break

                if not found:
                    result['missing_elements'].append(element)
                    total_gaps.append({
                        'requirement': req_name,
                        'element': element
                    })

            # 评定状态
            coverage_rate = len(result['covered_elements']) / len(req_detail['要件']) if req_detail['要件'] else 0

            if not result['missing_elements']:
                result['status'] = 'complete'
                result['suggestions'].append('要件基本完备')
            elif coverage_rate >= 0.5:
                result['status'] = 'partial'
                result['gaps'].append('部分要件证据不足')
                result['suggestions'].append('建议补充关键要件的证据')
            else:
                result['status'] = 'incomplete'
                result['gaps'].append('核心要件证据严重缺失')
                result['suggestions'].append('必须补充核心要件证据')

            check_results.append(result)

        # 计算整体覆盖率
        total_elements = sum(len(r['elements']) for r in check_results)
        covered_elements = sum(len(r['covered_elements']) for r in check_results)
        overall_coverage = covered_elements / total_elements if total_elements > 0 else 0

        return {
            'requirements': check_results,
            'overall_coverage': overall_coverage,
            'total_gaps': total_gaps,
            'coverage_level': self._get_coverage_level(overall_coverage)
        }

    def _get_coverage_level(self, coverage: float) -> str:
        """获取覆盖率等级"""
        if coverage >= 0.9:
            return 'excellent'
        elif coverage >= 0.7:
            return 'good'
        elif coverage >= 0.5:
            return 'fair'
        else:
            return 'poor'

    # ==================== 问题发现 ====================

    def _discover_issues(
        self,
        db: Session,
        case: Case,
        requirements_check: dict,
        evidence_inventory: dict
    ) -> dict:
        """
        发现问题 - 证据缺口、论证薄弱、程序瑕疵、时效风险
        """
        issues = {
            'evidence_gaps': [],
            'weak_arguments': [],
            'procedure_issues': [],
            'risk_points': []
        }

        # 1. 证据缺口
        for gap in requirements_check.get('total_gaps', []):
            issues['evidence_gaps'].append({
                'fact': gap.get('element', ''),
                'requirement': gap.get('requirement', ''),
                'severity': 'critical',
                'suggestion': f'需要补充证明"{gap.get("element")}"的证据',
                'obtain_method': self._suggest_obtain_method(gap.get('element', ''))
            })

        # 2. 信度不足的证据
        low_credibility = evidence_inventory.get('by_credibility', {}).get('low', {}).get('ids', [])
        if low_credibility:
            issues['weak_arguments'].append({
                'issue': f'{len(low_credibility)}份证据信度较低',
                'weakness': '证据证明力不足，可能影响论证',
                'strengthening': '建议补充原件、加强印证、或申请鉴定'
            })

        # 3. 程序问题检查
        procedure_issues = self._check_procedure_issues(case)
        issues['procedure_issues'] = procedure_issues

        # 4. 时效风险
        if case.filed_date:
            age_days = (datetime.now() - case.filed_date.replace(tzinfo=None)).days
            if age_days > 365:
                issues['risk_points'].append({
                    'point': f'案件已进行{age_days}天',
                    'probability': 'medium',
                    'impact': 'high',
                    'mitigation': '注意诉讼时效风险，及时推进程序'
                })

        return issues

    def _suggest_obtain_method(self, element: str) -> str:
        """建议获取方法"""
        methods = {
            '要约': '提供合同文本、磋商记录',
            '承诺': '提供合同文本、邮件确认',
            '主体适格': '提供营业执照、身份证明',
            '意思表示': '提供录音录像、书面文件',
            '违约行为': '提供对方违约的函件、记录',
            '损害事实': '提供损失清单、评估报告',
            '因果关系': '提供鉴定意见、专家证言'
        }

        for key, method in methods.items():
            if key in element:
                return method

        return '建议通过书面文件、电子数据、证人证言等方式获取'

    def _check_procedure_issues(self, case: Case) -> List[dict]:
        """检查程序问题"""
        issues = []

        # 检查必要字段
        case_status = case.status.value if hasattr(case.status, 'value') else str(case.status) if case.status else ''
        if not case.case_number and case_status not in ['RECEIVED', 'REVIEWING']:
            issues.append({
                'issue': '案件尚未正式立案',
                'risk': 'high',
                'suggestion': '尽快完成立案程序'
            })

        if not case.plaintiff:
            issues.append({
                'issue': '原告信息缺失',
                'risk': 'medium',
                'suggestion': '补充原告信息'
            })

        if not case.defendant:
            issues.append({
                'issue': '被告信息缺失',
                'risk': 'high',
                'suggestion': '补充被告信息以确定管辖'
            })

        return issues

    # ==================== 风险评估 ====================

    def _assess_risks(
        self,
        case: Case,
        issues: dict,
        evidence_inventory: dict
    ) -> dict:
        """
        风险评估
        """
        risks = {
            'overall_level': 'medium',
            'risk_items': [],
            'mitigation_strategies': []
        }

        # 评估证据风险
        evidence_count = evidence_inventory.get('total', 0)
        if evidence_count < 3:
            risks['risk_items'].append({
                'type': '证据不足',
                'level': 'high',
                'description': f'证据数量仅{evidence_count}份，可能难以支撑诉讼请求',
                'mitigation': '立即着手收集关键证据'
            })

        # 评估论证风险
        coverage = issues.get('requirements_check', {}).get('overall_coverage', 1.0)
        if coverage < 0.5:
            risks['risk_items'].append({
                'type': '要件证据不足',
                'level': 'high',
                'description': f'要件覆盖率仅{coverage*100:.0f}%，论证基础薄弱',
                'mitigation': '优先补充核心要件的证据'
            })

        # 评估时间风险
        if case.trial_date:
            days_to_trial = (case.trial_date.replace(tzinfo=None) - datetime.now()).days
            if days_to_trial < 7:
                risks['risk_items'].append({
                    'type': '准备时间紧迫',
                    'level': 'medium',
                    'description': f'距离开庭仅剩{days_to_trial}天',
                    'mitigation': '加快证据整理和文书准备'
                })

        # 综合评级
        high_risks = sum(1 for r in risks['risk_items'] if r['level'] == 'high')
        if high_risks >= 3:
            risks['overall_level'] = 'high'
        elif high_risks >= 1:
            risks['overall_level'] = 'medium'
        else:
            risks['overall_level'] = 'low'

        return risks

    # ==================== 建议生成 ====================

    def _generate_recommendations(
        self,
        issues: dict,
        requirements_check: dict,
        risk_assessment: dict
    ) -> List[dict]:
        """
        生成综合建议
        """
        recommendations = []

        # 1. 证据补充建议（按优先级）
        for gap in issues.get('evidence_gaps', [])[:5]:
            if gap.get('severity') == 'critical':
                recommendations.append({
                    'type': 'evidence',
                    'priority': 'critical',
                    'action': f"补充证据：{gap.get('fact')}",
                    'suggestion': gap.get('suggestion', ''),
                    'obtain_method': gap.get('obtain_method', ''),
                    'deadline': '紧急'
                })

        # 2. 论证加强建议
        for weak in issues.get('weak_arguments', [])[:3]:
            recommendations.append({
                'type': 'argument',
                'priority': 'important',
                'action': f"加强论证：{weak.get('issue')}",
                'suggestion': weak.get('strengthening', '')
            })

        # 3. 程序补救建议
        for issue in issues.get('procedure_issues', []):
            if issue.get('risk') in ['high', 'medium']:
                recommendations.append({
                    'type': 'procedure',
                    'priority': 'important' if issue.get('risk') == 'high' else 'normal',
                    'action': f"补救程序：{issue.get('issue')}",
                    'suggestion': issue.get('suggestion', '')
                })

        # 4. 风险管理
        for risk in risk_assessment.get('risk_items', []):
            recommendations.append({
                'type': 'risk',
                'priority': 'important' if risk.get('level') == 'high' else 'normal',
                'action': f"管控风险：{risk.get('type')}",
                'suggestion': risk.get('mitigation', '')
            })

        # 按优先级排序
        priority_order = {'critical': 0, 'important': 1, 'normal': 2}
        recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'normal'), 2))

        return recommendations

    def _generate_summary(
        self,
        case_understanding: dict,
        issues: dict,
        recommendations: list
    ) -> dict:
        """
        生成分析摘要
        """
        critical_count = sum(1 for r in recommendations if r.get('priority') == 'critical')
        important_count = sum(1 for r in recommendations if r.get('priority') == 'important')

        return {
            'case_type': case_understanding['case_type']['category_name'],
            'core_disputes': case_understanding['core_disputes'][:3],
            'evidence_summary': {
                'total': len(issues.get('evidence_gaps', [])),
                'critical_gaps': critical_count,
                'important_gaps': important_count
            },
            'top_recommendations': recommendations[:3],
            'overall_assessment': self._get_overall_assessment(critical_count, important_count)
        }

    def _get_overall_assessment(self, critical: int, important: int) -> str:
        """获取整体评估"""
        if critical >= 3:
            return '案件准备严重不足，需要立即补充关键证据'
        elif critical >= 1:
            return '案件存在重要缺口，建议优先解决'
        elif important >= 3:
            return '案件基本可行，但需要完善论证'
        else:
            return '案件准备较为充分，可以推进'


# 单例
senior_lawyer_engine = SeniorLawyerEngine()
