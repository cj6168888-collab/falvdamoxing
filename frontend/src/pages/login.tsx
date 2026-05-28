import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Scale, Eye, EyeOff, ArrowRight, MonitorDown, Shield, Zap, HardDrive } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuthStore } from '@/stores/auth.store';
import { ApiError } from '@/api/client';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (!username.trim()) {
        setError('请输入手机号、用户名或邮箱');
        setIsLoading(false);
        return;
      }
      if (!password) {
        setError('请输入密码');
        setIsLoading(false);
        return;
      }

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
        setError('网络错误，请检查网络连接后重试');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4 dark:from-slate-900 dark:to-slate-800">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30">
              <Scale className="h-8 w-8 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">法律大模型辅助系统</CardTitle>
          <CardDescription>请输入手机号、用户名或邮箱登录</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600 dark:bg-red-900/30 dark:text-red-400">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="username">手机号 / 用户名 / 邮箱</Label>
              <Input
                id="username"
                name="username"
                type="text"
                placeholder="请输入手机号、用户名或邮箱"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
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
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  disabled={isLoading}
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
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  登录中...
                </>
              ) : (
                <>
                  登录
                  <ArrowRight size={16} className="ml-2" />
                </>
              )}
            </Button>
            <p className="text-center text-sm text-gray-500 dark:text-gray-400">
              还没有账号？{' '}
              <Link
                to="/register"
                className="font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
              >
                立即注册
              </Link>
            </p>
            <p className="text-center text-sm">
              <Link
                to="/forgot-password"
                className="font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
              >
                忘记密码？
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>

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
          <a
            href="/downloads/legal-ai-client-setup.exe"
            className="inline-flex items-center gap-2 rounded-lg bg-teal-700 px-6 py-3 text-white hover:bg-teal-800 transition-colors font-medium"
          >
            <MonitorDown size={18} />
            下载 Windows 客户端
          </a>
          <span className="ml-3 text-xs text-gray-400">v2.1.0 · 约 43MB · Win10/11</span>
        </CardContent>
      </Card>
    </div>
  );
}
