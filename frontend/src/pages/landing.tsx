import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { BrandMark, ProductPreview } from '@/components/marketing/brand-mark';
import { ClientDownloadLink } from '@/components/marketing/client-download-link';
import { audiencePublicCopy, publicSiteHighlights } from '@/lib/public-site-copy';

const audiences = Object.values(audiencePublicCopy);

export default function LandingPage() {
  return (
    <main className="min-h-[100dvh] bg-[#F8FAFC] text-[#162033]">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-4 py-5 sm:px-6 lg:px-8">
        <BrandMark />
        <nav className="hidden items-center gap-7 text-sm font-medium text-slate-600 md:flex">
          <Link to="/law-firm" className="hover:text-[#0F766E]">律所</Link>
          <Link to="/enterprise" className="hover:text-[#0F766E]">企业</Link>
          <Link to="/personal" className="hover:text-[#0F766E]">个人</Link>
          <a href="#client-download" className="hover:text-[#0F766E]">客户端下载</a>
        </nav>
        <Button asChild className="bg-[#162033] hover:bg-[#22304a]">
          <Link to="/login">登录</Link>
        </Button>
      </header>

      <section className="mx-auto grid max-w-7xl items-center gap-12 px-4 pb-16 pt-8 sm:px-6 lg:grid-cols-[1fr_520px] lg:px-8 lg:pb-20">
        <div>
          <p className="mb-5 inline-flex rounded-full border border-teal-200 bg-teal-50 px-4 py-2 text-sm font-medium text-teal-800">
            法律 AI 的答案，必须能回到事实和材料
          </p>
          <h1 className="max-w-4xl text-4xl font-semibold leading-tight tracking-normal text-[#162033] sm:text-5xl lg:text-6xl">
            可复核的法律 AI 工作底稿系统
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
            把事实、材料、风险和下一步行动整理成可检查、可追溯、可协作的法律工作底稿。
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            {audiences.map((audience) => (
              <Button key={audience.type} asChild className="bg-[#0F766E] hover:bg-[#115E59]">
                <Link to={`/${audience.slug}`}>
                  {audience.primaryCta}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            ))}
          </div>
        </div>
        <ProductPreview
          title="法律工作底稿"
          items={['材料读取', '事实时间线', '证据链', '风险提示', '下一步行动']}
        />
      </section>

      <section className="mx-auto grid max-w-7xl gap-4 px-4 pb-16 sm:px-6 md:grid-cols-3 lg:px-8">
        {audiences.map((audience) => {
          const Icon = audience.icon;
          return (
            <Link
              key={audience.type}
              to={`/${audience.slug}`}
              className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:border-teal-300 hover:shadow-md"
            >
              <span className={`mb-5 inline-flex rounded-xl border p-3 ${audience.accentClass}`}>
                <Icon className="h-6 w-6" />
              </span>
              <h2 className="text-xl font-semibold text-[#162033]">{audience.label}</h2>
              <p className="mt-3 min-h-16 text-sm leading-6 text-slate-600">{audience.subhead}</p>
              <span className="mt-5 inline-flex items-center text-sm font-semibold text-[#0F766E]">
                {audience.secondaryCta}
                <ArrowRight className="ml-1 h-4 w-4 transition group-hover:translate-x-0.5" />
              </span>
            </Link>
          );
        })}
      </section>

      <section className="border-y border-slate-200 bg-white">
        <div className="mx-auto grid max-w-7xl gap-5 px-4 py-14 sm:px-6 md:grid-cols-3 lg:px-8">
          {publicSiteHighlights.map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.title} className="flex gap-4">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-[#0F766E]">
                  <Icon className="h-5 w-5" />
                </span>
                <div>
                  <h3 className="font-semibold text-[#162033]">{item.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{item.text}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section id="client-download" className="mx-auto flex max-w-7xl flex-col gap-5 px-4 py-12 sm:px-6 md:flex-row md:items-center md:justify-between lg:px-8">
        <div>
          <h2 className="text-2xl font-semibold">客户端下载</h2>
          <p className="mt-2 text-slate-600">手机访问时下载 Android APK，电脑访问时下载 Windows 客户端。</p>
        </div>
        <ClientDownloadLink />
      </section>
    </main>
  );
}
