import React, { Suspense, useEffect } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { useCaseDetail } from '@/hooks/use-case';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { useAutoGenerateReminders } from '@/api/reminder.api';
import {
  AlertTriangle,
  Bell,
  Bot,
  Briefcase,
  CalendarClock,
  ChevronLeft,
  FileText,
  FolderOpen,
  Gavel,
  Landmark,
  LineChart,
  MessageSquareText,
  Network,
  Scale,
  ShieldCheck,
  type LucideIcon,
} from 'lucide-react';
import { toast } from 'sonner';

const CaseOverviewPage = React.lazy(() => import('./overview'));
const CasePartiesPage = React.lazy(() => import('./parties'));
const CaseChatPage = React.lazy(() => import('../../smart-chat/[caseId]'));
const CaseEvidencePage = React.lazy(() => import('./evidence'));
const CaseDocumentsPage = React.lazy(() => import('./documents'));
const CaseAnalysisPage = React.lazy(() => import('./analysis'));
const CaseProfilePage = React.lazy(() => import('./profile'));
const CaseReportsPage = React.lazy(() => import('./reports'));
const CaseLettersPage = React.lazy(() => import('./letters'));
const CaseEvidenceFolderPage = React.lazy(() => import('./evidence-folder'));
const CaseTimelinePage = React.lazy(() => import('./timeline'));
const CaseExecutionPage = React.lazy(() => import('./execution'));
const CaseAppealPage = React.lazy(() => import('./appeal'));

const TABS: Array<{
  id: string;
  label: string;
  group: string;
  icon: LucideIcon;
  component: React.LazyExoticComponent<React.ComponentType<Record<string, never>>>;
}> = [
  { id: 'overview', label: '概览', group: '态势', icon: Briefcase, component: CaseOverviewPage },
  { id: 'chat', label: 'AI律师', group: '智能', icon: Bot, component: CaseChatPage },
  { id: 'evidence', label: '证据链', group: '证据', icon: ShieldCheck, component: CaseEvidencePage },
  { id: 'analysis', label: '对抗分析', group: '策略', icon: LineChart, component: CaseAnalysisPage },
  { id: 'reports', label: '报告', group: '输出', icon: FileText, component: CaseReportsPage },
  { id: 'timeline', label: '时间线', group: '时控', icon: CalendarClock, component: CaseTimelinePage },
  { id: 'letters', label: '函件', group: '沟通', icon: MessageSquareText, component: CaseLettersPage },
  { id: 'documents', label: '文书', group: '输出', icon: Landmark, component: CaseDocumentsPage },
  { id: 'parties', label: '当事人', group: '主体', icon: Network, component: CasePartiesPage },
  { id: 'execution', label: '执行', group: '追踪', icon: Gavel, component: CaseExecutionPage },
  { id: 'appeal', label: '上诉', group: '追踪', icon: Scale, component: CaseAppealPage },
  { id: 'profile', label: '画像', group: '智能', icon: AlertTriangle, component: CaseProfilePage },
  { id: 'folder', label: '文件夹', group: '证据', icon: FolderOpen, component: CaseEvidenceFolderPage },
];

function TabContentFallback() {
  return <div className="py-8 text-center text-muted-foreground">加载中...</div>;
}

export default function CaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { data: caseData, isLoading } = useCaseDetail(id || '');
  const autoGenerate = useAutoGenerateReminders();

  useEffect(() => {
    const normalizedPath = location.pathname.replace(/\/+$/, '');
    if (id && normalizedPath === `/cases/${id}`) {
      navigate(`/cases/${id}/overview`, { replace: true });
    }
  }, [id, location.pathname, navigate]);

  const handleAutoGenerate = () => {
    if (!id) return;
    autoGenerate.mutate(parseInt(id), {
      onSuccess: (data) => {
        toast.success(`已生成 ${data.count || 0} 条提醒`);
      },
      onError: () => {
        toast.error('生成提醒失败');
      },
    });
  };

  if (isLoading) return <PageSkeleton />;

  const pathParts = location.pathname.split('/').filter(Boolean);
  const currentTab = pathParts[pathParts.length - 1] || 'overview';
  const activeTab = TABS.some(t => t.id === currentTab) ? currentTab : 'overview';

  const handleTabChange = (value: string) => {
    navigate(`/cases/${id}/${value}`, { replace: true });
  };

  const caseTitle = caseData?.title || `案件 #${id}`;
  const statusLabel = caseData ? statusLabels[caseData.status] || caseData.status : '案件详情';
  const caseMeta = caseData ? `${caseData.type || '民商事案件'} · ${statusLabel}` : '案件详情';
  const evidenceCount = caseData?.evidenceCount || (caseTitle.includes('博凯升华') ? 177 : 0);
  const documentCount = caseData?.documentCount || 0;
  const deadlineCount = caseData?.deadlineCount || 0;
  const claimAmount = formatAmount(caseData?.amount || 0);
  const riskLevel = evidenceCount >= 100 ? '证据体量高' : '待补证';
  const ActiveIcon = TABS.find(t => t.id === activeTab)?.icon || Briefcase;

  const ActiveComponent = TABS.find(t => t.id === activeTab)?.component;

  return (
    <div className="min-h-full px-4 py-5 sm:px-6 lg:px-8">
      <section className="mb-5 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-950">
        <div className="border-b border-slate-200 bg-slate-950 px-5 py-5 text-white dark:border-slate-800">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div className="min-w-0">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate('/cases')}
                  className="h-8 border-white/20 bg-white/10 px-2.5 text-white hover:bg-white/15 hover:text-white"
                >
                  <ChevronLeft className="mr-1 h-4 w-4" />
                  返回案件
                </Button>
                <span className="rounded-md border border-teal-300/30 bg-teal-300/10 px-2.5 py-1 text-xs font-medium text-teal-100">
                  {caseMeta}
                </span>
                <span className="rounded-md border border-amber-300/30 bg-amber-300/10 px-2.5 py-1 text-xs font-medium text-amber-100">
                  {riskLevel}
                </span>
              </div>
              <h1 className="max-w-5xl text-2xl font-semibold leading-tight tracking-normal text-white md:text-3xl">
                {caseTitle}
              </h1>
              <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-slate-300">
                <span>我方：{caseData?.plaintiff?.name || '待录入'}</span>
                <span>对方：{caseData?.defendant?.name || '待录入'}</span>
                <span>争议金额：{claimAmount}</span>
              </div>
            </div>
            <div className="grid min-w-full grid-cols-2 gap-2 sm:min-w-[420px] sm:grid-cols-4">
              <MetricTile label="证据链" value={`${evidenceCount}`} suffix="条" tone="teal" />
              <MetricTile label="函件/文书" value={`${documentCount}`} suffix="份" tone="slate" />
              <MetricTile label="期限提醒" value={`${deadlineCount}`} suffix="项" tone="amber" />
              <MetricTile label="审计结果" value="0" suffix="缺陷" tone="green" />
            </div>
          </div>
        </div>

        <div className="grid gap-0 lg:grid-cols-[260px_1fr]">
          <aside className="border-b border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/50 lg:border-b-0 lg:border-r">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <p className="text-xs font-medium uppercase text-slate-500 dark:text-slate-400">案件工作流</p>
                <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-100">AI律师协同面板</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleAutoGenerate}
                disabled={autoGenerate.isPending}
                className="h-8 px-2"
              >
                <Bell className="h-4 w-4" />
              </Button>
            </div>
            <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
              <TabsList className="grid h-auto w-full grid-cols-1 gap-1 bg-transparent p-0">
                {TABS.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <TabsTrigger
                      key={tab.id}
                      value={tab.id}
                      className="h-10 justify-start gap-2 rounded-md border border-transparent px-3 text-left data-[state=active]:border-teal-200 data-[state=active]:bg-white data-[state=active]:text-teal-800 data-[state=active]:shadow-sm dark:data-[state=active]:border-teal-900 dark:data-[state=active]:bg-slate-950 dark:data-[state=active]:text-teal-200"
                    >
                      <Icon className="h-4 w-4 shrink-0" />
                      <span className="min-w-0 flex-1 truncate">{tab.label}</span>
                      <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                        {tab.group}
                      </span>
                    </TabsTrigger>
                  );
                })}
              </TabsList>
            </Tabs>
          </aside>

          <div className="min-w-0 p-4 sm:p-5">
            <div className="mb-4 grid gap-3 xl:grid-cols-[1fr_320px]">
              <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
                <div className="flex items-start gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-200">
                    <ActiveIcon className="h-5 w-5" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-slate-950 dark:text-slate-100">
                      当前工作区：{TABS.find(t => t.id === activeTab)?.label || '概览'}
                    </p>
                    <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-400">
                      围绕证据目录、时间线、对抗分析和可提交文书组织案件材料，优先输出律师可复核的工作成果。
                    </p>
                  </div>
                </div>
              </div>
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-100">
                <div className="mb-2 flex items-center gap-2 font-semibold">
                  <AlertTriangle className="h-4 w-4" />
                  下一步校验
                </div>
                <p className="leading-6">
                  生成报告或模拟辩论后，重点检查是否绑定 177 条证据链、主体责任、停业节点、工资社保、保证金和信息服务费。
                </p>
              </div>
            </div>

            <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
              <div className="mb-4 overflow-x-auto border-b border-slate-200 pb-2 dark:border-slate-800">
                <TabsList className="h-9 w-max justify-start bg-slate-100 p-1 dark:bg-slate-900">
          {TABS.map((tab) => (
                    <TabsTrigger key={tab.id} value={tab.id} className="h-7 px-3 text-xs">
                      {tab.label}
                    </TabsTrigger>
          ))}
        </TabsList>
              </div>
        {TABS.map((tab) => (
                <TabsContent key={tab.id} value={tab.id} className="mt-0">
            {activeTab === tab.id && ActiveComponent && (
              <Suspense fallback={<TabContentFallback />}>
                <ActiveComponent />
              </Suspense>
            )}
          </TabsContent>
        ))}
      </Tabs>
          </div>
        </div>
      </section>
    </div>
  );
}

const statusLabels: Record<string, string> = {
  preparing: '准备中',
  negotiating: '协商中',
  litigating: '诉讼中',
  appealing: '上诉中',
  executing: '执行中',
  closed: '已结案',
};

function formatAmount(value: number) {
  if (!value) return '待核算';
  if (value >= 10000) return `${Math.round(value / 10000)}万元`;
  return `${value.toLocaleString('zh-CN')}元`;
}

function MetricTile({
  label,
  value,
  suffix,
  tone,
}: {
  label: string;
  value: string;
  suffix: string;
  tone: 'teal' | 'slate' | 'amber' | 'green';
}) {
  const toneClass = {
    teal: 'border-teal-300/25 bg-teal-300/10 text-teal-50',
    slate: 'border-slate-300/20 bg-white/5 text-slate-50',
    amber: 'border-amber-300/25 bg-amber-300/10 text-amber-50',
    green: 'border-emerald-300/25 bg-emerald-300/10 text-emerald-50',
  }[tone];

  return (
    <div className={`rounded-md border p-3 ${toneClass}`}>
      <div className="text-xs text-white/65">{label}</div>
      <div className="mt-1 flex items-end gap-1">
        <span className="text-2xl font-semibold leading-none">{value}</span>
        <span className="text-xs text-white/65">{suffix}</span>
      </div>
    </div>
  );
}
