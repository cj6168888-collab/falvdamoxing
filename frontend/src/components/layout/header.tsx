import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Moon, Sun, Settings, LogOut, ChevronDown, Building2, Menu } from 'lucide-react';
import { TaskNotification } from './task-notification';
import { MobileSidebar } from './mobile-sidebar';
import { useAuthStore } from '@/stores/auth.store';
import { ROLE_LABELS, TENANT_TYPE_LABELS } from '@/types/auth';

export function Header({ mobileMenuOpen, onOpenMobileMenu, onCloseMobileMenu }: {
  mobileMenuOpen: boolean;
  onOpenMobileMenu: () => void;
  onCloseMobileMenu: () => void;
}) {
  const [darkMode, setDarkMode] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const user = useAuthStore((s) => s.user);
  const tenant = useAuthStore((s) => s.tenant);
  const logout = useAuthStore((s) => s.logout);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark');
  };

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  // Close menu on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const userInitials = user?.full_name
    ? user.full_name.slice(0, 2)
    : user?.username
      ? user.username.slice(0, 2).toUpperCase()
      : 'U';

  const roleLabel = user?.role ? ROLE_LABELS[user.role] : '';
  const tenantTypeLabel = tenant?.tenant_type ? TENANT_TYPE_LABELS[tenant.tenant_type] : '';

  return (
    <header className="flex h-16 items-center justify-between gap-3 border-b border-slate-200 bg-white/95 px-3 backdrop-blur dark:border-slate-800 dark:bg-slate-950/90 sm:px-4 lg:px-6">
      {/* Hamburger — mobile only */}
      <button
        onClick={onOpenMobileMenu}
        className="rounded-md p-2 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 lg:hidden"
        aria-label="打开菜单"
      >
        <Menu size={22} />
      </button>

      <MobileSidebar open={mobileMenuOpen} onClose={onCloseMobileMenu} />

      <div className="min-w-0 flex-1 items-center gap-3 text-sm text-slate-500 dark:text-slate-400 sm:flex">
        <div className="hidden h-8 items-center rounded-md border border-slate-200 bg-slate-50 px-3 text-xs font-medium text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 md:flex">
          预生产验收通过
        </div>
        {tenant && (
          <div className="flex min-w-0 items-center gap-1.5">
            <Building2 size={14} />
            <span className="truncate font-medium text-slate-700 dark:text-slate-200">
              [{tenantTypeLabel}] {tenant.name}
            </span>
          </div>
        )}
      </div>

      <div className="flex shrink-0 items-center gap-1 sm:gap-2 lg:gap-3">
        <button
          onClick={toggleDarkMode}
          className="rounded-md p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
          aria-label="切换深色模式"
        >
          {darkMode ? <Sun size={20} /> : <Moon size={20} />}
        </button>

        <TaskNotification />

        <button
          className="rounded-md p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
          aria-label="设置"
          onClick={() => navigate('/settings/api-keys')}
        >
          <Settings size={20} />
        </button>

        {/* User Menu */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="flex items-center gap-2 rounded-md p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label="用户菜单"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-teal-700 text-sm font-medium text-white">
              {userInitials}
            </div>
            <div className="hidden text-left md:block">
                <div className="text-sm font-medium text-slate-700 dark:text-slate-200">
                {user?.full_name || user?.username}
              </div>
              {roleLabel && (
                <div className="text-xs text-slate-500 dark:text-slate-400">{roleLabel}</div>
              )}
            </div>
            <ChevronDown size={14} className="text-slate-400" />
          </button>

          {userMenuOpen && (
            <div className="absolute right-0 top-full z-50 mt-1 w-56 rounded-lg border border-slate-200 bg-white py-1 shadow-lg dark:border-slate-800 dark:bg-slate-900">
              <div className="border-b border-slate-100 px-4 py-2 dark:border-slate-800">
                <div className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {user?.full_name || user?.username}
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400">{user?.email}</div>
                {tenant && (
                  <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    {tenantTypeLabel}：{tenant.name}
                  </div>
                )}
              </div>
              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
              >
                <LogOut size={14} />
                退出登录
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
