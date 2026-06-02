import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { ApiError } from '@/api/client';
import { BrandMark, ProductPreview } from '@/components/marketing/brand-mark';
import { ClientDownloadLink } from '@/components/marketing/client-download-link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { audienceFromSlug, audiencePublicCopy } from '@/lib/public-site-copy';
import { useAuthStore } from '@/stores/auth.store';

export default function LoginPage() {
  const { audienceSlug } = useParams();
  const audience = audienceFromSlug(audienceSlug) || 'law_firm';
  const copy = audiencePublicCopy[audience];
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');

    if (!username.trim()) {
      setError('请输入手机号、用户名或邮箱');
      return;
    }
    if (!password) {
      setError('请输入密码');
      return;
    }

    setIsLoading(true);
    try {
      await login(username.trim(), password);
      navigate('/dashboard');
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          setError('用户名或密码错误');
        } else if (err.status === 403) {
          setError('账号已被停用，请联系管理员');
        } else {
          setError(err.message || '登录失败，请重试');
        }
      } else {
        setError('网络错误，请检查连接后重试');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="grid min-h-[100dvh] bg-[#F8FAFC] text-[#162033] lg:grid-cols-[1.05fr_0.95fr]">
      <section className="hidden border-r border-slate-200 bg-white px-10 py-8 lg:flex lg:flex-col">
        <BrandMark />
        <div className="my-auto max-w-xl">
          <span className={`inline-flex rounded-full border px-4 py-2 text-sm font-medium ${copy.accentClass}`}>
            {copy.eyebrow}
          </span>
          <h1 className="mt-6 text-4xl font-semibold leading-tight tracking-normal">{copy.loginTitle}</h1>
          <p className="mt-4 text-lg leading-8 text-slate-600">{copy.subhead}</p>
          <div className="mt-8">
            <ProductPreview title={copy.previewTitle} items={copy.previewItems} />
          </div>
        </div>
      </section>

      <section className="flex items-center justify-center px-4 py-8 sm:px-6">
        <div className="w-full max-w-md">
          <div className="mb-8 flex items-center justify-between lg:hidden">
            <BrandMark />
          </div>
          <Link to={`/${copy.slug}`} className="mb-6 inline-flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-[#0F766E]">
            <ArrowLeft className="h-4 w-4" />
            返回{copy.label}入口
          </Link>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-6">
              <h2 className="text-2xl font-semibold">{copy.loginTitle}</h2>
              <p className="mt-2 text-sm text-slate-500">请输入账号信息，进入你的工作空间。</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {error && <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">{error}</div>}
              <div className="space-y-2">
                <Label htmlFor="username">手机号 / 用户名 / 邮箱</Label>
                <Input
                  id="username"
                  name="username"
                  type="text"
                  placeholder="请输入手机号、用户名或邮箱"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  autoComplete="username"
                  disabled={isLoading}
                  autoFocus
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">密码</Label>
                <div className="relative">
                  <Input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="请输入密码"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    autoComplete="current-password"
                    disabled={isLoading}
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((value) => !value)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    tabIndex={-1}
                    aria-label={showPassword ? '隐藏密码' : '显示密码'}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
              <Button type="submit" className="w-full bg-[#0F766E] hover:bg-[#115E59]" disabled={isLoading}>
                {isLoading ? '登录中...' : '登录'}
                {!isLoading && <ArrowRight size={16} className="ml-2" />}
              </Button>
            </form>

            <div className="mt-6 space-y-3 text-center text-sm">
              <p className="text-slate-500">
                还没有账号？{' '}
                <Link to={`/register/${copy.slug}`} className="font-medium text-[#0F766E] hover:text-[#115E59]">
                  {copy.registerTitle}
                </Link>
              </p>
              <Link to="/forgot-password" className="inline-flex font-medium text-slate-500 hover:text-[#0F766E]">
                忘记密码？
              </Link>
            </div>
          </div>

          <ClientDownloadLink variant="panel" className="mt-5" />
        </div>
      </section>
    </main>
  );
}
