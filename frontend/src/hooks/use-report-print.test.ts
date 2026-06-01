import { describe, expect, it } from 'vitest';
import { buildReportPrintContent, buildSectionPrintContent } from './use-report-print';
import type { ReportDetail, ReportSection } from '@/types/report.types';

const section: ReportSection = {
  id: 'section-1',
  outline_id: 'report-1',
  section_index: 1,
  title: '证据分析',
  content: '现有证据支持该事实。',
  key_points: [],
  status: 'completed',
  created_at: '2026-06-01T00:00:00Z',
  completed_at: '2026-06-01T00:01:00Z',
};

const report: ReportDetail = {
  id: 'report-1',
  case_id: 1,
  report_type: 'EVIDENCE_REPORT',
  report_type_name: '证据报告',
  report_type_icon: 'file-text',
  title: '证据分析报告',
  description: '',
  status: 'COMPLETED',
  progress: { total: 1, completed: 1, failed: 0, progress: 100, status: 'COMPLETED' },
  total_tokens: 100,
  processing_time: 2,
  version: 1,
  created_at: '2026-06-01T00:00:00Z',
  updated_at: '2026-06-01T00:00:00Z',
  completed_at: '2026-06-01T00:01:00Z',
  sections: [section],
  total_sections: 1,
  completed_sections: 1,
};

describe('report print workpaper notices', () => {
  it('includes review notices in full report print HTML', () => {
    const html = buildReportPrintContent(report);

    expect(html).toContain('AI 法律工作底稿');
    expect(html).toContain('导出/打印前核验提示');
    expect(html).toContain('不构成正式法律意见');
    expect(html).toContain('当事人、金额、事实证据对应、法条现行有效性、管辖、日期和签章');
  });

  it('includes review notices in section print HTML', () => {
    const html = buildSectionPrintContent(section, report.title);

    expect(html).toContain('AI 法律工作底稿');
    expect(html).toContain('打印前核验提示');
    expect(html).toContain('正式使用前请核验证据来源、事实对应、法律依据和人工确认状态');
  });
});
