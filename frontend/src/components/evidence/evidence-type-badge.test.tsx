import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { EvidenceTypeBadge } from '@/components/evidence/evidence-type-badge';

describe('EvidenceTypeBadge', () => {
  it('renders contract type with correct styling', () => {
    render(<EvidenceTypeBadge type="contract" label="合同" />);

    const badge = screen.getByText('合同');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-blue-100');
    expect(badge).toHaveClass('text-blue-700');
  });

  it('renders receipt type with correct styling', () => {
    render(<EvidenceTypeBadge type="receipt" label="收据" />);

    const badge = screen.getByText('收据');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-green-100');
    expect(badge).toHaveClass('text-green-700');
  });

  it('renders communication type with correct styling', () => {
    render(<EvidenceTypeBadge type="communication" label="微信记录" />);

    const badge = screen.getByText('微信记录');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-pink-100');
    expect(badge).toHaveClass('text-pink-700');
  });

  it('handles unknown type gracefully with default styling', () => {
    render(<EvidenceTypeBadge type="other" label="未知类型" />);

    const badge = screen.getByText('未知类型');
    expect(badge).toBeInTheDocument();
  });

  it('renders audio_video type with correct styling', () => {
    render(<EvidenceTypeBadge type="audio_video" label="录音" />);

    const badge = screen.getByText('录音');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-red-100');
    expect(badge).toHaveClass('text-red-700');
  });
});
