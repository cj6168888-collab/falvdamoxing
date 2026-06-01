import { QuickActions } from '@/components/dashboard/quick-actions';
import { render, screen } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('framer-motion', () => ({
  motion: {
    div: ({
      whileHover: _whileHover,
      whileTap: _whileTap,
      transition: _transition,
      ...props
    }: Record<string, unknown>) => <div {...(props as JSX.IntrinsicElements['div'])} />,
    button: ({
      whileHover: _whileHover,
      whileTap: _whileTap,
      transition: _transition,
      ...props
    }: Record<string, unknown>) => <button {...(props as JSX.IntrinsicElements['button'])} />,
  },
}));

beforeEach(() => {
  mockNavigate.mockClear();
});

describe('QuickActions', () => {
  it('renders all 4 action buttons', () => {
    render(<QuickActions />);

    expect(screen.getByText('新建案件')).toBeInTheDocument();
    expect(screen.getByText('证据上传')).toBeInTheDocument();
    expect(screen.getByText('文书草稿')).toBeInTheDocument();
    expect(screen.getByText('问题整理')).toBeInTheDocument();
  });

  it('shows descriptions for each action', () => {
    render(<QuickActions />);

    expect(screen.getByText('创建新的法律案件')).toBeInTheDocument();
    expect(screen.getByText('上传案件相关证据材料')).toBeInTheDocument();
    expect(screen.getByText('起草待核验法律文书')).toBeInTheDocument();
    expect(screen.getByText('整理问题并提示风险')).toBeInTheDocument();
  });

  it('calls navigate with correct route when new case is clicked', async () => {
    const user = userEvent.setup();
    render(<QuickActions />);

    const newCaseButton = screen.getByRole('button', { name: /新建案件/ });
    await user.click(newCaseButton);

    expect(mockNavigate).toHaveBeenCalledWith('/cases/new');
  });

  it('renders icons for each action', () => {
    render(<QuickActions />);

    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(4);
  });

  it('has correct aria-labels for accessibility', () => {
    render(<QuickActions />);

    expect(screen.getByRole('button', { name: /新建案件: 创建新的法律案件/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /证据上传: 上传案件相关证据材料/ })).toBeInTheDocument();
  });
});
