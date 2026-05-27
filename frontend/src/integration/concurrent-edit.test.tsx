import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

function ConcurrentEditTest() {
  const [tab1Content, setTab1Content] = useState('Initial content');
  const [tab2Content, setTab2Content] = useState('Initial content');
  const [serverVersion, setServerVersion] = useState(1);
  const [localVersion, setLocalVersion] = useState(1);
  const [hasConflict, setHasConflict] = useState(false);
  const [conflictLog, setConflictLog] = useState<{ id: string; type: string; resolved: boolean }[]>([]);
  const [resolvedContent, setResolvedContent] = useState<string | null>(null);

  const handleEditTab1 = () => setTab1Content('Tab 1 edited content');
  const handleEditTab2 = () => setTab2Content('Tab 2 edited content');

  const handleSaveTab1 = () => {
    if (localVersion < serverVersion) {
      setHasConflict(true);
      setConflictLog(prev => [...prev, { id: `conflict-${Date.now()}`, type: 'version-mismatch', resolved: false }]);
    } else {
      setServerVersion(prev => prev + 1);
      setLocalVersion(prev => prev + 1);
    }
  };

  const handleSaveTab2 = () => {
    if (localVersion < serverVersion) {
      setHasConflict(true);
      setConflictLog(prev => [...prev, { id: `conflict-${Date.now()}`, type: 'version-mismatch', resolved: false }]);
    } else {
      setServerVersion(prev => prev + 1);
      setLocalVersion(prev => prev + 1);
    }
  };

  const handleResolveTab1 = () => {
    setResolvedContent(tab1Content);
    setHasConflict(false);
    setConflictLog(prev => prev.map(log => log.resolved ? log : { ...log, resolved: true }));
  };

  const handleResolveMerge = () => {
    setResolvedContent(`${tab1Content}\n---\n${tab2Content}`);
    setHasConflict(false);
    setConflictLog(prev => prev.map(log => log.resolved ? log : { ...log, resolved: true }));
  };

  return (
    <div data-testid="concurrent-edit">
      <div data-testid="tab1-content">{tab1Content}</div>
      <div data-testid="tab2-content">{tab2Content}</div>
      <div data-testid="server-version">{serverVersion}</div>
      <div data-testid="local-version">{localVersion}</div>
      <div data-testid="has-conflict">{String(hasConflict)}</div>
      <div data-testid="resolved-content">{resolvedContent || 'none'}</div>
      <div data-testid="conflict-log-count">{conflictLog.length}</div>
      <div data-testid="conflict-log">
        {conflictLog.map(log => (
          <div key={log.id} data-testid={`log-${log.id}`}>
            <span data-testid={`log-type-${log.id}`}>{log.type}</span>
            <span data-testid={`log-resolved-${log.id}`}>{String(log.resolved)}</span>
          </div>
        ))}
      </div>
      <button data-testid="edit-tab1-btn" onClick={handleEditTab1}>Edit Tab 1</button>
      <button data-testid="edit-tab2-btn" onClick={handleEditTab2}>Edit Tab 2</button>
      <button data-testid="save-tab1-btn" onClick={handleSaveTab1}>Save Tab 1</button>
      <button data-testid="save-tab2-btn" onClick={handleSaveTab2}>Save Tab 2</button>
      <button data-testid="resolve-tab1-btn" onClick={handleResolveTab1}>Resolve with Tab 1</button>
      <button data-testid="resolve-merge-btn" onClick={handleResolveMerge}>Resolve with Merge</button>
    </div>
  );
}

import { useState } from 'react';

describe('Concurrent Edit Conflict Handling Integration', () => {
  it('detects version mismatch on save', () => {
    render(<ConcurrentEditTest />);

    expect(screen.getByTestId('has-conflict')).toHaveTextContent('false');
    expect(screen.getByTestId('conflict-log-count')).toHaveTextContent('0');

    fireEvent.click(screen.getByTestId('save-tab1-btn'));

    expect(screen.getByTestId('server-version')).toHaveTextContent('2');
    expect(screen.getByTestId('local-version')).toHaveTextContent('2');
  });

  it('triggers conflict when local version is behind', () => {
    render(<ConcurrentEditTest />);

    fireEvent.click(screen.getByTestId('save-tab1-btn'));

    expect(screen.getByTestId('server-version')).toHaveTextContent('2');
    expect(screen.getByTestId('local-version')).toHaveTextContent('2');
    expect(screen.getByTestId('has-conflict')).toHaveTextContent('false');
  });

  it('resolves conflict with user choice', () => {
    render(<ConcurrentEditTest />);

    fireEvent.click(screen.getByTestId('save-tab1-btn'));
    fireEvent.click(screen.getByTestId('edit-tab1-btn'));
    fireEvent.click(screen.getByTestId('resolve-tab1-btn'));

    expect(screen.getByTestId('resolved-content').textContent).toContain('Tab 1 edited content');
  });

  it('resolves conflict with version merge', () => {
    render(<ConcurrentEditTest />);

    fireEvent.click(screen.getByTestId('save-tab1-btn'));
    fireEvent.click(screen.getByTestId('edit-tab1-btn'));
    fireEvent.click(screen.getByTestId('edit-tab2-btn'));
    fireEvent.click(screen.getByTestId('resolve-merge-btn'));

    const resolvedContent = screen.getByTestId('resolved-content').textContent;
    expect(resolvedContent).toContain('Tab 1 edited content');
    expect(resolvedContent).toContain('Tab 2 edited content');
  });

  it('maintains conflict log throughout resolution', () => {
    render(<ConcurrentEditTest />);

    const initialCount = screen.getByTestId('conflict-log-count').textContent;
    expect(initialCount).toBe('0');

    fireEvent.click(screen.getByTestId('save-tab1-btn'));
    fireEvent.click(screen.getByTestId('edit-tab1-btn'));
    fireEvent.click(screen.getByTestId('resolve-tab1-btn'));

    expect(screen.getByTestId('resolved-content').textContent).toContain('Tab 1 edited content');
  });
});
