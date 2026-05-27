import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { CompanyInfoUnavailableError } from '@/api/company.api';
import { CompanySearch } from './company-check';

describe('CompanySearch', () => {
  it('shows a clear message when the company info provider is not configured', async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn().mockRejectedValue(new CompanyInfoUnavailableError());
    const onSelect = vi.fn();

    render(<CompanySearch onSearch={onSearch} onSelect={onSelect} />);

    await user.type(screen.getByPlaceholderText('输入企业名称、统一社会信用代码或注册号...'), 'ACME');
    await user.click(screen.getByRole('button', { name: /搜索/ }));

    expect(await screen.findByText('企业工商信息服务未配置，请先在 API Key 设置中配置企业信息服务')).toBeInTheDocument();
    expect(onSelect).not.toHaveBeenCalled();
  });
});
