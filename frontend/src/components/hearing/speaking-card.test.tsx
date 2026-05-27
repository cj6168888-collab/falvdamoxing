import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { SpeakingCard } from './speaking-card'

describe('SpeakingCard', () => {
  const defaultProps = {
    title: '原告陈述',
    content: '我方认为被告存在违约行为',
  }

  it('renders speaker title', () => {
    render(<SpeakingCard {...defaultProps} />)
    expect(screen.getByText('原告陈述')).toBeInTheDocument()
  })

  it('displays speaking content', () => {
    render(<SpeakingCard {...defaultProps} />)
    expect(screen.getByText('我方认为被告存在违约行为')).toBeInTheDocument()
  })

  it('renders gavel icon', () => {
    render(<SpeakingCard {...defaultProps} />)
    const iconContainer = document.querySelector('svg')
    expect(iconContainer).toBeInTheDocument()
  })

  it('handles multiline content with whitespace preservation', () => {
    const multilineContent = '第一点：违约事实\n第二点：损失计算'
    render(<SpeakingCard {...defaultProps} content={multilineContent} />)
    expect(screen.getByText(/第一点：违约事实/)).toBeInTheDocument()
  })

  it('renders with empty content', () => {
    render(<SpeakingCard {...defaultProps} content="" />)
    expect(screen.getByText('原告陈述')).toBeInTheDocument()
  })
})
