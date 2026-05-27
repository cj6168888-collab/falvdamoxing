import { useState } from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@/test/test-utils';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

interface DocumentVersion {
  version: number;
  content: string;
  savedAt: string;
  author: string;
}

interface DocumentVersionState {
  currentVersion: number;
  content: string;
  versionHistory: DocumentVersion[];
  isEditing: boolean;
  lastSaved: string | null;
  exportContent: string | null;
}

function DocumentVersionTest({ initialState }: { initialState: DocumentVersionState }) {
  const [state, setState] = useState<DocumentVersionState>(initialState);

  const autoSave = () => {
    setState(prev => ({
      ...prev,
      lastSaved: new Date().toISOString(),
    }));
  };

  const saveNewVersion = () => {
    setState(prev => {
      const newVersion = prev.currentVersion + 1;
      return {
        ...prev,
        currentVersion: newVersion,
        versionHistory: [
          ...prev.versionHistory,
          {
            version: newVersion,
            content: prev.content,
            savedAt: new Date().toISOString(),
            author: 'Test User',
          },
        ],
        lastSaved: new Date().toISOString(),
      };
    });
  };

  const rollbackToVersion = (version: number) => {
    setState(prev => {
      const targetVersion = prev.versionHistory.find(v => v.version === version);
      if (!targetVersion) return prev;
      return {
        ...prev,
        content: targetVersion.content,
        currentVersion: version,
      };
    });
  };

  const exportDocument = () => {
    setState(prev => ({
      ...prev,
      exportContent: prev.content,
    }));
  };

  return (
    <div data-testid="document-version">
      <div data-testid="current-version">{state.currentVersion}</div>
      <div data-testid="version-count">{state.versionHistory.length}</div>
      <div data-testid="last-saved">{state.lastSaved || 'never'}</div>
      <div data-testid="content">{state.content}</div>
      <div data-testid="export-content">{state.exportContent || 'not exported'}</div>

      <div data-testid="version-history">
        {state.versionHistory.map(v => (
          <div key={v.version} data-testid={`version-${v.version}`}>
            <span>v{v.version}</span>
            <button data-testid={`rollback-${v.version}`} onClick={() => rollbackToVersion(v.version)}>
              Rollback
            </button>
          </div>
        ))}
      </div>

      <button data-testid="auto-save-btn" onClick={autoSave}>Auto Save</button>
      <button data-testid="save-version-btn" onClick={saveNewVersion}>Save New Version</button>
      <button data-testid="export-btn" onClick={exportDocument}>Export</button>
    </div>
  );
}

describe('E2E: Document Version Management Loop', () => {
  const initialState: DocumentVersionState = {
    currentVersion: 1,
    content: 'Initial document content',
    versionHistory: [],
    isEditing: false,
    lastSaved: null,
    exportContent: null,
  };

  it('completes full version management loop', async () => {
    render(<DocumentVersionTest initialState={initialState} />);

    expect(screen.getByTestId('current-version')).toHaveTextContent('1');
    expect(screen.getByTestId('content')).toHaveTextContent('Initial document content');

    fireEvent.click(screen.getByTestId('auto-save-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('last-saved')).not.toHaveTextContent('never');
    });

    fireEvent.click(screen.getByTestId('save-version-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('current-version')).toHaveTextContent('2');
      expect(screen.getByTestId('version-count')).toHaveTextContent('1');
    });

    expect(screen.getByTestId('version-2')).toBeInTheDocument();
  });

  it('maintains complete and accurate version history', async () => {
    render(<DocumentVersionTest initialState={initialState} />);

    fireEvent.click(screen.getByTestId('save-version-btn'));
    fireEvent.click(screen.getByTestId('save-version-btn'));
    fireEvent.click(screen.getByTestId('save-version-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('current-version')).toHaveTextContent('4');
      expect(screen.getByTestId('version-count')).toHaveTextContent('3');
    });

    expect(screen.getByTestId('version-2')).toBeInTheDocument();
    expect(screen.getByTestId('version-3')).toBeInTheDocument();
    expect(screen.getByTestId('version-4')).toBeInTheDocument();
  });

  it('restores correct content on rollback', () => {
    const stateAfterV3: DocumentVersionState = {
      ...initialState,
      currentVersion: 3,
      content: 'Version 3 content',
      versionHistory: [
        { version: 1, content: 'Version 1 content', savedAt: '2024-01-01T09:00:00Z', author: 'Test User' },
        { version: 2, content: 'Version 2 content', savedAt: '2024-01-01T10:00:00Z', author: 'Test User' },
        { version: 3, content: 'Version 3 content', savedAt: '2024-01-02T10:00:00Z', author: 'Test User' },
      ],
    };

    render(<DocumentVersionTest initialState={stateAfterV3} />);

    expect(screen.getByTestId('current-version')).toHaveTextContent('3');
    expect(screen.getByTestId('content')).toHaveTextContent('Version 3 content');

    fireEvent.click(screen.getByTestId('rollback-2'));

    expect(screen.getByTestId('current-version')).toHaveTextContent('2');
    expect(screen.getByTestId('content')).toHaveTextContent('Version 2 content');
  });

  it('exports correct version content', async () => {
    render(<DocumentVersionTest initialState={initialState} />);

    fireEvent.click(screen.getByTestId('export-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('export-content')).toHaveTextContent('Initial document content');
    });
  });
});
