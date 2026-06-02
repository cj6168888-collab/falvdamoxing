import { Link, Navigate, useParams } from 'react-router-dom';
import { ArrowRight, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { BrandMark, ProductPreview } from '@/components/marketing/brand-mark';
import { ClientDownloadLink } from '@/components/marketing/client-download-link';
import { audienceFromSlug, audiencePublicCopy } from '@/lib/public-site-copy';

export default function AudienceLandingPage() {
  const { audienceSlug } = useParams();
  const audience = audienceFromSlug(audienceSlug);

  if (!audience) return <Navigate to="/" replace />;

  const copy = audiencePublicCopy[audience];
  const Icon = copy.icon;

  return (
    <main className="min-h-[100dvh] bg-[#F8FAFC] text-[#162033]">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-4 py-5 sm:px-6 lg:px-8">
        <BrandMark />
        <div className="flex items-center gap-3">
          <Button asChild variant="outline">
            <Link to={`/login/${copy.slug}`}>登录</Link>
          </Button>
          <Button asChild className="bg-[#0F766E] hover:bg-[#115E59]">
            <Link to={`/register/${copy.slug}`}>注册</Link>
          </Button>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl items-center gap-12 px-4 py-12 sm:px-6 lg:grid-cols-[1fr_520px] lg:px-8">
        <div>
          <span className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium ${copy.accentClass}`}>
            <Icon className="h-4 w-4" />
            {copy.eyebrow}
          </span>
          <h1 className="mt-6 max-w-4xl text-4xl font-semibold leading-tight tracking-normal sm:text-5xl">
            {copy.headline}
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">{copy.subhead}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild className="bg-[#0F766E] hover:bg-[#115E59]">
              <Link to={`/register/${copy.slug}`}>
                {copy.registerTitle}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link to={`/login/${copy.slug}`}>{copy.loginTitle}</Link>
            </Button>
          </div>
        </div>
        <ProductPreview title={copy.previewTitle} items={copy.previewItems} />
      </section>

      <section className="mx-auto grid max-w-7xl gap-4 px-4 pb-16 sm:px-6 md:grid-cols-4 lg:px-8">
        {copy.benefits.map((benefit) => (
          <div key={benefit} className="rounded-2xl border border-slate-200 bg-white p-5">
            <CheckCircle2 className="mb-4 h-5 w-5 text-[#0F766E]" />
            <p className="text-sm leading-6 text-slate-700">{benefit}</p>
          </div>
        ))}
      </section>

      <section className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-4 py-10 sm:px-6 md:flex-row md:items-center md:justify-between lg:px-8">
          <div>
            <h2 className="text-xl font-semibold">也可以使用客户端</h2>
            <p className="mt-2 text-sm text-slate-600">手机访问时下载 Android APK，电脑访问时下载 Windows 客户端。</p>
          </div>
          <ClientDownloadLink variant="panel" />
        </div>
      </section>
    </main>
  );
}
