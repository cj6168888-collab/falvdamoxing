import { render, screen } from '@/test/test-utils';
import { fireEvent } from '@testing-library/react';
import { ConfirmDialog } from './confirm-dialog';

describe('ConfirmDialog', () => {
  const defaultProps = {
    open: true,
    onOpenChange: vi.fn(),
    title: '确认删除',
    description: '此操作不可撤销',
    onConfirm: vi.fn(),
  };

  it('renders title and description', () => {
    render(<ConfirmDialog {...defaultProps} />);
    expect(screen.getByText('确认删除')).toBeInTheDocument();
    expect(screen.getByText('此操作不可撤销')).toBeInTheDocument();
  });

  it('renders confirm and cancel buttons', () => {
    render(<ConfirmDialog {...defaultProps} />);
    expect(screen.getByText('确认')).toBeInTheDocument();
    expect(screen.getByText('取消')).toBeInTheDocument();
  });

  it('calls onConfirm when confirm button clicked', () => {
    render(<ConfirmDialog {...defaultProps} />);
    fireEvent.click(screen.getByText('确认'));
    expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1);
  });

  it('calls onOpenChange when cancel button clicked', () => {
    render(<ConfirmDialog {...defaultProps} />);
    fireEvent.click(screen.getByText('取消'));
    expect(defaultProps.onOpenChange).toHaveBeenCalledWith(false);
  });

  it('shows loading state', () => {
    render(<ConfirmDialog {...defaultProps} isLoading />);
    expect(screen.getByText('处理中...')).toBeInTheDocument();
  });

  it('renders destructive variant', () => {
    render(<ConfirmDialog {...defaultProps} variant="destructive" />);
    expect(screen.getByText('确认')).toBeInTheDocument();
  });

  it('does not render when open is false', () => {
    render(<ConfirmDialog {...defaultProps} open={false} />);
    expect(screen.queryByText('确认删除')).not.toBeInTheDocument();
  });
});
