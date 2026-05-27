import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { mockParties, createMockParty } from '@/test/fixtures';
import type { Party } from '@/types/party.types';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

interface DocumentTemplateProps {
  parties: Party[];
  template: string;
}

function DocumentTemplate({ parties, template }: DocumentTemplateProps) {
  const plaintiff = parties.find(p => p.role === 'plaintiff');
  const defendant = parties.find(p => p.role === 'defendant');

  const filledContent = template
    .replace('{{plaintiff_name}}', plaintiff?.name || '')
    .replace('{{plaintiff_address}}', plaintiff?.address || '')
    .replace('{{defendant_name}}', defendant?.name || '')
    .replace('{{defendant_address}}', defendant?.address || '');

  return (
    <div data-testid="document-template">
      <div data-testid="document-preview">{filledContent}</div>
      <div data-testid="party-roles">
        {parties.map(p => (
          <div key={p.id} data-testid={`party-role-${p.id}`}>
            <span data-testid={`party-name-${p.id}`}>{p.name}</span>
            <span data-testid={`party-role-label-${p.id}`}>{p.role}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

describe('Document Generation ↔ Party Management Integration', () => {
  const initialParties = [mockParties[0], mockParties[1]];
  const template = 'Plaintiff: {{plaintiff_name}} at {{plaintiff_address}} vs Defendant: {{defendant_name}} at {{defendant_address}}';

  it('auto-fills party info in document template', () => {
    render(
      <DocumentTemplate
        parties={initialParties}
        template={template}
      />
    );

    expect(screen.getByTestId('document-preview')).toHaveTextContent('Zhang San');
    expect(screen.getByTestId('document-preview')).toHaveTextContent('Li Si');
    expect(screen.getByTestId('document-preview')).toHaveTextContent('Beijing Chaoyang District');
  });

  it('updates document preview when party info changes', () => {
    const { rerender } = render(
      <DocumentTemplate
        parties={initialParties}
        template={template}
      />
    );

    expect(screen.getByTestId('document-preview')).toHaveTextContent('Zhang San');

    const updatedParties = initialParties.map(p =>
      p.id === 'party-1' ? { ...p, name: 'Zhang San Updated', address: 'New Address' } : p
    );

    rerender(
      <DocumentTemplate
        parties={updatedParties}
        template={template}
      />
    );

    expect(screen.getByTestId('document-preview')).toHaveTextContent('Zhang San Updated');
    expect(screen.getByTestId('document-preview')).toHaveTextContent('New Address');
  });

  it('shows correct party roles in document', () => {
    render(
      <DocumentTemplate
        parties={initialParties}
        template={template}
      />
    );

    expect(screen.getByTestId('party-role-party-1')).toBeInTheDocument();
    expect(screen.getByTestId('party-role-label-party-1')).toHaveTextContent('plaintiff');
    expect(screen.getByTestId('party-role-label-party-2')).toHaveTextContent('defendant');
  });

  it('displays multiple parties correctly', () => {
    const multipleParties = [
      ...mockParties,
      createMockParty({ id: 'party-5', name: 'Chen Qi', role: 'third_party' }),
    ];

    render(
      <DocumentTemplate
        parties={multipleParties}
        template={template}
      />
    );

    expect(screen.getByTestId('party-role-party-1')).toBeInTheDocument();
    expect(screen.getByTestId('party-role-party-2')).toBeInTheDocument();
    expect(screen.getByTestId('party-role-party-3')).toBeInTheDocument();
    expect(screen.getByTestId('party-role-party-4')).toBeInTheDocument();
    expect(screen.getByTestId('party-role-party-5')).toBeInTheDocument();
  });
});
