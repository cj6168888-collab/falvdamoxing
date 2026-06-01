import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { EnterpriseDashboard, PersonalDashboard } from './audience-dashboards';

describe('audience dashboards', () => {
  it('frames the enterprise dashboard as a legal counsel workspace', () => {
    render(
      <MemoryRouter>
        <EnterpriseDashboard />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: '企业法律顾问工作台' })).toBeInTheDocument();
    expect(screen.getByText('靠谱的法律顾问感', { exact: false })).toBeInTheDocument();
    expect(screen.getByText('律师协作')).toBeInTheDocument();
  });

  it('frames the personal dashboard as a legal backstop instead of lawyer handoff', () => {
    render(
      <MemoryRouter>
        <PersonalDashboard />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: '个人法律后盾' })).toBeInTheDocument();
    expect(screen.getByText('先把人扶住', { exact: false })).toBeInTheDocument();
    expect(screen.getByText('获得下一步清单')).toBeInTheDocument();
  });
});
