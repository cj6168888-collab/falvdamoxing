import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { TemplateSelector } from '@/components/document/template-selector';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button' },
}));

const mockTemplates = [
  { id: 'tpl-1', name: '起诉状', category: '诉讼' },
  { id: 'tpl-2', name: '答辩状', category: '诉讼' },
  { id: 'tpl-3', name: '合同审查报告', category: '非诉' },
  { id: 'tpl-4', name: '律师函', category: '非诉' },
];

describe('TemplateSelector', () => {
  it('renders template list with all templates', () => {
    render(<TemplateSelector templates={mockTemplates} onSelect={vi.fn()} />);

    expect(screen.getByRole('button', { name: /全部/ })).toBeInTheDocument();
    expect(screen.getAllByText('起诉状')).toHaveLength(1);
    expect(screen.getAllByText('答辩状')).toHaveLength(1);
    expect(screen.getAllByText('合同审查报告')).toHaveLength(1);
    expect(screen.getAllByText('律师函')).toHaveLength(1);
  });

  it('filters templates by category when litigation is selected', async () => {
    const user = userEvent.setup();
    render(<TemplateSelector templates={mockTemplates} onSelect={vi.fn()} />);

    const buttons = screen.getAllByRole('button');
    const litigationButton = buttons.find(b => b.textContent === '诉讼');
    await user.click(litigationButton!);

    expect(screen.getAllByText('起诉状')).toHaveLength(1);
    expect(screen.getAllByText('答辩状')).toHaveLength(1);
    expect(screen.queryByText('合同审查报告')).not.toBeInTheDocument();
    expect(screen.queryByText('律师函')).not.toBeInTheDocument();
  });

  it('filters templates by category when non-litigation is selected', async () => {
    const user = userEvent.setup();
    render(<TemplateSelector templates={mockTemplates} onSelect={vi.fn()} />);

    const buttons = screen.getAllByRole('button');
    const nonLitigationButton = buttons.find(b => b.textContent === '非诉');
    await user.click(nonLitigationButton!);

    expect(screen.getAllByText('合同审查报告')).toHaveLength(1);
    expect(screen.getAllByText('律师函')).toHaveLength(1);
    expect(screen.queryByText('起诉状')).not.toBeInTheDocument();
    expect(screen.queryByText('答辩状')).not.toBeInTheDocument();
  });

  it('shows all templates when "全部" is selected', async () => {
    const user = userEvent.setup();
    render(<TemplateSelector templates={mockTemplates} onSelect={vi.fn()} />);

    const allButton = screen.getByRole('button', { name: /全部/ });
    await user.click(allButton);

    expect(screen.getAllByText('起诉状')).toHaveLength(1);
    expect(screen.getAllByText('答辩状')).toHaveLength(1);
    expect(screen.getAllByText('合同审查报告')).toHaveLength(1);
    expect(screen.getAllByText('律师函')).toHaveLength(1);
  });

  it('calls onSelect with correct template id when template is clicked', async () => {
    const handleSelect = vi.fn();
    const user = userEvent.setup();
    render(<TemplateSelector templates={mockTemplates} onSelect={handleSelect} />);

    const templateCard = screen.getByText('起诉状').closest('[class*="cursor-pointer"]') || screen.getByText('起诉状');
    await user.click(templateCard);

    expect(handleSelect).toHaveBeenCalledWith('tpl-1');
  });
});
