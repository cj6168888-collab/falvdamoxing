import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import CaseNewPage from './new';
import { useAuthStore } from '@/stores/auth.store';
import type { Tenant, TenantType } from '@/types/auth';

const mocks = vi.hoisted(() => ({
  createCase: vi.fn(),
}));

vi.mock('@/hooks/use-case', () => ({
  useCreateCase: () => ({
    mutateAsync: mocks.createCase,
    isPending: false,
  }),
}));

function tenantOf(type: TenantType): Tenant {
  return {
    id: `${type}-1`,
    name: `${type} tenant`,
    tenant_type: type,
    slug: `${type}-tenant`,
    logo_url: null,
    plan: 'free',
    subscription_status: 'active',
    is_active: true,
    created_at: null,
  };
}

function renderPage(initialEntry: string, tenantType: TenantType) {
  useAuthStore.setState({ tenant: tenantOf(tenantType) });
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <CaseNewPage />
    </MemoryRouter>
  );
}

describe('CaseNewPage audience templates', () => {
  beforeEach(() => {
    useAuthStore.setState({ tenant: null });
    mocks.createCase.mockReset();
    mocks.createCase.mockResolvedValue({ id: 'case-1' });
  });

  it('uses enterprise legal matter copy and preselects the requested template', () => {
    renderPage('/cases/new?template=debt_collection', 'enterprise');

    expect(screen.getByRole('heading', { name: '新建法律事项' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: '选择企业法律事项' })).toBeInTheDocument();
    expect(screen.getByText('事项信息 (已选择: 欠款催收)')).toBeInTheDocument();
    expect(screen.getByText('我方主体')).toBeInTheDocument();
    expect(screen.getByText('企业法律顾问第一轮问题')).toBeInTheDocument();
    expect(screen.getByText('金额与期限')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '创建事项' })).toBeInTheDocument();
  });

  it('uses personal legal backstop copy and preselects urgent risk', () => {
    renderPage('/cases/new?template=urgent_risk', 'personal');

    expect(screen.getByRole('heading', { name: '新建法律问题' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: '选择个人法律问题' })).toBeInTheDocument();
    expect(screen.getByText('问题信息 (已选择: 紧急风险判断)')).toBeInTheDocument();
    expect(screen.getByText('个人法律后盾第一轮问题')).toBeInTheDocument();
    expect(screen.getByText('是否有紧急期限或安全风险')).toBeInTheDocument();
    expect(screen.getByText('先保住证据')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '创建问题' })).toBeInTheDocument();
  });

  it('stores enterprise guidance answers in the created matter description', async () => {
    const user = userEvent.setup();
    renderPage('/cases/new?template=debt_collection', 'enterprise');

    await user.type(screen.getByPlaceholderText('例如：某客户拖欠货款催收、某合同付款条款审查'), '客户A欠款催收');
    await user.type(screen.getByPlaceholderText('说明业务背景、已发生的事实、目前想解决的问题和已采取行动'), '客户已逾期两个月。');
    await user.type(screen.getByPlaceholderText('公司名称、经办部门、业务背景、内部审批或负责人员。'), '吉林某科技公司，财务部经办。');
    await user.type(screen.getByPlaceholderText('合同额、欠款额、付款/交付/解除/仲裁等关键期限。'), '欠款 12 万，约定 5 月 20 日付款。');
    await user.click(screen.getByRole('button', { name: '创建事项' }));

    expect(mocks.createCase).toHaveBeenCalledWith(
      expect.objectContaining({
        title: '客户A欠款催收',
        cause: '欠款催收',
        description: expect.stringContaining('【企业法律顾问第一轮问题】'),
      })
    );
    expect(mocks.createCase.mock.calls[0][0].description).toContain('公司基本信息：吉林某科技公司，财务部经办。');
    expect(mocks.createCase.mock.calls[0][0].description).toContain('金额与期限：欠款 12 万，约定 5 月 20 日付款。');
  });

  it('stores personal guidance answers in a backstop-oriented description', async () => {
    const user = userEvent.setup();
    renderPage('/cases/new?template=urgent_risk', 'personal');

    await user.type(screen.getByPlaceholderText('例如：房东不退押金、公司拖欠工资、朋友借钱不还'), '房东不退押金');
    await user.type(screen.getByPlaceholderText('不用专业术语，按时间顺序说清发生了什么、现在最担心什么'), '房东说押金全部扣掉。');
    await user.type(screen.getByPlaceholderText('担心钱拿不回、被起诉、被辞退、安全风险、证据丢失等。'), '担心聊天记录不够，也担心对方拉黑。');
    await user.type(screen.getByPlaceholderText('先保存证据、先沟通、先投诉、先写说明、先确认期限等。'), '今天先把聊天和付款记录保存下来。');
    await user.click(screen.getByRole('button', { name: '创建问题' }));

    expect(mocks.createCase).toHaveBeenCalledWith(
      expect.objectContaining({
        title: '房东不退押金',
        cause: '紧急风险判断',
        description: expect.stringContaining('【个人法律后盾第一轮问题】'),
      })
    );
    expect(mocks.createCase.mock.calls[0][0].description).toContain('现在最担心什么：担心聊天记录不够，也担心对方拉黑。');
    expect(mocks.createCase.mock.calls[0][0].description).toContain('今天最想先解决的一步：今天先把聊天和付款记录保存下来。');
  });
});
