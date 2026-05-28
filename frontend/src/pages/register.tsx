import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Scale, Eye, EyeOff, ArrowRight, Building2, Briefcase, ArrowLeft, MonitorDown, Shield, Zap, HardDrive } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { authApi } from '@/api/auth.api';
import { useAuthStore } from '@/stores/auth.store';
import { ApiError } from '@/api/client';
import type { TenantType } from '@/types/auth';

export default function RegisterPage() {
  const [phone, setPhone] = useState('');
  const [smsCode, setSmsCode] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [tenantName, setTenantName] = useState('');
  const [tenantType, setTenantType] = useState<TenantType>('law_firm');
  const [isLoading, setIsLoading] = useState(false);
  const [isSendingCode, setIsSendingCode] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [error, setError] = useState('');
  const [smsHint, setSmsHint] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const register = useAuthStore((s) => s.register);

  useEffect(() => {
    if (countdown <= 0) return;
    const timer = window.setTimeout(() => setCountdown((value) => value - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [countdown]);

  const normalizePhone = () => phone.replace(/[\s\-()]/g, '').replace(/^\+86/, '').replace(/^86(?=1\d{10}$)/, '');

  const validateForm = (): string => {
    const normalizedPhone = normalizePhone();
    if (!/^1[3-9]\d{9}$/.test(normalizedPhone)) {
      return '请输入有效的手机号';
    }
    if (!/^\d{4,8}$/.test(smsCode.trim())) {
      return '请输入短信验证码';
    }
    if (username.trim() && !/^[a-zA-Z0-9_]{3,100}$/.test(username.trim())) {
      return '用户名只能包含3-100位字母、数字和下划线';
    }
    if (email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      return '请输入有效的邮箱地址';
    }
    if (!password || password.length < 6) {
      return '密码至少需要6个字符';
    }
    if (password !== confirmPassword) {
      return '两次输入的密码不一致';
    }
    if (!tenantName.trim()) {
      return '请输入组织名称';
    }
    return '';
  };

  const handleSendCode = async () => {
    const normalizedPhone = normalizePhone();
    setError('');
    setSmsHint('');

    if (!/^1[3-9]\d{9}$/.test(normalizedPhone)) {
      setError('请输入有效的手机号');
      return;
    }

    setIsSendingCode(true);
    try {
      const response = await authApi.sendSmsCode(normalizedPhone, 'register');
      setCountdown(Math.max(1, Math.ceil(response.expires_in > 60 ? 60 : response.expires_in)));
      setSmsHint(response.debug_code ? `验证码已发送，开发验证码：${response.debug_code}` : response.message);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message || '验证码发送失败');
      } else {
        setError('网络错误，请检查网络连接后重试');
      }
    } finally {
      setIsSendingCode(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setError('');
    setIsLoading(true);

    try {
      await register({
        phone: normalizePhone(),
        sms_code: smsCode.trim(),
        username: username.trim() || undefined,
        email: email.trim() || undefined,
        password,
        full_name: fullName.trim() || undefined,
        tenant_name: tenantName.trim(),
        tenant_type: tenantType,
      });
      navigate('/dashboard');
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 400) {
          const detail =
            err.details && typeof err.details === 'object' && 'detail' in err.details
              ? String((err.details as { detail?: unknown }).detail || '')
              : '';
          setError(detail || err.message || '注册失败');
        } else {
          setError(err.message || '注册失败，请重试');
        }
      } else {
        setError('网络错误，请检查网络连接后重试');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4 dark:from-slate-900 dark:to-slate-800">
      <Card className="w-full max-w-lg">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30">
              <Scale className="h-8 w-8 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">创建账号</CardTitle>
          <CardDescription>使用手机号验证后创建组织账号</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600 dark:bg-red-900/30 dark:text-red-400">
                {error}
              </div>
            )}
            {smsHint && (
              <div className="rounded-lg bg-blue-50 p-3 text-sm text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                {smsHint}
              </div>
            )}

            <div className="space-y-2">
              <Label>账户类型</Label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setTenantType('law_firm')}
                  className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 transition-all ${
                    tenantType === 'law_firm'
                      ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300'
                      : 'border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600'
                  }`}
                >
                  <Building2
                    size={24}
                    className={tenantType === 'law_firm' ? 'text-blue-500' : 'text-gray-400'}
                  />
                  <span className="text-sm font-medium">律所</span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">诉讼案件管理、证据分析</span>
                </button>
                <button
                  type="button"
                  onClick={() => setTenantType('enterprise')}
                  className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 transition-all ${
                    tenantType === 'enterprise'
                      ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300'
                      : 'border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600'
                  }`}
                >
                  <Briefcase
                    size={24}
                    className={tenantType === 'enterprise' ? 'text-blue-500' : 'text-gray-400'}
                  />
                  <span className="text-sm font-medium">企业</span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">合同管理、风险监控</span>
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">手机号</Label>
              <Input
                id="phone"
                type="tel"
                placeholder="请输入手机号"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                disabled={isLoading}
                autoComplete="tel"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="smsCode">短信验证码</Label>
              <div className="flex gap-2">
                <Input
                  id="smsCode"
                  type="text"
                  inputMode="numeric"
                  placeholder="请输入验证码"
                  value={smsCode}
                  onChange={(e) => setSmsCode(e.target.value)}
                  disabled={isLoading}
                  autoComplete="one-time-code"
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleSendCode}
                  disabled={isSendingCode || countdown > 0 || isLoading}
                  className="w-32 shrink-0"
                >
                  {countdown > 0 ? `${countdown}s` : isSendingCode ? '发送中' : '获取验证码'}
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="username">用户名（选填）</Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="字母/数字/下划线"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  disabled={isLoading}
                  autoComplete="username"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="fullName">姓名（选填）</Label>
                <Input
                  id="fullName"
                  type="text"
                  placeholder="您的真实姓名"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">邮箱（选填）</Label>
              <Input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                autoComplete="email"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tenantName">{tenantType === 'law_firm' ? '律所名称' : '企业名称'}</Label>
              <Input
                id="tenantName"
                type="text"
                placeholder={tenantType === 'law_firm' ? '例如：甲鼎律师事务所' : '例如：XX科技有限公司'}
                value={tenantName}
                onChange={(e) => setTenantName(e.target.value)}
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">密码</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="至少6个字符"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading}
                  autoComplete="new-password"
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">确认密码</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="再次输入密码"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={isLoading}
                autoComplete="new-password"
              />
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  创建账号中...
                </>
              ) : (
                <>
                  创建账号
                  <ArrowRight size={16} className="ml-2" />
                </>
              )}
            </Button>

            <p className="text-center text-sm text-gray-500 dark:text-gray-400">
              已有账号？{' '}
              <Link
                to="/login"
                className="flex items-center justify-center gap-1 font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
              >
                <ArrowLeft size={14} />
                返回登录
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>

      {/* Windows 客户端下载 */}
      <Card className="border-teal-200 bg-gradient-to-br from-teal-50 to-blue-50 dark:from-teal-950/30 dark:to-blue-950/30 dark:border-teal-900">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <MonitorDown className="h-5 w-5 text-teal-600" />
            Windows 桌面客户端
          </CardTitle>
          <CardDescription>
            下载安装到本地，数据更安全，体验更流畅
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-3 mb-4">
            <div className="flex items-start gap-2 text-sm">
              <Shield className="h-4 w-4 text-teal-500 mt-0.5 shrink-0" />
              <span className="text-gray-600 dark:text-gray-400">证据本地存储<br />不上传不共享</span>
            </div>
            <div className="flex items-start gap-2 text-sm">
              <Zap className="h-4 w-4 text-teal-500 mt-0.5 shrink-0" />
              <span className="text-gray-600 dark:text-gray-400">内嵌本地AI<br />离线也能分析</span>
            </div>
            <div className="flex items-start gap-2 text-sm">
              <HardDrive className="h-4 w-4 text-teal-500 mt-0.5 shrink-0" />
              <span className="text-gray-600 dark:text-gray-400">单机部署<br />无需服务器</span>
            </div>
          </div>
          <div className="flex gap-3 items-center">
            <a
              href="/downloads/legal-ai-client-setup.exe"
              className="inline-flex items-center gap-2 rounded-lg bg-teal-700 px-6 py-3 text-white hover:bg-teal-800 transition-colors font-medium"
            >
              <MonitorDown size={18} />
              下载 Windows 客户端
            </a>
            <span className="text-xs text-gray-400">v2.1.0 · 约 43MB · Win10/11</span>
          </div>
          <p className="mt-2 text-xs text-amber-600 dark:text-amber-400">
            如提示 SmartScreen，请点击"更多信息"→"仍要运行"。软件未购买代码签名证书，非安全问题。
          </p>
          <p className="mt-3 text-xs text-gray-400">
            支持 Windows 10/11。首次安装后，桌面快捷方式一键启动。
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
