import { useEffect, useState } from 'react';
import { fetchTenantProfile, updateTenantProfile, fetchTeamMembers, inviteMember, changeMemberRole, removeMember, fetchUsageStats, fetchStorageMode, setStorageMode, type TenantProfile, type TeamMember, type UsageStats, type StorageStatus } from '@/api/tenant.api';
import { useAuthStore } from '@/stores/auth.store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { EmptyState } from '@/components/common/empty-state';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { Users, Settings, BarChart3, Mail, Trash2, Shield, HardDrive } from 'lucide-react';

const ROLE_LABELS: Record<string, string> = {
  admin: '管理员',
  lawyer: '律师',
  assistant: '助理',
  client: '客户',
  viewer: '查看者',
};

const ROLE_COLORS: Record<string, string> = {
  admin: 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400',
  lawyer: 'bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400',
  assistant: 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400',
  client: 'bg-gray-100 text-gray-700 dark:bg-gray-900/20 dark:text-gray-400',
  viewer: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400',
};

function TenantProfileCard({ profile, onRefresh }: { profile: TenantProfile; onRefresh: () => void }) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(profile.name);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateTenantProfile({ name });
      onRefresh();
      setEditing(false);
    } catch {
      alert('保存失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2">
        <Settings className="h-5 w-5 text-gray-500" />
        <CardTitle>租户信息</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {editing ? (
          <div className="flex gap-2">
            <input
              className="flex-1 rounded border px-3 py-1 text-sm dark:bg-gray-800 dark:border-gray-700"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <Button size="sm" onClick={handleSave} disabled={saving}>保存</Button>
            <Button size="sm" variant="outline" onClick={() => { setName(profile.name); setEditing(false); }}>取消</Button>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <div>
              <p className="font-semibold text-lg">{profile.name}</p>
              <p className="text-sm text-gray-500">
                {profile.tenant_type === 'law_firm' ? '律所' : profile.tenant_type === 'enterprise' ? '企业' : '个人'} · {profile.slug}
              </p>
            </div>
            <Button size="sm" variant="outline" onClick={() => setEditing(true)}>编辑</Button>
          </div>
        )}
        <div className="flex gap-2 text-sm">
          <Badge variant="outline">{profile.plan}</Badge>
          <Badge variant={profile.subscription_status === 'active' ? 'default' : 'destructive'}>
            {profile.subscription_status === 'active' ? '已激活' : profile.subscription_status}
          </Badge>
          <Badge variant={profile.is_verified ? 'default' : 'secondary'}>
            {profile.is_verified ? '已认证' : '未认证'}
          </Badge>
        </div>
        <div className="grid grid-cols-3 gap-2 text-sm text-gray-500">
          <div>最大用户: {profile.max_users}</div>
          <div>最大案件: {profile.max_cases}</div>
          <div>日AI配额: {profile.ai_daily_quota}</div>
        </div>
      </CardContent>
    </Card>
  );
}

function UsageCard({ stats }: { stats: UsageStats }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2">
        <BarChart3 className="h-5 w-5 text-gray-500" />
        <CardTitle>使用统计</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-2xl font-bold">{stats.total_users}</p>
            <p className="text-xs text-gray-500">总用户（活跃: {stats.active_users}）</p>
          </div>
          <div>
            <p className="text-2xl font-bold">{stats.total_cases}</p>
            <p className="text-xs text-gray-500">案件总数</p>
          </div>
          <div>
            <p className="text-2xl font-bold">{stats.ai_calls_today}<span className="text-sm text-gray-400">/{stats.ai_daily_quota}</span></p>
            <p className="text-xs text-gray-500">今日AI调用</p>
          </div>
          <div>
            <p className="text-2xl font-bold">{stats.ai_calls_this_month}</p>
            <p className="text-xs text-gray-500">本月AI调用</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function StorageModeCard({ onRefresh }: { onRefresh: () => void }) {
  const [status, setStatus] = useState<StorageStatus | null>(null);
  const [switching, setSwitching] = useState(false);

  useEffect(() => {
    fetchStorageMode().then(setStatus).catch(() => {});
  }, []);

  const handleSwitch = async (mode: string) => {
    setSwitching(true);
    try {
      await setStorageMode(mode);
      setStatus((s) => s ? { ...s, mode } : null);
      onRefresh();
    } catch { alert('切换失败'); }
    finally { setSwitching(false); }
  };

  if (!status) return null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2">
        <HardDrive className="h-5 w-5 text-gray-500" />
        <CardTitle>证据存储模式</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            status.mode === 'local'
              ? 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400'
              : 'bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
          }`}>
            {status.mode === 'local' ? '本地存储' : '云端存储'}
          </span>
          {status.mode === 'cloud' && (
            <span className="text-xs text-gray-500">Bucket: {status.cloud_bucket}</span>
          )}
        </div>
        <p className="text-sm text-gray-500">
          {status.mode === 'local'
            ? '证据存储在服务器本地磁盘，适合单机部署。'
            : '证据存储在云端对象存储（OSS/S3），适合多节点部署和异地容灾。'}
        </p>
        <div className="flex gap-2">
          <Button size="sm" variant={status.mode === 'local' ? 'default' : 'outline'}
            onClick={() => handleSwitch('local')} disabled={switching}>
            本地模式
          </Button>
          <Button size="sm" variant={status.mode === 'cloud' ? 'default' : 'outline'}
            onClick={() => handleSwitch('cloud')}
            disabled={switching || !status.cloud_available}
            title={!status.cloud_available ? '云端存储未配置' : ''}>
            云端模式 {!status.cloud_available && '(未配置)'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function TeamCard({ members, onRefresh }: { members: TeamMember[]; onRefresh: () => void }) {
  const [inviting, setInviting] = useState(false);
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('assistant');
  const [message, setMessage] = useState('');

  const handleInvite = async () => {
    if (!email) return;
    setMessage('');
    try {
      const res = await inviteMember({ email, full_name: fullName || undefined, role });
      setMessage(res.message);
      setEmail('');
      setFullName('');
      setInviting(false);
      onRefresh();
    } catch (e: any) {
      setMessage(e?.response?.data?.detail || '邀请失败');
    }
  };

  const handleRemove = async (userId: string, username: string) => {
    if (!confirm(`确定移除 ${username}？`)) return;
    try {
      await removeMember(userId);
      onRefresh();
    } catch {
      alert('移除失败');
    }
  };

  const handleRoleChange = async (userId: string, newRole: string) => {
    try {
      await changeMemberRole({ user_id: userId, role: newRole });
      onRefresh();
    } catch {
      alert('角色变更失败');
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-gray-500" />
          <CardTitle>团队成员 ({members.length})</CardTitle>
        </div>
        <Button size="sm" onClick={() => setInviting(!inviting)}>
          <Mail className="mr-1 h-4 w-4" />邀请成员
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {inviting && (
          <div className="rounded border p-4 space-y-3 dark:border-gray-700">
            <input className="w-full rounded border px-3 py-2 text-sm dark:bg-gray-800 dark:border-gray-700" placeholder="邮箱地址" value={email} onChange={(e) => setEmail(e.target.value)} />
            <input className="w-full rounded border px-3 py-2 text-sm dark:bg-gray-800 dark:border-gray-700" placeholder="姓名（选填）" value={fullName} onChange={(e) => setFullName(e.target.value)} />
            <select className="w-full rounded border px-3 py-2 text-sm dark:bg-gray-800 dark:border-gray-700" value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="admin">管理员</option>
              <option value="lawyer">律师</option>
              <option value="assistant">助理</option>
              <option value="viewer">查看者</option>
            </select>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleInvite}>发送邀请</Button>
              <Button size="sm" variant="outline" onClick={() => setInviting(false)}>取消</Button>
            </div>
            {message && <p className="text-sm text-gray-500">{message}</p>}
          </div>
        )}
        {members.length === 0 ? (
          <p className="text-sm text-gray-500">暂无团队成员</p>
        ) : (
          <div className="space-y-2">
            {members.map((m) => (
              <div key={m.id} className="flex items-center justify-between rounded border p-3 dark:border-gray-700">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm">{m.full_name || m.username}</span>
                    <Badge className={`text-xs ${ROLE_COLORS[m.role] || ''}`}>{ROLE_LABELS[m.role] || m.role}</Badge>
                    {!m.is_active && <Badge variant="destructive" className="text-xs">已停用</Badge>}
                  </div>
                  <p className="text-xs text-gray-500">{m.email}{m.phone ? ` · ${m.phone}` : ''}</p>
                </div>
                <div className="flex items-center gap-1">
                  <select
                    className="rounded border px-2 py-1 text-xs dark:bg-gray-800 dark:border-gray-700"
                    value={m.role}
                    onChange={(e) => handleRoleChange(m.id, e.target.value)}
                  >
                    {Object.entries(ROLE_LABELS).map(([val, label]) => (
                      <option key={val} value={val}>{label}</option>
                    ))}
                  </select>
                  <Button size="sm" variant="ghost" onClick={() => handleRemove(m.id, m.full_name || m.username)}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function TenantPage() {
  const user = useAuthStore((s) => s.user);
  const [profile, setProfile] = useState<TenantProfile | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(false);
    try {
      const [p, m, s] = await Promise.all([
        fetchTenantProfile(),
        fetchTeamMembers(),
        fetchUsageStats(),
      ]);
      setProfile(p);
      setMembers(m);
      setStats(s);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) return <PageSkeleton />;
  if (error || !profile) {
    return <EmptyState title="无法加载租户信息" description="请检查网络连接后重试" actionLabel="重试" onAction={load} />;
  }

  const isAdmin = user?.role === 'admin';

  return (
    <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          <Shield className="inline mr-2 h-6 w-6" />
          租户管理
        </h1>
        <p className="mt-1 text-sm text-gray-500">管理您的团队、查看使用统计和订阅信息</p>
      </header>

      <TenantProfileCard profile={profile} onRefresh={load} />
      {stats && <UsageCard stats={stats} />}
      <StorageModeCard onRefresh={load} />
      {isAdmin && <TeamCard members={members} onRefresh={load} />}
      {!isAdmin && (
        <Card>
          <CardContent className="py-6 text-center text-sm text-gray-500">
            仅管理员可以管理团队成员。如需帮助，请联系您的租户管理员。
          </CardContent>
        </Card>
      )}
    </div>
  );
}
