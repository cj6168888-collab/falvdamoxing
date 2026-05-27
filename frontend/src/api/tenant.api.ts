import { apiClient } from './client';

export interface TenantProfile {
  id: string;
  name: string;
  tenant_type: string;
  slug: string;
  plan: string;
  subscription_status: string;
  max_users: number;
  max_cases: number;
  max_storage_gb: number;
  ai_daily_quota: number;
  ai_monthly_usage: number;
  is_active: boolean;
  is_verified: boolean;
  created_at: string | null;
}

export interface TeamMember {
  id: string;
  username: string;
  email: string;
  phone: string | null;
  full_name: string | null;
  role: string;
  is_active: boolean;
  is_email_verified: boolean;
  last_login_at: string | null;
  created_at: string | null;
}

export interface UsageStats {
  tenant_id: string;
  total_users: number;
  active_users: number;
  total_cases: number;
  ai_calls_today: number;
  ai_calls_this_month: number;
  ai_daily_quota: number;
  ai_monthly_usage: number;
  storage_used_mb: number;
}

export async function fetchTenantProfile(): Promise<TenantProfile> {
  const { data } = await apiClient.get('/api/tenant/profile');
  return data;
}

export async function updateTenantProfile(body: { name?: string; description?: string }) {
  const { data } = await apiClient.put('/api/tenant/profile', body);
  return data;
}

export async function fetchTeamMembers(): Promise<TeamMember[]> {
  const { data } = await apiClient.get('/api/tenant/members');
  return data;
}

export async function inviteMember(body: { email: string; full_name?: string; role: string }) {
  const { data } = await apiClient.post('/api/tenant/members/invite', body);
  return data;
}

export async function changeMemberRole(body: { user_id: string; role: string }) {
  const { data } = await apiClient.put('/api/tenant/members/role', body);
  return data;
}

export async function removeMember(userId: string) {
  const { data } = await apiClient.delete(`/api/tenant/members/${userId}`);
  return data;
}

export async function fetchUsageStats(): Promise<UsageStats> {
  const { data } = await apiClient.get('/api/tenant/usage');
  return data;
}
