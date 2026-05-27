import { render, screen, fireEvent } from '@testing-library/react';
import { EmptyState } from './empty-state';

describe('EmptyState', () => {
  it('renders title and description', () => {
    render(<EmptyState title="暂无数据" description="请添加新内容" />);
    expect(screen.getByText('暂无数据')).toBeInTheDocument();
    expect(screen.getByText('请添加新内容')).toBeInTheDocument();
  });

  it('renders action button when provided', () => {
    const handleClick = vi.fn();
    render(<EmptyState title="暂无数据" actionLabel="添加" onAction={handleClick} />);
    const button = screen.getByText('添加');
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('does not render action button when not provided', () => {
    render(<EmptyState title="暂无数据" />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
