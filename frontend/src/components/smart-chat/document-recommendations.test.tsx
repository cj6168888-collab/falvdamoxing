import { fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { DocumentRecommendations } from './document-recommendations';

const documents = [
  { type: '起诉状', reason: '用于梳理诉讼请求', priority: 'high' },
  { type: '证据目录', reason: '用于对应证据编号和证明目的', priority: 'medium' },
];

describe('Smart Chat DocumentRecommendations', () => {
  it('frames recommended documents as draft workpapers', () => {
    const onGenerateDoc = vi.fn();
    const onGenerateAllDocs = vi.fn();

    render(
      <DocumentRecommendations
        documents={documents}
        onGenerateDoc={onGenerateDoc}
        onGenerateAllDocs={onGenerateAllDocs}
      />,
    );

    expect(screen.getByText('推荐文书草稿（点击起草）')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /批量起草草稿/ })).toBeInTheDocument();
    expect(screen.queryByText(/一键.*全部.*生成/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /批量起草草稿/ }));
    expect(onGenerateAllDocs).toHaveBeenCalledWith(documents);
  });

  it('uses draft wording while generation is pending', () => {
    render(
      <DocumentRecommendations
        documents={documents}
        onGenerateDoc={vi.fn()}
        onGenerateAllDocs={vi.fn()}
        isGenerating
      />,
    );

    expect(screen.getByRole('button', { name: /起草中/ })).toBeDisabled();
  });
});
