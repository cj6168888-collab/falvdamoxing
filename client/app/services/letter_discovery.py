"""
函件自动发现服务 - 从证据中智能识别并提取函件
扫描案件证据中的函件类文件，AI分析提取关键信息，自动生成函件记录
支持三种数据源：EvidenceItem V2、EvidenceFolderFile、Document
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
import json
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.letter import Letter, LetterDirection, LetterType, ReplyRequirement, UrgentLevel
from app.models.evidence import EvidenceItem, EvidenceType, EvidenceSourceParty
from app.models.case import Case
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

# 函件关键词匹配规则 - 覆盖所有常见函件类型
LETTER_KEYWORDS = {
    "lawyer_letter": ["律师函", "律师函告", "法律函件", "律师通知", "律师意见书"],
    "demand_letter": ["催告函", "催款函", "催款通知", "催缴函", "催讨函", "还款催告", "催收", "催收函"],
    "notice": ["通知书", "通知函", "告知函", "通知", "告知书"],
    "response": ["回复函", "答复函", "回函", "答辩函", "回应函"],
    "reminder": ["提醒函", "温馨提示", "提醒通知"],
    "warning": ["警告函", "警示函", "警告通知", "最后通牒"],
    "negotiation": ["协商函", "和解函", "调解函", "商洽函"],
    "explanation": ["说明函", "情况说明", "声明函", "澄清函"],
}

# 最宽泛的函件识别关键词 - 只要文件名或内容含这些就是函件候选
BROAD_LETTER_KEYWORDS = [
    "函", "催告", "催收", "通知", "回复", "声明", "告知",
    "lawyer letter", "demand letter", "notice letter",
]


class LetterDiscoveryService:
    """函件自动发现服务"""

    def discover_letters(self, case_id: int, db: Session) -> Dict[str, Any]:
        """
        扫描案件证据，自动发现并提取函件
        数据源优先级：EvidenceFolderFile > EvidenceItem > Document
        """
        result = {"discovered": 0, "skipped": 0, "errors": 0, "letters": []}

        # 1. 获取已存在的函件关联证据ID
        existing_evidence_ids = self._get_existing_evidence_links(case_id, db)

        # 2. 从三个数据源获取候选
        candidates = []

        # 2a. EvidenceFolderFile - 文件夹扫描记录（最常见的数据源）
        folder_candidates = self._get_folder_file_candidates(case_id, db)
        candidates.extend(folder_candidates)

        # 2b. EvidenceItem V2
        evidence_candidates = self._get_evidence_item_candidates(case_id, db)
        candidates.extend(evidence_candidates)

        # 2c. Document legacy
        doc_candidates = self._get_document_candidates(case_id, db)
        candidates.extend(doc_candidates)

        if not candidates:
            return result

        # 3. 去重（按文件名+内容哈希）
        seen = set()
        unique_candidates = []
        for c in candidates:
            key = self._get_candidate_key(c)
            if key not in seen:
                seen.add(key)
                unique_candidates.append(c)

        # 4. 逐个分析
        for evidence in unique_candidates:
            try:
                evidence_id = self._get_evidence_id(evidence)

                if evidence_id and evidence_id in existing_evidence_ids:
                    result["skipped"] += 1
                    continue

                letter_info = self._extract_letter_info(evidence)
                if not letter_info:
                    continue

                letter = self._create_letter_from_evidence(case_id, evidence, letter_info, db)
                if letter:
                    result["discovered"] += 1
                    name = self._get_candidate_name(evidence)
                    result["letters"].append({
                        "id": letter.id,
                        "title": letter.title,
                        "letter_type": letter.letter_type.value,
                        "direction": letter.direction.value,
                        "source_evidence_id": evidence_id,
                        "source_evidence_name": name,
                    })
            except Exception as e:
                logger.error(f"函件发现失败: error={e}")
                result["errors"] += 1

        return result

    def _get_folder_file_candidates(self, case_id: int, db: Session) -> List[Any]:
        """从 EvidenceFolderFile 获取候选（文件夹扫描记录）"""
        try:
            from app.models.evidence_folder import EvidenceFolderFile
            files = db.query(EvidenceFolderFile).filter(
                EvidenceFolderFile.case_id == case_id,
                EvidenceFolderFile.status == "completed"
            ).all()

            candidates = []
            for f in files:
                if self._is_letter_file(f):
                    candidates.append(f)
            return candidates
        except Exception as e:
            logger.warning(f"查询EvidenceFolderFile失败: {e}")
            return []

    def _get_evidence_item_candidates(self, case_id: int, db: Session) -> List[Any]:
        """从 EvidenceItem V2 获取候选"""
        try:
            # 放宽条件：不要求 extracted_content 非空，文件名匹配也可以
            items = db.query(EvidenceItem).filter(
                EvidenceItem.case_id == case_id,
                EvidenceItem.status.in_(["已处理", "已索引", "待处理", "处理中"])
            ).all()

            candidates = []
            for ev in items:
                if self._is_letter_evidence(ev):
                    candidates.append(ev)
            return candidates
        except Exception as e:
            logger.warning(f"查询EvidenceItem失败: {e}")
            return []

    def _get_document_candidates(self, case_id: int, db: Session) -> List[Any]:
        """从 Document legacy 获取候选"""
        try:
            from app.models.document import Document
            docs = db.query(Document).filter(
                Document.case_id == case_id
            ).all()

            candidates = []
            for doc in docs:
                if self._is_letter_document(doc):
                    candidates.append(doc)
            return candidates
        except Exception as e:
            logger.warning(f"查询Document失败: {e}")
            return []

    def _is_letter_file(self, folder_file) -> bool:
        """判断 EvidenceFolderFile 是否为函件类"""
        filename = getattr(folder_file, 'file_name', '') or ''
        category = getattr(folder_file, 'auto_category', '') or ''

        # 自动分类为 CORRESPONDENCE
        if category == "CORRESPONDENCE":
            return True

        # 文件名含"函"
        if '函' in filename:
            return True

        # 宽泛关键词匹配文件名
        for kw in BROAD_LETTER_KEYWORDS:
            if kw.lower() in filename.lower():
                return True

        # 内容匹配
        content = getattr(folder_file, 'extracted_content', '') or ''
        if content:
            for kw in BROAD_LETTER_KEYWORDS:
                if kw.lower() in content[:1000].lower():
                    return True

        return False

    def _is_letter_evidence(self, evidence: EvidenceItem) -> bool:
        """判断 EvidenceItem 是否为函件类"""
        # 1. 证据类型直接匹配
        if evidence.evidence_type == "CORRESPONDENCE":
            return True

        # 2. 文件名/显示名称匹配
        name = (evidence.display_name or evidence.original_filename or "")
        if '函' in name:
            return True
        for kw in BROAD_LETTER_KEYWORDS:
            if kw.lower() in name.lower():
                return True

        # 3. 内容关键词匹配
        content = (evidence.extracted_content or evidence.raw_content or evidence.summary or "")
        if not content:
            return False

        for kw in BROAD_LETTER_KEYWORDS:
            if kw.lower() in content[:1000].lower():
                return True

        return False

    def _is_letter_document(self, doc) -> bool:
        """判断 legacy Document 是否为函件类"""
        doc_type = getattr(doc, 'doc_type', '') or ''
        if '函' in doc_type:
            return True

        filename = getattr(doc, 'filename', '') or ''
        if '函' in filename:
            return True
        for kw in BROAD_LETTER_KEYWORDS:
            if kw.lower() in filename.lower():
                return True

        content = getattr(doc, 'content', '') or getattr(doc, 'content_summary', '') or ''
        if not content:
            return False

        for kw in BROAD_LETTER_KEYWORDS:
            if kw.lower() in content[:1000].lower():
                return True

        return False

    def _get_candidate_key(self, candidate) -> str:
        """生成候选的唯一标识用于去重"""
        name = self._get_candidate_name(candidate)
        content = self._get_candidate_content(candidate)
        content_hash = hash(content[:200]) if content else 0
        return f"{name}_{content_hash}"

    def _get_candidate_name(self, candidate) -> str:
        """获取候选名称"""
        if hasattr(candidate, 'file_name'):
            return candidate.file_name or ''
        if hasattr(candidate, 'display_name'):
            return candidate.display_name or candidate.original_filename or ''
        if hasattr(candidate, 'filename'):
            return candidate.filename or ''
        return ''

    def _get_candidate_content(self, candidate) -> str:
        """获取候选内容"""
        if hasattr(candidate, 'extracted_content') and candidate.extracted_content:
            return candidate.extracted_content
        if hasattr(candidate, 'content') and candidate.content:
            return candidate.content
        if hasattr(candidate, 'summary') and candidate.summary:
            return candidate.summary
        if hasattr(candidate, 'auto_summary') and candidate.auto_summary:
            return candidate.auto_summary
        return ''

    def _get_evidence_id(self, candidate) -> Optional[str]:
        """获取候选的证据ID"""
        if hasattr(candidate, 'evidence_id') and candidate.evidence_id:
            return str(candidate.evidence_id)
        if hasattr(candidate, 'id'):
            return str(candidate.id)
        return None

    def _get_existing_evidence_links(self, case_id: int, db: Session) -> set:
        """获取已关联证据的函件"""
        existing = set()
        try:
            letters = db.query(Letter).filter(
                Letter.case_id == case_id,
                Letter.related_evidence_ids.isnot(None)
            ).all()
            for letter in letters:
                if letter.related_evidence_ids:
                    try:
                        ids = letter.related_evidence_ids if isinstance(letter.related_evidence_ids, list) else json.loads(letter.related_evidence_ids)
                        existing.update(str(i) for i in ids)
                    except:
                        pass
        except Exception as e:
            logger.warning(f"查询已关联证据失败: {e}")
        return existing

    def _extract_letter_info(self, evidence) -> Optional[Dict]:
        """从证据内容中提取函件信息"""
        content = self._get_candidate_content(evidence)
        name = self._get_candidate_name(evidence)

        # 即使没有内容，只要有文件名含"函"，也创建基本记录
        if not content and '函' not in name:
            return None

        # 先用规则快速提取
        rule_result = self._rule_based_extract(content, name)

        # 如果规则提取不完整，用AI补充
        if (not rule_result.get('title') or not rule_result.get('letter_type') or rule_result.get('letter_type') == 'other') and len(content) > 50:
            ai_result = self._ai_extract_letter_info(content, name)
            if ai_result:
                for key, value in ai_result.items():
                    if value and not rule_result.get(key):
                        rule_result[key] = value

        # 确保至少有标题
        if not rule_result.get('title') and name:
            rule_result['title'] = name

        return rule_result if rule_result.get('title') else None

    def _rule_based_extract(self, content: str, name: str) -> Dict:
        """基于规则快速提取函件信息"""
        info = {"title": "", "letter_type": "other", "sender": "", "recipient": "", "letter_date": None, "direction": ""}

        # 提取标题
        if name:
            info["title"] = name

        if content:
            lines = content.split('\n')
            for line in lines[:10]:
                line = line.strip()
                if len(line) > 5 and len(line) < 100:
                    for keywords in LETTER_KEYWORDS.values():
                        for kw in keywords:
                            if kw in line:
                                info["title"] = line
                                break
                        if info["title"] != name:
                            break
                    if info["title"] != name:
                        break

        # 提取函件类型
        search_text = (content[:2000] if content else '') + ' ' + name
        for letter_type, keywords in LETTER_KEYWORDS.items():
            for kw in keywords:
                if kw in search_text:
                    info["letter_type"] = letter_type
                    break
            if info["letter_type"] != "other":
                break

        # 提取日期
        if content:
            date_patterns = [
                r'(\d{4})[年\-/](\d{1,2})[月\-/](\d{1,2})日?',
                r'(\d{4})\.(\d{1,2})\.(\d{1,2})',
            ]
            for pattern in date_patterns:
                match = re.search(pattern, content[:2000])
                if match:
                    try:
                        info["letter_date"] = datetime(
                            int(match.group(1)), int(match.group(2)), int(match.group(3))
                        )
                        break
                    except:
                        pass

        # 提取发送方/接收方
        if content and len(content) > 100:
            sender_patterns = [
                r'(?:发函方|发件人|发出方|致函方)[：:]\s*(.+?)(?:\n|$)',
            ]
            for pattern in sender_patterns:
                match = re.search(pattern, content[:3000])
                if match:
                    info["sender"] = match.group(1).strip()[:100]
                    break

            recipient_patterns = [
                r'(?:致|收件方|收件人|发送给)[：:]\s*(.+?)(?:\n|$)',
            ]
            for pattern in recipient_patterns:
                match = re.search(pattern, content[:3000])
                if match:
                    info["recipient"] = match.group(1).strip()[:100]
                    break

        return info

    def _ai_extract_letter_info(self, content: str, name: str) -> Optional[Dict]:
        """使用AI提取函件信息"""
        if len(content) < 50:
            return None

        prompt = f"""请分析以下文档，判断是否为法律函件，并提取关键信息。

文档名称：{name}
文档内容（前3000字）：
{content[:3000]}

请以JSON格式返回以下字段（仅返回JSON，不要其他内容）：
{{
    "title": "函件标题",
    "letter_type": "函件类型，必须是以下之一：lawyer_letter/demand_letter/notice/response/reminder/warning/negotiation/explanation/other",
    "sender": "发送方名称",
    "recipient": "接收方名称",
    "direction": "方向：incoming（收到对方函件）或outgoing（我方发出函件）",
    "content_summary": "内容摘要（100字以内）",
    "key_demands": "核心诉求（100字以内）",
    "reply_required": "是否需要回复：required/recommended/optional/not_required",
    "urgent_level": "紧急程度：critical/high/medium/low/none"
}}"""

        try:
            response = llm_service.chat([
                {"role": "system", "content": "你是法律文档分析专家，擅长从文档中提取结构化信息。请只返回JSON格式。"},
                {"role": "user", "content": prompt}
            ], model="qwen-plus")

            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"AI提取函件信息失败: {e}")

        return None

    def _create_letter_from_evidence(self, case_id: int, evidence, info: Dict, db: Session) -> Optional[Letter]:
        """从证据创建函件记录"""
        evidence_id = self._get_evidence_id(evidence)
        evidence_name = self._get_candidate_name(evidence)

        # 判断方向
        direction = info.get("direction", "")
        if direction not in ["incoming", "outgoing"]:
            source_party = getattr(evidence, 'source_party', '')
            if source_party == EvidenceSourceParty.THEIR_SIDE.value:
                direction = "incoming"
            elif source_party == EvidenceSourceParty.OUR_SIDE.value:
                direction = "outgoing"
            else:
                # EvidenceFolderFile 没有 source_party，根据文件名推断
                auto_category = getattr(evidence, 'auto_category', '') or ''
                if '对方' in evidence_name or '收到' in evidence_name:
                    direction = "incoming"
                elif '我方' in evidence_name or '发出' in evidence_name:
                    direction = "outgoing"
                else:
                    direction = "incoming"

        # 函件类型
        letter_type_str = info.get("letter_type", "other")
        try:
            letter_type = LetterType(letter_type_str)
        except:
            letter_type = LetterType.OTHER

        # 回复要求
        reply_required_str = info.get("reply_required", "optional")
        try:
            reply_required = ReplyRequirement(reply_required_str)
        except:
            reply_required = ReplyRequirement.OPTIONAL

        # 紧急程度
        urgent_level_str = info.get("urgent_level", "medium")
        try:
            urgent_level = UrgentLevel(urgent_level_str)
        except:
            urgent_level = UrgentLevel.MEDIUM

        # 内容摘要
        content_summary = info.get("content_summary", "")
        if not content_summary:
            content = self._get_candidate_content(evidence)
            content_summary = content[:500] if content else ""

        # 核心诉求
        key_demands = info.get("key_demands", "")
        if not key_demands:
            proves_facts = getattr(evidence, 'proves_facts', None)
            if proves_facts:
                try:
                    facts = proves_facts if isinstance(proves_facts, list) else json.loads(proves_facts)
                    key_demands = "; ".join(str(f.get("fact", "")) for f in facts[:3] if f.get("fact"))
                except:
                    key_demands = ""

        # 关联证据ID
        related_evidence_ids = [evidence_id] if evidence_id else []

        letter = Letter(
            case_id=case_id,
            direction=LetterDirection(direction),
            letter_type=letter_type,
            title=info.get("title", evidence_name or "未命名函件"),
            sender=info.get("sender") or None,
            recipient=info.get("recipient") or None,
            letter_date=info.get("letter_date"),
            received_date=datetime.now() if direction == "incoming" else None,
            content_summary=content_summary or None,
            key_demands=key_demands or None,
            reply_required=reply_required,
            urgent_level=urgent_level,
            related_evidence_ids=related_evidence_ids,
            mail_status="draft",
        )

        db.add(letter)
        db.commit()
        db.refresh(letter)
        return letter


# 全局实例
letter_discovery_service = LetterDiscoveryService()
