import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { AppealMilestone } from './appeal-milestone'

describe('AppealMilestone', () => {
  it('renders milestone title', () => {
    render(<AppealMilestone completedCount={0} />)
    expect(screen.getByText('上诉里程碑')).toBeInTheDocument()
  })

  it('renders all five milestones', () => {
    render(<AppealMilestone completedCount={0} />)
    expect(screen.getByText('递交上诉状')).toBeInTheDocument()
    expect(screen.getByText('缴纳上诉费')).toBeInTheDocument()
    expect(screen.getByText('提交答辩状')).toBeInTheDocument()
    expect(screen.getByText('二审开庭')).toBeInTheDocument()
    expect(screen.getByText('二审判决')).toBeInTheDocument()
  })

  it('shows completed milestones with checkmark', () => {
    render(<AppealMilestone completedCount={2} />)
    const completedItems = document.querySelectorAll('.text-green-600')
    expect(completedItems).toHaveLength(2)
  })

  it('shows pending milestones with circle', () => {
    render(<AppealMilestone completedCount={2} />)
    const pendingItems = document.querySelectorAll('.text-muted-foreground')
    expect(pendingItems.length).toBeGreaterThanOrEqual(3)
  })

  it('shows all completed when count is 5', () => {
    render(<AppealMilestone completedCount={5} />)
    const completedItems = document.querySelectorAll('.text-green-600')
    expect(completedItems).toHaveLength(5)
  })

  it('shows all pending when count is 0', () => {
    render(<AppealMilestone completedCount={0} />)
    const completedItems = document.querySelectorAll('.text-green-600')
    expect(completedItems).toHaveLength(0)
  })
})
