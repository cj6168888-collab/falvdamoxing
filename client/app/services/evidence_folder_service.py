"""
证据文件夹处理服务
自动扫描、整理、分析证据文件夹中的文件
"""
import os
import hashlib
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.evidence_folder import (
    EvidenceFolderScan, EvidenceFolderFile,
    EvidenceFolderConfig, ScanStatus, ScanType,
    FileProcessStatus
)
from app.models.evidence import EvidenceItem, EvidenceStatus
from app.models.case import Case
from app.db.database import SessionLocal, Base, engine
from app.utils.file_parser import FileParser

logger = logging.getLogger(__name__)


class EvidenceFolderService:
    """
    证据文件夹处理服务
    负责扫描文件夹、提取内容、自动分类、创建证据记录
    """

    # 支持的文件格式
    SUPPORTED_FORMATS = {
        'pdf', 'docx', 'doc', 'xlsx', 'xls',
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff',
        'txt', 'md', 'rtf',
    }

    # 证据类型关键词映射
    EVIDENCE_TYPE_KEYWORDS = {
        'CONTRACT': ['合同', '协议', '协议书', '合作', '约定', '条款'],
        'CORRESPONDENCE': ['函', '邮件', '书信', '通知', '告知', '回复', '催告'],
        'PAYMENT': ['发票', '收据', '付款', '转账', '汇款', '凭证', '账单'],
        'IDENTITY': ['身份证', '营业执照', '法人', '代理人', '委托书'],
        'AUDIO_VIDEO': ['录音', '录像', '视频', '音频'],
        'DOCUMENT': ['判决', '裁定', '决定', '书', '证明'],
        'EXPERT': ['鉴定', '评估', '审计', '检验'],
    }

    def __init__(self, case_id: int):
        self.case_id = case_id
        self.db = SessionLocal()
        self.file_parser = FileParser()
        self._ensure_config_exists()
        # 确保案件专属存储目录存在
        self._ensure_case_storage_dir()

    def _ensure_config_exists(self):
        """确保配置文件存在"""
        config = self.db.query(EvidenceFolderConfig).filter(
            EvidenceFolderConfig.case_id == self.case_id
        ).first()

        if not config:
            config = EvidenceFolderConfig(
                case_id=self.case_id,
                supported_formats=list(self.SUPPORTED_FORMATS),
                auto_ocr=True,
                auto_classify=True,
                auto_deduplicate=False,  # 每个案件独立处理，不跨案件去重
                include_subfolders=True,
            )
            self.db.add(config)
            self.db.commit()

    def _ensure_case_storage_dir(self):
        """确保案件专属存储目录存在"""
        case_dir = os.path.join(self.file_parser.storage_path, str(self.case_id))
        os.makedirs(case_dir, exist_ok=True)

    def get_case(self) -> Optional[Case]:
        """获取关联的案件"""
        return self.db.query(Case).filter(Case.id == self.case_id).first()

    def get_folder_path(self) -> Optional[str]:
        """获取证据文件夹路径"""
        case = self.get_case()
        return case.evidence_folder_path if case else None

    def get_config(self) -> Optional[EvidenceFolderConfig]:
        """获取配置"""
        return self.db.query(EvidenceFolderConfig).filter(
            EvidenceFolderConfig.case_id == self.case_id
        ).first()

    # ==================== 扫描操作 ====================

    def full_scan(self) -> EvidenceFolderScan:
        """
        全量扫描证据文件夹
        扫描所有文件并处理
        """
        folder_path = self.get_folder_path()
        if not folder_path or not os.path.exists(folder_path):
            raise ValueError(f"证据文件夹路径无效: {folder_path}")

        # 创建扫描记录
        scan = EvidenceFolderScan(
            case_id=self.case_id,
            scan_type=ScanType.FULL,
            status=ScanStatus.RUNNING,
            scan_path=folder_path,
        )
        self.db.add(scan)
        self.db.commit()

        try:
            # 获取所有支持的文件
            file_paths = self._scan_directory(folder_path)

            scan.files_found = len(file_paths)
            scan.status = ScanStatus.RUNNING
            self.db.commit()

            # 处理每个文件
            processed = 0
            failed = 0
            skipped = 0
            batch_size = 10  # 每10个文件提交一次

            for i, file_path in enumerate(file_paths):
                result = self._process_single_file(file_path, scan.id)
                if result['status'] == 'success':
                    processed += 1
                elif result['status'] == 'skipped':
                    skipped += 1
                else:
                    failed += 1

                scan.files_processed = processed
                scan.files_failed = failed
                scan.files_skipped = skipped

                # 批量提交，减少数据库往返
                if (i + 1) % batch_size == 0:
                    self.db.commit()

            self.db.commit()

            # 完成扫描
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.utcnow()
            self.db.commit()

            # 更新案件的扫描信息
            case = self.get_case()
            if case:
                case.evidence_last_scan_time = datetime.utcnow()
                case.evidence_last_sync_count = processed
                self.db.commit()

            return scan

        except Exception as e:
            scan.status = ScanStatus.FAILED
            scan.error_message = str(e)
            scan.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def incremental_scan(self, file_paths: List[str] = None) -> Dict[str, Any]:
        """
        增量扫描 - 只处理新增或修改的文件

        Args:
            file_paths: 要处理的文件路径列表，不传则自动检测

        Returns:
            处理结果统计
        """
        folder_path = self.get_folder_path()
        if not folder_path:
            raise ValueError("证据文件夹未配置")

        # 如果没有指定文件，自动扫描
        if not file_paths:
            all_files = self._scan_directory(folder_path)
            existing_hashes = self._get_existing_file_hashes()
            file_paths = [f for f in all_files if (h := self._get_file_hash(f)) and h not in existing_hashes]

        if not file_paths:
            return {
                'status': 'no_new_files',
                'message': '没有新文件需要处理',
                'processed': 0,
            }

        # 创建增量扫描记录
        scan = EvidenceFolderScan(
            case_id=self.case_id,
            scan_type=ScanType.INCREMENTAL,
            status=ScanStatus.RUNNING,
            scan_path=folder_path,
            files_found=len(file_paths),
        )
        self.db.add(scan)
        self.db.commit()

        results = {
            'status': 'completed',
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }

        for file_path in file_paths:
            result = self._process_single_file(file_path, scan.id)
            if result['status'] == 'success':
                results['processed'] += 1
            elif result['status'] == 'skipped':
                results['skipped'] += 1
            else:
                results['failed'] += 1
            results['details'].append(result)

            scan.files_processed = results['processed']
            scan.files_failed = results['failed']
            scan.files_skipped = results['skipped']
            self.db.commit()

        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.utcnow()
        self.db.commit()

        return results

    def _scan_directory(self, folder_path: str) -> List[str]:
        """扫描目录，返回所有支持的文件路径"""
        files = []
        config = self.get_config()
        supported = set(config.supported_formats) if config and config.supported_formats else self.SUPPORTED_FORMATS
        include_subfolders = config.include_subfolders if config else True

        try:
            folder = Path(folder_path)

            if include_subfolders:
                pattern = '**/*'
            else:
                pattern = '*'

            for file_path in folder.glob(pattern):
                if file_path.is_file():
                    ext = file_path.suffix.lower().lstrip('.')
                    if ext in supported:
                        # 排除临时文件
                        if not self._should_exclude(file_path.name):
                            files.append(str(file_path.absolute()))
        except Exception as e:
            logger.error(f"扫描目录失败: {folder_path}, 错误: {e}")

        return files

    def _should_exclude(self, filename: str) -> bool:
        """判断文件是否应该排除"""
        exclude_patterns = ['~$', '.tmp', '.temp', '.DS_Store', 'Thumbs.db', '.ini', '_page_']
        for pattern in exclude_patterns:
            if pattern in filename:
                return True
        return False

    # ==================== 文件处理 ====================

    def _process_single_file(
        self,
        file_path: str,
        scan_id: int = None
    ) -> Dict[str, Any]:
        """
        处理单个文件 - 每个案件独立复制文件到案件专属目录

        Args:
            file_path: 源文件路径
            scan_id: 关联的扫描记录ID

        Returns:
            处理结果
        """
        try:
            folder_root = self.get_folder_path()
            if not folder_root:
                raise ValueError("证据文件夹路径未配置")

            path = Path(file_path)

            # 检查文件是否存在
            if not path.exists():
                return {
                    'status': 'error',
                    'message': '文件不存在',
                    'file_path': file_path,
                }

            # 复制文件到案件专属存储目录（每个案件独立存储）
            case_storage = os.path.join(self.file_parser.storage_path, str(self.case_id))
            os.makedirs(case_storage, exist_ok=True)
            case_file_path = os.path.join(case_storage, path.name)
            
            # 如果案件专属目录中已有同名文件，检查是否需要更新
            needs_copy = True
            if os.path.exists(case_file_path):
                src_hash = self._get_file_hash(file_path)
                dst_hash = self._get_file_hash(case_file_path)
                if src_hash == dst_hash:
                    needs_copy = False  # 文件相同，无需重复复制
            
            if needs_copy:
                import shutil
                shutil.copy2(file_path, case_file_path)
                logger.info(f"[文件复制] {path.name} -> 案件{self.case_id}专属目录")

            # 使用案件专属目录中的文件进行后续处理
            actual_file_path = case_file_path

            # 计算文件哈希（使用案件专属目录中的文件）
            file_hash = self._get_file_hash(actual_file_path)

            # 检查是否已在当前案件中处理过（仅在当前案件内去重）
            existing = self.db.query(EvidenceFolderFile).filter(
                and_(
                    EvidenceFolderFile.case_id == self.case_id,
                    EvidenceFolderFile.file_hash == file_hash
                )
            ).first()

            if existing:
                return {
                    'status': 'skipped',
                    'reason': 'duplicate_in_case',
                    'message': '文件已在当前案件中处理',
                    'existing_id': existing.id,
                    'file_path': file_path,
                }

            # 创建文件记录（使用案件专属目录中的文件）
            file_record = EvidenceFolderFile(
                case_id=self.case_id,
                file_path=actual_file_path,
                file_name=path.name,
                file_extension=path.suffix.lower().lstrip('.'),
                file_size=path.stat().st_size,
                relative_path=str(path.relative_to(Path(folder_root))),
                file_hash=file_hash,
                last_modified=datetime.fromtimestamp(path.stat().st_mtime),
                status=FileProcessStatus.PROCESSING,
                scan_id=scan_id,
            )
            self.db.add(file_record)
            self.db.commit()

            # 提取内容（从案件专属目录中的文件）
            extracted_content = self._extract_content(actual_file_path)
            file_record.extracted_content = extracted_content
            file_record.extracted_content_length = len(extracted_content) if extracted_content else 0
            file_record.ocr_used = 'OCR' in extracted_content if extracted_content else False

            # 自动分类
            category = self._auto_classify(extracted_content, path.name)
            file_record.auto_category = category

            # 生成摘要
            summary = self._generate_summary(extracted_content)
            file_record.auto_summary = summary

            # 更新状态
            file_record.status = FileProcessStatus.COMPLETED
            file_record.processed = True
            file_record.processed_at = datetime.utcnow()
            self.db.commit()

            # 创建证据记录
            evidence = self._create_evidence_record(
                file_record=file_record,
                content=extracted_content,
                category=category,
                summary=summary,
            )

            if evidence:
                file_record.evidence_id = evidence.id
                self.db.commit()

            return {
                'status': 'success',
                'file_path': actual_file_path,
                'file_record_id': file_record.id,
                'evidence_id': evidence.id if evidence else None,
                'category': category,
                'content_length': file_record.extracted_content_length,
            }

        except Exception as e:
            logger.error(f"处理文件失败: {file_path}, 错误: {e}")

            # 更新错误状态
            try:
                self.db.query(EvidenceFolderFile).filter(
                    EvidenceFolderFile.case_id == self.case_id,
                    EvidenceFolderFile.file_name == path.name
                ).update({
                    'status': FileProcessStatus.FAILED,
                    'error_message': str(e),
                })
                self.db.commit()
            except:
                pass

            return {
                'status': 'error',
                'message': str(e),
                'file_path': file_path,
            }

    def _extract_content(self, file_path: str) -> str:
        """提取文件内容"""
        try:
            return self.file_parser.parse(file_path)
        except Exception as e:
            logger.error(f"提取内容失败: {file_path}, 错误: {e}")
            return f"[内容提取失败] {str(e)}"

    def _auto_classify(self, content: str, filename: str) -> str:
        """根据内容自动分类"""
        text = (content or '') + ' ' + filename

        # 统计每个类型的关键词匹配次数
        scores = {}
        for evidence_type, keywords in self.EVIDENCE_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[evidence_type] = score

        if scores:
            # 返回得分最高的类型
            return max(scores, key=scores.get)
        return 'OTHER'

    def _generate_summary(self, content: str) -> str:
        """
        生成摘要 - 法律应用专用：证据完整性优先，不得截断任何字符

        重要原则：证据中的每一个字符都可能包含关键法律信息，
        任何截断都可能导致重要事实被遗漏。因此：
        - 5000字以内：保留完整内容
        - 5000字以上：保留完整内容（不再截断）
        - 仅做格式规范化，不做任何内容删减
        """
        if not content:
            return ""

        # 去除首尾空白，保留所有内容
        content = content.strip()

        # 法律应用原则：证据内容不得截断
        # 无论内容多长，都保留完整内容供后续分析
        return content

    def _create_evidence_record(
        self,
        file_record: EvidenceFolderFile,
        content: str,
        category: str,
        summary: str,
    ) -> Optional[EvidenceItem]:
        """创建证据记录 - 根据文件内容和用途自动生成规范名称"""
        try:
            # 生成内容哈希
            content_hash = hashlib.md5((content or '').encode()).hexdigest()

            # 从内容中提取实体标签，用于生成规范名称
            entity_tags = self._extract_entity_tags(content, file_record.file_name)
            proves_facts = self._extract_provable_facts(content)

            # 生成规范显示名称（基于证据类型和证明事实）
            display_name = self._generate_display_name(
                category,
                proves_facts,
                entity_tags,
                file_record.file_name
            )

            evidence = EvidenceItem(
                id=self._generate_evidence_id(),
                case_id=self.case_id,
                source_type='file',
                original_filename=file_record.file_name,
                display_name=display_name,
                file_path=file_record.file_path,
                raw_content=content,
                extracted_content=content,
                summary=summary,
                evidence_type=category,
                status=EvidenceStatus.PROCESSED.value,
                source_party='己方',
                proves_facts=proves_facts,
                entity_tags=entity_tags,
            )
            evidence.generate_content_hash()
            evidence.generate_file_hash()

            self.db.add(evidence)
            self.db.flush()

            logger.info(f"[证据创建] {file_record.file_name} -> {display_name} (类型: {category})")
            return evidence
        except Exception as e:
            logger.error(f"创建证据记录失败: {e}")
            return None

    def _extract_entity_tags(self, content: str, filename: str) -> list:
        """从内容中提取实体标签（当事人、组织、金额等）"""
        tags = []
        text = (content or '') + ' ' + (filename or '')

        # 提取公司名称（常见模式）
        import re
        company_patterns = [
            r'([\u4e00-\u9fa5]{2,10}(?:科技|药业|环保|新材料|生物|工程|建设|装饰|实业|集团|控股|投资|发展|管理|咨询|服务|贸易|进出口|制造|有限|股份|公司))',
        ]
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            for m in matches[:3]:
                if len(m) >= 4 and len(m) <= 30:
                    tags.append({'type': 'ORG', 'value': m})

        # 提取金额
        amount_patterns = [
            r'(\d+(?:,\d{3})*(?:\.\d+)?(?:万|元|千|百))',
        ]
        for pattern in amount_patterns:
            matches = re.findall(pattern, text)
            for m in matches[:2]:
                tags.append({'type': 'AMOUNT', 'value': m})

        # 提取日期
        date_patterns = [
            r'(\d{4}[\u5e74/-]\d{1,2}[\u6708/-]\d{1,2}\u65e5?)',
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            for m in matches[:2]:
                tags.append({'type': 'DATE', 'value': m})

        return tags[:10]

    def _extract_provable_facts(self, content: str) -> list:
        """提取可证明的事实"""
        if not content:
            return []

        facts = []
        import re

        # 事实提取规则
        fact_patterns = [
            (r'(\w+)欠(\w+)[\d,.]+[元万]', '债务关系'),
            (r'(\w+)年(\w+)月(\w+)日', '时间节点'),
            (r'甲方[：:]?(\w+)', '甲方身份'),
            (r'乙方[：:]?(\w+)', '乙方身份'),
            (r'签订', '合同签订'),
            (r'违约', '违约事实'),
            (r'付款|支付|转账', '付款事实'),
            (r'发票|收据', '票据事实'),
            (r'保证金|押金|定金', '保证金事实'),
            (r'采购|购买|订货', '采购事实'),
            (r'合同|协议', '合同关系'),
            (r'通知|告知|催告', '通知事实'),
            (r'解散|注销|停业', '公司变更事实'),
        ]

        for pattern, fact_type in fact_patterns:
            matches = re.findall(pattern, content)
            if matches:
                val = matches[0]
                if isinstance(val, tuple):
                    val = ''.join(str(v) for v in val if v)
                facts.append({
                    'fact': f"{fact_type}: {val[:50]}",
                    'fact_type': fact_type,
                    'confidence': 0.7
                })

        return facts[:5]

    def _generate_display_name(self, evidence_type: str, proves_facts: list, entity_tags: list, original_filename: str) -> str:
        """
        根据证据类型和司法作用生成规范显示名称

        命名规则：[证据类型简称]-[关键主体/事由]
        """
        if not evidence_type or evidence_type == 'OTHER':
            # 无法分类，使用原始文件名截断
            base = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
            # 去除常见前缀噪声
            for prefix in ['企业微信', '微信', '钉钉', 'QQ', '邮件', 'email_', 'IMG_', 'DOC_', '1_', '转PDF_']:
                if base.startswith(prefix):
                    base = base[len(prefix):]
                    break
            return f"其他证据-{base[:15]}" if base else "其他证据"

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
            # 回退：使用原始文件名（去除扩展名和噪声前缀）
            base = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
            for prefix in ['企业微信', '微信', '钉钉', 'QQ', '邮件', 'email_', 'IMG_', 'DOC_', '1_', '转PDF_']:
                if base.startswith(prefix):
                    base = base[len(prefix):]
                    break
            return f"{type_name}-{base[:15]}" if base else type_name

    def _generate_evidence_id(self) -> str:
        """生成唯一证据ID"""
        import uuid
        return str(uuid.uuid4())

    # ==================== 辅助方法 ====================

    def _get_file_hash(self, file_path: str) -> str:
        """计算文件MD5哈希"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败: {file_path}, 错误: {e}")
            return ""

    def _get_existing_file_hashes(self) -> Set[str]:
        """获取已处理文件的哈希集合"""
        records = self.db.query(EvidenceFolderFile.file_hash).filter(
            EvidenceFolderFile.case_id == self.case_id
        ).all()
        return {r[0] for r in records if r[0]}

    def get_file_records(
        self,
        status: str = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """获取文件记录列表"""
        query = self.db.query(EvidenceFolderFile).filter(
            EvidenceFolderFile.case_id == self.case_id
        )

        if status:
            query = query.filter(EvidenceFolderFile.status == status)

        total = query.count()
        records = query.order_by(EvidenceFolderFile.detected_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'records': [r.to_dict() for r in records]
        }

    def get_folder_status(self) -> Dict[str, Any]:
        """获取文件夹状态"""
        case = self.get_case()
        if not case:
            return {'error': '案件不存在'}

        folder_path = case.evidence_folder_path
        exists = os.path.exists(folder_path) if folder_path else False

        # 统计
        stats = {
            'total': 0,
            'processed': 0,
            'pending': 0,
            'failed': 0,
            'skipped': 0,
        }

        if exists:
            counts = self.db.query(
                EvidenceFolderFile.status,
                EvidenceFolderFile.id
            ).filter(
                EvidenceFolderFile.case_id == self.case_id
            ).all()

            for status, _ in counts:
                stats['total'] += 1
                if status == FileProcessStatus.COMPLETED:
                    stats['processed'] += 1
                elif status == FileProcessStatus.PENDING:
                    stats['pending'] += 1
                elif status == FileProcessStatus.FAILED:
                    stats['failed'] += 1
                elif status == FileProcessStatus.SKIPPED:
                    stats['skipped'] += 1

        # 最近文件
        recent = self.db.query(EvidenceFolderFile).filter(
            EvidenceFolderFile.case_id == self.case_id
        ).order_by(EvidenceFolderFile.detected_at.desc()).limit(5).all()

        return {
            'case_id': self.case_id,
            'folder_path': folder_path,
            'folder_exists': exists,
            'is_enabled': case.evidence_folder_enabled,
            'last_scan_time': case.evidence_last_scan_time.isoformat() if case.evidence_last_scan_time else None,
            'last_sync_count': case.evidence_last_sync_count,
            'stats': stats,
            'recent_files': [r.to_dict() for r in recent],
        }

    def delete_file_record(self, file_record_id: int) -> bool:
        """删除文件记录"""
        record = self.db.query(EvidenceFolderFile).filter(
            EvidenceFolderFile.id == file_record_id,
            EvidenceFolderFile.case_id == self.case_id
        ).first()

        if record:
            # 同时删除关联的证据记录
            if record.evidence_id:
                evidence = self.db.query(EvidenceItem).filter(
                    EvidenceItem.id == record.evidence_id
                ).first()
                if evidence:
                    self.db.delete(evidence)

            self.db.delete(record)
            self.db.commit()
            return True
        return False

    def reprocess_file(self, file_record_id: int) -> Dict[str, Any]:
        """重新处理文件"""
        record = self.db.query(EvidenceFolderFile).filter(
            EvidenceFolderFile.id == file_record_id,
            EvidenceFolderFile.case_id == self.case_id
        ).first()

        if not record:
            return {'status': 'error', 'message': '文件记录不存在'}

        # 清除哈希，避免被去重逻辑跳过
        record.file_hash = None
        record.content_hash = None
        record.status = FileProcessStatus.PENDING
        record.processed = False
        record.error_message = None
        self.db.commit()

        # 删除关联的证据记录
        if record.evidence_id:
            evidence = self.db.query(EvidenceItem).filter(
                EvidenceItem.id == record.evidence_id
            ).first()
            if evidence:
                self.db.delete(evidence)
            record.evidence_id = None
            self.db.commit()

        # 创建增量扫描记录用于关联
        scan = EvidenceFolderScan(
            case_id=self.case_id,
            scan_type=ScanType.INCREMENTAL,
            status=ScanStatus.RUNNING,
            scan_path=record.file_path,
        )
        self.db.add(scan)
        self.db.commit()

        # 重新处理（传入 scan_id）
        return self._process_single_file(record.file_path, scan.id)

    def close(self):
        """关闭数据库连接"""
        if self.db:
            self.db.close()

