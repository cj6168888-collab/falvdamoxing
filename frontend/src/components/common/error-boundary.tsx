import { AlertTriangle } from 'lucide-react';

interface ErrorBoundaryProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({ message = '加载失败', onRetry }: ErrorBoundaryProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-red-200 bg-red-50 p-8 text-center dark:border-red-800 dark:bg-red-950/30">
      <AlertTriangle className="mb-4 h-12 w-12 text-red-500" />
      <h3 className="text-lg font-semibold text-red-700 dark:text-red-400">{message}</h3>
      {onRetry && (
        <button onClick={onRetry} className="mt-4 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700">
          重试
        </button>
      )}
    </div>
  );
}
