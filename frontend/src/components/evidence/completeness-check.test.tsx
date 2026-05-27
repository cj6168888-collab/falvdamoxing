import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { CompletenessCheck } from '@/components/evidence/completeness-check';
import * as useEvidence from '@/hooks/use-evidence';

vi.mock('@/hooks/use-evidence');

function mockCompletenessResult(
  data: unknown,
  isLoading = false
): ReturnType<typeof useEvidence.useEvidenceCompleteness> {
  return { data, isLoading } as unknown as ReturnType<typeof useEvidence.useEvidenceCompleteness>;
}

describe('CompletenessCheck', () => {
  it('renders completeness progress bar and percentage', () => {
    vi.mocked(useEvidence.useEvidenceCompleteness).mockReturnValue(
      mockCompletenessResult({ completeness: 75, gaps: [] })
    );

    render(<CompletenessCheck caseId="case-1" />);

    expect(screen.getByText('75% 完整')).toBeInTheDocument();
  });

  it('shows gap list when there are gaps', () => {
    vi.mocked(useEvidence.useEvidenceCompleteness).mockReturnValue(
      mockCompletenessResult({
        completeness: 60,
        gaps: [
          { type: 'Bank statements', suggestion: 'Add bank transfer records' },
          { type: 'Witness testimony', suggestion: 'Collect witness testimony' },
        ],
      })
    );

    render(<CompletenessCheck caseId="case-1" />);

    expect(screen.getByText('Bank statements')).toBeInTheDocument();
    expect(screen.getByText('Add bank transfer records')).toBeInTheDocument();
    expect(screen.getByText('Witness testimony')).toBeInTheDocument();
    expect(screen.getByText('Collect witness testimony')).toBeInTheDocument();
  });

  it('shows complete state when no gaps', () => {
    vi.mocked(useEvidence.useEvidenceCompleteness).mockReturnValue(
      mockCompletenessResult({ completeness: 100, gaps: [] })
    );

    render(<CompletenessCheck caseId="case-1" />);

    expect(screen.getByText('100% 完整')).toBeInTheDocument();
    expect(screen.queryByText('Bank statements')).not.toBeInTheDocument();
  });

  it('shows loading state when loading', () => {
    vi.mocked(useEvidence.useEvidenceCompleteness).mockReturnValue(
      mockCompletenessResult(undefined, true)
    );

    render(<CompletenessCheck caseId="case-1" />);

    expect(screen.queryByText(/% 完整/)).not.toBeInTheDocument();
  });

  it('handles zero completeness correctly', () => {
    vi.mocked(useEvidence.useEvidenceCompleteness).mockReturnValue(
      mockCompletenessResult({
        completeness: 0,
        gaps: [{ type: 'All evidence', suggestion: 'Add all required evidence' }],
      })
    );

    render(<CompletenessCheck caseId="case-1" />);

    expect(screen.getByText('0% 完整')).toBeInTheDocument();
    expect(screen.getByText('All evidence')).toBeInTheDocument();
  });
});
