import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { DeadlineReference } from '@/components/timeline/deadline-reference';

describe('DeadlineReference', () => {
  it('renders reference table with all legal deadline types', () => {
    render(<DeadlineReference />);

    expect(screen.getByText('常用法定期限参考')).toBeInTheDocument();
    expect(screen.getByText('普通民事诉讼')).toBeInTheDocument();
    expect(screen.getByText('身体伤害')).toBeInTheDocument();
    expect(screen.getByText('租金纠纷')).toBeInTheDocument();
    expect(screen.getByText('借款纠纷')).toBeInTheDocument();
    expect(screen.getByText('答辩期')).toBeInTheDocument();
    expect(screen.getByText('举证期限')).toBeInTheDocument();
    expect(screen.getByText('民事上诉')).toBeInTheDocument();
    expect(screen.getByText('执行申请')).toBeInTheDocument();
  });

  it('shows correct periods for each deadline type', () => {
    render(<DeadlineReference />);

    expect(screen.getAllByText('3年').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('1年').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('15日').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('30日')).toBeInTheDocument();
    expect(screen.getByText('2年')).toBeInTheDocument();
  });

  it('renders in a grid layout', () => {
    const { container } = render(<DeadlineReference />);
    const grid = container.querySelector('.grid');
    expect(grid).toHaveClass('grid-cols-2');
  });

  it('displays all 8 reference items', () => {
    render(<DeadlineReference />);

    const referenceItems = [
      '普通民事诉讼',
      '身体伤害',
      '租金纠纷',
      '借款纠纷',
      '答辩期',
      '举证期限',
      '民事上诉',
      '执行申请',
    ];

    referenceItems.forEach((item) => {
      expect(screen.getByText(item)).toBeInTheDocument();
    });
  });

  it('shows period values with correct formatting', () => {
    render(<DeadlineReference />);

    const threeYearElements = screen.getAllByText('3年');
    expect(threeYearElements.length).toBeGreaterThanOrEqual(2);
  });
});
