import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { AppealArgumentCard } from './appeal-argument-card'

describe('AppealArgumentCard', () => {
  it('renders argument title', () => {
    render(<AppealArgumentCard title="程序违法" type="程序问题" />)
    expect(screen.getByText('程序违法')).toBeInTheDocument()
  })

  it('displays argument type', () => {
    render(<AppealArgumentCard title="程序违法" type="程序问题" />)
    expect(screen.getByText('程序问题')).toBeInTheDocument()
  })

  it('shows success probability when provided', () => {
    render(<AppealArgumentCard title="程序违法" type="程序问题" successProbability={75} />)
    expect(screen.getByText('成功率: 75%')).toBeInTheDocument()
  })

  it('renders progress bar for success probability', () => {
    render(<AppealArgumentCard title="程序违法" type="程序问题" successProbability={75} />)
    const progressBar = document.querySelector('[role="progressbar"]')
    expect(progressBar).toBeInTheDocument()
  })

  it('hides probability section when not provided', () => {
    render(<AppealArgumentCard title="程序违法" type="程序问题" />)
    expect(screen.queryByText(/成功率/)).not.toBeInTheDocument()
  })

  it('hides probability section when explicitly undefined', () => {
    render(<AppealArgumentCard title="程序违法" type="程序问题" successProbability={undefined} />)
    expect(screen.queryByText(/成功率/)).not.toBeInTheDocument()
  })
})
