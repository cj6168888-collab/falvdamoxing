import { CorrectionForm } from '@/components/evidence/correction-form';
import { render, screen } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

describe('CorrectionForm', () => {
  it('renders form fields correctly', () => {
    render(<CorrectionForm evidenceId="ev-1" onSubmit={vi.fn()} />);

    expect(screen.getByText('人工纠偏')).toBeInTheDocument();
    expect(screen.getByText('证据编号：ev-1')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('修正类型')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('修正证明方向')).toBeInTheDocument();
    expect(screen.getByText('提交纠偏')).toBeInTheDocument();
  });

  it('calls onSubmit with form data when submitted', async () => {
    const handleSubmit = vi.fn();
    const user = userEvent.setup();

    render(<CorrectionForm evidenceId="ev-1" onSubmit={handleSubmit} />);

    const typeInput = screen.getByPlaceholderText('修正类型');
    const proofInput = screen.getByPlaceholderText('修正证明方向');

    await user.type(typeInput, '书证');
    await user.type(proofInput, '证明借款事实');

    const submitButton = screen.getByText('提交纠偏');
    await user.click(submitButton);

    expect(handleSubmit).toHaveBeenCalledWith({
      type: '书证',
      proofDirection: '证明借款事实',
    });
  });

  it('updates input values on change', async () => {
    const user = userEvent.setup();
    render(<CorrectionForm evidenceId="ev-1" onSubmit={vi.fn()} />);

    const typeInput = screen.getByPlaceholderText('修正类型');
    await user.type(typeInput, '物证');

    expect(typeInput).toHaveValue('物证');
  });

  it('renders with correct evidenceId context', () => {
    render(<CorrectionForm evidenceId="ev-123" onSubmit={vi.fn()} />);

    expect(screen.getByText('证据编号：ev-123')).toBeInTheDocument();
  });

  it('submits empty values when fields are not filled', async () => {
    const handleSubmit = vi.fn();
    const user = userEvent.setup();

    render(<CorrectionForm evidenceId="ev-1" onSubmit={handleSubmit} />);

    const submitButton = screen.getByText('提交纠偏');
    await user.click(submitButton);

    expect(handleSubmit).toHaveBeenCalledWith({
      type: '',
      proofDirection: '',
    });
  });
});
