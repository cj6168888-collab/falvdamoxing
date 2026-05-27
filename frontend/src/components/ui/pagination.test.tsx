import { render, screen, fireEvent } from '@testing-library/react';
import { Pagination } from './pagination';

describe('Pagination', () => {
  it('renders current page and total pages', () => {
    render(<Pagination page={2} totalPages={10} onPageChange={() => {}} />);
    expect(screen.getByText('2 / 10')).toBeInTheDocument();
  });

  it('disables previous button on first page', () => {
    render(<Pagination page={1} totalPages={5} onPageChange={() => {}} />);
    const prevButton = screen.getAllByRole('button')[0];
    expect(prevButton).toBeDisabled();
  });

  it('disables next button on last page', () => {
    render(<Pagination page={5} totalPages={5} onPageChange={() => {}} />);
    const nextButton = screen.getAllByRole('button')[1];
    expect(nextButton).toBeDisabled();
  });

  it('calls onPageChange when previous button clicked', () => {
    const handleChange = vi.fn();
    render(<Pagination page={3} totalPages={10} onPageChange={handleChange} />);
    const prevButton = screen.getAllByRole('button')[0];
    fireEvent.click(prevButton);
    expect(handleChange).toHaveBeenCalledWith(2);
  });

  it('calls onPageChange when next button clicked', () => {
    const handleChange = vi.fn();
    render(<Pagination page={3} totalPages={10} onPageChange={handleChange} />);
    const nextButton = screen.getAllByRole('button')[1];
    fireEvent.click(nextButton);
    expect(handleChange).toHaveBeenCalledWith(4);
  });
});
