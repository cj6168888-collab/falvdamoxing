import { useEffect, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';

export function useScanEvents(caseId: number) {
  const queryClient = useQueryClient();

  const handleEvent = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['evidence-folder-status', caseId] });
    queryClient.invalidateQueries({ queryKey: ['evidence-folder-files', caseId] });
  }, [caseId, queryClient]);

  useEffect(() => {
    if (!caseId) return;

    const url = `/api/evidence-folder/cases/${caseId}/scan-events`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = () => {
      handleEvent();
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [caseId, handleEvent]);
}
