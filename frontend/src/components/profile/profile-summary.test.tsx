import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { ProfileSummary } from './profile-summary';
import * as profileHooks from '@/hooks/use-profile';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

function mockProfileResult(
  profile: unknown,
  isLoading = false
): ReturnType<typeof profileHooks.useCaseProfile> {
  return { profile, isLoading, isError: false } as unknown as ReturnType<typeof profileHooks.useCaseProfile>;
}

describe('ProfileSummary', () => {
  it('renders profile summary information', () => {
    vi.spyOn(profileHooks, 'useCaseProfile').mockReturnValue(mockProfileResult({
      caseId: 'case-1',
      summary: 'Test summary',
      coreDispute: 'Loan delivery dispute',
      keyEvidence: ['Contract', 'Receipt'],
      winProbability: 75,
      riskLevel: 'medium',
      userPreferences: [],
      commonDocuments: [],
      focusAreas: [],
      evidenceGaps: [],
      lastUpdated: '2024-01-01',
    }));

    render(<ProfileSummary caseId="case-1" />);

    expect(screen.getByText('Loan delivery dispute')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
    expect(screen.getByText('medium')).toBeInTheDocument();
  });

  it('shows win probability', () => {
    vi.spyOn(profileHooks, 'useCaseProfile').mockReturnValue(mockProfileResult({
      caseId: 'case-1',
      summary: 'Test',
      coreDispute: 'Test dispute',
      keyEvidence: [],
      winProbability: 85,
      riskLevel: 'low',
      userPreferences: [],
      commonDocuments: [],
      focusAreas: [],
      evidenceGaps: [],
      lastUpdated: '2024-01-01',
    }));

    render(<ProfileSummary caseId="case-1" />);

    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  it('shows risk level', () => {
    vi.spyOn(profileHooks, 'useCaseProfile').mockReturnValue(mockProfileResult({
      caseId: 'case-1',
      summary: 'Test',
      coreDispute: 'Test dispute',
      keyEvidence: [],
      winProbability: 50,
      riskLevel: 'high',
      userPreferences: [],
      commonDocuments: [],
      focusAreas: [],
      evidenceGaps: [],
      lastUpdated: '2024-01-01',
    }));

    render(<ProfileSummary caseId="case-1" />);

    expect(screen.getByText('high')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    vi.spyOn(profileHooks, 'useCaseProfile').mockReturnValue(mockProfileResult(null, true));

    render(<ProfileSummary caseId="case-1" />);

    expect(screen.queryByText('案件画像')).not.toBeInTheDocument();
  });

  it('shows empty state when no profile data', () => {
    vi.spyOn(profileHooks, 'useCaseProfile').mockReturnValue(mockProfileResult(null));

    render(<ProfileSummary caseId="case-1" />);

    expect(screen.getByText('暂无画像数据')).toBeInTheDocument();
  });
});
