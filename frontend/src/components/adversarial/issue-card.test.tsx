import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@/test/test-utils'
import { IssueCard } from './issue-card'

describe('IssueCard', () => {
  const mockIssue = {
    id: '1',
    caseId: 'case-1',
    title: '证据不足',
    priority: 'high' as const,
    ourPosition: '需要补充关键证据',
    keyEvidence: [],
    status: 'active' as const,
    createdAt: '2024-01-01',
    updatedAt: '2024-01-01',
  }

  const defaultProps = {
    issue: mockIssue,
    onClick: vi.fn(),
  }

  it('renders issue title', () => {
    render(<IssueCard {...defaultProps} />)
    expect(screen.getByText('证据不足')).toBeInTheDocument()
  })

  it('shows priority badge', () => {
    render(<IssueCard {...defaultProps} />)
    expect(screen.getByText('high')).toBeInTheDocument()
  })

  it('displays our position content', () => {
    render(<IssueCard {...defaultProps} />)
    expect(screen.getByText('需要补充关键证据')).toBeInTheDocument()
  })

  it('calls onClick handler when clicked', () => {
    const onClick = vi.fn()
    render(<IssueCard {...defaultProps} onClick={onClick} />)
    fireEvent.click(screen.getByText('证据不足'))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('renders medium priority correctly', () => {
    render(<IssueCard {...defaultProps} issue={{ ...mockIssue, priority: 'medium' }} />)
    expect(screen.getByText('medium')).toBeInTheDocument()
  })

  it('renders low priority correctly', () => {
    render(<IssueCard {...defaultProps} issue={{ ...mockIssue, priority: 'low' }} />)
    expect(screen.getByText('low')).toBeInTheDocument()
  })
})
