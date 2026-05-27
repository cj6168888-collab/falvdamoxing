import { useState, useCallback } from 'react';

export function useAutoSave(key: string, _intervalMs: number = 30000) {
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const save = useCallback(
    async (content: string) => {
      setIsSaving(true);
      try {
        localStorage.setItem(`draft-${key}`, JSON.stringify({ content, timestamp: Date.now() }));
        setLastSaved(new Date());
      } finally {
        setIsSaving(false);
      }
    },
    [key]
  );

  return { lastSaved, isSaving, save };
}
