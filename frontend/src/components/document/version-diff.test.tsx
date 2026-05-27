import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { VersionDiff, VersionHistory } from '@/components/document/version-diff';

const TEXT = {
  comparison: '\u7248\u672c\u5bf9\u6bd4',
  unified: '\u7edf\u4e00',
  split: '\u5e76\u6392',
  close: '\u5173\u95ed',
  history: '\u7248\u672c\u5386\u53f2',
  current: '\u5f53\u524d',
  compareVersions: '\u5bf9\u6bd4\u7248\u672c',
  cancelCompare: '\u53d6\u6d88\u5bf9\u6bd4',
  chooseTwo: '\u9009\u62e9\u4e24\u4e2a\u7248\u672c\u8fdb\u884c\u5bf9\u6bd4',
  compare: '\u5bf9\u6bd4',
  draft: '\u8349\u7a3f',
  review: '\u5ba1\u6838\u4e2d',
  final: '\u5b9a\u7a3f',
};

describe('VersionDiff', () => {
  const mockOldVersion = {
    version: 1,
    content: 'Plaintiff Zhang v Defendant Li\n\nClaims:\n1. Repay principal 100000\n2. Pay interest 5000',
    timestamp: '2026-04-01T10:00:00Z',
    author: 'system',
  };

  const mockNewVersion = {
    version: 2,
    content: 'Plaintiff Zhang, Beijing\nDefendant Li, Beijing\n\nClaims:\n1. Repay principal 100000\n2. Pay interest 5000\n3. Pay litigation costs',
    timestamp: '2026-04-02T10:00:00Z',
    author: 'user',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders version comparison header', () => {
    render(<VersionDiff oldVersion={mockOldVersion} newVersion={mockNewVersion} />);

    expect(screen.getByText(TEXT.comparison)).toBeTruthy();
    expect(screen.getByText(/v1/)).toBeTruthy();
    expect(screen.getByText(/v2/)).toBeTruthy();
  });

  it('displays diff statistics', () => {
    render(<VersionDiff oldVersion={mockOldVersion} newVersion={mockNewVersion} />);

    expect(screen.getByText(/\+\d/)).toBeTruthy();
    expect(screen.getByText(/-\d/)).toBeTruthy();
  });

  it('toggles between unified and split view', () => {
    render(<VersionDiff oldVersion={mockOldVersion} newVersion={mockNewVersion} />);

    expect(screen.getByText(TEXT.unified)).toBeTruthy();
    fireEvent.click(screen.getByText(TEXT.split));
    expect(screen.getByText(TEXT.split)).toBeTruthy();
  });

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn();
    render(<VersionDiff oldVersion={mockOldVersion} newVersion={mockNewVersion} onClose={onClose} />);

    fireEvent.click(screen.getByText(TEXT.close));

    expect(onClose).toHaveBeenCalled();
  });

  it('highlights added lines in green', () => {
    render(<VersionDiff oldVersion={mockOldVersion} newVersion={mockNewVersion} />);

    expect(document.querySelectorAll('.bg-green-50').length).toBeGreaterThan(0);
  });

  it('highlights removed lines in red', () => {
    render(<VersionDiff oldVersion={mockOldVersion} newVersion={mockNewVersion} />);

    expect(document.querySelectorAll('.bg-red-50').length).toBeGreaterThan(0);
  });

  it('renders split view with two columns', () => {
    render(<VersionDiff oldVersion={mockOldVersion} newVersion={mockNewVersion} />);

    fireEvent.click(screen.getByText(TEXT.split));

    expect(document.querySelectorAll('.grid-cols-2 > div').length).toBe(2);
  });
});

describe('VersionHistory', () => {
  const mockVersions = [
    { version: 3, content: 'Version 3 content', timestamp: '2026-04-03T10:00:00Z', author: 'user' },
    { version: 2, content: 'Version 2 content', timestamp: '2026-04-02T10:00:00Z', author: 'AI' },
    { version: 1, content: 'Version 1 content', timestamp: '2026-04-01T10:00:00Z', author: 'system' },
  ];

  it('renders version list', () => {
    render(<VersionHistory versions={mockVersions} currentVersion={3} onSelect={vi.fn()} onCompare={vi.fn()} />);

    expect(screen.getByText(TEXT.history)).toBeTruthy();
    expect(screen.getByText('v3')).toBeTruthy();
    expect(screen.getByText('v2')).toBeTruthy();
    expect(screen.getByText('v1')).toBeTruthy();
  });

  it('marks current version', () => {
    render(<VersionHistory versions={mockVersions} currentVersion={2} onSelect={vi.fn()} onCompare={vi.fn()} />);

    expect(screen.getByText('v2')).toBeTruthy();
    expect(screen.getByText(TEXT.current)).toBeTruthy();
  });

  it('calls onSelect when version is clicked', () => {
    const onSelect = vi.fn();
    render(<VersionHistory versions={mockVersions} currentVersion={3} onSelect={onSelect} onCompare={vi.fn()} />);

    fireEvent.click(screen.getByText('v1').closest('.cursor-pointer')!);

    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it('enters compare mode when compare button is clicked', () => {
    render(<VersionHistory versions={mockVersions} currentVersion={3} onSelect={vi.fn()} onCompare={vi.fn()} />);

    fireEvent.click(screen.getByText(TEXT.compareVersions));

    expect(screen.getByText(TEXT.cancelCompare)).toBeTruthy();
    expect(screen.getByText(new RegExp(TEXT.chooseTwo))).toBeTruthy();
  });

  it('exits compare mode when cancel is clicked', () => {
    render(<VersionHistory versions={mockVersions} currentVersion={3} onSelect={vi.fn()} onCompare={vi.fn()} />);

    fireEvent.click(screen.getByText(TEXT.compareVersions));
    fireEvent.click(screen.getByText(TEXT.cancelCompare));

    expect(screen.getByText(TEXT.compareVersions)).toBeTruthy();
  });

  it('selects two versions for comparison', () => {
    const onCompare = vi.fn();
    render(<VersionHistory versions={mockVersions} currentVersion={3} onSelect={vi.fn()} onCompare={onCompare} />);

    fireEvent.click(screen.getByText(TEXT.compareVersions));
    fireEvent.click(screen.getByText('v1').closest('.cursor-pointer')!);
    fireEvent.click(screen.getByText('v2').closest('.cursor-pointer')!);

    expect(onCompare).toHaveBeenCalledWith(1, 2);
  });

  it('displays formatted dates', () => {
    render(<VersionHistory versions={mockVersions} currentVersion={3} onSelect={vi.fn()} onCompare={vi.fn()} />);

    expect(screen.getByText('2026/4/3')).toBeTruthy();
    expect(screen.getByText('2026/4/2')).toBeTruthy();
  });

  it('shows compare button for non-current versions', () => {
    render(<VersionHistory versions={mockVersions} currentVersion={3} onSelect={vi.fn()} onCompare={vi.fn()} />);

    expect(screen.getAllByText(TEXT.compare).length).toBe(mockVersions.length - 1);
  });

  it('displays version status badges', () => {
    const versionsWithStatus = [
      { version: 1, content: 'Draft', timestamp: '2026-04-01T10:00:00Z', author: 'system', status: 'draft' as const },
      { version: 2, content: 'Review', timestamp: '2026-04-02T10:00:00Z', author: 'user', status: 'review' as const },
      { version: 3, content: 'Final', timestamp: '2026-04-03T10:00:00Z', author: 'admin', status: 'final' as const },
    ];

    render(<VersionHistory versions={versionsWithStatus} currentVersion={3} onSelect={vi.fn()} onCompare={vi.fn()} />);

    expect(screen.getByText(TEXT.draft)).toBeTruthy();
    expect(screen.getByText(TEXT.review)).toBeTruthy();
    expect(screen.getByText(TEXT.final)).toBeTruthy();
  });
});
