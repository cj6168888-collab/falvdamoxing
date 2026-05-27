import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { QuickQuestions } from './quick-questions';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

describe('QuickQuestions', () => {
  it('renders quick question buttons', () => {
    const questions = ['What is my deadline?', 'How to submit evidence?'];
    render(<QuickQuestions questions={questions} onSelect={vi.fn()} />);

    expect(screen.getByText('What is my deadline?')).toBeInTheDocument();
    expect(screen.getByText('How to submit evidence?')).toBeInTheDocument();
  });

  it('calls onSelect with question when clicked', () => {
    const questions = ['What is my deadline?', 'How to submit evidence?'];
    const onSelect = vi.fn();
    render(<QuickQuestions questions={questions} onSelect={onSelect} />);

    fireEvent.click(screen.getByText('What is my deadline?'));

    expect(onSelect).toHaveBeenCalledWith('What is my deadline?');
  });

  it('shows all questions in the list', () => {
    const questions = ['Q1', 'Q2', 'Q3', 'Q4'];
    render(<QuickQuestions questions={questions} onSelect={vi.fn()} />);

    questions.forEach((q) => {
      expect(screen.getByText(q)).toBeInTheDocument();
    });
  });

  it('renders empty state when no questions', () => {
    render(<QuickQuestions questions={[]} onSelect={vi.fn()} />);

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
