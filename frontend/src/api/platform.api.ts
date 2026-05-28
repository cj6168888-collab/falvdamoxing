import axiosInstance from './client';

export interface PlatformStats {
  total_tenants: number;
  pending_approvals: number;
  active_tenants: number;
  total_users: number;
  total_revenue_monthly: number;
  ai_calls_today: number;
}

export interface TenantDetail {
  id: string;
  name: string;
  tenant_type: string;
  slug: string;
  plan: string;
  subscription_status: string;
  approval_status: string;
  billing_cycle: string;
  billing_amount: number;
  billing_due_date: string | null;
  max_users: number;
  max_cases: number;
  ai_daily_quota: number;
  ai_monthly_usage: number;
  is_active: boolean;
  registered_from: string | null;
  created_at: string | null;
  user_count: number;
}

export async function fetchPlatformStats(): Promise<PlatformStats> {
  const { data } = await axiosInstance.get('/api/platform/stats');
  return data;
}

export async function fetchAllTenants(status?: string): Promise<TenantDetail[]> {
  const params = status ? { status } : {};
  const { data } = await axiosInstance.get('/api/platform/tenants', { params });
  return data;
}

export async function approveTenant(body: {
  tenant_id: string;
  plan: string;
  billing_cycle: string;
  billing_amount: number;
  max_users: number;
  max_cases: number;
  ai_daily_quota: number;
}) {
  const { data } = await axiosInstance.post('/api/platform/tenants/approve', body);
  return data;
}

export async function rejectTenant(body: { tenant_id: string; reason: string }) {
  const { data } = await axiosInstance.post('/api/platform/tenants/reject', body);
  return data;
}

export async function updateBilling(body: { tenant_id: string; billing_cycle: string; billing_amount: number }) {
  const { data } = await axiosInstance.put('/api/platform/tenants/billing', body);
  return data;
}

export async function toggleTenant(tenantId: string) {
  const { data } = await axiosInstance.post(`/api/platform/tenants/${tenantId}/toggle`);
  return data;
}
