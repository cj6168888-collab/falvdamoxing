import { useCallback } from 'react';
import type { ReportDetail, ReportSection } from '@/types/report.types';

/**
 * 报告打印 Hook
 * 提供报告打印功能，支持自定义格式
 */
export function useReportPrint() {

  /**
   * 直接打印当前页面
   */
  const printCurrentPage = useCallback(() => {
    window.print();
  }, []);

  /**
   * 打印指定元素
   * @param elementId 元素 ID
   */
  const printElement = useCallback((elementId: string) => {
    const element = document.getElementById(elementId);
    if (!element) {
      console.error('Print element not found:', elementId);
      return;
    }
    printWithStyles(element);
  }, []);

  /**
   * 打印报告内容
   * @param report 报告详情
   */
  const printReport = useCallback((report: ReportDetail) => {
    const printContent = buildReportPrintContent(report);
    openPrintWindow(printContent, report.title);
  }, []);

  /**
   * 打印报告章节
   * @param section 章节内容
   * @param reportTitle 报告标题
   */
  const printSection = useCallback((section: ReportSection, reportTitle: string) => {
    const printContent = buildSectionPrintContent(section, reportTitle);
    openPrintWindow(printContent, `${reportTitle} - ${section.title}`);
  }, []);

  return {
    printCurrentPage,
    printElement,
    printReport,
    printSection,
  };
}

/**
 * 构建报告打印内容
 */
export function buildReportPrintContent(report: ReportDetail): string {
  const sections = report.sections || [];
  const createdDate = report.created_at
    ? new Date(report.created_at).toLocaleDateString('zh-CN')
    : '未知';

  let sectionsHtml = '';
  sections.forEach((section, index) => {
    if (section.content) {
      // 转换 Markdown 内容为 HTML
      const contentHtml = markdownToHtml(section.content);
      sectionsHtml += `
        <div class="report-section">
          <div class="report-section-title">
            <span>${index + 1}. ${escapeHtml(section.title)}</span>
          </div>
          <div class="report-section-content">
            ${contentHtml}
          </div>
        </div>
      `;
    }
  });

  return `
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>${escapeHtml(report.title)}</title>
      <style>
        body {
          font-family: 'SimSun', '宋体', 'Noto Serif SC', serif;
          font-size: 12pt;
          line-height: 1.8;
          color: #333;
          max-width: 800px;
          margin: 0 auto;
          padding: 20pt;
        }
        .report-header {
          text-align: center;
          margin-bottom: 24pt;
          padding-bottom: 16pt;
          border-bottom: 2px solid #333;
        }
        .report-title {
          font-size: 18pt;
          font-weight: bold;
          margin-bottom: 8pt;
        }
        .report-meta {
          font-size: 10pt;
          color: #666;
        }
        .report-meta span {
          margin: 0 8pt;
        }
        .workpaper-notice {
          margin: 16pt 0 20pt;
          padding: 10pt 12pt;
          border: 1px solid #d97706;
          background: #fffbeb;
          color: #7c2d12;
          font-size: 10pt;
          line-height: 1.6;
        }
        .workpaper-notice strong {
          display: block;
          margin-bottom: 4pt;
        }
        .report-section {
          margin-bottom: 20pt;
          page-break-inside: avoid;
        }
        .report-section-title {
          font-size: 14pt;
          font-weight: bold;
          margin-bottom: 10pt;
          padding-bottom: 6pt;
          border-bottom: 1px solid #ddd;
        }
        .report-section-content {
          text-indent: 2em;
        }
        .report-section-content p {
          margin: 8pt 0;
        }
        .report-section-content ul,
        .report-section-content ol {
          margin: 8pt 0;
          padding-left: 2em;
        }
        .report-section-content li {
          margin-bottom: 4pt;
        }
        .report-section-content strong {
          font-weight: bold;
        }
        .report-footer {
          margin-top: 30pt;
          padding-top: 12pt;
          border-top: 1px solid #ddd;
          text-align: center;
          font-size: 10pt;
          color: #999;
        }
        @media print {
          body { padding: 0; }
          .report-section { page-break-inside: avoid; }
        }
      </style>
    </head>
    <body>
      <div class="report-header">
        <div class="report-title">${escapeHtml(report.title)}</div>
        <div class="report-meta">
          <span>AI 法律工作底稿</span>
          <span>|</span>
          <span>类型: ${escapeHtml(report.report_type_name)}</span>
          <span>|</span>
          <span>版本: V${report.version}</span>
          <span>|</span>
          <span>生成时间: ${createdDate}</span>
        </div>
      </div>

      <div class="workpaper-notice">
        <strong>导出/打印前核验提示</strong>
        本报告仅用于事实整理、证据分析和风险提示，不构成正式法律意见。提交、对外发送或庭审使用前，请人工核验当事人、金额、事实证据对应、法条现行有效性、管辖、日期和签章。
      </div>

      <div class="report-body">
        ${sectionsHtml}
      </div>

      <div class="report-footer">
        <p>法律案件追踪系统 - AI 法律工作底稿 - ${new Date().toLocaleDateString('zh-CN')} 打印</p>
      </div>
    </body>
    </html>
  `;
}

/**
 * 构建章节打印内容
 */
export function buildSectionPrintContent(section: ReportSection, reportTitle: string): string {
  const contentHtml = markdownToHtml(section.content || '');
  const completedDate = section.completed_at
    ? new Date(section.completed_at).toLocaleString('zh-CN')
    : '未知';

  return `
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>${escapeHtml(section.title)}</title>
      <style>
        body {
          font-family: 'SimSun', '宋体', 'Noto Serif SC', serif;
          font-size: 12pt;
          line-height: 1.8;
          color: #333;
          max-width: 800px;
          margin: 0 auto;
          padding: 20pt;
        }
        .section-header {
          margin-bottom: 16pt;
          padding-bottom: 12pt;
          border-bottom: 2px solid #333;
        }
        .section-title {
          font-size: 16pt;
          font-weight: bold;
          margin-bottom: 8pt;
        }
        .section-meta {
          font-size: 10pt;
          color: #666;
        }
        .workpaper-notice {
          margin: 16pt 0 20pt;
          padding: 10pt 12pt;
          border: 1px solid #d97706;
          background: #fffbeb;
          color: #7c2d12;
          font-size: 10pt;
          line-height: 1.6;
        }
        .workpaper-notice strong {
          display: block;
          margin-bottom: 4pt;
        }
        .section-content {
          text-indent: 2em;
        }
        .section-content p {
          margin: 10pt 0;
        }
        .section-content ul,
        .section-content ol {
          margin: 10pt 0;
          padding-left: 2em;
        }
        .section-footer {
          margin-top: 30pt;
          padding-top: 12pt;
          border-top: 1px solid #ddd;
          text-align: center;
          font-size: 10pt;
          color: #999;
        }
      </style>
    </head>
    <body>
      <div class="section-header">
        <div class="section-title">${escapeHtml(section.title)}</div>
        <div class="section-meta">
          <span>AI 法律工作底稿</span>
          <span>|</span>
          <span>来自: ${escapeHtml(reportTitle)}</span>
          <span>|</span>
          <span>完成时间: ${completedDate}</span>
        </div>
      </div>

      <div class="workpaper-notice">
        <strong>打印前核验提示</strong>
        本章节仅为报告工作底稿片段。正式使用前请核验证据来源、事实对应、法律依据和人工确认状态。
      </div>

      <div class="section-content">
        ${contentHtml}
      </div>

      <div class="section-footer">
        <p>法律案件追踪系统 - AI 法律工作底稿 - ${new Date().toLocaleDateString('zh-CN')} 打印</p>
      </div>
    </body>
    </html>
  `;
}

/**
 * 使用打印样式打开新窗口
 */
function printWithStyles(element: HTMLElement): void {
  const printWindow = window.open('', '_blank');
  if (!printWindow) return;

  const content = element.innerHTML;
  const styles = `
    <style>
      body {
        font-family: 'SimSun', '宋体', serif;
        font-size: 12pt;
        line-height: 1.6;
        padding: 20pt;
      }
      @media print {
        body { padding: 0; }
      }
    </style>
  `;

  printWindow.document.write(`
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>打印</title>
      ${styles}
    </head>
    <body>${content}</body>
    </html>
  `);
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
  printWindow.close();
}

/**
 * 打开打印窗口
 */
function openPrintWindow(html: string, _title: string): void {
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    alert('无法打开打印窗口，请检查浏览器设置');
    return;
  }
  printWindow.document.write(html);
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
}

/**
 * HTML 转义
 */
function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * 简单的 Markdown 到 HTML 转换
 */
function markdownToHtml(markdown: string): string {
  let html = markdown;

  // 转义 HTML
  html = escapeHtml(html);

  // 代码块
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');

  // 行内代码
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // 标题
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // 粗体
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // 斜体
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // 无序列表
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

  // 有序列表
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

  // 换行
  html = html.replace(/\n\n/g, '</p><p>');
  html = '<p>' + html + '</p>';

  // 清理空段落
  html = html.replace(/<p><\/p>/g, '');
  html = html.replace(/<p>(\s*)<\/p>/g, '');

  return html;
}

export default useReportPrint;
