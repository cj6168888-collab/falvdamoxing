"""
AI 数据提取服务 - 统一处理 LLM 输出的结构化提取与数据库同步
"""
import re
import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

logger = logging.getLogger(__name__)

from app.models.case import Case
from app.models.case_claim import CaseClaim

class ExtractionService:
    """负责从 AI 文本中提取并持久化法律事实"""

    def auto_update_case_parties(self, db: Session, case_id: int, text: str) -> Dict[str, bool]:
        """
        从 AI 分析文本中提取当事人并更新数据库
        """
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return {"updated": False, "error": True}

        updated = False
        results = {"plaintiff": False, "defendant": False, "third_party": False}

        try:
            # 强化正则匹配
            patterns = {
                "plaintiff": [r'原告[是为：:]\s*([^\n，。,;]{2,50})', r'委托人[是为：:]\s*([^\n，。,;]{2,50})'],
                "defendant": [r'被告[是为：:]\s*([^\n，。,;]{2,50})', r'相对人[是为：:]\s*([^\n，。,;]{2,50})'],
                "third_party": [r'第三人[是为：:]\s*([^\n，。,;]{2,50})']
            }

            for key, pattern_list in patterns.items():
                for p in pattern_list:
                    match = re.search(p, text)
                    if match and match.group(1).strip():
                        val = match.group(1).strip()
                        # 逻辑：如果当前为空，或者新提取的名称更长（通常包含更完整信息），则更新
                        current_val = getattr(case, key)
                        if not current_val or len(val) > len(current_val):
                            setattr(case, key, val)
                            results[key] = True
                            updated = True
                            break

            if updated:
                db.commit()
                logger.info(f"[Extraction] 案件 {case_id} 当事人信息已自动同步")
            
            return {"updated": updated, "results": results}
        except Exception as e:
            logger.error(f"[Extraction] 当事人提取失败: {e}")
            return {"updated": False, "error": True}

    def extract_json_from_markdown(self, text: str) -> Optional[Dict]:
        """从 Markdown 代码块中安全提取 JSON"""
        if not text:
            return None
            
        # 优先匹配 ```json ... ```
        json_match = re.search(r'```json\s*([\s\S]*?)```', text)
        if json_match:
            try:
                content = json_match.group(1).strip()
                # 处理可能的转义字符
                return json.loads(content)
            except Exception as e:
                logger.warning(f"[Extraction] JSON 解析失败 (Markdown): {e}")

        # 次优匹配大括号结构
        try:
            # 寻找第一个 { 和最后一个 }
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
        except Exception:
            pass
            
        return None

    def sync_suggested_claims(self, db: Session, case_id: int, claims_data: List[Dict[str, Any]]) -> int:
        """
        从 AI 建议中同步诉讼请求（战役）
        """
        if not claims_data:
            return 0
            
        added_count = 0
        for item in claims_data:
            title = item.get("title") or item.get("claim")
            if not title:
                continue
                
            # 检查是否已存在类似标题的战役
            exists = db.query(CaseClaim).filter(
                CaseClaim.case_id == case_id,
                CaseClaim.title == title
            ).first()
            
            if not exists:
                new_claim = CaseClaim(
                    case_id=case_id,
                    title=title,
                    amount=item.get("amount", 0),
                    description=item.get("description", ""),
                    status="suggested"
                )
                db.add(new_claim)
                added_count += 1
        
        if added_count > 0:
            db.commit()
            
        return added_count

extraction_service = ExtractionService()
