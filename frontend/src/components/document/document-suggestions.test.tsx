import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { DocumentSuggestions } from '@/components/document/document-suggestions';

describe('DocumentSuggestions', () => {
  it('renders suggested documents correctly', () => {
    const suggestions = [
      { type: '起诉状', reason: '基于案件类型推荐' },
      { type: '证据目录', reason: '证据数量较多，建议整理' },
    ];

    render(<DocumentSuggestions suggestions={suggestions} onGenerate={vi.fn()} />);

    expect(screen.getByText('AI 推荐文书')).toBeInTheDocument();
    expect(screen.getByText('起诉状')).toBeInTheDocument();
    expect(screen.getByText('证据目录')).toBeInTheDocument();
    expect(screen.getByText('基于案件类型推荐')).toBeInTheDocument();
    expect(screen.getByText('证据数量较多，建议整理')).toBeInTheDocument();
  });

  it('calls onGenerate with correct type when generate button is clicked', async () => {
    const handleGenerate = vi.fn();
    const suggestions = [
      { type: '起诉状', reason: '基于案件类型推荐' },
      { type: '证据目录', reason: '证据数量较多，建议整理' },
    ];

    const user = userEvent.setup();
    render(<DocumentSuggestions suggestions={suggestions} onGenerate={handleGenerate} />);

    const generateButtons = screen.getAllByText('生成');
    await user.click(generateButtons[0]);

    expect(handleGenerate).toHaveBeenCalledWith('起诉状');
  });

  it('shows recommendation reason for each suggestion', () => {
    const suggestions = [
      { type: '答辩状', reason: '对方已起诉，需要准备答辩' },
    ];

    render(<DocumentSuggestions suggestions={suggestions} onGenerate={vi.fn()} />);

    expect(screen.getByText('对方已起诉，需要准备答辩')).toBeInTheDocument();
  });

  it('shows no suggestions state when list is empty', () => {
    render(<DocumentSuggestions suggestions={[]} onGenerate={vi.fn()} />);

    expect(screen.queryByText('AI 推荐文书')).not.toBeInTheDocument();
  });

  it('handles null suggestions gracefully', () => {
    render(<DocumentSuggestions suggestions={null} onGenerate={vi.fn()} />);

    expect(screen.queryByText('AI 推荐文书')).not.toBeInTheDocument();
  });
});
