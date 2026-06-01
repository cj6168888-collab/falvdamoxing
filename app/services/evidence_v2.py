"""
证据服务 V2
完整的证据处理引擎：智能分类、信度评估、去重检查、关系分析
"""
import os
import json
import hashlib
import re
import uuid
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.evidence import (
    EvidenceItem, EvidenceRelationship, EvidenceFact,
    EvidenceDuplicateCheck, EvidenceKeywordIndex,
    EvidenceType, EvidenceSourceParty, EvidenceStatus
)
from app.models.case import Case
from app.models.document import Document
from app.models.letter import Letter, LetterType, LetterDirection
from app.services.letter_discovery import LetterDiscoveryService
from app.db.database import SessionLocal
from app.config import settings


class EvidenceServiceV2:
    """
    证据服务 V2
    完整的证据处理流程，支持去重、智能分类、信度评估、关系分析
    """

    # 证据类型信息
    EVIDENCE_TYPES = {
        'CONTRACT': {'name': '合同协议类', 'icon': '📄', 'color': '#1890ff'},
        'CORRESPONDENCE': {'name': '函件沟通类', 'icon': '📧', 'color': '#52c41a'},
        'PAYMENT': {'name': '支付凭证类', 'icon': '💰', 'color': '#faad14'},
        'IDENTITY': {'name': '身份证明类', 'icon': '🪪', 'color': '#722ed1'},
        'AUDIO_VIDEO': {'name': '视听资料类', 'icon': '🎬', 'color': '#eb2f96'},
        'TESTIMONY': {'name': '证人证言类', 'icon': '👤', 'color': '#13c2c2'},
        'EXPERT': {'name': '鉴定意见类', 'icon': '🔬', 'color': '#2f54d2'},
        'DOCUMENT': {'name': '书证类', 'icon': '📃', 'color': '#fa8c16'},
        'MATERIAL': {'name': '物证类', 'icon': '📦', 'color': '#8c8c8c'},
        'OTHER': {'name': '其他类', 'icon': '📎', 'color': '#bfbfbf'},
    }

    # 关系类型信息
    RELATIONSHIP_TYPES = {
        'SUPPORT': {'name': '支持关系', 'description': '证明同一事实', 'color': '#52c41a'},
        'CONTRADICT': {'name': '矛盾关系', 'description': '证明相反事实', 'color': '#f5222d'},
        'SUPPLEMENT': {'name': '补充关系', 'description': '补强其他证据', 'color': '#1890ff'},
        'DERIVE': {'name': '派生关系', 'description': '派生于其他证据', 'color': '#722ed1'},
        'DEPEND': {'name': '依赖关系', 'description': '依赖其他证据生效', 'color': '#faad14'}
    }

    # 去重相似度阈值
    DUPLICATE_SIMILARITY_THRESHOLD = 0.85  # 高于此值视为重复
    SUSPECTED_SIMILARITY_THRESHOLD = 0.70  # 高于此值视为疑似重复

    def __init__(self, llm_service=None):
        self.llm = llm_service
        self.db = SessionLocal()

    def _get_db(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()

    # ==================== 核心处理流程 ====================

    def process_evidence(
        self,
        case_id: int,
        source_type: str = 'file',
        content: str = None,
        file_path: str = None,
        original_filename: str = None,
        source_party: str = '己方',
        metadata: dict = None
    ) -> dict:
        """
        完整的证据处理流程

        Args:
            case_id: 案件ID
            source_type: 来源类型 (file/text/input)
            content: 文本内容
            file_path: 文件路径
            original_filename: 原始文件名
            source_party: 来源方 (己方/对方/第三方/法院)
            metadata: 其他元数据

        Returns:
            处理结果
        """
        db = self._get_db()
        try:
            # 1. 去重检查
            duplicate_check = self._check_duplicate(db, case_id, content, file_path)

            if duplicate_check['is_duplicate']:
                existing = db.query(EvidenceItem).filter(
                    EvidenceItem.id == duplicate_check['existing_id']
                ).first()

                return {
                    'status': 'duplicate',
                    'type': 'exact_match',
                    'existing_evidence': existing.to_dict() if existing else None,
                    'similarity': duplicate_check['similarity'],
                    'message': f"发现完全相同的证据，已存在于证据库中"
                }

            if duplicate_check.get('suspected'):
                return {
                    'status': 'suspected_duplicate',
                    'type': 'suspected',
                    'existing_id': duplicate_check['existing_id'],
                    'similarity': duplicate_check['similarity'],
                    'suggestion': '发现高度相似的证据，是否仍要添加？',
                    'existing_evidence': None
                }

            # 2. 创建证据项
            evidence = EvidenceItem(
                id=str(uuid.uuid4()),
                case_id=case_id,
                source_type=source_type,
                original_filename=original_filename or (file_path and os.path.basename(file_path)),
                file_path=file_path,
                raw_content=content or '',
                source_party=source_party,
                status=EvidenceStatus.PROCESSING.value,
                **(metadata or {})
            )

            # 3. 内容提取
            evidence.extracted_content = self._extract_content(evidence)

            # 4. 生成摘要
            evidence.summary = self._generate_summary(evidence.extracted_content or evidence.raw_content)

            # 5. 生成内容哈希
            evidence.generate_content_hash()

            # 6. 生成文件哈希
            if file_path:
                evidence.generate_file_hash()

            # 保存
            db.add(evidence)
            db.flush()

            # 7. 分类（同步处理，使用规则）
            classification = self._classify_evidence_sync(evidence.extracted_content, case_id)
            evidence.evidence_type = classification['type']
            evidence.proves_facts = classification['facts']

            # 8. 关键词提取（同步）
            keywords_result = self._extract_keywords_sync(evidence.extracted_content)
            evidence.keywords = keywords_result['keywords']
            evidence.entity_tags = keywords_result['entities']

            # 9. 状态更新
            evidence.status = EvidenceStatus.PROCESSED.value
            evidence.processed_at = datetime.utcnow()

            # 10. 保存去重记录
            self._save_duplicate_record(db, case_id, evidence, duplicate_check)

            db.commit()

            return {
                'status': 'success',
                'evidence': evidence.to_dict(),
                'classification': classification,
                'keywords': keywords_result
            }

        except Exception as e:
            db.rollback()
            return {
                'status': 'error',
                'message': str(e)
            }
        finally:
            db.close()

    def analyze_evidence(self, evidence_id: str, force_refresh: bool = False) -> dict:
        """
        分析已有证据记录（不创建新记录）

        Args:
            evidence_id: 证据ID
            force_refresh: 是否强制重新分析

        Returns:
            分析结果
        """
        db = self._get_db()
        try:
            # 获取证据记录
            evidence = db.query(EvidenceItem).filter(
                EvidenceItem.id == evidence_id,
                EvidenceItem.is_current == True
            ).first()

            if not evidence:
                return {'status': 'error', 'message': '证据不存在'}

            # 如果不是强制刷新且已有分析，跳过
            if not force_refresh:
                if evidence.evidence_type and evidence.credibility_score and evidence.credibility_score > 0:
                    return {
                        'status': 'already_processed',
                        'evidence_id': evidence_id,
                        'message': '证据已分析完成'
                    }

            # 重新提取内容（强制从文件提取，防止占位符）
            placeholder_patterns = [
                '[PDF文档]', '[图片证据]', '[Word文档]', '[扫描件', '识别失败',
                '内容解析待处理', '文件已上传', '内容提取'
            ]
            is_placeholder = (
                not evidence.extracted_content or
                len(evidence.extracted_content) < 100 or
                any(p in (evidence.extracted_content or '') for p in placeholder_patterns)
            )

            if is_placeholder and evidence.file_path:
                if os.path.exists(evidence.file_path):
                    evidence.extracted_content = self._extract_content(evidence)
                elif evidence.raw_content and not any(p in (evidence.raw_content or '') for p in placeholder_patterns):
                    # 如果文件不存在但有原始内容（非占位符），使用原始内容
                    evidence.extracted_content = evidence.raw_content

            # 分类
            classification = self._classify_evidence_sync(evidence.extracted_content, evidence.case_id)
            evidence.evidence_type = classification['type']
            evidence.proves_facts = classification['facts']

            # 如果是函件类型，自动创建Letter记录
            letter_created = False
            if classification['type'] == 'CORRESPONDENCE':
                letter_created = self._auto_create_letter_from_evidence(db, evidence, classification)

            # 关键词提取
            keywords_result = self._extract_keywords_sync(evidence.extracted_content)
            evidence.keywords = keywords_result['keywords']
            evidence.entity_tags = keywords_result['entities']

            # 生成摘要
            evidence.summary = self._generate_summary(
                evidence.extracted_content or evidence.raw_content
            )

            # 状态更新
            evidence.status = EvidenceStatus.PROCESSED.value
            evidence.processed_at = datetime.utcnow()

            db.commit()

            return {
                'status': 'success',
                'evidence_id': evidence_id,
                'classification': classification,
                'letter_created': letter_created,
                'keywords': keywords_result['keywords'],
                'entities': keywords_result['entities']
            }

        except Exception as e:
            db.rollback()
            return {'status': 'error', 'message': str(e)}
        finally:
            db.close()

    def _check_duplicate(
        self,
        db: Session,
        case_id: int,
        content: str = None,
        file_path: str = None
    ) -> dict:
        """
        检查是否重复
        """
        result = {
            'is_duplicate': False,
            'suspected': False,
            'existing_id': None,
            'similarity': 0.0
        }

        # 文件哈希检查
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()

                existing = db.query(EvidenceItem).filter(
                    and_(
                        EvidenceItem.case_id == case_id,
                        EvidenceItem.file_hash == file_hash,
                        EvidenceItem.is_current == True
                    )
                ).first()

                if existing:
                    result['is_duplicate'] = True
                    result['existing_id'] = existing.id
                    result['similarity'] = 1.0
                    return result
            except Exception:
                pass

        # 内容哈希检查
        if content:
            normalized = self._normalize_text(content)
            content_hash = hashlib.sha256(normalized.encode('utf-8')).hexdigest()

            existing = db.query(EvidenceItem).filter(
                and_(
                    EvidenceItem.case_id == case_id,
                    EvidenceItem.content_hash == content_hash,
                    EvidenceItem.is_current == True
                )
            ).first()

            if existing:
                result['is_duplicate'] = True
                result['existing_id'] = existing.id
                result['similarity'] = 1.0
                return result

        return result

    def _normalize_text(self, text: str) -> str:
        """规范化文本"""
        if not text:
            return ""
        text = re.sub(r'\s+', '', text)
        text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
        return text.lower()

    def _extract_content(self, evidence: EvidenceItem) -> str:
        """提取文本内容"""
        if evidence.raw_content:
            return evidence.raw_content.strip()

        if evidence.file_path and os.path.exists(evidence.file_path):
            ext = os.path.splitext(evidence.file_path)[1].lower()

            try:
                if ext == '.txt':
                    with open(evidence.file_path, 'r', encoding='utf-8') as f:
                        return f.read()
                elif ext in ['.pdf', '.docx', '.doc']:
                    # 简单处理，实际项目中应使用专业库
                    return self._extract_from_file(evidence.file_path, ext)
            except Exception:
                pass

        return evidence.raw_content or ''

    def _extract_from_file(self, file_path: str, ext: str) -> str:
        """从文件提取文本"""
        try:
            # 文本文件
            if ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

            # PDF/Word 文件 - 使用 file_parser
            elif ext in ['.pdf', '.docx', '.doc']:
                from app.utils.file_parser import file_parser
                return file_parser.parse(file_path)

            # 图片文件 - 使用 OCR
            elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                from app.utils.file_parser import file_parser
                return file_parser.parse(file_path)

        except Exception as e:
            print(f"[_extract_from_file] Error extracting {ext} file: {e}")

        return ''

    def _generate_summary(self, content: str) -> str:
        """
        生成摘要 - 法律应用专用：证据完整性优先，不得截断任何字符

        重要原则：证据中的每一个字符都可能包含关键法律信息，
        任何截断都可能导致重要事实被遗漏。因此：
        - 保留完整原始内容，不做任何智能提取筛选
        - 不限制内容长度
        - 仅做格式规范化，不做任何内容删减
        """
        if not content:
            return ''

        # 法律应用原则：证据内容不得截断
        # 无论内容多长，都保留完整内容供后续分析
        return content

    def _classify_evidence_sync(self, content: str, case_id: int) -> dict:
        """
        证据分类：AI逐字逐句分析，理解证据性质后自动归类
        不使用关键词触发，每个证据都要AI理解判断
        """
        if not content or len(content.strip()) < 10:
            return {
                'type': 'OTHER',
                'type_info': self.EVIDENCE_TYPES['OTHER'],
                'facts': []
            }

        if self.llm:
            return self._classify_with_llm(content, case_id)
        else:
            return self._classify_with_llm(content, case_id)

    def _classify_with_llm(self, content: str, case_id: int) -> dict:
        """
        使用LLM进行证据分类
        AI逐字逐句理解证据内容，判断证据性质
        """
        classification_prompt = f"""你是一个专业的法律AI助手。请仔细阅读以下证据内容，分析它是什么性质的证据。

证据内容：
---
{content}
---

请从以下类型中选择最合适的一个：
- CONTRACT（合同协议类）：正式的合同、协议、补充协议等，有双方签字盖章的法律文件
- CORRESPONDENCE（函件文书类）：信函、邮件、通知、告知书、催告函等，用于沟通、通知、催告的文件
- PAYMENT（付款凭证类）：发票、收据、转账记录、银行流水等付款相关凭证
- IDENTITY（身份证明类）：身份证、营业执照、授权委托书等身份证明文件
- AUDIO_VIDEO（视听资料类）：录音、录像、视频等
- TESTIMONY（证人证言类）：证人证言、笔录等
- EXPERT（鉴定评估类）：鉴定报告、评估报告等专业意见
- DOCUMENT（政府文件类）：证书、批复、决定、裁定等官方文��
- OTHER（其他）：不属于以上类型的其他证据

请以JSON格式返回分析结果：
{{"type": "类型", "reason": "简短理由（不超过50字）"}}

只返回JSON，不要其他内容："""

        try:
            result = self._call_llm(classification_prompt)
            import json
            import re
            match = re.search(r'\{[^}]+\}', result)
            if match:
                data = json.loads(match.group())
                ev_type = data.get('type', 'OTHER').upper()
                if ev_type not in self.EVIDENCE_TYPES:
                    ev_type = 'OTHER'
                return {
                    'type': ev_type,
                    'type_info': self.EVIDENCE_TYPES.get(ev_type, self.EVIDENCE_TYPES['OTHER']),
                    'reason': data.get('reason', ''),
                    'facts': self._extract_provable_facts(content)
                }
        except Exception as e:
            pass

        return {
            'type': 'OTHER',
            'type_info': self.EVIDENCE_TYPES['OTHER'],
            'facts': self._extract_provable_facts(content)
        }

    def _call_llm(self, prompt: str) -> str:
        """调用LLM服务"""
        try:
            from app.services.llm_service import LLMService
            llm = LLMService()
            response = llm.chat([{"role": "user", "content": prompt}])
            return response.get('content', '')
        except Exception as e:
            return ''

    def _auto_create_letter_from_evidence(self, db: Session, evidence: Any, classification: dict) -> bool:
        """自动从证据创建Letter记录（仅当证据类型为CORRESPONDENCE时）"""
        try:
            # 检查是否已存在关联的Letter
            existing = db.query(Letter).filter(
                Letter.case_id == evidence.case_id,
                Letter.related_evidence_ids.contains(evidence.id)
            ).first()
            if existing:
                return False

            # 判断收发方向
            source_party = getattr(evidence, 'source_party', '')
            if source_party == EvidenceSourceParty.THEIR_SIDE.value:
                direction = LetterDirection.INCOMING
            elif source_party == EvidenceSourceParty.OUR_SIDE.value:
                direction = LetterDirection.OUTGOING
            else:
                direction = LetterDirection.INCOMING

            # 从内容摘要中提取核心诉求
            key_demands = ""
            proves_facts = classification.get('facts', [])
            if proves_facts:
                key_demands = "; ".join(str(f.get("fact", "")) for f in proves_facts[:3] if f.get("fact"))

            # 创建Letter记录
            letter = Letter(
                case_id=evidence.case_id,
                direction=direction,
                letter_type=LetterType.OTHER,
                title=evidence.display_name or evidence.original_filename or "函件",
                content_summary=evidence.summary if evidence.summary else "",
                key_demands=key_demands or None,
                related_evidence_ids=[evidence.id],
                related_document_id=None
            )
            db.add(letter)
            db.flush()
            return True
        except Exception as e:
            return False

    def _extract_provable_facts(self, content: str) -> list:
        """提取可证明的事实"""
        if not content:
            return []

        facts = []

        # 简单的事实提取规则
        fact_patterns = [
            (r'(\w+)欠(\w+)[\d,.]+[元万]?', '债务关系'),
            (r'(\w+)年(\w+)月(\w+)日', '时间节点'),
            (r'甲方[：:]?(\w+)', '甲方身份'),
            (r'乙方[：:]?(\w+)', '乙方身份'),
            (r'签订', '合同签订'),
            (r'违约', '违约事实'),
        ]

        for pattern, fact_type in fact_patterns:
            matches = re.findall(pattern, content)
            if matches:
                facts.append({
                    'fact': f"{fact_type}: {matches[0] if isinstance(matches[0], str) else matches[0][0]}" if isinstance(matches[0], tuple) else matches[0],
                    'fact_type': fact_type,
                    'confidence': 0.7
                })

        return facts[:5]  # 最多5个事实

    def _generate_display_name(self, evidence_type: str, proves_facts: list, entity_tags: list, original_filename: str) -> str:
        """
        根据证据类型和司法作用生成规范显示名称

        命名规则：[证据类型简称]-[关键主体/事由]
        例如：
        - 合同类："采购合同-博凯升华"
        - 付款类："付款凭证-展柜打样款"
        - 函件类："往来函件-催款通知"
        - 身份类："主体资格-营业执照"
        """
        if not evidence_type or evidence_type == 'OTHER':
            # 无法分类，使用原始文件名截断
            return original_filename[:30] if original_filename else '未命名证据'

        # 证据类型映射到中文简称
        type_names = {
            'CONTRACT': '合同',
            'CORRESPONDENCE': '往来函件',
            'PAYMENT': '付款凭证',
            'IDENTITY': '主体资格',
            'AUDIO_VIDEO': '视听资料',
            'TESTIMONY': '证人证言',
            'EXPERT': '鉴定意见',
            'DOCUMENT': '书证',
            'ELECTRONIC': '电子数据',
            'PHOTO': '照片',
            'OTHER': '其他证据',
        }

        type_name = type_names.get(evidence_type, '证据')

        # 从实体标签中提取关键信息
        key_subject = ''
        for tag in (entity_tags or []):
            if tag.get('type') in ('PARTY', 'ORG', 'PERSON'):
                val = tag.get('value', '')
                if val and len(val) <= 15:
                    key_subject = val
                    break

        # 从证明事实中提取关键事由
        key_matter = ''
        for fact in (proves_facts or []):
            fact_text = fact.get('fact', '') if isinstance(fact, dict) else str(fact)
            # 提取冒号后的内容
            if '：' in fact_text:
                key_matter = fact_text.split('：', 1)[1][:15]
            elif ':' in fact_text:
                key_matter = fact_text.split(':', 1)[1][:15]
            if key_matter:
                break

        # 组合名称
        if key_subject:
            return f"{type_name}-{key_subject}"
        elif key_matter:
            return f"{type_name}-{key_matter}"
        else:
            # 回退：使用原始文件名（去除扩展名，截断）
            base_name = original_filename.rsplit('.', 1)[0] if original_filename and '.' in original_filename else original_filename
            # 去除常见前缀噪声
            for prefix in ['企业微信', '微信', '钉钉', 'QQ', '邮件', 'email_', 'IMG_', 'DOC_']:
                if base_name.startswith(prefix):
                    base_name = base_name[len(prefix):]
                    break
            return f"{type_name}-{base_name[:15]}" if base_name else f"{type_name}"

    def _extract_keywords_sync(self, content: str) -> dict:
        """同步关键词提取"""
        if not content:
            return {'keywords': [], 'entities': []}

        keywords = []
        entities = []

        # 提取金额
        money_pattern = r'[\d,]+[万千佰亿万]?[元]?'
        money_matches = re.findall(money_pattern, content)
        for m in money_matches[:3]:
            entities.append({'type': 'MONEY', 'value': m})
            keywords.append(m)

        # 提取日期
        date_pattern = r'(\d{4})[年\-\/](\d{1,2})[月\-\/](\d{1,2})[日]?'
        date_matches = re.findall(date_pattern, content)
        for d in date_matches[:3]:
            date_str = f"{d[0]}年{d[1]}月{d[2]}日"
            entities.append({'type': 'DATE', 'value': date_str})
            keywords.append(date_str)

        # 提取当事人（简化）
        party_patterns = [
            r'([\u4e00-\u9fa5]{2,6})(?:公司|厂|店|企业|个人)',
            r'甲方[：:]?([\u4e00-\u9fa5]{2,4})',
            r'乙方[：:]?([\u4e00-\u9fa5]{2,4})',
            r'([\u4e00-\u9fa5]{2,4})(?:男|女)',
        ]

        for pattern in party_patterns:
            matches = re.findall(pattern, content)
            for m in matches[:2]:
                entities.append({'type': 'PARTY', 'value': m})
                if m not in keywords:
                    keywords.append(m)

        # 提取关键词（出现频率高的词）
        words = re.findall(r'[\u4e00-\u9fa5]{2,4}', content)
        word_freq = {}
        for w in words:
            if len(w) >= 2:
                word_freq[w] = word_freq.get(w, 0) + 1

        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        for w, _ in top_words:
            if w not in keywords:
                keywords.append(w)

        return {
            'keywords': keywords[:20],  # 最多20个关键词
            'entities': entities[:10]   # 最多10个实体
        }

    def _save_duplicate_record(
        self,
        db: Session,
        case_id: int,
        evidence: EvidenceItem,
        duplicate_check: dict
    ):
        """保存去重记录"""
        record = EvidenceDuplicateCheck(
            id=str(uuid.uuid4()),
            case_id=case_id,
            new_evidence_hash=evidence.content_hash,
            new_filename=evidence.original_filename,
            existing_evidence_id=duplicate_check.get('existing_id'),
            is_duplicate=duplicate_check.get('is_duplicate', False),
            duplicate_status='new' if not duplicate_check.get('is_duplicate') else 'confirmed',
            suggested_action='skip' if duplicate_check.get('is_duplicate') else 'create'
        )
        db.add(record)

    # ==================== 查询接口 ====================

    def get_evidence_full_content(self, case_id: int) -> str:
        """
        获取案件所有证据的完整内容文本
        用于对抗性分析等需要全文的场景

        Returns:
            格式化的完整证据内容字符串
        """
        db = self._get_db()
        try:
            docs = db.query(Document).filter(
                Document.case_id == case_id
            ).all()
            evidence_items = db.query(EvidenceItem).filter(
                and_(
                    EvidenceItem.case_id == case_id,
                    EvidenceItem.is_current == True
                )
            ).all()

            if not docs and not evidence_items:
                return ""

            total_count = len(docs) + len(evidence_items)
            evidence_text = f"【案件证据 - 完整内容】（共 {total_count} 份证据/文档）\n\n"

            for i, doc in enumerate(docs, 1):
                evidence_text += f"{'='*60}\n"
                evidence_text += f"【证据{i}】文件名称：{doc.filename}\n"
                evidence_text += f"【证据{i}】文档类型：{doc.doc_type or '未分类'}\n"
                evidence_text += f"{'='*60}\n"

                # 优先使用完整内容 content，fallback 到 summary
                full_content = doc.content
                if full_content and len(full_content) > 50:
                    evidence_text += f"【证据{i}】完整内容如下：\n{full_content}\n\n"
                elif doc.content_summary and len(doc.content_summary) > 20:
                    evidence_text += f"【证据{i}】内容摘要：\n{doc.content_summary}\n\n"
                else:
                    evidence_text += f"【证据{i}】内容：未提取到文本内容（请检查文件是否正确上传）\n\n"

            offset = len(docs)
            for i, evidence in enumerate(evidence_items, offset + 1):
                name = evidence.display_name or evidence.original_filename or f"证据{evidence.id}"
                content = evidence.extracted_content or evidence.raw_content or evidence.summary or ""
                proves_facts = evidence.proves_facts or []
                evidence_text += f"{'='*60}\n"
                evidence_text += f"【证据{i}】证据ID：{evidence.id}\n"
                evidence_text += f"【证据{i}】证据名称：{name}\n"
                evidence_text += f"【证据{i}】证据编号：{evidence.evidence_number or '未编号'}\n"
                evidence_text += f"【证据{i}】证据类型：{evidence.evidence_type or '未分类'}\n"
                evidence_text += f"【证据{i}】来源方：{evidence.source_party or '未标注'}\n"
                evidence_text += f"{'='*60}\n"
                if evidence.summary:
                    evidence_text += f"【证据{i}】AI摘要：\n{evidence.summary}\n\n"
                if proves_facts:
                    evidence_text += (
                        f"【证据{i}】证明事实：\n"
                        f"{json.dumps(proves_facts, ensure_ascii=False)}\n\n"
                    )
                if content and len(content) > 20:
                    evidence_text += f"【证据{i}】可用文本内容：\n{content[:2500]}\n"
                    if len(content) > 2500:
                        evidence_text += "（内容较长，已保留前2500字供模型定位；完整原文仍保存在证据库。）\n"
                    evidence_text += "\n"
                elif not evidence.summary and not proves_facts:
                    evidence_text += f"【证据{i}】内容：未提取到文本内容（请检查证据处理状态）\n\n"

            return evidence_text

        finally:
            db.close()

    def get_evidence_list(self, case_id: int, filters: dict = None) -> List[dict]:
        """
        获取证据列表
        """
        db = self._get_db()
        try:
            query = db.query(EvidenceItem).filter(
                and_(
                    EvidenceItem.case_id == case_id,
                    EvidenceItem.is_current == True
                )
            )

            if filters:
                if filters.get('evidence_type'):
                    query = query.filter(EvidenceItem.evidence_type == filters['evidence_type'])
                if filters.get('source_party'):
                    query = query.filter(EvidenceItem.source_party == filters['source_party'])
                if filters.get('status'):
                    query = query.filter(EvidenceItem.status == filters['status'])

            evidence_list = query.order_by(EvidenceItem.created_at.desc()).all()
            return [e.to_dict() for e in evidence_list]
        finally:
            db.close()

    def get_evidence_by_id(self, evidence_id: str) -> dict:
        """获取单个证据详情"""
        db = self._get_db()
        try:
            evidence = db.query(EvidenceItem).filter(EvidenceItem.id == evidence_id).first()
            if evidence:
                return evidence.to_dict()
            return None
        finally:
            db.close()

    def get_evidence_relationships(self, case_id: int) -> List[dict]:
        """获取证据关系"""
        db = self._get_db()
        try:
            relationships = db.query(EvidenceRelationship).filter(
                EvidenceRelationship.case_id == case_id
            ).all()
            return [r.to_graph_edge() for r in relationships]
        finally:
            db.close()

    def get_evidence_summary(self, case_id: int) -> dict:
        """获取证据汇总"""
        db = self._get_db()
        try:
            evidence_list = db.query(EvidenceItem).filter(
                EvidenceItem.case_id == case_id
            ).all()

            if not evidence_list:
                return {
                    'total': 0,
                    'by_type': {},
                    'by_source': {},
                    'avg_credibility': 0,
                    'gaps': []
                }

            # 按类型统计
            by_type = {}
            by_source = {}
            total_credibility = 0

            for e in evidence_list:
                # 类型
                ev_type = e.evidence_type
                if ev_type not in by_type:
                    by_type[ev_type] = {'count': 0, 'evidence': []}
                by_type[ev_type]['count'] += 1
                by_type[ev_type]['evidence'].append(e.id)

                # 来源
                source = e.source_party
                if source not in by_source:
                    by_source[source] = 0
                by_source[source] += 1

                total_credibility += e.credibility_score

            # 计算缺口
            gaps = self._identify_evidence_gaps(case_id, evidence_list)

            return {
                'total': len(evidence_list),
                'by_type': by_type,
                'by_source': by_source,
                'avg_credibility': total_credibility / len(evidence_list) if evidence_list else 0,
                'gaps': gaps
            }
        finally:
            db.close()

    def _identify_evidence_gaps(self, case_id: int, evidence_list: list) -> list:
        """识别证据缺口"""
        gaps = []

        # 获取案件信息
        db = self._get_db()
        try:
            case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                return gaps

            # 根据案件类型判断需要的证据
            case_type = case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type)

            # 常见证据缺口
            required_checks = [
                ('身份证明', 'IDENTITY', ['身份证', '营业执照', '授权委托书']),
                ('合同文件', 'CONTRACT', ['合同', '协议']),
                ('付款凭证', 'PAYMENT', ['发票', '收据', '转账记录']),
                ('函件往来', 'CORRESPONDENCE', ['函', '邮件', '通知'])
            ]

            existing_types = [e.evidence_type for e in evidence_list]

            for gap_name, gap_type, keywords in required_checks:
                if gap_type not in existing_types:
                    # 检查内容中是否有关键词
                    has_keyword = False
                    for e in evidence_list:
                        content = (e.extracted_content or '') + (e.raw_content or '')
                        if any(kw in content for kw in keywords):
                            has_keyword = True
                            break

                    if not has_keyword:
                        gaps.append({
                            'name': gap_name,
                            'type': gap_type,
                            'suggestion': f'建议补充{gap_name}相关证据',
                            'priority': 'important'
                        })

            return gaps[:5]  # 最多5个缺口
        finally:
            db.close()

    # ==================== 关系分析 ====================

    def analyze_relationships(self, case_id: int) -> dict:
        """
        分析证据之间的关系
        """
        db = self._get_db()
        try:
            evidence_list = db.query(EvidenceItem).filter(
                and_(
                    EvidenceItem.case_id == case_id,
                    EvidenceItem.is_current == True
                )
            ).all()

            if len(evidence_list) < 2:
                return {
                    'status': 'insufficient',
                    'message': '证据数量不足，无法分析关系',
                    'relationships': []
                }

            # 简化实现：基于关键词和内容相似度
            relationships = []

            for i, ev_a in enumerate(evidence_list):
                for ev_b in evidence_list[i+1:]:
                    # 法律应用：使用完整内容，不截断
                    content_a = ev_a.extracted_content or ev_a.raw_content or ''
                    content_b = ev_b.extracted_content or ev_b.raw_content or ''

                    similarity = self._calculate_similarity(content_a, content_b)

                    if similarity > 0.5:
                        # 确定关系类型
                        if similarity > 0.8:
                            rel_type = 'SUPPORT'
                        elif similarity > 0.6:
                            rel_type = 'SUPPLEMENT'
                        else:
                            rel_type = 'RELATED'

                        rel = EvidenceRelationship(
                            id=str(uuid.uuid4()),
                            case_id=case_id,
                            from_evidence_id=ev_a.id,
                            to_evidence_id=ev_b.id,
                            relationship_type=rel_type,
                            strength=similarity * 100,
                            analysis_note=f'内容相似度: {similarity:.2f}',
                            confidence=0.7,
                            is_auto_generated=True
                        )
                        db.add(rel)
                        relationships.append(rel)

            db.commit()

            return {
                'status': 'success',
                'new_relationships': len(relationships),
                'relationships': [r.to_graph_edge() for r in relationships]
            }
        except Exception as e:
            db.rollback()
            return {'status': 'error', 'message': str(e)}
        finally:
            db.close()

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """简单的文本相似度计算"""
        if not text1 or not text2:
            return 0.0

        # 简单实现：基于关键词重叠
        words1 = set(re.findall(r'[\u4e00-\u9fa5]{2,}', text1))
        words2 = set(re.findall(r'[\u4e00-\u9fa5]{2,}', text2))

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    # ==================== 证据图谱数据 ====================

    def get_graph_data(self, case_id: int, view_type: str = 'default') -> dict:
        """
        获取图谱可视化数据
        """
        db = self._get_db()
        try:
            # 获取证据
            evidence_list = db.query(EvidenceItem).filter(
                and_(
                    EvidenceItem.case_id == case_id,
                    EvidenceItem.is_current == True
                )
            ).all()

            # 构建节点
            nodes = []
            for ev in evidence_list:
                node = ev.to_graph_node()
                nodes.append(node)

            # 获取关系
            relationships = db.query(EvidenceRelationship).filter(
                EvidenceRelationship.case_id == case_id
            ).all()

            edges = []
            for rel in relationships:
                edge = rel.to_graph_edge()
                edges.append(edge)

            # 图例
            legend = {
                'node_types': {
                    'evidence': {'name': '证据', 'icon': '📎'},
                    'fact': {'name': '案件事实', 'icon': '📌'}
                },
                'edge_types': {k: v for k, v in self.RELATIONSHIP_TYPES.items()},
                'credibility': [
                    {'range': '80-100', 'color': '#52c41a', 'label': '高证明力参考'},
                    {'range': '60-79', 'color': '#faad14', 'label': '中证明力参考'},
                    {'range': '40-59', 'color': '#fa8c16', 'label': '低证明力参考'},
                    {'range': '0-39', 'color': '#f5222d', 'label': '待补充'}
                ]
            }

            return {
                'nodes': nodes,
                'edges': edges,
                'legend': legend,
                'summary': self.get_evidence_summary(case_id)
            }
        finally:
            db.close()

    # ==================== 证据更新 ====================

    def update_evidence(
        self,
        evidence_id: str,
        updates: dict
    ) -> dict:
        """更新证据"""
        db = self._get_db()
        try:
            evidence = db.query(EvidenceItem).filter(
                EvidenceItem.id == evidence_id
            ).first()

            if not evidence:
                return {'status': 'error', 'message': '证据不存在'}

            # 更新字段
            allowed_fields = ['summary', 'evidence_type', 'source_party',
                            'proves_facts', 'keywords', 'entity_tags']

            for field in allowed_fields:
                if field in updates:
                    setattr(evidence, field, updates[field])

            evidence.updated_at = datetime.utcnow()

            db.commit()

            return {
                'status': 'success',
                'evidence': evidence.to_dict()
            }
        except Exception as e:
            db.rollback()
            return {'status': 'error', 'message': str(e)}
        finally:
            db.close()

    def delete_evidence(self, evidence_id: str) -> dict:
        """删除证据"""
        db = self._get_db()
        try:
            evidence = db.query(EvidenceItem).filter(
                EvidenceItem.id == evidence_id
            ).first()

            if not evidence:
                return {'status': 'error', 'message': '证据不存在'}

            # 软删除
            evidence.is_current = False
            evidence.updated_at = datetime.utcnow()

            db.commit()

            return {'status': 'success', 'message': '证据已删除'}
        except Exception as e:
            db.rollback()
            return {'status': 'error', 'message': str(e)}
        finally:
            db.close()

    # ==================== 统计 ====================

    def get_statistics(self, case_id: int) -> dict:
        """获取证据统计"""
        db = self._get_db()
        try:
            evidence_list = db.query(EvidenceItem).filter(
                EvidenceItem.case_id == case_id
            ).all()

            # 基础统计
            total = len(evidence_list)

            # 按类型统计
            by_type = {}
            for e in evidence_list:
                t = e.evidence_type
                if t not in by_type:
                    by_type[t] = {'count': 0, 'avg_credibility': 0, 'total_credibility': 0}
                by_type[t]['count'] += 1
                by_type[t]['total_credibility'] += e.credibility_score

            for t in by_type:
                if by_type[t]['count'] > 0:
                    by_type[t]['avg_credibility'] = by_type[t]['total_credibility'] / by_type[t]['count']

            # 按来源统计
            by_source = {}
            for e in evidence_list:
                s = e.source_party
                if s not in by_source:
                    by_source[s] = 0
                by_source[s] += 1

            # 信度分布
            credibility_distribution = {
                'high': 0,    # 80-100
                'medium': 0,  # 60-79
                'low': 0,     # 40-59
                'very_low': 0 # 0-39
            }

            for e in evidence_list:
                cs = e.credibility_score
                if cs >= 80:
                    credibility_distribution['high'] += 1
                elif cs >= 60:
                    credibility_distribution['medium'] += 1
                elif cs >= 40:
                    credibility_distribution['low'] += 1
                else:
                    credibility_distribution['very_low'] += 1

            return {
                'total': total,
                'by_type': by_type,
                'by_source': by_source,
                'credibility_distribution': credibility_distribution,
                'avg_credibility': sum(e.credibility_score for e in evidence_list) / total if total > 0 else 0
            }
        finally:
            db.close()


# 单例
evidence_service_v2 = EvidenceServiceV2()
