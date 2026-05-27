import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { DuplicateDetector } from '@/components/evidence/duplicate-detector';

describe('DuplicateDetector', () => {
  it('shows duplicate warning when duplicates exist', () => {
    const duplicates = [
      { id: 'dup-1', name: '合同副本', similarity: 95 },
      { id: 'dup-2', name: '收据复印件', similarity: 80 },
    ];

    render(<DuplicateDetector duplicates={duplicates} onMerge={vi.fn()} />);

    expect(screen.getByText('重复检测')).toBeInTheDocument();
    expect(screen.getByText('合同副本')).toBeInTheDocument();
    expect(screen.getByText('收据复印件')).toBeInTheDocument();
    expect(screen.getByText('相似度: 95%')).toBeInTheDocument();
    expect(screen.getByText('相似度: 80%')).toBeInTheDocument();
  });

  it('shows merge buttons for each duplicate', () => {
    const duplicates = [
      { id: 'dup-1', name: '合同副本', similarity: 95 },
    ];

    render(<DuplicateDetector duplicates={duplicates} onMerge={vi.fn()} />);

    const mergeButtons = screen.getAllByText('合并');
    expect(mergeButtons).toHaveLength(1);
  });

  it('shows no duplicates state when list is empty', () => {
    render(<DuplicateDetector duplicates={[]} onMerge={vi.fn()} />);

    expect(screen.queryByText('重复检测')).not.toBeInTheDocument();
  });

  it('calls onMerge with correct ids when merge button is clicked', async () => {
    const handleMerge = vi.fn();
    const duplicates = [
      { id: 'dup-1', name: '合同副本', similarity: 95 },
      { id: 'dup-2', name: '收据复印件', similarity: 80 },
    ];

    const user = userEvent.setup();
    render(<DuplicateDetector duplicates={duplicates} onMerge={handleMerge} />);

    const mergeButtons = screen.getAllByText('合并');
    await user.click(mergeButtons[0]);

    expect(handleMerge).toHaveBeenCalledWith(['dup-1']);
  });

  it('handles null duplicates gracefully', () => {
    render(<DuplicateDetector duplicates={null} onMerge={vi.fn()} />);

    expect(screen.queryByText('重复检测')).not.toBeInTheDocument();
  });
});
