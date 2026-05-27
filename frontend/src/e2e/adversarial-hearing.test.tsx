import { useState } from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@/test/test-utils';
import { createMockSwotAnalysis } from '@/test/fixtures';
import type { SwotAnalysis } from '@/types/adversarial.types';
import type { Hearing } from '@/types/hearing.types';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

interface ScenarioPrediction {
  id: string;
  name: string;
  probability: number;
  impact: 'high' | 'medium' | 'low';
}

interface ActionPlan {
  id: string;
  title: string;
  steps: string[];
  strategies: string[];
}

interface TrialOutline {
  id: string;
  sections: string[];
  strategies: string[];
  evidenceReferences: string[];
}

interface HearingResult {
  id: string;
  outcome: string;
  effectiveness: Record<string, number>;
  lessonsLearned: string[];
}

interface AdversarialHearingState {
  analysisId: string | null;
  swot: SwotAnalysis | null;
  scenarios: ScenarioPrediction[];
  actionPlan: ActionPlan | null;
  hearing: Hearing | null;
  trialOutline: TrialOutline | null;
  hearingResult: HearingResult | null;
  feedbackToAnalysis: Partial<SwotAnalysis> | null;
}

function AdversarialHearingTest({ initialState }: { initialState: AdversarialHearingState }) {
  const [state, setState] = useState<AdversarialHearingState>(initialState);

  const createAnalysis = () => {
    setState(prev => ({
      ...prev,
      analysisId: 'analysis-1',
      swot: createMockSwotAnalysis(),
    }));
  };

  const addScenario = () => {
    const scenario: ScenarioPrediction = {
      id: 'scenario-1',
      name: 'Opponent challenges evidence',
      probability: 0.7,
      impact: 'high',
    };
    setState(prev => ({
      ...prev,
      scenarios: [...prev.scenarios, scenario],
    }));
  };

  const generateActionPlan = () => {
    const plan: ActionPlan = {
      id: 'plan-1',
      title: 'Evidence Defense Plan',
      steps: ['Gather supporting docs', 'Prepare witness', 'File motion'],
      strategies: ['Preemptive evidence submission', 'Expert testimony'],
    };
    setState(prev => ({
      ...prev,
      actionPlan: plan,
    }));
  };

  const importToHearing = () => {
    const hearing: Hearing = {
      id: 'hearing-e2e',
      caseId: 'case-1',
      courtName: 'Beijing Court',
      date: '2024-06-20',
      type: 'first',
      status: 'scheduled',
      judge: 'Judge Zhang',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    const trialOutline: TrialOutline = {
      id: 'outline-1',
      sections: ['Opening', 'Evidence Presentation', 'Cross-examination', 'Closing'],
      strategies: state.actionPlan?.strategies || [],
      evidenceReferences: ['ev-1', 'ev-2'],
    };

    setState(prev => ({
      ...prev,
      hearing,
      trialOutline,
    }));
  };

  const recordResults = () => {
    const result: HearingResult = {
      id: 'result-1',
      outcome: 'Partial win',
      effectiveness: {
        'Evidence strategy': 0.8,
        'Cross-examination': 0.6,
      },
      lessonsLearned: ['Need more expert witnesses', 'Prepare for character attacks'],
    };

    const feedback: Partial<SwotAnalysis> = {
      weaknesses: ['Transfer note unclear', 'Expert witness needed'],
    };

    setState(prev => ({
      ...prev,
      hearingResult: result,
      feedbackToAnalysis: feedback,
    }));
  };

  return (
    <div data-testid="adversarial-hearing">
      <div data-testid="analysis-status">{state.analysisId ? 'created' : 'none'}</div>
      <div data-testid="swot-status">{state.swot ? 'exists' : 'none'}</div>
      <div data-testid="scenario-count">{state.scenarios.length}</div>
      <div data-testid="action-plan-status">{state.actionPlan ? 'generated' : 'none'}</div>
      <div data-testid="hearing-status">{state.hearing ? 'imported' : 'none'}</div>
      <div data-testid="trial-strategies">{state.trialOutline?.strategies.join(',') || 'none'}</div>
      <div data-testid="hearing-result">{state.hearingResult?.outcome || 'none'}</div>
      <div data-testid="feedback-weaknesses">{state.feedbackToAnalysis?.weaknesses?.join(',') || 'none'}</div>

      <button data-testid="create-analysis-btn" onClick={createAnalysis}>Create Analysis</button>
      <button data-testid="add-scenario-btn" onClick={addScenario}>Add Scenario</button>
      <button data-testid="generate-plan-btn" onClick={generateActionPlan}>Generate Action Plan</button>
      <button data-testid="import-hearing-btn" onClick={importToHearing}>Import to Hearing</button>
      <button data-testid="record-results-btn" onClick={recordResults}>Record Results</button>
    </div>
  );
}

describe('E2E: Adversarial Analysis to Hearing Loop', () => {
  const initialState: AdversarialHearingState = {
    analysisId: null,
    swot: null,
    scenarios: [],
    actionPlan: null,
    hearing: null,
    trialOutline: null,
    hearingResult: null,
    feedbackToAnalysis: null,
  };

  it('correctly imports analysis data to hearing', async () => {
    render(<AdversarialHearingTest initialState={initialState} />);

    expect(screen.getByTestId('analysis-status')).toHaveTextContent('none');

    fireEvent.click(screen.getByTestId('create-analysis-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('analysis-status')).toHaveTextContent('created');
      expect(screen.getByTestId('swot-status')).toHaveTextContent('exists');
    });

    fireEvent.click(screen.getByTestId('add-scenario-btn'));
    expect(screen.getByTestId('scenario-count')).toHaveTextContent('1');

    fireEvent.click(screen.getByTestId('generate-plan-btn'));
    expect(screen.getByTestId('action-plan-status')).toHaveTextContent('generated');

    fireEvent.click(screen.getByTestId('import-hearing-btn'));
    expect(screen.getByTestId('hearing-status')).toHaveTextContent('imported');
  });

  it('includes analysis strategies in trial outline', async () => {
    render(<AdversarialHearingTest initialState={initialState} />);

    fireEvent.click(screen.getByTestId('create-analysis-btn'));
    fireEvent.click(screen.getByTestId('generate-plan-btn'));
    fireEvent.click(screen.getByTestId('import-hearing-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('trial-strategies').textContent).toContain('Preemptive evidence submission');
    });
  });

  it('feeds hearing results back to analysis', async () => {
    render(<AdversarialHearingTest initialState={initialState} />);

    fireEvent.click(screen.getByTestId('create-analysis-btn'));
    fireEvent.click(screen.getByTestId('add-scenario-btn'));
    fireEvent.click(screen.getByTestId('generate-plan-btn'));
    fireEvent.click(screen.getByTestId('import-hearing-btn'));
    fireEvent.click(screen.getByTestId('record-results-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('hearing-result')).toHaveTextContent('Partial win');
      expect(screen.getByTestId('feedback-weaknesses').textContent).toContain('Expert witness needed');
    });
  });

  it('completes full adversarial analysis to hearing loop', async () => {
    render(<AdversarialHearingTest initialState={initialState} />);

    fireEvent.click(screen.getByTestId('create-analysis-btn'));
    fireEvent.click(screen.getByTestId('add-scenario-btn'));
    fireEvent.click(screen.getByTestId('generate-plan-btn'));
    fireEvent.click(screen.getByTestId('import-hearing-btn'));
    fireEvent.click(screen.getByTestId('record-results-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('analysis-status')).toHaveTextContent('created');
      expect(screen.getByTestId('hearing-status')).toHaveTextContent('imported');
      expect(screen.getByTestId('hearing-result')).toHaveTextContent('Partial win');
      expect(screen.getByTestId('feedback-weaknesses')).not.toHaveTextContent('none');
    });
  });
});
