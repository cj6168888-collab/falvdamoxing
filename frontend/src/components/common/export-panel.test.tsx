import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { ExportPanel } from './export-panel';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

describe('ExportPanel', () => {
  it('renders export button', () => {
    render(
      <ExportPanel
        title="Case Report"
        formats={[{ label: 'PDF', ext: 'pdf' }]}
        onExport={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /导出/ })).toBeInTheDocument();
  });

  it('shows available formats when dialog is open', () => {
    render(
      <ExportPanel
        title="Case Report"
        formats={[
          { label: 'PDF', ext: 'pdf' },
          { label: 'Word', ext: 'docx' },
        ]}
        onExport={vi.fn()}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /导出/ }));

    expect(screen.getByText(/PDF/)).toBeInTheDocument();
    expect(screen.getByText(/Word/)).toBeInTheDocument();
  });

  it('calls onExport with format when format button is clicked', () => {
    const onExport = vi.fn();
    render(
      <ExportPanel
        title="Case Report"
        formats={[
          { label: 'PDF', ext: 'pdf' },
          { label: 'Word', ext: 'docx' },
        ]}
        onExport={onExport}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /导出/ }));

    const formatButtons = screen.getAllByRole('button');
    const pdfButton = formatButtons.find(b => b.textContent?.includes('PDF'));
    fireEvent.click(pdfButton!);

    expect(onExport).toHaveBeenCalledWith('pdf');
  });

  it('shows all format options', () => {
    const formats = [
      { label: 'PDF', ext: 'pdf' },
      { label: 'Word', ext: 'docx' },
      { label: 'Excel', ext: 'xlsx' },
    ];

    render(
      <ExportPanel
        title="Report"
        formats={formats}
        onExport={vi.fn()}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /导出/ }));

    formats.forEach((f) => {
      expect(screen.getByText(new RegExp(f.label))).toBeInTheDocument();
    });
  });
});
