import { NavLink } from 'react-router-dom';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  Shield,
  Scale,
  Clock,
  TrendingUp,
  Gavel,
  Bell,
  Settings,
  Key,
  MessageSquare,
  History,
  BrainCircuit,
  Network,
  ClipboardCheck,
  Users,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useCurrentCase } from '@/contexts/use-current-case';

const CASE_ID_FALLBACK = '1';

interface MobileSidebarProps {
  open: boolean;
  onClose: () => void;
}

function MobileNavItem({ to, icon: Icon, label, onClick }: {
  to: string;
  icon: typeof LayoutDashboard;
  label: string;
  onClick: () => void;
}) {
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-colors',
          isActive
            ? 'bg-teal-50 text-teal-800 dark:bg-teal-950/50 dark:text-teal-200'
            : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
        )
      }
    >
      <Icon size={20} className="shrink-0" />
      <span>{label}</span>
      <ChevronRight size={16} className="ml-auto text-slate-400" />
    </NavLink>
  );
}

export function MobileSidebar({ open, onClose }: MobileSidebarProps) {
  const { currentCaseId } = useCurrentCase();
  const activeCaseId = currentCaseId || CASE_ID_FALLBACK;

  return (
    <Sheet open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <SheetContent side="left" className="w-72 p-0">
        <SheetHeader className="border-b border-slate-200 px-4 py-4 dark:border-slate-800">
          <SheetTitle>
            <span className="text-base font-semibold text-slate-950 dark:text-slate-50">
              法律大模型
            </span>
            <span className="ml-2 text-xs text-slate-500 dark:text-slate-400">
              AI案件指挥台
            </span>
          </SheetTitle>
        </SheetHeader>

        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <div className="space-y-1">
            <MobileNavItem to="/dashboard" icon={LayoutDashboard} label="总览工作台" onClick={onClose} />
            <MobileNavItem to="/cases" icon={Briefcase} label="案件管理" onClick={onClose} />
            <MobileNavItem to={`/cases/${activeCaseId}/chat`} icon={MessageSquare} label="AI律师" onClick={onClose} />
            <MobileNavItem to={`/cases/${activeCaseId}/documents`} icon={FileText} label="文书生成" onClick={onClose} />
            <MobileNavItem to={`/cases/${activeCaseId}/evidence`} icon={Shield} label="证据管理" onClick={onClose} />
            <MobileNavItem to={`/evidence-graph/${activeCaseId}`} icon={Network} label="证据图谱" onClick={onClose} />
            <MobileNavItem to={`/evidence-guide/${activeCaseId}`} icon={ClipboardCheck} label="证据引导" onClick={onClose} />
            <MobileNavItem to={`/cases/${activeCaseId}/analysis`} icon={TrendingUp} label="对抗分析" onClick={onClose} />
            <MobileNavItem to={`/insight/${activeCaseId}`} icon={BrainCircuit} label="增强分析" onClick={onClose} />
            <MobileNavItem to={`/hearing/${activeCaseId}`} icon={Scale} label="出庭抗辩" onClick={onClose} />
            <MobileNavItem to={`/timeline/${activeCaseId}`} icon={Clock} label="时间把控" onClick={onClose} />
            <MobileNavItem to={`/appeal/${activeCaseId}`} icon={Gavel} label="上诉追踪" onClick={onClose} />
            <MobileNavItem to={`/execution/${activeCaseId}`} icon={Users} label="执行跟踪" onClick={onClose} />
            <MobileNavItem to="/reminders" icon={Bell} label="提醒中心" onClick={onClose} />
            <MobileNavItem to={`/analysis-history/${activeCaseId}`} icon={History} label="流式分析" onClick={onClose} />
          </div>

          <div className="mt-4 border-t border-slate-200 pt-4 dark:border-slate-800">
            <MobileNavItem to="/settings/api-keys" icon={Key} label="API Key 配置" onClick={onClose} />
            <MobileNavItem to="/settings/tenant" icon={Settings} label="租户管理" onClick={onClose} />
          </div>
        </nav>
      </SheetContent>
    </Sheet>
  );
}
