import { useMutation } from '@tanstack/react-query';
import axiosInstance from '@/api/client';

export function useExport() {
  return useMutation({
    mutationFn: async ({ url, format, data }: { url: string; format: string; data?: unknown }) => {
      const response = await axiosInstance.post(url, { format, ...(data as Record<string, unknown>) }, { responseType: 'blob' });
      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `export.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    },
  });
}
