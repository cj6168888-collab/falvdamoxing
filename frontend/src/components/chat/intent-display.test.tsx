import { describe, expect, it } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { IntentDisplay } from './intent-display';

describe('IntentDisplay', () => {
  it('uses recognition-reference wording instead of confidence wording', () => {
    render(<IntentDisplay intent="证据分析" confidence={0.86} />);

    expect(screen.getByText('意图: 证据分析')).toBeInTheDocument();
    expect(screen.getByText('识别参考 86%')).toBeInTheDocument();
    expect(screen.queryByText(/置信度/)).not.toBeInTheDocument();
  });
});
