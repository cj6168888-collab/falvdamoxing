import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, Eye, EyeOff, KeyRound, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { authApi } from '@/api/auth.api';
import { ApiError } from '@/api/client';

export default function ForgotPasswordPage() {
  const [phone, setPhone] = useState('');
  const [smsCode, setSmsCode] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSendingCode, setIsSendingCode] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [error, setError] = useState('');
  const [hint, setHint] = useState('');
  const [success, setSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (countdown <= 0) return;
    const timer = window.setTimeout(() => setCountdown((value) => value - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [countdown]);

  const normalizePhone = () => phone.replace(/[\s\-()]/g, '').replace(/^\+86/, '').replace(/^86(?=1\d{10}$)/, '');

  const handleSendCode = async () => {
    const normalizedPhone = normalizePhone();
    setError('');
    setHint('');

    if (!/^1[3-9]\d{9}$/.test(normalizedPhone)) {
      setError('请输入有效的手机号');
      return;
    }

    setIsSendingCode(true);
    try {
      const response = await authApi.sendSmsCode(normalizedPhone, 'password_reset');
      setCountdown(Math.max(1, Math.ceil(response.expires_in > 60 ? 60 : response.expires_in)));
      setHint(response.debug_code ? `验证码已发送，开发验证码：${response.debug_code}` : response.message);
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

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const normalizedPhone = normalizePhone();
    setError('');

    if (!/^1[3-9]\d{9}$/.test(normalizedPhone)) {
      setError('请输入有效的手机号');
      return;
    }
    if (!/^\d{4,8}$/.test(smsCode.trim())) {
      setError('请输入短信验证码');
      return;
    }
    if (password.length < 6) {
      setError('密码至少需要6个字符');
      return;
    }
    if (password !== confirmPassword) {
      setError('两次输入的密码不一致');
      return;
    }

    setIsSubmitting(true);
    try {
      await authApi.resetPassword({
        phone: normalizedPhone,
        sms_code: smsCode.trim(),
        new_password: password,
      });
      setSuccess(true);
      window.setTimeout(() => navigate('/login'), 1200);
    } catch (err) {
      if (err instanceof ApiError) {
        const detail =
          err.details && typeof err.details === 'object' && 'detail' in err.details
            ? String((err.details as { detail?: unknown }).detail || '')
            : '';
        setError(detail || err.message || '密码重置失败');
      } else {
        setError('网络错误，请检查网络连接后重试');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4 dark:from-slate-900 dark:to-slate-800">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30">
              {success ? (
                <CheckCircle2 className="h-8 w-8 text-green-600 dark:text-green-400" />
              ) : (
                <KeyRound className="h-8 w-8 text-blue-600 dark:text-blue-400" />
              )}
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">找回密码</CardTitle>
          <CardDescription>验证手机号后设置新密码</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600 dark:bg-red-900/30 dark:text-red-400">
                {error}
              </div>
            )}
            {hint && (
              <div className="rounded-lg bg-blue-50 p-3 text-sm text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                {hint}
              </div>
            )}
            {success && (
              <div className="rounded-lg bg-green-50 p-3 text-sm text-green-700 dark:bg-green-900/30 dark:text-green-300">
                密码已重置，正在返回登录页
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="phone">手机号</Label>
              <Input
                id="phone"
                type="tel"
                placeholder="请输入注册手机号"
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                disabled={isSubmitting || success}
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
                  onChange={(event) => setSmsCode(event.target.value)}
                  disabled={isSubmitting || success}
                  autoComplete="one-time-code"
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleSendCode}
                  disabled={isSendingCode || countdown > 0 || isSubmitting || success}
                  className="w-32 shrink-0"
                >
                  {countdown > 0 ? `${countdown}s` : isSendingCode ? '发送中' : '获取验证码'}
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">新密码</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="至少6个字符"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  disabled={isSubmitting || success}
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
              <Label htmlFor="confirmPassword">确认新密码</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="再次输入新密码"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                disabled={isSubmitting || success}
                autoComplete="new-password"
              />
            </div>

            <Button type="submit" className="w-full" disabled={isSubmitting || success}>
              {isSubmitting ? (
                <>
                  <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  重置中...
                </>
              ) : (
                <>
                  重置密码
                  <RotateCcw size={16} className="ml-2" />
                </>
              )}
            </Button>

            <p className="text-center text-sm text-gray-500 dark:text-gray-400">
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
    </div>
  );
}
