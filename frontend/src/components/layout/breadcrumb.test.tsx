import { render, screen } from '@testing-library/react';
import { Breadcrumb } from './breadcrumb';
import { MemoryRouter } from 'react-router-dom';

const renderWithRouter = (ui: React.ReactElement) => {
  return render(
    <MemoryRouter future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
      {ui}
    </MemoryRouter>
  );
};

describe('Breadcrumb', () => {
  it('renders single item without link', () => {
    renderWithRouter(<Breadcrumb items={[{ label: '首页' }]} />);
    expect(screen.getByText('首页')).toBeInTheDocument();
  });

  it('renders multiple items with links', () => {
    renderWithRouter(
      <Breadcrumb items={[
        { label: '首页', href: '/' },
        { label: '案件', href: '/cases' },
        { label: '详情' },
      ]} />
    );
    expect(screen.getByText('首页')).toBeInTheDocument();
    expect(screen.getByText('案件')).toBeInTheDocument();
    expect(screen.getByText('详情')).toBeInTheDocument();
  });

  it('renders separator icons between items', () => {
    renderWithRouter(
      <Breadcrumb items={[
        { label: '首页', href: '/' },
        { label: '案件' },
      ]} />
    );
    // ChevronRight icons should be present
    const chevrons = document.querySelectorAll('svg');
    expect(chevrons.length).toBeGreaterThan(0);
  });
});
