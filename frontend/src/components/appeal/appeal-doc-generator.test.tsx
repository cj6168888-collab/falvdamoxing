import { fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { AppealDocGenerator } from './appeal-doc-generator';

describe('AppealDocGenerator', () => {
  it('uses draft wording for appeal documents', () => {
    const onGenerate = vi.fn();
    render(<AppealDocGenerator caseId="42" onGenerate={onGenerate} />);

    expect(screen.getByText('上诉文书草稿')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /起草上诉状草稿/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /起草答辩意见草稿/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /整理新证据清单草稿/ })).toBeInTheDocument();
    expect(screen.queryByText(/生成上诉状/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /起草上诉状草稿/ }));
    expect(onGenerate).toHaveBeenCalledWith('上诉状');
  });
});
