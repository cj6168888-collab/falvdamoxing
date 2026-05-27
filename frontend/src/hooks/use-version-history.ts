import { useState, useCallback } from 'react';

export function useVersionHistory() {
  const [versions, setVersions] = useState<{ version: number; content: string; timestamp: string }[]>([]);
  const [currentVersion, setCurrentVersion] = useState(0);

  const addVersion = useCallback((content: string) => {
    setVersions((prev) => [...prev, { version: prev.length + 1, content, timestamp: new Date().toISOString() }]);
    setCurrentVersion((prev) => prev + 1);
  }, []);

  const getVersion = useCallback(
    (version: number) => {
      return versions.find((v) => v.version === version);
    },
    [versions]
  );

  const revertToVersion = useCallback((version: number) => {
    setCurrentVersion(version);
  }, []);

  return { versions, currentVersion, addVersion, getVersion, revertToVersion };
}
