import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { ChatMessage } from './chat-message';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

describe('ChatMessage', () => {
  it('renders user message', () => {
    render(
      <ChatMessage
        role="user"
        content="Hello, I need help"
        timestamp="10:30 AM"
      />
    );

    expect(screen.getByText('Hello, I need help')).toBeInTheDocument();
    expect(screen.getByText('10:30 AM')).toBeInTheDocument();
  });

  it('renders assistant message', () => {
    render(
      <ChatMessage
        role="assistant"
        content="How can I assist you?"
        timestamp="10:31 AM"
      />
    );

    expect(screen.getByText('How can I assist you?')).toBeInTheDocument();
    expect(screen.getByText('10:31 AM')).toBeInTheDocument();
  });

  it('shows timestamp', () => {
    render(
      <ChatMessage
        role="user"
        content="Test"
        timestamp="2:45 PM"
      />
    );

    expect(screen.getByText('2:45 PM')).toBeInTheDocument();
  });

  it('renders long message content', () => {
    const longContent = 'This is a very long message that spans multiple lines and contains detailed information about the legal case and its proceedings.';
    render(
      <ChatMessage
        role="assistant"
        content={longContent}
        timestamp="3:00 PM"
      />
    );

    expect(screen.getByText(longContent)).toBeInTheDocument();
  });
});
