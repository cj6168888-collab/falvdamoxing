import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { ChatInput } from './chat-input';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

describe('ChatInput', () => {
  it('renders input field and send button', () => {
    render(<ChatInput onSend={vi.fn()} />);

    expect(screen.getByPlaceholderText('输入您的问题...')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('calls onSend with message when send button is clicked', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const textarea = screen.getByPlaceholderText('输入您的问题...');
    fireEvent.change(textarea, { target: { value: 'What is the deadline?' } });

    fireEvent.click(screen.getByRole('button'));

    expect(onSend).toHaveBeenCalledWith('What is the deadline?');
  });

  it('does not call onSend when input is empty', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    fireEvent.click(screen.getByRole('button'));

    expect(onSend).not.toHaveBeenCalled();
  });

  it('submits message on Enter key', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const textarea = screen.getByPlaceholderText('输入您的问题...');
    fireEvent.change(textarea, { target: { value: 'Test message' } });
    fireEvent.keyDown(textarea, { key: 'Enter' });

    expect(onSend).toHaveBeenCalledWith('Test message');
  });

  it('clears input after sending', () => {
    render(<ChatInput onSend={vi.fn()} />);

    const textarea = screen.getByPlaceholderText('输入您的问题...');
    fireEvent.change(textarea, { target: { value: 'Hello' } });
    fireEvent.click(screen.getByRole('button'));

    expect(textarea).toHaveValue('');
  });
});
