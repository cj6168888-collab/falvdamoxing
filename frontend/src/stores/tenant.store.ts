import { create } from 'zustand';
import type { Tenant, TenantType } from '@/types/auth';

interface TenantStore {
  tenant: Tenant | null;
  tenantType: TenantType | null;

  // Computed
  isLawFirm: () => boolean;
  isEnterprise: () => boolean;
  isPersonal: () => boolean;

  // Actions
  setTenant: (tenant: Tenant | null) => void;
  getTenantType: () => TenantType | null;
}

export const useTenantStore = create<TenantStore>((set, get) => ({
  tenant: null,
  tenantType: null,

  isLawFirm: () => get().tenantType === 'law_firm',
  isEnterprise: () => get().tenantType === 'enterprise',
  isPersonal: () => get().tenantType === 'personal',

  setTenant: (tenant) => {
    set({
      tenant,
      tenantType: tenant?.tenant_type ?? null,
    });
  },

  getTenantType: () => get().tenantType,
}));

// Sync tenant from auth store
export function syncTenantFromAuth(tenant: Tenant | null) {
  useTenantStore.getState().setTenant(tenant);
}
