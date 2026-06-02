import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Eye, EyeOff, MonitorDown } from 'lucide-react';
import { ApiError } from '@/api/client';
import { authApi } from '@/api/auth.api';
import { BrandMark, ProductPreview } from '@/components/marketing/brand-mark';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  audienceFromSlug,
  audiencePublicCopy,
  audienceSlugs,
  type PublicAudience,
} from '@/lib/public-site-copy';
import { useAuthStore } from '@/stores/auth.store';

export default function RegisterPage() {
  const { audienceSlug } = useParams();
  const initialAudience = audienceFromSlug(audienceSlug) || 'law_firm';
  const [audience, setAudience] = useState<PublicAudience>(initialAudience);
  const copy = audiencePublicCopy[audience];
  const [phone, setPhone] = useState('');
  const [smsCode, setSmsCode] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [tenantName, setTenantName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSendingCode, setIsSendingCode] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [error, setError] = useState('');
  const [smsHint, setSmsHint] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const register = useAuthStore((s) => s.register);

  useEffect(() => {
    const nextAudience = audienceFromSlug(audienceSlug);
    if (nextAudience) setAudience(nextAudience);
  }, [audienceSlug]);

  useEffect(() => {
    if (countdown <= 0) return;
    const timer = window.setTimeout(() => setCountdown((value) => value - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [countdown]);

  const normalizePhone = () => phone.replace(/[\s\-()]/g, '').replace(/^\+86/, '').replace(/^86(?=1\d{10}$)/, '');

  const validateForm = () => {
    const normalizedPhone = normalizePhone();
    if (!/^1[3-9]\d{9}$/.test(normalizedPhone)) return '请输入有效的手机号';
    if (!/^\d{4,8}$/.test(smsCode.trim())) return '请输入短信验证码';
    if (username.trim() && !/^[a-zA-Z0-9_]{3,100}$/.test(username.trim())) {
      return '用户名只能包含 3-100 位字母、数字和下划线';
    }
    if (email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) return '请输入有效的邮箱地址';
    if (!password || password.length < 6) return '密码至少需要 6 个字符';
    if (password !== confirmPassword) return '两次输入的密码不一致';
    if (!tenantName.trim()) return audience === 'personal' ? '请设置个人空间名称' : '请输入组织名称';
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
      setError(err instanceof ApiError ? err.message || '验证码发送失败' : '网络错误，请检查连接后重试');
    } finally {
      setIsSendingCode(false);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
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
        tenant_type: audience,
      });
      navigate('/dashboard');
    } catch (err) {
      if (err instanceof ApiError) {
        const detail =
          err.details && typeof err.details === 'object' && 'detail' in err.details
            ? String((err.details as { detail?: unknown }).detail || '')
            : '';
        setError(detail || err.message || '注册失败，请重试');
      } else {
        setError('网络错误，请检查连接后重试');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="grid min-h-[100dvh] bg-[#F8FAFC] text-[#162033] lg:grid-cols-[1fr_1fr]">
      <section className="hidden border-r border-slate-200 bg-white px-10 py-8 lg:flex lg:flex-col">
        <BrandMark />
        <div className="my-auto max-w-xl">
          <span className={`inline-flex rounded-full border px-4 py-2 text-sm font-medium ${copy.accentClass}`}>
            {copy.eyebrow}
          </span>
          <h1 className="mt-6 text-4xl font-semibold leading-tight tracking-normal">{copy.registerTitle}</h1>
          <p className="mt-4 text-lg leading-8 text-slate-600">{copy.subhead}</p>
          <div className="mt-8">
            <ProductPreview title={copy.previewTitle} items={copy.previewItems} />
          </div>
        </div>
      </section>

      <section className="flex items-center justify-center px-4 py-8 sm:px-6">
        <div className="w-full max-w-lg">
          <div className="mb-8 lg:hidden">
            <BrandMark />
          </div>
          <Link to={`/${copy.slug}`} className="mb-6 inline-flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-[#0F766E]">
            <ArrowLeft className="h-4 w-4" />
            返回{copy.label}入口
          </Link>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-6">
              <h2 className="text-2xl font-semibold">{copy.registerTitle}</h2>
              <p className="mt-2 text-sm text-slate-500">手机号验证后创建空间，后续可继续邀请团队成员。</p>
            </div>

            <div className="mb-5 grid grid-cols-3 gap-2">
              {Object.values(audiencePublicCopy).map((item) => {
                const Icon = item.icon;
                const active = audience === item.type;
                return (
                  <button
                    key={item.type}
                    type="button"
                    onClick={() => setAudience(item.type)}
                    className={`rounded-xl border p-3 text-left text-sm transition ${
                      active ? 'border-teal-300 bg-teal-50 text-teal-800' : 'border-slate-200 text-slate-600 hover:border-slate-300'
                    }`}
                  >
                    <Icon className="mb-2 h-4 w-4" />
                    {item.label}
                  </button>
                );
              })}
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {error && <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">{error}</div>}
              {smsHint && <div className="rounded-lg bg-teal-50 p-3 text-sm text-teal-700">{smsHint}</div>}

              <div className="space-y-2">
                <Label htmlFor="phone">手机号</Label>
                <Input id="phone" type="tel" placeholder="请输入手机号" value={phone} onChange={(event) => setPhone(event.target.value)} disabled={isLoading} autoComplete="tel" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="smsCode">短信验证码</Label>
                <div className="flex gap-2">
                  <Input id="smsCode" type="text" inputMode="numeric" placeholder="请输入验证码" value={smsCode} onChange={(event) => setSmsCode(event.target.value)} disabled={isLoading} autoComplete="one-time-code" />
                  <Button type="button" variant="outline" onClick={handleSendCode} disabled={isSendingCode || countdown > 0 || isLoading} className="w-32 shrink-0">
                    {countdown > 0 ? `${countdown}s` : isSendingCode ? '发送中' : '获取验证码'}
                  </Button>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="username">用户名（选填）</Label>
                  <Input id="username" type="text" placeholder="字母/数字/下划线" value={username} onChange={(event) => setUsername(event.target.value)} disabled={isLoading} autoComplete="username" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="fullName">姓名（选填）</Label>
                  <Input id="fullName" type="text" placeholder="你的真实姓名" value={fullName} onChange={(event) => setFullName(event.target.value)} disabled={isLoading} />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">邮箱（选填）</Label>
                <Input id="email" type="email" placeholder="your@email.com" value={email} onChange={(event) => setEmail(event.target.value)} disabled={isLoading} autoComplete="email" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="tenantName">{copy.workspaceLabel}</Label>
                <Input id="tenantName" type="text" placeholder={copy.workspacePlaceholder} value={tenantName} onChange={(event) => setTenantName(event.target.value)} disabled={isLoading} />
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="password">密码</Label>
                  <div className="relative">
                    <Input id="password" type={showPassword ? 'text' : 'password'} placeholder="至少 6 个字符" value={password} onChange={(event) => setPassword(event.target.value)} disabled={isLoading} autoComplete="new-password" className="pr-10" />
                    <button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600" tabIndex={-1} aria-label={showPassword ? '隐藏密码' : '显示密码'}>
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">确认密码</Label>
                  <Input id="confirmPassword" type="password" placeholder="再次输入密码" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} disabled={isLoading} autoComplete="new-password" />
                </div>
              </div>
              <Button type="submit" className="w-full bg-[#0F766E] hover:bg-[#115E59]" disabled={isLoading}>
                {isLoading ? '创建账号中...' : copy.registerTitle}
                {!isLoading && <ArrowRight size={16} className="ml-2" />}
              </Button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-500">
              已有账号？{' '}
              <Link to={`/login/${audienceSlugs[audience]}`} className="font-medium text-[#0F766E] hover:text-[#115E59]">
                返回登录
              </Link>
            </p>
          </div>

          <a href="/downloads/LegalAI-Windows-Client-v2.1.0.zip" className="mt-5 flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-600 hover:border-teal-300 hover:text-[#0F766E]">
            <MonitorDown className="h-4 w-4" />
            下载 Windows 客户端
          </a>
        </div>
      </section>
    </main>
  );
}
