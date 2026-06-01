import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { CredibilityScore } from '@/components/evidence/credibility-score';

describe('CredibilityScore', () => {
  it('renders score with correct percentage', () => {
    render(
      <CredibilityScore
        score={85}
        dimensions={[
          { name: '合法性', score: 90 },
          { name: '关联性', score: 80 },
        ]}
      />,
    );

    expect(screen.getByText('证明力参考')).toBeInTheDocument();
    expect(screen.getByText('仅作工作底稿中的证据风险参考，不等同于法院采信结论。')).toBeInTheDocument();
    expect(screen.getAllByText(/85%/).length).toBeGreaterThanOrEqual(1);
  });

  it('renders dimension scores correctly', () => {
    render(
      <CredibilityScore
        score={75}
        dimensions={[
          { name: '合法性', score: 90 },
          { name: '关联性', score: 70 },
          { name: '真实性', score: 65 },
        ]}
      />,
    );

    expect(screen.getByText('合法性')).toBeInTheDocument();
    expect(screen.getByText('关联性')).toBeInTheDocument();
    expect(screen.getByText('真实性')).toBeInTheDocument();
  });

  it('renders progress bars for score visualization', () => {
    render(
      <CredibilityScore
        score={60}
        dimensions={[{ name: '合法性', score: 75 }]}
      />,
    );

    const progressBars = document.querySelectorAll('[role="progressbar"]');
    expect(progressBars.length).toBeGreaterThan(0);
  });

  it('handles zero score correctly', () => {
    render(
      <CredibilityScore
        score={0}
        dimensions={[{ name: '合法性', score: 0 }]}
      />,
    );

    expect(screen.getAllByText(/0%/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('合法性')).toBeInTheDocument();
  });

  it('handles perfect score correctly', () => {
    render(
      <CredibilityScore
        score={100}
        dimensions={[{ name: '合法性', score: 100 }]}
      />,
    );

    expect(screen.getAllByText(/100%/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('合法性')).toBeInTheDocument();
  });
});
