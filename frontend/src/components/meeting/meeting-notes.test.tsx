import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { MeetingNotes } from './meeting-notes';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

describe('MeetingNotes', () => {
  it('renders meeting notes content', () => {
    render(
      <MeetingNotes
        initialNotes="Meeting discussion summary"
        onSave={vi.fn()}
      />
    );

    expect(screen.getByText('会议纪要')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Meeting discussion summary')).toBeInTheDocument();
  });

  it('shows edit button', () => {
    render(
      <MeetingNotes
        initialNotes="Test notes"
        onSave={vi.fn()}
      />
    );

    expect(screen.getByText('保存纪要')).toBeInTheDocument();
  });

  it('calls onSave when save button is clicked', () => {
    const onSave = vi.fn();
    render(
      <MeetingNotes
        initialNotes="Original notes"
        onSave={onSave}
      />
    );

    fireEvent.click(screen.getByText('保存纪要'));
    expect(onSave).toHaveBeenCalledWith('Original notes');
  });

  it('shows empty state when no initial notes', () => {
    render(
      <MeetingNotes
        onSave={vi.fn()}
      />
    );

    const textarea = screen.getByPlaceholderText('输入会议纪要...');
    expect(textarea).toHaveValue('');
  });

  it('updates notes when edited', () => {
    render(
      <MeetingNotes
        initialNotes=""
        onSave={vi.fn()}
      />
    );

    const textarea = screen.getByPlaceholderText('输入会议纪要...');
    fireEvent.change(textarea, { target: { value: 'Updated notes' } });

    expect(textarea).toHaveValue('Updated notes');
  });
});
