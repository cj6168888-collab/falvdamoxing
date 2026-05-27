import { useMutation } from '@tanstack/react-query';
import { recordStatement } from '@/api/hearing.api';

export function useCrossExamination() {
  return useMutation({
    mutationFn: ({ hearingId, data }: { hearingId: string; data: Record<string, unknown> }) => recordStatement(hearingId, data),
  });
}
