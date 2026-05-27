import {
  useCreateExecutionRecord,
  useExecutionOverview as useExecutionOverviewApi,
  useUpdateExecutionOverview,
} from '@/api/execution.api';

export function useExecutionData(caseId: string) {
  return useExecutionOverviewApi(caseId);
}

export function useAddExecutionRecord(caseId = '') {
  return useCreateExecutionRecord(caseId);
}

export function useUpdateExecution(caseId = '') {
  return useUpdateExecutionOverview(caseId);
}
