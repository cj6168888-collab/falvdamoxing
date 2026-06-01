import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import CaseNewPage from './new';
import { useAuthStore } from '@/stores/auth.store';
import type { Tenant, TenantType } from '@/types/auth';

vi.mock('@/hooks/use-case', () => ({
  useCreateCase: () => ({
    mutateAsync: vi.fn(),
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
  });

  it('uses enterprise legal matter copy and preselects the requested template', () => {
    renderPage('/cases/new?template=debt_collection', 'enterprise');

    expect(screen.getByRole('heading', { name: '新建法律事项' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: '选择企业法律事项' })).toBeInTheDocument();
    expect(screen.getByText('事项信息 (已选择: 欠款催收)')).toBeInTheDocument();
    expect(screen.getByText('我方主体')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '创建事项' })).toBeInTheDocument();
  });

  it('uses personal legal backstop copy and preselects urgent risk', () => {
    renderPage('/cases/new?template=urgent_risk', 'personal');

    expect(screen.getByRole('heading', { name: '新建法律问题' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: '选择个人法律问题' })).toBeInTheDocument();
    expect(screen.getByText('问题信息 (已选择: 紧急风险判断)')).toBeInTheDocument();
    expect(screen.getByText('先保住证据')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '创建问题' })).toBeInTheDocument();
  });
});
