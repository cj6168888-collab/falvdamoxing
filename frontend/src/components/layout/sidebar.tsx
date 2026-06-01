import { NavLink } from 'react-router-dom';
import { useState } from 'react';
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
  ChevronLeft,
  ChevronRight,
  Scale as ScaleIcon,
  Users,
  Settings,
  Key,
  MessageSquare,
  ChevronDown,
  ChevronRight as ChevronRightIcon,
  History,
  BrainCircuit,
  Network,
  ClipboardCheck,
  ShieldCheck,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useCurrentCase } from '@/contexts/use-current-case';
import { useAuthStore } from '@/stores/auth.store';
import { getAudienceLabels } from '@/lib/audience-copy';

const CASE_ID_FALLBACK = '1';

interface NavItem {
  icon: LucideIcon;
  label: string;
  path?: string;
  key: string;
  children?: NavItem[];
}

function useCaseNavItems() {
  const { currentCaseId } = useCurrentCase();
  const activeCaseId = currentCaseId || CASE_ID_FALLBACK;
  const isPlatformAdmin = useAuthStore((s) => s.user?.is_platform_admin);
  const tenantType = useAuthStore((s) => s.tenant?.tenant_type);
  const labels = getAudienceLabels(tenantType);

  const navItems: NavItem[] = [
    { icon: LayoutDashboard, label: '总览工作台', path: '/dashboard', key: 'dashboard' },
    { icon: Briefcase, label: labels.caseList, path: '/cases', key: 'cases' },
    { icon: MessageSquare, label: labels.chatTab, path: `/cases/${activeCaseId}/chat`, key: 'ai-lawyer' },
    { icon: FileText, label: labels.documentsTab, path: `/cases/${activeCaseId}/documents`, key: 'documents' },
    { icon: Shield, label: labels.evidenceTab, path: `/cases/${activeCaseId}/evidence`, key: 'evidence' },
    { icon: Network, label: labels.evidenceGraph, path: `/evidence-graph/${activeCaseId}`, key: 'evidence-graph' },
    { icon: ClipboardCheck, label: labels.evidenceGuide, path: `/evidence-guide/${activeCaseId}`, key: 'evidence-guide' },
    { icon: TrendingUp, label: labels.analysisTab, path: `/cases/${activeCaseId}/analysis`, key: 'analysis' },
    { icon: BrainCircuit, label: labels.insight, path: `/insight/${activeCaseId}`, key: 'insight' },
    { icon: History, label: labels.streamingAnalysis, path: `/analysis-history/${activeCaseId}`, key: 'streaming-analysis' },
    { icon: Scale, label: labels.hearing, path: `/hearing/${activeCaseId}`, key: 'hearing' },
    { icon: Clock, label: labels.timelineTab, path: `/timeline/${activeCaseId}`, key: 'timeline' },
    { icon: Gavel, label: labels.progress, path: `/progress/${activeCaseId}`, key: 'progress' },
    { icon: ScaleIcon, label: labels.appealTab, path: `/appeal/${activeCaseId}`, key: 'appeal' },
    { icon: Users, label: labels.executionTab, path: `/execution/${activeCaseId}`, key: 'execution' },
    { icon: Bell, label: '提醒中心', path: '/reminders', key: 'reminders' },
    {
      icon: Settings,
      label: '系统设置',
      key: 'settings',
      children: [
        { icon: Key, label: 'API Key 配置', path: '/settings/api-keys', key: 'api-keys' },
        { icon: Users, label: '租户管理', path: '/settings/tenant', key: 'tenant' },
        ...(isPlatformAdmin
          ? [{ icon: ShieldCheck, label: '平台管理', path: '/platform', key: 'platform' }]
          : []),
      ],
    },
  ];

  return navItems;
}

interface NavItemProps {
  item: NavItem;
  collapsed: boolean;
  level?: number;
}

function NavItemComponent({ item, collapsed, level = 0 }: NavItemProps) {
  const [expanded, setExpanded] = useState(false);
  const hasChildren = item.children && item.children.length > 0;
  const Icon = item.icon;

  if (hasChildren) {
    return (
      <li>
        <button
          onClick={() => setExpanded(!expanded)}
          className={cn(
            'w-full flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors',
            'text-slate-600 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-50',
            level > 0 && 'ml-4'
          )}
          title={collapsed ? item.label : undefined}
        >
          <Icon size={20} className="shrink-0" />
          {!collapsed && (
            <>
              <span className="flex-1 text-left">{item.label}</span>
              {expanded ? (
                <ChevronDown size={16} className="text-muted-foreground" />
              ) : (
                <ChevronRightIcon size={16} className="text-muted-foreground" />
              )}
            </>
          )}
        </button>
        {!collapsed && expanded && (
          <ul className="mt-1 space-y-1">
            {item.children!.map((child) => (
              <NavItemComponent
                key={child.key}
                item={child}
                collapsed={collapsed}
                level={level + 1}
              />
            ))}
          </ul>
        )}
      </li>
    );
  }

  if (!item.path) return null;

  return (
    <li>
      <NavLink
        to={item.path}
        className={({ isActive }) =>
          cn(
            'flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors',
            level > 0 && 'ml-4',
            isActive
              ? 'bg-teal-50 text-teal-800 shadow-[inset_3px_0_0_#0f766e] dark:bg-teal-950/50 dark:text-teal-200'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-50'
          )
        }
        title={collapsed ? item.label : undefined}
      >
        <Icon size={20} className="shrink-0" />
        {!collapsed && <span>{item.label}</span>}
      </NavLink>
    </li>
  );
}

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const navItems = useCaseNavItems();
  const tenantType = useAuthStore((s) => s.tenant?.tenant_type);
  const labels = getAudienceLabels(tenantType);

  return (
    <aside
      className={cn(
        'hidden flex-col border-r border-slate-200 bg-white/95 transition-all duration-300 dark:border-slate-800 dark:bg-slate-950/95 lg:flex',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      <div className="flex h-16 items-center justify-between border-b border-slate-200 px-4 dark:border-slate-800">
        {!collapsed && (
          <div>
            <span className="block text-base font-semibold text-slate-950 dark:text-slate-50">
              法律大模型
            </span>
            <span className="block text-xs text-slate-500 dark:text-slate-400">
              {labels.workspaceSubtitle}
            </span>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="rounded-md p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
          aria-label={collapsed ? '展开侧边栏' : '收起侧边栏'}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto py-4">
        <ul className="space-y-1 px-2">
          {navItems.map((item) => (
            <NavItemComponent key={item.key} item={item} collapsed={collapsed} />
          ))}
        </ul>
      </nav>
    </aside>
  );
}
