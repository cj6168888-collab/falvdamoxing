import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { MeetingTemplate } from './meeting-template';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

describe('MeetingTemplate', () => {
  it('renders meeting template form', () => {
    render(<MeetingTemplate onSelect={vi.fn()} />);

    expect(screen.getByText('会议类型')).toBeInTheDocument();
  });

  it('shows all meeting type options', () => {
    render(<MeetingTemplate onSelect={vi.fn()} />);

    expect(screen.getByText('商务谈判')).toBeInTheDocument();
    expect(screen.getByText('调解会议')).toBeInTheDocument();
    expect(screen.getByText('证据交换')).toBeInTheDocument();
    expect(screen.getByText('庭前会议')).toBeInTheDocument();
  });

  it('calls onSelect with type when button is clicked', () => {
    const onSelect = vi.fn();
    render(<MeetingTemplate onSelect={onSelect} />);

    fireEvent.click(screen.getByText('商务谈判'));
    expect(onSelect).toHaveBeenCalledWith('商务谈判');
  });

  it('calls onSelect with correct type for each option', () => {
    const onSelect = vi.fn();
    render(<MeetingTemplate onSelect={onSelect} />);

    fireEvent.click(screen.getByText('调解会议'));
    expect(onSelect).toHaveBeenCalledWith('调解会议');

    fireEvent.click(screen.getByText('证据交换'));
    expect(onSelect).toHaveBeenCalledWith('证据交换');
  });
});
