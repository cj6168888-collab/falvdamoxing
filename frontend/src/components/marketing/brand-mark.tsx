import { Link } from 'react-router-dom';
import { Scale } from 'lucide-react';
import { cn } from '@/lib/utils';

export function LegalDraftLogo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 48 48"
      aria-hidden="true"
      className={cn('h-11 w-11 shrink-0', className)}
      fill="none"
    >
      <rect x="3" y="3" width="42" height="42" rx="12" fill="#162033" />
      <path d="M16 12h14l6 6v18H16V12Z" fill="#F8FAFC" />
      <path d="M30 12v7h7" fill="#D9F3F0" />
      <path d="M19 23h18" stroke="#0F766E" strokeWidth="2.6" strokeLinecap="round" />
      <path d="M24 23v10" stroke="#162033" strokeWidth="2.6" strokeLinecap="round" />
      <path d="M20 27l-4 7h8l-4-7Z" fill="#0F766E" />
      <path d="M34 27l-4 7h8l-4-7Z" fill="#0F766E" />
      <path d="M21 17h8" stroke="#94A3B8" strokeWidth="2" strokeLinecap="round" />
      <path d="M21 38h12" stroke="#B45309" strokeWidth="2.6" strokeLinecap="round" />
      <circle cx="12" cy="15" r="2.3" fill="#0F766E" />
      <circle cx="12" cy="24" r="2.3" fill="#0F766E" />
      <path d="M12 17.5v6" stroke="#0F766E" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

export function BrandMark({ className }: { className?: string }) {
  return (
    <Link to="/" className={cn('inline-flex items-center gap-3', className)}>
      <LegalDraftLogo />
      <span className="leading-tight">
        <span className="block text-base font-semibold tracking-normal text-[#162033]">法律大模型辅助系统</span>
        <span className="block text-xs text-slate-500">可复核的法律 AI 工作底稿</span>
      </span>
    </Link>
  );
}

export function ProductPreview({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_24px_80px_rgba(22,32,51,0.12)]">
      <div className="mb-4 flex items-center justify-between border-b border-slate-100 pb-4">
        <div>
          <p className="text-sm font-semibold text-[#162033]">{title}</p>
          <p className="text-xs text-slate-500">事实、材料、风险、行动同步整理</p>
        </div>
        <span className="rounded-full bg-teal-50 px-3 py-1 text-xs font-medium text-teal-700">可复核</span>
      </div>
      <div className="space-y-3">
        {items.map((item, index) => (
          <div key={item} className="grid grid-cols-[28px_1fr_auto] items-center gap-3">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
              {index + 1}
            </span>
            <div>
              <div className="h-2.5 rounded-full bg-slate-200" style={{ width: `${82 - index * 8}%` }} />
              <p className="mt-1 text-sm font-medium text-slate-700">{item}</p>
            </div>
            <Scale className="h-4 w-4 text-teal-600" />
          </div>
        ))}
      </div>
      <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
        重要结论必须保留材料依据，并支持人工复核。
      </div>
    </div>
  );
}
