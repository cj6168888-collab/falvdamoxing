import { describe, expect, it } from 'vitest';
import { getAudienceLabels, getAudienceMode } from './audience-copy';

describe('audience-copy', () => {
  it('keeps law firm as the fallback audience', () => {
    expect(getAudienceMode(undefined)).toBe('law_firm');
    expect(getAudienceLabels(undefined).caseList).toBe('案件管理');
  });

  it('uses business-oriented labels for enterprise tenants', () => {
    const labels = getAudienceLabels('enterprise');

    expect(labels.caseList).toBe('法律事项');
    expect(labels.analysisTab).toBe('风险识别');
    expect(labels.executionTab).toBe('回款跟踪');
  });

  it('uses plain-language labels for personal tenants', () => {
    const labels = getAudienceLabels('personal');

    expect(labels.caseList).toBe('我的法律问题');
    expect(labels.timelineTab).toBe('下一步');
    expect(labels.evidenceTab).toBe('证据保全');
  });
});
