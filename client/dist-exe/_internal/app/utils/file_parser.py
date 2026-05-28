"""
文件解析工具
支持 PDF、Word、图片等格式
"""
import os
import re
from typing import Optional, Tuple
import hashlib


class FileParser:
    """文件解析器"""

    # 允许的文件扩展名（白名单）
    SUPPORTED_TYPES = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".doc": "doc",
        ".txt": "txt",
        ".jpg": "image",
        ".jpeg": "image",
        ".png": "image",
        ".bmp": "image",
        ".tiff": "image"
    }

    # 禁止的文件魔术头（部分常见危险类型）
    FORBIDDEN_SIGNATURES = [
        (b"MZ", "可执行文件 (.exe)"),
        (b"%PDF", None),   # PDF本身允许，但排除多重包装
        (b"<script", "HTML/脚本注入文件"),
        (b"<?php", "PHP 文件"),
        (b"<%", "ASP 文件"),
        (b"\x89PNG\r\n\x1a\n", None),  # PNG 正常，跳过
    ]

    def __init__(self, storage_path: str = "./data/files"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    def _detect_file_type(self, content: bytes, filename: str) -> bool:
        """通过文件头魔术数检测真实文件类型，拒绝伪装文件"""
        # 检查魔术头
        for sig, label in self.FORBIDDEN_SIGNATURES:
            if content[:len(sig)] == sig:
                if label is not None:
                    return False
        return True

    def parse(self, file_path: str) -> str:
        """
        解析文件内容

        Args:
            file_path: 文件路径

        Returns:
            提取的文本内容
        """
        ext = os.path.splitext(file_path)[1].lower()
        file_type = self.SUPPORTED_TYPES.get(ext, "unknown")

        if file_type == "pdf":
            return self._parse_pdf(file_path)
        elif file_type in ["docx", "doc"]:
            return self._parse_docx(file_path)
        elif file_type == "txt":
            return self._parse_txt(file_path)
        elif file_type == "image":
            return self._parse_image(file_path)
        else:
            return f"不支持的文件类型: {ext}"

    def _parse_pdf(self, file_path: str) -> str:
        """解析 PDF 文件 - 支持文字版和扫描件"""
        try:
            # 方法1: PyPDF2 提取文字
            from PyPDF2 import PdfReader

            reader = PdfReader(file_path)
            text_parts = []

            for page in reader.pages:
                try:
                    text = page.extract_text()
                    if text and text.strip():
                        text_parts.append(text.strip())
                except Exception as e:
                    print(f"Page text extraction failed: {e}")
                    continue

            # 检查是否为扫描件（无文字内容）
            if not text_parts or not any(t.strip() for t in text_parts if t):
                # 尝试将 PDF 页面转为图片进行 OCR
                return self._parse_pdf_scanned(file_path)

            return "\n\n".join(text_parts)

        except ImportError:
            return "[PDF 解析失败] 需要安装 PyPDF2: pip install PyPDF2"
        except Exception as e:
            return f"[PDF 解析失败] {str(e)}"

    def _parse_pdf_scanned(self, file_path: str) -> str:
        """解析扫描件 PDF (通过 OCR)"""
        # 尝试使用 fitz (PyMuPDF) 转为图片
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)

            if len(doc) == 0:
                return "[扫描件 PDF] 该 PDF 无有效页面"

            print(f"[PDF OCR] Processing PDF with {len(doc)} pages...")
            ocr_texts = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                # 将页面转为图片 (更高分辨率)
                pix = page.get_pixmap(dpi=300)
                img_path = file_path + f"_page_{page_num}.png"
                pix.save(img_path)
                print(f"[PDF OCR] Processing page {page_num + 1}, saved to {img_path}")

                # 对图片进行 OCR
                ocr_result = self._parse_image(img_path)
                print(f"[PDF OCR] Page {page_num + 1} OCR result length: {len(ocr_result) if ocr_result else 0}")

                # 检查是否识别成功
                if ocr_result and not ocr_result.startswith("[图片识别失败]") and \
                   not ocr_result.startswith("[图片 OCR") and len(ocr_result.strip()) > 10:
                    ocr_texts.append(f"[第 {page_num + 1} 页]\n{ocr_result}")

                # 清理临时图片
                try:
                    import os
                    os.remove(img_path)
                except:
                    pass

            if ocr_texts:
                return "[扫描件 OCR 识别结果]\n\n" + "\n\n".join(ocr_texts)
            else:
                return "[扫描件 PDF] 该 PDF 为扫描件，OCR 识别失败。请确保：\n1. PaddleOCR 模型已正确下载\n2. 图片清晰可读\n3. 已在后端终端查看详细 OCR 错误日志"

        except ImportError:
            return "[扫描件 PDF] 需要安装 PyMuPDF: pip install PyMuPDF"
        except Exception as ocr_error:
            import traceback
            print(f"[PDF OCR] Error: {type(ocr_error).__name__}: {ocr_error}")
            traceback.print_exc()
            return f"[扫描件 PDF] OCR 处理出错: {type(ocr_error).__name__}: {str(ocr_error)}"

    def _parse_docx(self, file_path: str) -> str:
        """解析 Word 文件"""
        try:
            from docx import Document

            doc = Document(file_path)
            text_parts = []

            # 提取段落
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)

            # 提取表格
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_parts.append(" | ".join(row_text))

            return "\n".join(text_parts)
        except ImportError:
            return "Word 解析需要安装 python-docx: pip install python-docx"
        except Exception as e:
            return f"Word 解析失败: {str(e)}"

    def _parse_txt(self, file_path: str) -> str:
        """解析文本文件"""
        try:
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            return "文本文件编码不支持"
        except Exception as e:
            return f"文本解析失败: {str(e)}"

    def _parse_image(self, file_path: str) -> str:
        """解析图片文件 (OCR) - 使用 RapidOCR 作为主要引擎"""
        # 方案1: RapidOCR (基于 ONNX Runtime，更稳定)
        try:
            from rapidocr_onnxruntime import RapidOCR
            ocr = RapidOCR()
            result, elapse = ocr(file_path)
            if result:
                text_parts = []
                for line in result:
                    # line format: [box, text, confidence]
                    if len(line) >= 2 and line[1] and line[1].strip():
                        text_parts.append(line[1].strip())
                if text_parts:
                    return "\n".join(text_parts)
        except ImportError:
            pass  # RapidOCR 未安装
        except Exception as e:
            print(f"RapidOCR 识别失败 [{os.path.basename(file_path)}]: {e}")

        # 方案2: PaddleOCR (备用)
        try:
            import os as _os
            _os.environ['FLAGS_use_mkldnn'] = '0'
            _os.environ['FLAGS_use_onednn'] = '0'
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False, use_gpu=False, enable_mkldnn=False)
            result = ocr.ocr(file_path)
            text_parts = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        text = line[1][0] if isinstance(line[1], tuple) else str(line[1])
                        if text and text.strip():
                            text_parts.append(text.strip())
            if text_parts:
                return "\n".join(text_parts)
        except ImportError:
            pass
        except Exception as e:
            print(f"PaddleOCR 识别失败 [{os.path.basename(file_path)}]: {e}")

        # 方案3: Tesseract OCR (最后备用)
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang='chi_sim+eng')
            if text and text.strip():
                return text.strip()
        except Exception:
            pass

        # 所有 OCR 方案都失败，返回原始文件名
        return f"[图片文件] {os.path.basename(file_path)}"

    def save_file(self, content: bytes, filename: str, case_id: int) -> Tuple[str, str]:
        """
        保存上传的文件

        Args:
            content: 文件内容
            filename: 原始文件名
            case_id: 案件 ID

        Returns:
            (存储路径, 文件哈希)
        """
        # 验证文件类型（防止扩展名欺骗）
        if not self._detect_file_type(content, filename):
            raise ValueError("文件类型与内容不匹配，可能存在伪装风险")

        # 危险字符过滤（防止路径遍历）
        # 保留中文、字母、数字、点、下划线、连字符、括号等常见文件名合法字符
        safe_filename = re.sub(r'[<>"|?*\\/:]', '_', filename)
        if not safe_filename or safe_filename.startswith('.'):
            safe_filename = 'uploaded_file' + os.path.splitext(filename)[1]

        # 生成唯一文件名
        ext = os.path.splitext(safe_filename)[1].lower()
        file_hash = hashlib.md5(content).hexdigest()
        new_filename = f"{case_id}_{file_hash}{ext}"

        # 创建案件目录
        case_dir = os.path.join(self.storage_path, str(case_id))
        os.makedirs(case_dir, exist_ok=True)

        # 保存文件
        file_path = os.path.join(case_dir, new_filename)
        with open(file_path, 'wb') as f:
            f.write(content)

        return file_path, file_hash

    def get_file_type(self, filename: str) -> str:
        """获取文件类型"""
        ext = os.path.splitext(filename)[1].lower()
        return self.SUPPORTED_TYPES.get(ext, "unknown")


# 单例模式
file_parser = FileParser()
