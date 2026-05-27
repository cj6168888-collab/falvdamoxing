import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { ExecutionProgress } from './execution-progress'

describe('ExecutionProgress', () => {
  it('renders progress title', () => {
    render(<ExecutionProgress totalAmount={100000} executedAmount={50000} />)
    expect(screen.getByText('执行进度')).toBeInTheDocument()
  })

  it('displays total amount', () => {
    render(<ExecutionProgress totalAmount={100000} executedAmount={50000} />)
    expect(screen.getByText('¥100,000')).toBeInTheDocument()
  })

  it('displays executed amount', () => {
    render(<ExecutionProgress totalAmount={100000} executedAmount={30000} />)
    expect(screen.getByText('¥30,000')).toBeInTheDocument()
  })

  it('displays remaining amount', () => {
    render(<ExecutionProgress totalAmount={100000} executedAmount={30000} />)
    expect(screen.getByText('¥70,000')).toBeInTheDocument()
  })

  it('renders progress bar', () => {
    render(<ExecutionProgress totalAmount={100000} executedAmount={50000} />)
    const progressBar = document.querySelector('[role="progressbar"]')
    expect(progressBar).toBeInTheDocument()
  })

  it('handles zero total amount', () => {
    render(<ExecutionProgress totalAmount={0} executedAmount={0} />)
    expect(screen.getByText('执行进度')).toBeInTheDocument()
  })
})
