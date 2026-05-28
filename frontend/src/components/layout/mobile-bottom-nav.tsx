import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Briefcase, MessageSquare, Shield, Menu } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useCurrentCase } from '@/contexts/use-current-case';

const CASE_ID_FALLBACK = '1';

interface TabProps {
  to: string;
  icon: typeof LayoutDashboard;
  label: string;
}

function BottomTab({ to, icon: Icon, label }: TabProps) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          'flex flex-col items-center justify-center gap-0.5 px-1 py-2 text-[11px] font-medium transition-colors',
          isActive
            ? 'text-teal-700 dark:text-teal-300'
            : 'text-slate-500 dark:text-slate-400'
        )
      }
    >
      <Icon size={20} />
      <span>{label}</span>
    </NavLink>
  );
}

interface MobileBottomNavProps {
  onOpenMenu: () => void;
}

export function MobileBottomNav({ onOpenMenu }: MobileBottomNavProps) {
  const { currentCaseId } = useCurrentCase();
  const activeCaseId = currentCaseId || CASE_ID_FALLBACK;

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 flex items-center justify-around border-t border-slate-200 bg-white/95 pb-[env(safe-area-inset-bottom,0px)] backdrop-blur dark:border-slate-800 dark:bg-slate-950/95 lg:hidden">
      <BottomTab to="/dashboard" icon={LayoutDashboard} label="工作台" />
      <BottomTab to="/cases" icon={Briefcase} label="案件" />
      <BottomTab to={`/cases/${activeCaseId}/chat`} icon={MessageSquare} label="AI律师" />
      <BottomTab to={`/cases/${activeCaseId}/evidence`} icon={Shield} label="证据" />
      <button
        onClick={onOpenMenu}
        className="flex flex-col items-center justify-center gap-0.5 px-1 py-2 text-[11px] font-medium text-slate-500 dark:text-slate-400"
        aria-label="更多菜单"
      >
        <Menu size={20} />
        <span>更多</span>
      </button>
    </nav>
  );
}
