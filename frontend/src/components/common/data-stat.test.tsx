import { render, screen } from '@testing-library/react';
import { DataStat } from './data-stat';

describe('DataStat', () => {
  it('renders label and number value', () => {
    render(<DataStat label="案件数" value={42} />);
    expect(screen.getByText('案件数')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('formats large numbers', () => {
    render(<DataStat label="总数" value={1234567} />);
    expect(screen.getByText('1,234,567')).toBeInTheDocument();
  });

  it('renders string value', () => {
    render(<DataStat label="状态" value="进行中" />);
    expect(screen.getByText('进行中')).toBeInTheDocument();
  });

  it('renders trend when positive', () => {
    render(<DataStat label="新增" value={10} trend={{ value: 15, positive: true }} />);
    expect(screen.getByText(/15%/)).toBeInTheDocument();
    const trendEl = screen.getByText(/15%/).closest('p');
    expect(trendEl?.className).toContain('text-green-600');
  });

  it('renders trend when negative', () => {
    render(<DataStat label="减少" value={5} trend={{ value: 10, positive: false }} />);
    expect(screen.getByText(/10%/)).toBeInTheDocument();
    const trendEl = screen.getByText(/10%/).closest('p');
    expect(trendEl?.className).toContain('text-red-600');
  });
});
