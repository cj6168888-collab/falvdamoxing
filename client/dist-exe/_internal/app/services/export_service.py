"""
统一导出服务
支持将各种生成内容导出为 PDF、Word、图片 等格式
"""
import os
import io
import uuid
import tempfile
from datetime import datetime
from typing import Optional, Union, Dict, Any
from pathlib import Path

from app.config import settings


class ExportService:
    """导出服务 - 支持多种格式"""

    # 支持的导出格式
    SUPPORTED_FORMATS = ["pdf", "docx", "markdown", "txt", "html", "png", "jpg", "jpeg"]

    # 格式对应的MIME类型
    MIME_TYPES = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "markdown": "text/markdown",
        "txt": "text/plain",
        "html": "text/html",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg"
    }

    def __init__(self):
        self.export_dir = getattr(settings, 'EXPORT_DIR', 'exports')
        os.makedirs(self.export_dir, exist_ok=True)

    def export_content(
        self,
        content: str,
        title: str,
        output_format: str = "pdf",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        导出内容到指定格式

        Args:
            content: 要导出的内容（支持Markdown格式）
            title: 文档标题
            output_format: 输出格式 (pdf/docx/markdown/txt/html)
            metadata: 元数据信息

        Returns:
            包含文件路径、下载URL等信息的字典
        """
        if output_format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的格式: {output_format}")

        # 生成文件名
        safe_title = self._sanitize_filename(title)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_title}_{timestamp}"

        # 创建导出目录
        case_dir = os.path.join(self.export_dir, f"case_{metadata.get('case_id', 'general')}" if metadata else "general")
        os.makedirs(case_dir, exist_ok=True)

        file_path = None
        file_size = 0
        actual_format = output_format

        try:
            if output_format == "pdf":
                # 尝试PDF，如果失败则使用HTML
                try:
                    file_path = self._export_to_pdf(content, case_dir, filename, metadata)
                except Exception:
                    # PDF导出失败，自动使用HTML
                    file_path = self._export_to_html(content, case_dir, filename, metadata)
                    actual_format = "html"  # 实际格式为HTML
            elif output_format == "docx":
                try:
                    file_path = self._export_to_docx(content, case_dir, filename, metadata)
                except Exception:
                    # Word导出失败，使用HTML
                    file_path = self._export_to_html(content, case_dir, filename, metadata)
                    actual_format = "html"
            elif output_format == "markdown":
                file_path = self._export_to_markdown(content, case_dir, filename, metadata)
            elif output_format == "txt":
                file_path = self._export_to_txt(content, case_dir, filename, metadata)
            elif output_format == "html":
                file_path = self._export_to_html(content, case_dir, filename, metadata)
            elif output_format in ["png", "jpg", "jpeg"]:
                try:
                    file_path = self._export_to_image(content, case_dir, filename, metadata, output_format)
                except Exception as e:
                    # 图片导出失败，使用HTML
                    file_path = self._export_to_html(content, case_dir, filename, metadata)
                    actual_format = "html"

            if file_path and os.path.exists(file_path):
                file_size = os.path.getsize(file_path)

            return {
                "success": True,
                "file_path": file_path,
                "filename": os.path.basename(file_path) if file_path else None,
                "format_used": actual_format,  # 返回实际使用的格式
                "requested_format": output_format,  # 用户请求的格式
                "mime_type": self.MIME_TYPES.get(actual_format, "application/octet-stream"),
                "file_size": file_size,
                "generated_at": datetime.now().isoformat(),
                "download_url": f"/api/exports/download/{os.path.basename(file_path)}" if file_path else None,
                "note": "PDF格式已自动转换为HTML，可在浏览器中打印为PDF" if actual_format == "html" and output_format == "pdf" else None
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "format": output_format
            }

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符"""
        import re
        # 移除非法的文件名字符
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # 限制长度
        return filename[:50] if len(filename) > 50 else filename

    def _export_to_markdown(
        self,
        content: str,
        output_dir: str,
        filename: str,
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """导出为 Markdown 格式"""
        filepath = os.path.join(output_dir, f"{filename}.md")

        # 添加头部信息
        header = f"""---
title: {metadata.get('title', filename) if metadata else filename}
case_id: {metadata.get('case_id', '') if metadata else ''}
generated_at: {datetime.now().isoformat()}
document_type: {metadata.get('document_type', '') if metadata else ''}
---

"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(header)
            f.write(content)

        return filepath

    def _export_to_txt(
        self,
        content: str,
        output_dir: str,
        filename: str,
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """导出为纯文本格式（移除Markdown格式）"""
        filepath = os.path.join(output_dir, f"{filename}.txt")

        # 简单的Markdown转纯文本
        text = self._markdown_to_plain_text(content)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)

        return filepath

    def _export_to_html(
        self,
        content: str,
        output_dir: str,
        filename: str,
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """导出为 HTML 格式"""
        filepath = os.path.join(output_dir, f"{filename}.html")

        # 简单的Markdown转HTML
        html_content = self._markdown_to_html(content)

        # 元数据和标题
        doc_title = metadata.get('title', filename) if metadata else filename
        case_id = metadata.get('case_id', 'N/A') if metadata else 'N/A'
        doc_type = metadata.get('document_type', '') if metadata else ''
        gen_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>""" + doc_title + """</title>
    <style>
        body {
            font-family: "Microsoft YaHei", "SimSun", serif;
            line-height: 1.8;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            color: #333;
        }
        h1 { color: #1a1a1a; border-bottom: 2px solid #1890ff; padding-bottom: 10px; }
        h2 { color: #333; margin-top: 30px; }
        h3 { color: #555; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background-color: #f5f5f5; }
        blockquote { border-left: 4px solid #1890ff; margin: 20px 0; padding: 10px 20px; background-color: #f9f9f9; }
        code { background-color: #f5f5f5; padding: 2px 6px; border-radius: 3px; }
        pre { background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .metadata {
            background-color: #e6f7ff;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
            font-size: 14px;
        }
        /* 证据图片样式 - 不变形，保持原始比例 */
        .evidence-image {
            page-break-inside: avoid;
            margin: 15px 0;
            padding: 10px;
            background: #fafafa;
            border: 1px solid #eee;
        }
        .evidence-image img {
            width: 100%;
            height: auto;
            display: block;
            border: 1px solid #ddd;
        }
        .evidence-image p {
            font-size: 12px;
            color: #888;
            text-align: center;
            margin: 8px 0 0 0;
        }
        @media print {
            .evidence-image { page-break-inside: avoid; }
        }
    </style>
</head>
<body>
    """ + html_content + """
    <hr>
    <footer style="text-align: center; color: #999; margin-top: 50px; font-size: 12px;">
        <p>本文档由法律大模型自动生成 | 生成时间: """ + gen_time + """</p>
    </footer>
</body>
</html>
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

        return filepath

    def _export_to_pdf(
        self,
        content: str,
        output_dir: str,
        filename: str,
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """导出为 PDF 格式"""
        filepath = os.path.join(output_dir, f"{filename}.pdf")

        try:
            # 方法1: 使用reportlab直接生成PDF
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            # 注册中文字体
            try:
                pdfmetrics.registerFont(TTFont('SimSun', 'C:/Windows/Fonts/simsun.ttc'))
                pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
                font_name = 'SimSun'
                bold_font_name = 'SimHei'
            except Exception:
                font_name = 'Helvetica'
                bold_font_name = 'Helvetica'

            # 创建PDF
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )

            # 创建样式
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=bold_font_name,
                fontSize=18,
                spaceAfter=20,
                alignment=1  # 居中
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontName=bold_font_name,
                fontSize=14,
                spaceBefore=15,
                spaceAfter=10,
                textColor='#333333'
            )

            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=11,
                leading=18,
                spaceAfter=8
            )

            # 转换Markdown为PDF内容
            story = []

            # 添加标题
            doc_title = metadata.get('title', filename) if metadata else filename
            story.append(Paragraph(doc_title, title_style))
            story.append(Spacer(1, 0.3*cm))

            # 添加元数据
            if metadata:
                meta_text = f"<b>案件编号:</b> {metadata.get('case_id', 'N/A')} | <b>文档类型:</b> {metadata.get('document_type', 'N/A')} | <b>生成时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                story.append(Paragraph(meta_text, body_style))
                story.append(Spacer(1, 0.5*cm))

            # 解析Markdown内容
            lines = content.split('\n')
            in_table = False
            table_rows = []

            for line in lines:
                line_orig = line.strip()

                if not line_orig:
                    if in_table:
                        in_table = False
                    story.append(Spacer(1, 0.2*cm))
                    continue

                # 标题
                if line_orig.startswith('### '):
                    story.append(Paragraph(line_orig[4:], heading_style))
                elif line_orig.startswith('## '):
                    story.append(Paragraph(line_orig[3:], heading_style))
                elif line_orig.startswith('# '):
                    story.append(Paragraph(line_orig[2:], title_style))

                # 表格
                elif line_orig.startswith('|'):
                    # 跳过表头分隔符
                    if '---' in line_orig:
                        continue
                    # 处理表格行
                    cells = [c.strip() for c in line_orig.strip('|').split('|')]
                    table_rows.append(cells)

                # 列表
                elif line_orig.startswith('- ') or line_orig.startswith('* '):
                    # 检查是否是图片（以!开头）
                    if line_orig.startswith('- ![') or line_orig.startswith('* !['):
                        # 嵌入图片: - ![name](file://path)
                        import re as regex_module
                        img_match = regex_module.search(r'!\[([^\]]*)\]\((file:///[^\)]+)\)', line_orig)
                        if not img_match:
                            img_match = regex_module.search(r'!\[([^\]]*)\]\((file://[^)]+)\)', line_orig)
                        if img_match:
                            img_name = img_match.group(1)
                            img_path = img_match.group(2)
                            # 去掉 file:/// 前缀并转换路径
                            img_path = img_path.replace('file:///', '')
                            img_path = img_path.replace('file://', '')
                            # Windows路径可能需要转换
                            img_path = img_path.replace('/', '\\')
                            if os.path.exists(img_path):
                                try:
                                    from reportlab.platypus import Image as RLImage
                                    img_obj = RLImage(img_path, width=10*cm, height=8*cm)
                                    img_obj.hAlign = 'CENTER'
                                    story.append(img_obj)
                                    story.append(Paragraph(f"▲ {img_name}", body_style))
                                    story.append(Spacer(1, 0.3*cm))
                                    continue
                                except Exception:
                                    pass  # 图片加载失败，fall through到文字显示
                            story.append(Paragraph(f"• {line_orig}", body_style))
                    else:
                        story.append(Paragraph(f"• {line_orig[2:]}", body_style))

                # 图片行（非列表格式）: ![name](file://path) 或 <img> HTML标签
                elif line_orig.startswith('![') or '<img' in line_orig:
                    import re as regex_module
                    # 处理 Markdown 图片
                    img_match = regex_module.search(r'!\[([^\]]*)\]\((file://[^)]+)\)', line_orig)
                    if img_match:
                        img_name = img_match.group(1)
                        img_path = img_match.group(2).replace('file:///', '').replace('file://', '').replace('/', '\\')
                        if os.path.exists(img_path):
                            try:
                                from reportlab.platypus import Image as RLImage
                                # 使用更大尺寸，保持原始比例
                                img_obj = RLImage(img_path, width=15*cm, height=12*cm)
                                img_obj.hAlign = 'CENTER'
                                story.append(img_obj)
                                story.append(Paragraph(f"▲ {img_name}", body_style))
                                story.append(Spacer(1, 0.5*cm))
                                continue
                            except Exception:
                                pass
                        story.append(Paragraph(f"[图片] {img_path}", body_style))
                    # 处理 HTML img 标签
                    elif '<img' in line_orig:
                        html_img_match = regex_module.search(r'<img[^>]+src=["\'](file://[^"\']+)["\']', line_orig)
                        if html_img_match:
                            img_path = html_img_match.group(1).replace('file:///', '').replace('file://', '').replace('/', '\\')
                            if os.path.exists(img_path):
                                try:
                                    from reportlab.platypus import Image as RLImage
                                    img_obj = RLImage(img_path, width=15*cm, height=12*cm)
                                    img_obj.hAlign = 'CENTER'
                                    story.append(img_obj)
                                    story.append(Spacer(1, 0.5*cm))
                                    continue
                                except Exception:
                                    pass

                # 普通段落
                else:
                    # 清理Markdown格式
                    clean_line = self._clean_markdown_for_pdf(line_orig)
                    if clean_line:
                        story.append(Paragraph(clean_line, body_style))

            # 生成PDF
            doc.build(story)
            return filepath

        except ImportError as e:
            # 如果reportlab不可用，生成HTML然后提示用户
            html_path = self._export_to_html(content, output_dir, filename, metadata)
            # 将HTML重命名为.html，添加提示
            hint_path = os.path.join(output_dir, f"{filename}_hint.txt")
            with open(hint_path, 'w', encoding='utf-8') as f:
                f.write(f"PDF导出需要安装reportlab库。\nHTML版本已生成: {html_path}\n\n")
                f.write(f"请使用以下命令安装:\npip install reportlab\n\n")
                f.write("或者在浏览器中打开HTML文件，选择打印为PDF。")
            return html_path  # 返回HTML文件作为备选

        except Exception as e:
            # 回退到HTML
            return self._export_to_html(content, output_dir, filename, metadata)

    def _export_to_docx(
        self,
        content: str,
        output_dir: str,
        filename: str,
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """导出为 Word (DOCX) 格式"""
        filepath = os.path.join(output_dir, f"{filename}.docx")

        try:
            from docx import Document
            from docx.shared import Pt, RGBColor, Inches
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.enum.style import WD_STYLE_TYPE

            doc = Document()

            # 设置默认字体
            style = doc.styles['Normal']
            font = style.font
            font.name = '宋体'
            font.size = Pt(11)

            # 添加标题
            doc_title = metadata.get('title', filename) if metadata else filename
            title_para = doc.add_heading(doc_title, level=0)
            title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # 添加元数据
            if metadata:
                meta_para = doc.add_paragraph()
                meta_para.add_run(f"案件编号: {metadata.get('case_id', 'N/A')} | ").font.size = Pt(9)
                meta_para.add_run(f"文档类型: {metadata.get('document_type', 'N/A')} | ").font.size = Pt(9)
                meta_para.add_run(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}").font.size = Pt(9)

            doc.add_paragraph()  # 空行

            # 解析Markdown内容
            lines = content.split('\n')
            in_table = False

            for line in lines:
                line = line.strip()

                if not line:
                    continue

                # 标题
                if line.startswith('### '):
                    doc.add_heading(line[4:], level=3)
                elif line.startswith('## '):
                    doc.add_heading(line[3:], level=2)
                elif line.startswith('# '):
                    doc.add_heading(line[2:], level=1)

                # 表格
                elif line.startswith('|'):
                    if '---' in line:
                        continue
                    cells = [c.strip() for c in line.strip('|').split('|')]
                    table = doc.add_table(rows=1, cols=len(cells))
                    table.style = 'Table Grid'
                    hdr_cells = table.rows[0].cells
                    for i, cell in enumerate(cells):
                        hdr_cells[i].text = cell

                # 列表中的图片: - ![name](file://path) 或 HTML img
                elif line.startswith('- ![') or line.startswith('* ![') or '<img' in line:
                    import re as regex_module
                    # 处理 Markdown 图片
                    img_match = regex_module.search(r'!\[([^\]]*)\]\((file://[^)]+)\)', line)
                    if img_match:
                        img_name = img_match.group(1)
                        img_path = img_match.group(2).replace('file:///', '').replace('file://', '')
                        img_path = img_path.replace('/', '\\')
                        if os.path.exists(img_path):
                            try:
                                from docx.shared import Cm
                                para = doc.add_paragraph()
                                run = para.add_run()
                                run.add_picture(img_path, width=Cm(16))  # 增大到16cm
                                cap = doc.add_paragraph(f"▲ {img_name}")
                                cap.runs[0].font.size = Pt(9)
                                cap.runs[0].italic = True
                                continue
                            except Exception:
                                pass
                    # 处理 HTML img 标签
                    elif '<img' in line:
                        html_img_match = regex_module.search(r'<img[^>]+src=["\'](file://[^"\']+)["\']', line)
                        if html_img_match:
                            img_path = html_img_match.group(1).replace('file:///', '').replace('file://', '').replace('/', '\\')
                            if os.path.exists(img_path):
                                try:
                                    from docx.shared import Cm
                                    para = doc.add_paragraph()
                                    run = para.add_run()
                                    run.add_picture(img_path, width=Cm(16))  # 增大到16cm
                                    continue
                                except Exception:
                                    pass
                    doc.add_paragraph(line[2:], style='List Bullet')

                # 列表（非图片）
                elif line.startswith('- ') or line.startswith('* '):
                    doc.add_paragraph(line[2:], style='List Bullet')

                # 引用
                elif line.startswith('>'):
                    para = doc.add_paragraph(line[1:].strip())
                    para.style = 'Quote'

                # 普通段落
                else:
                    clean_line = self._clean_markdown_for_docx(line)
                    if clean_line:
                        doc.add_paragraph(clean_line)

            # 添加页脚
            doc.add_paragraph()
            footer = doc.add_paragraph("─" * 40)
            footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
            footer_text = doc.add_paragraph(f"本文档由法律大模型自动生成 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            footer_text.alignment = WD_ALIGN_PARAGRAPH.CENTER
            footer_text.runs[0].font.size = Pt(9)
            footer_text.runs[0].font.color.rgb = RGBColor(0x99, 0x99, 0x99)

            # 保存文档
            doc.save(filepath)
            return filepath

        except ImportError:
            # 如果python-docx不可用，回退到HTML
            html_path = self._export_to_html(content, output_dir, filename, metadata)
            hint_path = os.path.join(output_dir, f"{filename}_word_fallback.txt")
            with open(hint_path, 'w', encoding='utf-8') as f:
                f.write(f"Word导出需要安装python-docx库。\nHTML版本已生成: {html_path}\n\n")
                f.write(f"请使用以下命令安装:\npip install python-docx\n\n")
                f.write("或者在浏览器中打开HTML文件，复制内容到Word。")
            return html_path

        except Exception as e:
            return self._export_to_html(content, output_dir, filename, metadata)

    def _markdown_to_plain_text(self, content: str) -> str:
        """将Markdown转换为纯文本"""
        import re

        lines = content.split('\n')
        result = []

        for line in lines:
            line = line.strip()

            # 移除标题标记
            if line.startswith('#'):
                line = re.sub(r'^#+\s*', '', line)

            # 移除链接但保留文字
            line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)

            # 移除加粗和斜体标记
            line = re.sub(r'\*\*([^\*]+)\*\*', r'\1', line)
            line = re.sub(r'\*([^\*]+)\*', r'\1', line)

            # 移除表格分隔符
            if '---' in line:
                continue

            result.append(line)

        return '\n'.join(result)

    def _markdown_to_html(self, content: str) -> str:
        """将Markdown转换为HTML"""
        import re

        lines = content.split('\n')
        result = []
        in_list = False
        in_table = False

        for line in lines:
            line = line.strip()

            if not line:
                if in_list:
                    in_list = False
                    result.append('</ul>')
                if in_table:
                    in_table = False
                    result.append('</table>')
                result.append('')
                continue

            # 标题
            if line.startswith('### '):
                if in_list:
                    in_list = False
                    result.append('</ul>')
                result.append(f'<h3>{line[4:]}</h3>')
            elif line.startswith('## '):
                if in_list:
                    in_list = False
                    result.append('</ul>')
                result.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('# '):
                if in_list:
                    in_list = False
                    result.append('</ul>')
                result.append(f'<h1>{line[2:]}</h1>')

            # 表格
            elif line.startswith('|'):
                if '---' in line:
                    continue
                if not in_table:
                    in_table = True
                    result.append('<table border="1" cellpadding="5" style="border-collapse: collapse; width: 100%;">')
                cells = [c.strip() for c in line.strip('|').split('|')]
                result.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')

            # 列表
            elif line.startswith('- ') or line.startswith('* '):
                if not in_list:
                    in_list = True
                    result.append('<ul>')
                result.append(f'<li>{line[2:]}</li>')

            # 引用
            elif line.startswith('>'):
                result.append(f'<blockquote>{line[1:].strip()}</blockquote>')

            # 普通段落
            else:
                # 处理内联格式 - 使用更安全的正则
                try:
                    line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
                    line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
                    line = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', line)
                except re.error:
                    pass  # 忽略无效正则
                result.append(f'<p>{line}</p>')

        if in_list:
            result.append('</ul>')
        if in_table:
            result.append('</table>')

        return '\n'.join(result)

    def _clean_markdown_for_pdf(self, content: str) -> str:
        """清理Markdown格式用于PDF"""
        import re

        # 移除链接但保留文字
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)

        # 保留加粗和斜体
        # content = re.sub(r'\*\*([^\*]+)\*\*', r'<b>\1</b>', content)
        # content = re.sub(r'\*([^\*]+)\*', r'<i>\1</i>', content)

        return content

    def _clean_markdown_for_docx(self, content: str) -> str:
        """清理Markdown格式用于Word"""
        import re

        # 移除链接但保留文字
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)

        return content

    def _export_to_image(
        self,
        content: str,
        output_dir: str,
        filename: str,
        metadata: Optional[Dict[str, Any]],
        image_format: str = "png"
    ) -> str:
        """导出为图片格式 (PNG/JPG)"""
        from PIL import Image, ImageDraw, ImageFont
        import re

        # 确定文件扩展名和格式
        ext = f".{image_format}"
        pil_format = "JPEG" if image_format in ["jpeg", "jpg"] else "PNG"

        filepath = os.path.join(output_dir, f"{filename}{ext}")

        # 解析Markdown内容
        lines = content.split('\n')
        rendered_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                rendered_lines.append("")
                continue

            # 标题处理
            if line.startswith('### '):
                rendered_lines.append(f"【{line[4:]}】")
            elif line.startswith('## '):
                rendered_lines.append(f"【{line[3:]}】")
            elif line.startswith('# '):
                rendered_lines.append(f"{line[2:]}")
            elif line.startswith('|'):
                # 表格行简化
                if '---' not in line:
                    cells = [c.strip() for c in line.strip('|').split('|')]
                    rendered_lines.append(" | ".join(cells))
            elif line.startswith('- ') or line.startswith('* '):
                rendered_lines.append(f"• {line[2:]}")
            else:
                # 清理Markdown格式
                clean = re.sub(r'\*\*([^\*]+)\*\*', r'\1', line)
                clean = re.sub(r'\*([^\*]+)\*', r'\1', clean)
                clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean)
                rendered_lines.append(clean)

        # 将内容合并
        full_text = "\n".join(rendered_lines)

        # 图片设置
        img_width = 1200
        line_height = 28
        padding = 40
        header_height = 100

        # 加载字体
        try:
            font_large = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 20)
            font_normal = ImageFont.truetype("C:/Windows/Fonts/simsun.ttc", 14)
            font_small = ImageFont.truetype("C:/Windows/Fonts/simsun.ttc", 12)
        except:
            try:
                font_large = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
                font_normal = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 14)
                font_small = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 12)
            except:
                font_large = ImageFont.load_default()
                font_normal = ImageFont.load_default()
                font_small = ImageFont.load_default()

        # 计算每行的高度
        text_lines = []
        max_text_width = img_width - 2 * padding

        for line in full_text.split('\n'):
            if not line:
                text_lines.append("")
                continue

            # 判断是否为标题
            if line.startswith('【') and line.endswith('】'):
                font = font_large
                line = line[1:-1]
            elif line.startswith('•'):
                font = font_normal
            else:
                font = font_normal

            # 简单的自动换行
            words = line
            while words:
                # 使用getbbox代替textsize
                bbox = font.getbbox(words)
                text_width = bbox[2] - bbox[0]
                if text_width <= max_text_width:
                    text_lines.append(words)
                    break
                # 找到一个合适的断点
                for i in range(len(words) - 1, 0, -1):
                    bbox = font.getbbox(words[:i])
                    if bbox[2] - bbox[0] <= max_text_width * 0.9:
                        text_lines.append(words[:i+1].strip())
                        words = words[i+1:].strip()
                        break
                else:
                    text_lines.append(words[:50].strip())
                    words = words[50:].strip()

        # 计算图片高度
        img_height = header_height + len(text_lines) * line_height + 2 * padding + 60

        # 创建图片
        img = Image.new('RGB', (img_width, img_height), 'white')
        draw = ImageDraw.Draw(img)

        # 绘制标题
        title = metadata.get('title', filename) if metadata else filename
        draw.text((padding, 30), title, fill='#1a1a1a', font=font_large)

        # 绘制元数据
        meta = f"案件编号: {metadata.get('case_id', 'N/A')} | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        draw.text((padding, 70), meta, fill='#666666', font=font_small)

        # 分隔线
        draw.line([(padding, 95), (img_width - padding, 95)], fill='#cccccc', width=1)

        # 绘制内容
        y = header_height + padding
        for line in text_lines:
            if not line:
                y += line_height // 2
                continue

            # 判断是否为标题
            if line.startswith('【') and line.endswith('】'):
                draw.text((padding, y), line[1:-1], fill='#333333', font=font_large)
                y += line_height + 5
            elif line.startswith('•'):
                draw.text((padding + 20, y), line[1:], fill='#333333', font=font_normal)
                y += line_height
            elif line.startswith('|'):
                draw.text((padding, y), line, fill='#333333', font=font_small)
                y += line_height
            else:
                draw.text((padding, y), line, fill='#333333', font=font_normal)
                y += line_height

            # 防止超出图片
            if y > img_height - padding - 40:
                break

        # 绘制页脚
        footer = f"本文档由法律大模型自动生成 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        draw.text((padding, img_height - 40), footer, fill='#999999', font=font_small)

        # 保存图片
        img.save(filepath, format=pil_format)
        return filepath

    def get_download_path(self, filename: str) -> Optional[str]:
        """获取下载文件路径"""
        # 搜索所有导出目录
        for root, dirs, files in os.walk(self.export_dir):
            if filename in files:
                return os.path.join(root, filename)
        return None

    def list_exports(self, case_id: Optional[int] = None) -> list:
        """列出所有导出文件"""
        exports = []
        search_dir = os.path.join(self.export_dir, f"case_{case_id}") if case_id else self.export_dir

        if os.path.exists(search_dir):
            for root, dirs, files in os.walk(search_dir):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    stat = os.stat(filepath)
                    exports.append({
                        "filename": filename,
                        "path": filepath,
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "format": os.path.splitext(filename)[1][1:]
                    })

        return sorted(exports, key=lambda x: x['created_at'], reverse=True)


# 全局导出服务实例
export_service = ExportService()
