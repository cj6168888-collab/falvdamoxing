import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './sidebar';
import { Header } from './header';
import { useAuthStore } from '@/stores/auth.store';
import { useTenantStore } from '@/stores/tenant.store';

export function AppShell() {
  const tenant = useAuthStore((s) => s.tenant);
  const setTenant = useTenantStore((s) => s.setTenant);

  // Sync tenant to tenant store whenever it changes
  useEffect(() => {
    setTenant(tenant);
  }, [tenant, setTenant]);

  return (
    <div className="flex h-screen bg-slate-100 text-slate-950 dark:bg-slate-950 dark:text-slate-100">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto bg-[linear-gradient(180deg,#f8fafc_0%,#eef3f1_100%)] dark:bg-[linear-gradient(180deg,#020617_0%,#07110f_100%)]">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
