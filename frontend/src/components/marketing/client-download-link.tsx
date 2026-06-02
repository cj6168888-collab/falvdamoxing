import { useEffect, useState } from 'react';
import { MonitorDown, Smartphone } from 'lucide-react';
import { cn } from '@/lib/utils';
import { CLIENT_DOWNLOADS } from '@/lib/downloads';

interface ClientDownloadLinkProps {
  className?: string;
  variant?: 'button' | 'panel';
}

export function ClientDownloadLink({ className, variant = 'button' }: ClientDownloadLinkProps) {
  const [androidAvailable, setAndroidAvailable] = useState(false);

  useEffect(() => {
    let cancelled = false;

    fetch(CLIENT_DOWNLOADS.android.href, { method: 'HEAD' })
      .then((response) => {
        if (!cancelled) setAndroidAvailable(response.ok);
      })
      .catch(() => {
        if (!cancelled) setAndroidAvailable(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const baseClass =
    variant === 'panel'
      ? 'flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-600 hover:border-teal-300 hover:text-[#0F766E]'
      : 'inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition';

  return (
    <>
      {androidAvailable ? (
        <a
          href={CLIENT_DOWNLOADS.android.href}
          className={cn(baseClass, variant === 'button' && 'bg-[#0F766E] text-white hover:bg-[#115E59]', 'md:hidden', className)}
        >
          <Smartphone className="h-4 w-4" />
          {CLIENT_DOWNLOADS.android.label}
        </a>
      ) : (
        <span
          className={cn(
            baseClass,
            variant === 'button' && 'bg-slate-200 text-slate-500',
            'cursor-not-allowed md:hidden',
            className
          )}
          aria-disabled="true"
        >
          <Smartphone className="h-4 w-4" />
          {CLIENT_DOWNLOADS.android.unavailableLabel}
        </span>
      )}
      <a
        href={CLIENT_DOWNLOADS.windows.href}
        className={cn(baseClass, variant === 'button' && 'bg-[#162033] text-white hover:bg-[#22304a]', 'hidden md:inline-flex', className)}
      >
        <MonitorDown className="h-4 w-4" />
        {CLIENT_DOWNLOADS.windows.label}
      </a>
    </>
  );
}
