import axiosInstance from '@/api/client';

export interface ExportResult {
  success: boolean;
  filename?: string;
  download_url?: string;
  format_used?: string;
  requested_format?: string;
  error?: string;
}

export interface DocumentExportPayload {
  document_type: string;
  format: 'pdf' | 'docx' | 'markdown' | 'txt' | 'html';
  custom_content?: string;
}

export async function exportCaseDocument(
  caseId: string | number,
  payload: DocumentExportPayload,
): Promise<ExportResult> {
  return axiosInstance.post(`/api/exports/document/${caseId}`, payload).then((res) => res.data);
}

export async function exportAdversarialAnalysis(
  analysisId: string | number,
  format: DocumentExportPayload['format'] = 'markdown',
): Promise<ExportResult> {
  return axiosInstance
    .post(`/api/exports/adversarial-analysis/${analysisId}?format=${format}`)
    .then((res) => res.data);
}

export async function downloadExportFile(result: ExportResult): Promise<void> {
  if (!result.success || !result.download_url || !result.filename) {
    throw new Error(result.error || '导出文件不可下载');
  }

  const response = await axiosInstance.get(result.download_url, { responseType: 'blob' });
  triggerBlobDownload(response.data, result.filename);
}

function triggerBlobDownload(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);
}
