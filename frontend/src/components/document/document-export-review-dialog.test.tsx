import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DocumentExportReviewDialog } from './document-export-review-dialog';

describe('DocumentExportReviewDialog', () => {
  it('requires every review item before confirming export', () => {
    const onConfirm = vi.fn();

    render(
      <DocumentExportReviewDialog
        open
        documentTitle="起诉状草稿"
        exportLabel="导出 Word"
        onOpenChange={vi.fn()}
        onConfirm={onConfirm}
      />,
    );

    const confirmButton = screen.getByRole('button', { name: '导出 Word' });
    expect(confirmButton).toBeDisabled();
    expect(screen.getByText('0/8 项已核验')).toBeInTheDocument();
    expect(screen.getByText('法院、管辖依据和案由已核对')).toBeInTheDocument();
    expect(screen.getByText('法条、案例、案号和现行有效性已另行核验')).toBeInTheDocument();
    expect(screen.getByText('授权材料和对外发送后果已向委托人确认')).toBeInTheDocument();

    for (const checkbox of screen.getAllByRole('checkbox')) {
      fireEvent.click(checkbox);
    }

    expect(screen.getByText('8/8 项已核验')).toBeInTheDocument();
    expect(confirmButton).toBeEnabled();

    fireEvent.click(confirmButton);
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('resets checklist when reopened', () => {
    const { rerender } = render(
      <DocumentExportReviewDialog
        open
        documentTitle="代理词草稿"
        onOpenChange={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );

    fireEvent.click(screen.getAllByRole('checkbox')[0]);
    expect(screen.getByText('1/8 项已核验')).toBeInTheDocument();

    rerender(
      <DocumentExportReviewDialog
        open={false}
        documentTitle="代理词草稿"
        onOpenChange={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );

    rerender(
      <DocumentExportReviewDialog
        open
        documentTitle="代理词草稿"
        onOpenChange={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );

    expect(screen.getByText('0/8 项已核验')).toBeInTheDocument();
  });
});
