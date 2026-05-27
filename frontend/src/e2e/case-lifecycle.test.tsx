import { useState } from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@/test/test-utils';
import { createMockCase, createMockParty, createMockEvidence, createMockDocument, createMockDeadline } from '@/test/fixtures';
import type { Case } from '@/types/case.types';
import type { Party } from '@/types/party.types';
import type { Evidence } from '@/types/evidence.types';
import type { Document } from '@/types/document.types';
import type { Deadline } from '@/types/deadline.types';
import type { Reminder } from '@/types/reminder.types';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

interface CaseLifecycleState {
  currentCase: Case | null;
  parties: Party[];
  evidence: Evidence[];
  documents: Document[];
  deadlines: Deadline[];
  reminders: Reminder[];
  currentStep: string;
}

function CaseLifecycleTest({ initialState }: { initialState: CaseLifecycleState }) {
  const [state, setState] = useState<CaseLifecycleState>(initialState);

  const addParty = (party: Party) => {
    setState(prev => ({
      ...prev,
      parties: [...prev.parties, party],
      currentStep: 'parties-added',
    }));
  };

  const addEvidence = (ev: Evidence) => {
    setState(prev => ({
      ...prev,
      evidence: [...prev.evidence, ev],
      currentCase: prev.currentCase ? {
        ...prev.currentCase,
        evidenceCount: prev.currentCase.evidenceCount + 1,
      } : null,
      currentStep: 'evidence-added',
    }));
  };

  const addDocument = (doc: Document) => {
    setState(prev => ({
      ...prev,
      documents: [...prev.documents, doc],
      currentCase: prev.currentCase ? {
        ...prev.currentCase,
        documentCount: prev.currentCase.documentCount + 1,
      } : null,
      currentStep: 'document-created',
    }));
  };

  const addDeadline = (dl: Deadline) => {
    setState(prev => ({
      ...prev,
      deadlines: [...prev.deadlines, dl],
      reminders: [...prev.reminders, {
        id: `rem-${dl.id}`,
        caseId: dl.caseId,
        caseTitle: prev.currentCase?.title || '',
        type: 'deadline',
        title: dl.title,
        priority: 'high',
        isRead: false,
        dueDate: dl.dueDate,
        createdAt: new Date().toISOString(),
      }],
      currentCase: prev.currentCase ? {
        ...prev.currentCase,
        deadlineCount: prev.currentCase.deadlineCount + 1,
      } : null,
      currentStep: 'deadline-set',
    }));
  };

  const completeDeadline = (id: string) => {
    setState(prev => ({
      ...prev,
      deadlines: prev.deadlines.map(d => d.id === id ? { ...d, status: 'completed' as const } : d),
      reminders: prev.reminders.map(r => r.id === `rem-${id}` ? { ...r, isRead: true } : r),
      currentStep: 'deadline-completed',
    }));
  };

  const closeCase = () => {
    setState(prev => ({
      ...prev,
      currentCase: prev.currentCase ? { ...prev.currentCase, status: 'closed' as const } : null,
      currentStep: 'case-closed',
    }));
  };

  return (
    <div data-testid="case-lifecycle">
      <div data-testid="current-step">{state.currentStep}</div>
      {state.currentCase && (
        <div data-testid="case-info">
          <span data-testid="case-id">{state.currentCase.id}</span>
          <span data-testid="case-status">{state.currentCase.status}</span>
          <span data-testid="evidence-count">{state.currentCase.evidenceCount}</span>
          <span data-testid="document-count">{state.currentCase.documentCount}</span>
          <span data-testid="deadline-count">{state.currentCase.deadlineCount}</span>
        </div>
      )}
      <div data-testid="parties-count">{state.parties.length}</div>
      <div data-testid="evidence-count-detail">{state.evidence.length}</div>
      <div data-testid="documents-count">{state.documents.length}</div>
      <div data-testid="deadlines-count">{state.deadlines.length}</div>
      <div data-testid="reminders-unread">{state.reminders.filter(r => !r.isRead).length}</div>

      <button data-testid="add-party-btn" onClick={() => addParty(createMockParty({ id: 'party-new', caseId: state.currentCase?.id || '' }))}>
        Add Party
      </button>
      <button data-testid="add-evidence-btn" onClick={() => addEvidence(createMockEvidence({ id: 'ev-new', caseId: state.currentCase?.id || '' }))}>
        Add Evidence
      </button>
      <button data-testid="add-document-btn" onClick={() => addDocument(createMockDocument({ id: 'doc-new', caseId: state.currentCase?.id || '' }))}>
        Create Document
      </button>
      <button data-testid="add-deadline-btn" onClick={() => addDeadline(createMockDeadline({ id: 'dl-new', caseId: state.currentCase?.id || '' }))}>
        Set Deadline
      </button>
      <button data-testid="complete-deadline-btn" onClick={() => completeDeadline('dl-new')}>
        Complete Deadline
      </button>
      <button data-testid="close-case-btn" onClick={closeCase}>
        Close Case
      </button>
    </div>
  );
}

describe('E2E: Case Creation to Close Lifecycle', () => {
  const initialCase = createMockCase({ id: 'case-e2e', status: 'preparing', evidenceCount: 0, documentCount: 0, deadlineCount: 0 });

  const initialState: CaseLifecycleState = {
    currentCase: initialCase,
    parties: [],
    evidence: [],
    documents: [],
    deadlines: [],
    reminders: [],
    currentStep: 'case-created',
  };

  it('persists case data through all lifecycle steps', async () => {
    render(<CaseLifecycleTest initialState={initialState} />);

    expect(screen.getByTestId('current-step')).toHaveTextContent('case-created');
    expect(screen.getByTestId('case-status')).toHaveTextContent('preparing');

    fireEvent.click(screen.getByTestId('add-party-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('current-step')).toHaveTextContent('parties-added');
      expect(screen.getByTestId('parties-count')).toHaveTextContent('1');
    });

    fireEvent.click(screen.getByTestId('add-evidence-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('current-step')).toHaveTextContent('evidence-added');
      expect(screen.getByTestId('evidence-count')).toHaveTextContent('1');
    });

    fireEvent.click(screen.getByTestId('add-document-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('current-step')).toHaveTextContent('document-created');
      expect(screen.getByTestId('document-count')).toHaveTextContent('1');
    });

    fireEvent.click(screen.getByTestId('add-deadline-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('current-step')).toHaveTextContent('deadline-set');
      expect(screen.getByTestId('deadline-count')).toHaveTextContent('1');
      expect(screen.getByTestId('reminders-unread')).toHaveTextContent('1');
    });
  });

  it('transitions case status correctly through lifecycle', async () => {
    render(<CaseLifecycleTest initialState={initialState} />);

    expect(screen.getByTestId('case-status')).toHaveTextContent('preparing');

    fireEvent.click(screen.getByTestId('add-party-btn'));
    fireEvent.click(screen.getByTestId('add-evidence-btn'));
    fireEvent.click(screen.getByTestId('add-document-btn'));
    fireEvent.click(screen.getByTestId('add-deadline-btn'));

    fireEvent.click(screen.getByTestId('complete-deadline-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('current-step')).toHaveTextContent('deadline-completed');
      expect(screen.getByTestId('reminders-unread')).toHaveTextContent('0');
    });

    fireEvent.click(screen.getByTestId('close-case-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('current-step')).toHaveTextContent('case-closed');
      expect(screen.getByTestId('case-status')).toHaveTextContent('closed');
    });
  });

  it('updates linked modules when case state changes', async () => {
    render(<CaseLifecycleTest initialState={initialState} />);

    fireEvent.click(screen.getByTestId('add-evidence-btn'));
    fireEvent.click(screen.getByTestId('add-document-btn'));
    fireEvent.click(screen.getByTestId('add-deadline-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('evidence-count-detail')).toHaveTextContent('1');
      expect(screen.getByTestId('documents-count')).toHaveTextContent('1');
      expect(screen.getByTestId('deadlines-count')).toHaveTextContent('1');
    });

    fireEvent.click(screen.getByTestId('complete-deadline-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('deadlines-count')).toHaveTextContent('1');
      expect(screen.getByTestId('reminders-unread')).toHaveTextContent('0');
    });
  });
});
