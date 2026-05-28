import { useEffect, useState } from 'react';
import {
  fetchPlatformStats,
  fetchAllTenants,
  approveTenant,
  rejectTenant,
  updateBilling,
  toggleTenant,
  type PlatformStats,
  type TenantDetail,
} from '@/api/platform.api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { EmptyState } from '@/components/common/empty-state';
import {
  Building2,
  Users,
  Clock,
  CheckCircle,
  XCircle,
  DollarSign,
  Settings,
  BarChart3,
  Shield,
  Zap,
} from 'lucide-react';

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400',
  approved: 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400',
  rejected: 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400',
};

const STATUS_LABELS: Record<string, string> = {
  pending: '待审批',
  approved: '已批准',
  rejected: '已拒绝',
};

function StatsRow({ stats }: { stats: PlatformStats }) {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
      <Card>
        <CardContent className="flex items-center gap-3 py-4">
          <Building2 className="h-8 w-8 text-blue-500" />
          <div><p className="text-2xl font-bold">{stats.total_tenants}</p><p className="text-xs text-gray-500">总租户</p></div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="flex items-center gap-3 py-4">
          <Clock className="h-8 w-8 text-yellow-500" />
          <div><p className="text-2xl font-bold">{stats.pending_approvals}</p><p className="text-xs text-gray-500">待审批</p></div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="flex items-center gap-3 py-4">
          <CheckCircle className="h-8 w-8 text-green-500" />
          <div><p className="text-2xl font-bold">{stats.active_tenants}</p><p className="text-xs text-gray-500">活跃中</p></div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="flex items-center gap-3 py-4">
          <Users className="h-8 w-8 text-purple-500" />
          <div><p className="text-2xl font-bold">{stats.total_users}</p><p className="text-xs text-gray-500">总用户</p></div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="flex items-center gap-3 py-4">
          <DollarSign className="h-8 w-8 text-emerald-500" />
          <div><p className="text-2xl font-bold">{stats.total_revenue_monthly}</p><p className="text-xs text-gray-500">月营收（元）</p></div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="flex items-center gap-3 py-4">
          <Zap className="h-8 w-8 text-orange-500" />
          <div><p className="text-2xl font-bold">{stats.ai_calls_today}</p><p className="text-xs text-gray-500">今日AI调用</p></div>
        </CardContent>
      </Card>
    </div>
  );
}

function TenantRow({ t, onRefresh }: { t: TenantDetail; onRefresh: () => void }) {
  const [showApprove, setShowApprove] = useState(false);
  const [plan, setPlan] = useState(t.plan);
  const [amount, setAmount] = useState(t.billing_amount || 0);
  const [maxUsers, setMaxUsers] = useState(t.max_users);
  const [maxCases, setMaxCases] = useState(t.max_cases);
  const [aiQuota, setAiQuota] = useState(t.ai_daily_quota);
  const [rejectReason, setRejectReason] = useState('');
  const [showReject, setShowReject] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleApprove = async () => {
    setLoading(true);
    await approveTenant({
      tenant_id: t.id, plan, billing_cycle: 'monthly', billing_amount: amount,
      max_users: maxUsers, max_cases: maxCases, ai_daily_quota: aiQuota,
    });
    setShowApprove(false); setLoading(false); onRefresh();
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) return;
    await rejectTenant({ tenant_id: t.id, reason: rejectReason });
    setShowReject(false); onRefresh();
  };

  const handleRecordPayment = async () => {
    const amt = prompt('缴费金额（元）:', String(amount));
    if (!amt) return;
    setLoading(true);
    try {
      const { recordPayment } = await import('@/api/platform.api');
      await recordPayment({ tenant_id: t.id, amount: Number(amt), billing_cycle: 'monthly' });
      onRefresh();
    } catch { alert('操作失败'); }
    finally { setLoading(false); }
  };

  return (
    <div className="rounded-lg border p-4 dark:border-gray-700 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="font-semibold">{t.name}</span>
          <Badge className={STATUS_COLORS[t.approval_status] || ''}>
            {STATUS_LABELS[t.approval_status] || t.approval_status}
          </Badge>
          <Badge variant="outline">{t.tenant_type === 'law_firm' ? '律所' : '企业'}</Badge>
          {!t.is_active && <Badge variant="destructive">已停用</Badge>}
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>{t.user_count} 用户</span>
          <span>|</span>
          <span>套餐: {t.plan}</span>
          <span>|</span>
          <span>{t.billing_amount}元/{t.billing_cycle === 'monthly' ? '月' : '年'}</span>
        </div>
      </div>

      <div className="text-xs text-gray-400">
        注册时间: {t.created_at?.slice(0, 10) || '-'} |
        AI配额: {t.ai_monthly_usage}/{t.ai_daily_quota}/天 |
        来源: {t.registered_from || '-'}
      </div>

      <div className="flex gap-2">
        {t.approval_status === 'pending' && (
          <>
            <Button size="sm" onClick={() => setShowApprove(true)}>
              <CheckCircle className="mr-1 h-3 w-3" /> 批准
            </Button>
            <Button size="sm" variant="destructive" onClick={() => setShowReject(true)}>
              <XCircle className="mr-1 h-3 w-3" /> 拒绝
            </Button>
          </>
        )}
        {t.approval_status === 'approved' && (
          <div className="flex gap-2 flex-wrap">
            <Button size="sm" variant="outline" onClick={handleRecordPayment} disabled={loading}>
              <DollarSign className="mr-1 h-3 w-3" /> 缴费
            </Button>
            <Button size="sm" variant="outline" onClick={() => setShowApprove(true)}>
              <Settings className="mr-1 h-3 w-3" /> 套餐
            </Button>
            <Button size="sm" variant="outline" onClick={() => toggleTenant(t.id).then(onRefresh)}>
              {t.is_active ? '停用' : '启用'}
            </Button>
          </div>
        )}
      </div>

      {showApprove && (
        <div className="rounded border p-3 space-y-2 dark:border-gray-600">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <label className="text-xs text-gray-500">套餐</label>
              <select className="w-full rounded border px-2 py-1 dark:bg-gray-800" value={plan} onChange={(e) => setPlan(e.target.value)}>
                <option value="free">免费版</option>
                <option value="trial">试用版</option>
                <option value="pro">专业版</option>
                <option value="enterprise">企业版</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500">月费(元)</label>
              <input type="number" className="w-full rounded border px-2 py-1 dark:bg-gray-800" value={amount} onChange={(e) => setAmount(Number(e.target.value))} />
            </div>
            <div>
              <label className="text-xs text-gray-500">子账户数</label>
              <input type="number" className="w-full rounded border px-2 py-1 dark:bg-gray-800" value={maxUsers} onChange={(e) => setMaxUsers(Number(e.target.value))} />
            </div>
            <div>
              <label className="text-xs text-gray-500">最大案件</label>
              <input type="number" className="w-full rounded border px-2 py-1 dark:bg-gray-800" value={maxCases} onChange={(e) => setMaxCases(Number(e.target.value))} />
            </div>
            <div>
              <label className="text-xs text-gray-500">日AI配额</label>
              <input type="number" className="w-full rounded border px-2 py-1 dark:bg-gray-800" value={aiQuota} onChange={(e) => setAiQuota(Number(e.target.value))} />
            </div>
          </div>
          <div className="flex gap-2">
            <Button size="sm" onClick={handleApprove} disabled={loading}>保存套餐</Button>
            <Button size="sm" variant="outline" onClick={() => setShowApprove(false)}>取消</Button>
          </div>
        </div>
      )}

      {showReject && (
        <div className="rounded border p-3 space-y-2 dark:border-gray-600">
          <input className="w-full rounded border px-3 py-2 text-sm dark:bg-gray-800" placeholder="拒绝理由" value={rejectReason} onChange={(e) => setRejectReason(e.target.value)} />
          <div className="flex gap-2">
            <Button size="sm" variant="destructive" onClick={handleReject}>确认拒绝</Button>
            <Button size="sm" variant="outline" onClick={() => setShowReject(false)}>取消</Button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function PlatformAdminPage() {
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [tenants, setTenants] = useState<TenantDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const [s, t] = await Promise.all([
        fetchPlatformStats(),
        fetchAllTenants(filter || undefined),
      ]);
      setStats(s);
      setTenants(t);
    } catch {
      // handled by axios interceptor
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [filter]);

  if (loading) return <PageSkeleton />;
  if (!stats) return <EmptyState title="无权限" description="仅平台超级管理员可访问此页面" />;

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
      <header className="flex items-center gap-3">
        <Shield className="h-7 w-7 text-teal-600" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">平台管理中心</h1>
          <p className="text-sm text-gray-500">管理所有租户、审批注册、计费配置</p>
        </div>
      </header>

      <StatsRow stats={stats} />

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" /> 租户列表
          </CardTitle>
          <select
            className="rounded border px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="">全部</option>
            <option value="pending">待审批</option>
            <option value="approved">已批准</option>
            <option value="rejected">已拒绝</option>
          </select>
        </CardHeader>
        <CardContent className="space-y-3">
          {tenants.length === 0 ? (
            <p className="text-center text-sm text-gray-500 py-8">暂无数据</p>
          ) : (
            tenants.map((t) => <TenantRow key={t.id} t={t} onRefresh={load} />)
          )}
        </CardContent>
      </Card>
    </div>
  );
}
