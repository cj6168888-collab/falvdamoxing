import { render, screen } from '@/test/test-utils';
import { StatusBadge } from './status-badge';

describe('StatusBadge', () => {
  it('renders with correct label', () => {
    render(<StatusBadge label="进行中" variant="in-progress" />);
    expect(screen.getByText('进行中')).toBeInTheDocument();
  });

  it('renders completed variant', () => {
    render(<StatusBadge label="已完成" variant="completed" />);
    expect(screen.getByText('已完成')).toBeInTheDocument();
  });

  it('renders urgent variant', () => {
    render(<StatusBadge label="紧急" variant="urgent" />);
    expect(screen.getByText('紧急')).toBeInTheDocument();
  });

  it('renders warning variant', () => {
    render(<StatusBadge label="预警" variant="warning" />);
    expect(screen.getByText('预警')).toBeInTheDocument();
  });

  it('renders draft variant', () => {
    render(<StatusBadge label="草稿" variant="draft" />);
    expect(screen.getByText('草稿')).toBeInTheDocument();
  });

  it('renders closed variant', () => {
    render(<StatusBadge label="已关闭" variant="closed" />);
    expect(screen.getByText('已关闭')).toBeInTheDocument();
  });

  it('defaults to draft variant when no variant provided', () => {
    render(<StatusBadge label="测试" />);
    expect(screen.getByText('测试')).toBeInTheDocument();
  });
});
