import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '@/api/client';

export interface FolderFileRecord {
  id: number;
  case_id: number;
  file_path: string;
  file_name: string;
  file_extension: string;
  file_size: number | null;
  relative_path: string;
  file_hash: string;
  detected_at: string;
  last_modified: string;
  processed: boolean;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'skipped';
  error_message: string | null;
  evidence_id: string | null;
  extracted_content_length: number;
  ocr_used: boolean;
  auto_category: string | null;
  auto_summary: string | null;
  processed_at: string | null;
}

export interface FolderConfig {
  case_id: number;
  folder_path: string | null;
  enabled: boolean;
  last_scan_time: string | null;
  last_sync_count: number;
  is_monitoring: boolean;
  config: {
    supported_formats: string[] | null;
    auto_ocr: boolean;
    auto_classify: boolean;
    auto_deduplicate: boolean;
    include_subfolders: boolean;
  };
}

export interface FolderStatus {
  case_id: number;
  folder_path: string | null;
  folder_exists: boolean;
  is_enabled: boolean;
  is_monitoring: boolean;
  last_scan_time: string | null;
  last_sync_count: number;
  stats: {
    total: number;
    processed: number;
    pending: number;
    failed: number;
    skipped: number;
  };
  recent_files: FolderFileRecord[];
}

export interface FileListResponse {
  total: number;
  page: number;
  page_size: number;
  records: FolderFileRecord[];
}

export interface ScanHistoryResponse {
  total: number;
  page: number;
  page_size: number;
  scans: {
    id: number;
    scan_type: string;
    status: string;
    started_at: string | null;
    completed_at: string | null;
    files_found: number;
    files_processed: number;
    files_failed: number;
    files_skipped: number;
    error_message: string | null;
  }[];
}

export async function getFolderConfig(caseId: number) {
  return axiosInstance.get<FolderConfig>(`/api/evidence-folder/cases/${caseId}/config`).then(res => res.data);
}

export async function updateFolderConfig(caseId: number, data: { folder_path: string; enabled: boolean }) {
  return axiosInstance.put(`/api/evidence-folder/cases/${caseId}/config`, data).then(res => res.data);
}

export async function getFolderStatus(caseId: number) {
  return axiosInstance.get<FolderStatus>(`/api/evidence-folder/cases/${caseId}/status`).then(res => res.data);
}

export async function getFolderFiles(caseId: number, params?: { status?: string; page?: number; page_size?: number }) {
  return axiosInstance.get<FileListResponse>(`/api/evidence-folder/cases/${caseId}/files`, { params }).then(res => res.data);
}

export async function getScanHistory(caseId: number, params?: { page?: number; page_size?: number }) {
  return axiosInstance.get<ScanHistoryResponse>(`/api/evidence-folder/cases/${caseId}/scans`, { params }).then(res => res.data);
}

export async function triggerScan(caseId: number, scanType: 'full' | 'incremental' = 'full') {
  return axiosInstance.post(`/api/evidence-folder/cases/${caseId}/scan`, { scan_type: scanType }).then(res => res.data);
}

export async function triggerIncrementalScan(caseId: number) {
  return axiosInstance.post(`/api/evidence-folder/cases/${caseId}/scan-incremental`).then(res => res.data);
}

export async function enableMonitoring(caseId: number) {
  return axiosInstance.post(`/api/evidence-folder/cases/${caseId}/enable-monitor`).then(res => res.data);
}

export async function disableMonitoring(caseId: number) {
  return axiosInstance.post(`/api/evidence-folder/cases/${caseId}/disable-monitor`).then(res => res.data);
}

export async function deleteFileRecord(caseId: number, fileId: number) {
  return axiosInstance.delete(`/api/evidence-folder/cases/${caseId}/files/${fileId}`).then(res => res.data);
}

export async function reprocessFile(caseId: number, fileId: number) {
  return axiosInstance.post(`/api/evidence-folder/cases/${caseId}/files/${fileId}/reprocess`).then(res => res.data);
}

// ============ React Query Hooks ============

export function useFolderConfig(caseId: number) {
  return useQuery({
    queryKey: ['evidence-folder-config', caseId],
    queryFn: () => getFolderConfig(caseId),
    enabled: !!caseId,
  });
}

export function useFolderStatus(caseId: number, refetchInterval?: number) {
  return useQuery({
    queryKey: ['evidence-folder-status', caseId],
    queryFn: () => getFolderStatus(caseId),
    enabled: !!caseId,
    refetchInterval: refetchInterval || ((query) => query.state.data?.is_monitoring ? 5000 : false),
  });
}

export function useFolderFiles(caseId: number, params?: { status?: string; page?: number; page_size?: number }) {
  return useQuery({
    queryKey: ['evidence-folder-files', caseId, params],
    queryFn: () => getFolderFiles(caseId, params),
    enabled: !!caseId,
  });
}

export function useScanHistory(caseId: number, params?: { page?: number; page_size?: number }) {
  return useQuery({
    queryKey: ['evidence-folder-scans', caseId, params],
    queryFn: () => getScanHistory(caseId, params),
    enabled: !!caseId,
  });
}

export function useUpdateFolderConfig(caseId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { folder_path: string; enabled: boolean }) => updateFolderConfig(caseId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence-folder-config', caseId] });
      queryClient.invalidateQueries({ queryKey: ['evidence-folder-status', caseId] });
    },
  });
}

export function useTriggerScan(caseId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (scanType: 'full' | 'incremental') => triggerScan(caseId, scanType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence-folder-status', caseId] });
      queryClient.invalidateQueries({ queryKey: ['evidence-folder-files', caseId] });
      queryClient.invalidateQueries({ queryKey: ['evidence-folder-scans', caseId] });
    },
  });
}

export function useEnableMonitoring(caseId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => enableMonitoring(caseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence-folder-config', caseId] });
      queryClient.invalidateQueries({ queryKey: ['evidence-folder-status', caseId] });
    },
  });
}

export function useDisableMonitoring(caseId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => disableMonitoring(caseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence-folder-config', caseId] });
      queryClient.invalidateQueries({ queryKey: ['evidence-folder-status', caseId] });
    },
  });
}

export function useDeleteFileRecord(caseId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (fileId: number) => deleteFileRecord(caseId, fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence-folder-files', caseId] });
      queryClient.invalidateQueries({ queryKey: ['evidence-folder-status', caseId] });
    },
  });
}

export function useReprocessFile(caseId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (fileId: number) => reprocessFile(caseId, fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence-folder-files', caseId] });
      queryClient.invalidateQueries({ queryKey: ['evidence-folder-status', caseId] });
    },
  });
}
