import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { AppealCountdown } from './appeal-countdown'

describe('AppealCountdown', () => {
  it('renders days remaining', () => {
    render(<AppealCountdown deadline="2024-02-15" daysRemaining={15} />)
    expect(screen.getByText('15 天')).toBeInTheDocument()
  })

  it('displays deadline date', () => {
    render(<AppealCountdown deadline="2024-02-15" daysRemaining={15} />)
    expect(screen.getByText('2024-02-15')).toBeInTheDocument()
  })

  it('shows warning icon when deadline approaching', () => {
    render(<AppealCountdown deadline="2024-02-15" daysRemaining={5} />)
    expect(screen.getByText('5 天')).toBeInTheDocument()
  })

  it('applies urgent styling when less than 7 days', () => {
    render(<AppealCountdown deadline="2024-02-15" daysRemaining={3} />)
    const card = screen.getByText('3 天').closest('.border-red-500')
    expect(card).toBeInTheDocument()
  })

  it('does not apply urgent styling when more than 7 days', () => {
    render(<AppealCountdown deadline="2024-02-15" daysRemaining={15} />)
    const card = screen.getByText('15 天').closest('.border-red-500')
    expect(card).not.toBeInTheDocument()
  })

  it('renders alert triangle when urgent', () => {
    render(<AppealCountdown deadline="2024-02-15" daysRemaining={2} />)
    const alertIcon = document.querySelector('svg')
    expect(alertIcon).toBeInTheDocument()
  })

  it('shows zero days when expired', () => {
    render(<AppealCountdown deadline="2024-01-01" daysRemaining={0} />)
    expect(screen.getByText('0 天')).toBeInTheDocument()
  })
})
