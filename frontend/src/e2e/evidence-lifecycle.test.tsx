import { useState } from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@/test/test-utils';
import { createMockEvidence } from '@/test/fixtures';
import type { Evidence } from '@/types/evidence.types';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

interface EvidenceLifecycleState {
  evidence: Evidence[];
  credibilityScores: Record<string, number>;
  linkedIssues: Record<string, string[]>;
  duplicates: string[];
  manualCorrections: Record<string, Partial<Evidence>>;
  graphNodes: string[];
  graphEdges: Array<{ source: string; target: string; type: string }>;
  completenessScore: number;
  diagnosisResults: Record<string, string[]>;
}

function EvidenceLifecycleTest({ initialState }: { initialState: EvidenceLifecycleState }) {
  const [state, setState] = useState<EvidenceLifecycleState>(initialState);

  const uploadEvidence = (ev: Evidence) => {
    setState(prev => ({
      ...prev,
      evidence: [...prev.evidence, ev],
      graphNodes: [...prev.graphNodes, ev.id],
      credibilityScores: { ...prev.credibilityScores, [ev.id]: ev.credibilityScore ?? 0 },
      completenessScore: prev.completenessScore + 10,
    }));
  };

  const linkToIssue = (evidenceId: string, issueId: string) => {
    setState(prev => ({
      ...prev,
      linkedIssues: {
        ...prev.linkedIssues,
        [evidenceId]: [...(prev.linkedIssues[evidenceId] || []), issueId],
      },
      completenessScore: prev.completenessScore + 5,
    }));
  };

  const detectDuplicates = () => {
    setState(prev => {
      const duplicates = prev.evidence
        .filter((ev, idx) => prev.evidence.findIndex(e => e.name === ev.name) !== idx)
        .map(ev => ev.id);
      return { ...prev, duplicates };
    });
  };

  const applyCorrection = (evidenceId: string, corrections: Partial<Evidence>) => {
    setState(prev => ({
      ...prev,
      evidence: prev.evidence.map(ev =>
        ev.id === evidenceId ? { ...ev, ...corrections } : ev
      ),
      credibilityScores: { ...prev.credibilityScores, [evidenceId]: corrections.credibilityScore ?? prev.credibilityScores[evidenceId] },
      manualCorrections: { ...prev.manualCorrections, [evidenceId]: corrections },
      completenessScore: prev.completenessScore + 15,
    }));
  };

  const runDiagnosis = () => {
    setState(prev => {
      const results: Record<string, string[]> = {};
      prev.evidence.forEach(ev => {
        results[ev.id] = (ev.credibilityScore ?? 0) > 70 ? ['strong'] : ['weak', 'needs-corroboration'];
      });
      return { ...prev, diagnosisResults: results };
    });
  };

  return (
    <div data-testid="evidence-lifecycle">
      <div data-testid="evidence-count">{state.evidence.length}</div>
      <div data-testid="completeness-score">{state.completenessScore}</div>
      <div data-testid="graph-nodes">{state.graphNodes.join(',')}</div>
      <div data-testid="duplicates">{state.duplicates.join(',')}</div>
      <div data-testid="diagnosis-results">{JSON.stringify(state.diagnosisResults)}</div>

      <button
        data-testid="upload-btn"
        onClick={() => uploadEvidence(createMockEvidence({ id: `ev-${state.evidence.length + 1}`, name: `Evidence ${state.evidence.length + 1}`, credibilityScore: 65 }))}
      >
        Upload Evidence
      </button>
      <button
        data-testid="link-issue-btn"
        onClick={() => linkToIssue('ev-1', 'issue-1')}
      >
        Link to Issue
      </button>
      <button data-testid="detect-duplicates-btn" onClick={detectDuplicates}>
        Detect Duplicates
      </button>
      <button
        data-testid="correct-btn"
        onClick={() => applyCorrection('ev-1', { credibilityScore: 85, name: 'Corrected Evidence' })}
      >
        Correct Evidence
      </button>
      <button data-testid="diagnose-btn" onClick={runDiagnosis}>
        Run Diagnosis
      </button>
    </div>
  );
}

describe('E2E: Evidence Full Lifecycle', () => {
  const initialState: EvidenceLifecycleState = {
    evidence: [],
    credibilityScores: {},
    linkedIssues: {},
    duplicates: [],
    manualCorrections: {},
    graphNodes: [],
    graphEdges: [],
    completenessScore: 0,
    diagnosisResults: {},
  };

  it('flows evidence data through all lifecycle stages', async () => {
    render(<EvidenceLifecycleTest initialState={initialState} />);

    expect(screen.getByTestId('evidence-count')).toHaveTextContent('0');
    expect(screen.getByTestId('completeness-score')).toHaveTextContent('0');

    fireEvent.click(screen.getByTestId('upload-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('evidence-count')).toHaveTextContent('1');
      expect(screen.getByTestId('completeness-score')).toHaveTextContent('10');
    });

    fireEvent.click(screen.getByTestId('link-issue-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('completeness-score')).toHaveTextContent('15');
    });

    fireEvent.click(screen.getByTestId('detect-duplicates-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('duplicates')).toHaveTextContent('');
    });

    fireEvent.click(screen.getByTestId('correct-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('completeness-score')).toHaveTextContent('30');
    });

    fireEvent.click(screen.getByTestId('diagnose-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('diagnosis-results').textContent).toContain('strong');
    });
  });

  it('auto-assigns credibility score on upload', async () => {
    render(<EvidenceLifecycleTest initialState={initialState} />);

    fireEvent.click(screen.getByTestId('upload-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('evidence-count')).toHaveTextContent('1');
      expect(screen.getByTestId('completeness-score')).toHaveTextContent('10');
    });
  });

  it('updates completeness score after each action', async () => {
    render(<EvidenceLifecycleTest initialState={initialState} />);

    fireEvent.click(screen.getByTestId('upload-btn'));
    expect(screen.getByTestId('completeness-score')).toHaveTextContent('10');

    fireEvent.click(screen.getByTestId('link-issue-btn'));
    expect(screen.getByTestId('completeness-score')).toHaveTextContent('15');

    fireEvent.click(screen.getByTestId('correct-btn'));
    expect(screen.getByTestId('completeness-score')).toHaveTextContent('30');
  });

  it('reflects current evidence state in graph', async () => {
    render(<EvidenceLifecycleTest initialState={initialState} />);

    fireEvent.click(screen.getByTestId('upload-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('graph-nodes')).toHaveTextContent('ev-1');
    });

    fireEvent.click(screen.getByTestId('upload-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('graph-nodes')).toHaveTextContent('ev-1,ev-2');
    });
  });

  it('re-diagnoses after corrections', async () => {
    render(<EvidenceLifecycleTest initialState={initialState} />);

    fireEvent.click(screen.getByTestId('upload-btn'));
    fireEvent.click(screen.getByTestId('diagnose-btn'));

    await waitFor(() => {
      const results = JSON.parse(screen.getByTestId('diagnosis-results').textContent || '{}');
      expect(results['ev-1']).toContain('weak');
    });

    fireEvent.click(screen.getByTestId('correct-btn'));
    fireEvent.click(screen.getByTestId('diagnose-btn'));

    await waitFor(() => {
      const results = JSON.parse(screen.getByTestId('diagnosis-results').textContent || '{}');
      expect(results['ev-1']).toContain('strong');
    });
  });
});
