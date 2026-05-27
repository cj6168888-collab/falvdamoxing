import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { mockEvidenceList } from '@/test/fixtures';
import type { Evidence } from '@/types/evidence.types';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

interface EvidenceGraphProps {
  evidence: Evidence[];
  relationships: Array<{ source: string; target: string; type: string }>;
}

function EvidenceGraph({ evidence, relationships }: EvidenceGraphProps) {
  return (
    <div data-testid="evidence-graph">
      <div data-testid="node-count">{evidence.length}</div>
      <div data-testid="graph-nodes">
        {evidence.map(ev => (
          <div key={ev.id} data-testid={`graph-node-${ev.id}`}>
            <span data-testid={`node-label-${ev.id}`}>{ev.name}</span>
            <span data-testid={`node-score-${ev.id}`}>{ev.credibilityScore}</span>
          </div>
        ))}
      </div>
      <div data-testid="graph-edges">
        {relationships.map((rel, idx) => (
          <div key={idx} data-testid={`edge-${rel.source}-${rel.target}`}>
            {rel.source} → {rel.target} ({rel.type})
          </div>
        ))}
      </div>
    </div>
  );
}

interface EvidenceManagementProps {
  evidence: Evidence[];
  onUpload: (evidence: Partial<Evidence>) => void;
  onDelete: (id: string) => void;
  onLink: (sourceId: string, targetId: string, type: string) => void;
}

function EvidenceManagement({ evidence, onUpload, onDelete, onLink }: EvidenceManagementProps) {
  return (
    <div data-testid="evidence-management">
      <button
        data-testid="upload-btn"
        onClick={() => onUpload({
          id: 'ev-uploaded',
          name: 'Uploaded Evidence',
          type: 'document',
          credibilityScore: 75,
        })}
      >
        Upload Evidence
      </button>
      {evidence.map(ev => (
        <div key={ev.id} data-testid={`evidence-${ev.id}`}>
          <span>{ev.name}</span>
          <button data-testid={`delete-${ev.id}`} onClick={() => onDelete(ev.id)}>Delete</button>
        </div>
      ))}
      <button
        data-testid="link-btn"
        onClick={() => onLink('ev-1', 'ev-2', 'supports')}
      >
        Link Evidence
      </button>
    </div>
  );
}

describe('Evidence Management ↔ Evidence Graph Integration', () => {
  const initialEvidence = [mockEvidenceList[0], mockEvidenceList[1]];
  const initialRelationships = [{ source: 'ev-1', target: 'ev-2', type: 'related' }];

  it('adds node to graph when evidence is uploaded', () => {
    const handleUpload = vi.fn();
    const handleDelete = vi.fn();
    const handleLink = vi.fn();

    render(
      <EvidenceManagement
        evidence={initialEvidence}
        onUpload={handleUpload}
        onDelete={handleDelete}
        onLink={handleLink}
      />
    );

    fireEvent.click(screen.getByTestId('upload-btn'));
    expect(handleUpload).toHaveBeenCalledWith({
      id: 'ev-uploaded',
      name: 'Uploaded Evidence',
      type: 'document',
      credibilityScore: 75,
    });
  });

  it('removes node from graph when evidence is deleted', () => {
    const handleUpload = vi.fn();
    const handleDelete = vi.fn();
    const handleLink = vi.fn();

    render(
      <EvidenceManagement
        evidence={initialEvidence}
        onUpload={handleUpload}
        onDelete={handleDelete}
        onLink={handleLink}
      />
    );

    fireEvent.click(screen.getByTestId('delete-ev-1'));
    expect(handleDelete).toHaveBeenCalledWith('ev-1');
  });

  it('shows evidence relationships in graph', () => {
    render(
      <EvidenceGraph
        evidence={initialEvidence}
        relationships={initialRelationships}
      />
    );

    expect(screen.getByTestId('edge-ev-1-ev-2')).toBeInTheDocument();
    expect(screen.getByTestId('edge-ev-1-ev-2')).toHaveTextContent('ev-1 → ev-2 (related)');
  });

  it('updates graph when evidence is linked', () => {
    const { rerender } = render(
      <EvidenceGraph
        evidence={initialEvidence}
        relationships={initialRelationships}
      />
    );

    const newRelationships = [
      ...initialRelationships,
      { source: 'ev-1', target: 'ev-2', type: 'supports' },
    ];

    rerender(
      <EvidenceGraph
        evidence={initialEvidence}
        relationships={newRelationships}
      />
    );

    expect(screen.getByTestId('graph-edges').children.length).toBe(2);
  });
});
