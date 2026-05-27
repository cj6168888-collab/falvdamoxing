import { Save, CheckCircle, AlertCircle } from 'lucide-react';

interface AutoSaveIndicatorProps {
  status: 'idle' | 'saving' | 'saved' | 'error';
  lastSaved?: Date;
}

export function AutoSaveIndicator({ status, lastSaved }: AutoSaveIndicatorProps) {
  return (
    <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
      {status === 'saving' && <><Save className="h-3 w-3 animate-spin" /><span>正在保存...</span></>}
      {status === 'saved' && <><CheckCircle className="h-3 w-3 text-green-500" /><span>{lastSaved ? `已保存 ${lastSaved.toLocaleTimeString()}` : '已保存'}</span></>}
      {status === 'error' && <><AlertCircle className="h-3 w-3 text-red-500" /><span>保存失败</span></>}
      {status === 'idle' && <span>未修改</span>}
    </div>
  );
}
