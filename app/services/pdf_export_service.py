"""
PDF导出服务（biz-10）
支持文书和证据册PDF导出

依赖：
- reportlab (已安装)
- PyMuPDF (已安装)
- python-docx (已安装，处理docx转PDF)
"""

from typing import Dict, List, Optional, Any, Union
import os
import io
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.pdfgen import canvas

# 注册中文字体
try:
    # Windows
    pdfmetrics.registerFont(TTFont('SimSun', 'C:/Windows/Fonts/simsun.ttc'))
    pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
    CHINESE_FONT = 'SimSun'
    CHINESE_FONT_BOLD = 'SimHei'
except Exception:
    try:
        # Linux
        pdfmetrics.registerFont(TTFont('NotoSansCJK', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'))
        CHINESE_FONT = 'NotoSansCJK'
        CHINESE_FONT_BOLD = 'NotoSansCJK'
    except Exception:
        CHINESE_FONT = 'Helvetica'
        CHINESE_FONT_BOLD = 'Helvetica'


class PDFExportService:
    """
    PDF导出服务（biz-10）
    
    支持：
    - 法律文书PDF导出
    - 证据册PDF导出
    - 案件材料打包导出
    """
    
    def __init__(self, output_dir: str = "data/exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_document(
        self,
        content: str,
        title: str,
        output_filename: Optional[str] = None,
        document_type: str = "法律文书",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        导出法律文书为PDF
        
        Args:
            content: 文书内容
            title: 文书标题
            output_filename: 输出文件名（不含扩展名）
            document_type: 文书类型
            metadata: 元数据（案号、当事人等）
            
        Returns:
            生成的PDF文件路径
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{document_type}_{timestamp}.pdf"
        
        output_path = self.output_dir / output_filename
        
        # 创建PDF文档
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # 构建样式
        styles = self._create_styles()
        
        # 构建内容
        story = []
        
        # 标题
        story.append(Paragraph(title, styles['document_title']))
        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
        story.append(Spacer(1, 0.5*cm))
        
        # 元数据
        if metadata:
            meta_text = self._format_metadata(metadata)
            story.append(Paragraph(meta_text, styles['metadata']))
            story.append(Spacer(1, 0.5*cm))
        
        # 正文内容
        paragraphs = self._parse_content(content)
        for para in paragraphs:
            style = styles['body'] if para['type'] == 'body' else styles.get(para['type'], styles['body'])
            story.append(Paragraph(para['text'], style))
            story.append(Spacer(1, 0.3*cm))
        
        # 页脚
        def footer(canvas, doc):
            canvas.saveState()
            canvas.setFont(CHINESE_FONT, 9)
            page_num = canvas.getPageNumber()
            text = f"- {page_num} -"
            canvas.drawCentredString(A4[0]/2, 1*cm, text)
            canvas.restoreState()
        
        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        
        return str(output_path)
    
    def export_evidence_book(
        self,
        case_data: Dict,
        evidence_list: List[Dict],
        output_filename: Optional[str] = None
    ) -> str:
        """
        导出证据册为PDF
        
        Args:
            case_data: 案件数据
            evidence_list: 证据列表
            output_filename: 输出文件名
            
        Returns:
            生成的PDF文件路径
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            case_no = case_data.get('case_number', '未知案件')
            output_filename = f"证据册_{case_no}_{timestamp}.pdf"
        
        output_path = self.output_dir / output_filename
        
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = self._create_styles()
        story = []
        
        # 封面
        story.append(Spacer(1, 3*cm))
        story.append(Paragraph("证据册", styles['cover_title']))
        story.append(Spacer(1, 1*cm))
        
        # 案件信息
        case_info = f"""
        <b>案号：</b>{case_data.get('case_number', '未编号')}<br/>
        <b>案件名称：</b>{case_data.get('title', '')}<br/>
        <b>案由：</b>{case_data.get('cause', '')}<br/>
        <b>原告：</b>{case_data.get('plaintiff', '')}<br/>
        <b>被告：</b>{case_data.get('defendant', '')}<br/>
        <b>编制日期：</b>{datetime.now().strftime('%Y年%m月%d日')}
        """
        story.append(Paragraph(case_info, styles['case_info']))
        story.append(PageBreak())
        
        # 证据目录
        story.append(Paragraph("证据目录", styles['section_title']))
        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
        story.append(Spacer(1, 0.5*cm))
        
        # 证据目录表
        table_data = [["序号", "证据名称", "证据类型", "页码", "份数"]]
        for i, ev in enumerate(evidence_list, 1):
            table_data.append([
                str(i),
                ev.get('name', ev.get('original_filename', '未知')),
                self._get_evidence_type_name(ev.get('evidence_type', '')),
                str(i * 2 - 1),  # 估计页码
                "1"
            ])
        
        table = Table(table_data, colWidths=[1.5*cm, 7*cm, 3*cm, 2*cm, 1.5*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), CHINESE_FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, -1), CHINESE_FONT),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
        ]))
        story.append(table)
        story.append(PageBreak())
        
        # 证据详情
        story.append(Paragraph("证据内容", styles['section_title']))
        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
        story.append(Spacer(1, 0.5*cm))
        
        for i, ev in enumerate(evidence_list, 1):
            # 每份证据单独页面
            ev_block = [
                Paragraph(f"证据{i}：{ev.get('name', ev.get('original_filename', '未知'))}", styles['evidence_title']),
                Spacer(1, 0.3*cm),
            ]
            
            # 证据基本信息
            ev_meta = f"""
            <b>证据类型：</b>{self._get_evidence_type_name(ev.get('evidence_type', ''))}<br/>
            <b>来源：</b>{ev.get('source_party', '未知')}<br/>
            <b>提交日期：</b>{ev.get('created_at', '')}
            """
            ev_block.append(Paragraph(ev_meta, styles['evidence_meta']))
            ev_block.append(Spacer(1, 0.3*cm))
            
            # 证据摘要/内容
            summary = ev.get('summary', ev.get('extracted_content', ev.get('raw_content', '')))
            if summary:
                if len(summary) > 2000:
                    summary = summary[:2000] + "..."
                ev_block.append(Paragraph(f"<b>内容摘要：</b><br/>{summary}", styles['evidence_content']))
            
            # 三性分析（如果有）
            if ev.get('three_natures_analysis'):
                analysis = ev['three_natures_analysis']
                analysis_text = f"""
                <b>真实性：</b>{analysis.get('authenticity', '未分析')}（{analysis.get('authenticity_score', 0):.0f}分）<br/>
                <b>合法性：</b>{analysis.get('legality', '未分析')}（{analysis.get('legality_score', 0):.0f}分）<br/>
                <b>关联性：</b>{analysis.get('relevance', '未分析')}（{analysis.get('relevance_score', 0):.0f}分）
                """
                ev_block.append(Spacer(1, 0.3*cm))
                ev_block.append(Paragraph(analysis_text, styles['analysis']))
            
            story.append(KeepTogether(ev_block))
            
            if i < len(evidence_list):
                story.append(PageBreak())
        
        # 页码和日期
        def footer(canvas, doc):
            canvas.saveState()
            canvas.setFont(CHINESE_FONT, 9)
            page_num = canvas.getPageNumber()
            text = f"证据册 - {page_num} -"
            canvas.drawCentredString(A4[0]/2, 1*cm, text)
            canvas.restoreState()
        
        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        
        return str(output_path)
    
    def export_case_materials(
        self,
        case_data: Dict,
        documents: List[Dict],
        evidence_list: List[Dict],
        analysis_reports: List[Dict]
    ) -> str:
        """
        导出完整案件材料包（ZIP包含多个PDF）
        
        Returns:
            生成的ZIP文件路径
        """
        import zipfile
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        case_no = case_data.get('case_number', '未知案件')
        zip_filename = f"案件材料_{case_no}_{timestamp}.zip"
        zip_path = self.output_dir / zip_filename
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. 案件信息
            info_pdf = self.export_document(
                content=case_data.get('description', ''),
                title=f"案件信息：{case_data.get('title', '')}",
                output_filename=f"案件信息_{case_no}.pdf",
                document_type="案件信息",
                metadata={
                    "案号": case_data.get('case_number', ''),
                    "案件类型": case_data.get('case_type', ''),
                    "原告": case_data.get('plaintiff', ''),
                    "被告": case_data.get('defendant', ''),
                }
            )
            zf.write(info_pdf, Path(info_pdf).name)
            
            # 2. 证据册
            if evidence_list:
                evidence_pdf = self.export_evidence_book(case_data, evidence_list)
                zf.write(evidence_pdf, Path(evidence_pdf).name)
            
            # 3. 分析报告
            for i, report in enumerate(analysis_reports, 1):
                report_pdf = self.export_document(
                    content=report.get('content', report.get('analysis', '')),
                    title=report.get('title', f'分析报告{i}'),
                    output_filename=f"分析报告_{case_no}_{i}.pdf",
                    document_type="分析报告"
                )
                zf.write(report_pdf, Path(report_pdf).name)
            
            # 4. 文档
            for i, doc in enumerate(documents, 1):
                doc_pdf = self.export_document(
                    content=doc.get('content', doc.get('content_summary', '')),
                    title=doc.get('filename', f'文档{i}'),
                    output_filename=f"文档_{case_no}_{i}.pdf",
                    document_type="文档"
                )
                zf.write(doc_pdf, Path(doc_pdf).name)
        
        return str(zip_path)
    
    def _create_styles(self) -> Dict:
        """创建PDF样式"""
        styles = getSampleStyleSheet()
        
        # 文档标题
        styles.add(ParagraphStyle(
            name='document_title',
            fontName=CHINESE_FONT_BOLD,
            fontSize=22,
            leading=30,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        # 元数据
        styles.add(ParagraphStyle(
            name='metadata',
            fontName=CHINESE_FONT,
            fontSize=10,
            leading=16,
            alignment=TA_LEFT,
            textColor=colors.grey
        ))
        
        # 正文
        styles.add(ParagraphStyle(
            name='body',
            fontName=CHINESE_FONT,
            fontSize=12,
            leading=20,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            firstLineIndent=24
        ))
        
        # 封面标题
        styles.add(ParagraphStyle(
            name='cover_title',
            fontName=CHINESE_FONT_BOLD,
            fontSize=28,
            leading=36,
            alignment=TA_CENTER
        ))
        
        # 案件信息
        styles.add(ParagraphStyle(
            name='case_info',
            fontName=CHINESE_FONT,
            fontSize=14,
            leading=24,
            alignment=TA_LEFT
        ))
        
        # 章节标题
        styles.add(ParagraphStyle(
            name='section_title',
            fontName=CHINESE_FONT_BOLD,
            fontSize=16,
            leading=24,
            alignment=TA_LEFT
        ))
        
        # 证据标题
        styles.add(ParagraphStyle(
            name='evidence_title',
            fontName=CHINESE_FONT_BOLD,
            fontSize=14,
            leading=20,
            alignment=TA_LEFT
        ))
        
        # 证据元数据
        styles.add(ParagraphStyle(
            name='evidence_meta',
            fontName=CHINESE_FONT,
            fontSize=10,
            leading=16,
            alignment=TA_LEFT,
            textColor=colors.grey
        ))
        
        # 证据内容
        styles.add(ParagraphStyle(
            name='evidence_content',
            fontName=CHINESE_FONT,
            fontSize=11,
            leading=18,
            alignment=TA_LEFT
        ))
        
        # 分析结果
        styles.add(ParagraphStyle(
            name='analysis',
            fontName=CHINESE_FONT,
            fontSize=10,
            leading=16,
            alignment=TA_LEFT,
            textColor=colors.Color(0.2, 0.4, 0.6)
        ))
        
        return styles
    
    def _format_metadata(self, metadata: Dict) -> str:
        """格式化元数据为HTML"""
        parts = []
        for key, value in metadata.items():
            if value:
                parts.append(f"<b>{key}：</b>{value}")
        return "<br/>".join(parts)
    
    def _parse_content(self, content: str) -> List[Dict]:
        """解析内容文本，返回段落列表"""
        paragraphs = []
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测标题行
            if line.startswith('#'):
                paragraphs.append({'type': 'title', 'text': line.lstrip('#').strip()})
            elif line.startswith('##'):
                paragraphs.append({'type': 'section_title', 'text': line.lstrip('#').strip()})
            elif line.startswith('###'):
                paragraphs.append({'type': 'subsection_title', 'text': line.lstrip('#').strip()})
            else:
                paragraphs.append({'type': 'body', 'text': line})
        
        return paragraphs
    
    def _get_evidence_type_name(self, evidence_type: str) -> str:
        """获取证据类型中文名称"""
        type_map = {
            'CONTRACT': '合同协议类',
            'CORRESPONDENCE': '函件沟通类',
            'PAYMENT': '支付凭证类',
            'IDENTITY': '身份证明类',
            'AUDIO_VIDEO': '视听资料类',
            'TESTIMONY': '证人证言类',
            'EXPERT': '鉴定意见类',
            'DOCUMENT': '书证类',
            'MATERIAL': '物证类',
            'OTHER': '其他类',
        }
        return type_map.get(evidence_type, evidence_type)


# 全局实例
pdf_export_service = PDFExportService()
