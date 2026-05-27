import { toast as sonnerToast } from 'sonner';

export function useToast() {
  const toast = ({ title, description, variant = 'default' }: { title?: string; description?: string; variant?: 'default' | 'destructive' }) => {
    if (variant === 'destructive') {
      sonnerToast.error(description || title || '');
    } else if (title) {
      sonnerToast.success(title, { description });
    } else {
      sonnerToast(description || '');
    }
  };

  return { toast };
}
