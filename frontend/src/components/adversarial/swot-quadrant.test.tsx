import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { SwotQuadrant } from './swot-quadrant'

describe('SwotQuadrant', () => {
  const defaultProps = {
    strengths: ['证据充分', '法律依据明确'],
    weaknesses: ['时间紧迫'],
    opponentWeaknesses: ['证据链不完整'],
    opponentStrengths: ['专业律师团队'],
  }

  it('renders all four quadrant headers', () => {
    render(<SwotQuadrant {...defaultProps} />)
    expect(screen.getByText('我方优势')).toBeInTheDocument()
    expect(screen.getByText('我方劣势')).toBeInTheDocument()
    expect(screen.getByText('对方劣势')).toBeInTheDocument()
    expect(screen.getByText('对方优势')).toBeInTheDocument()
  })

  it('displays strength items', () => {
    render(<SwotQuadrant {...defaultProps} />)
    expect(screen.getByText('证据充分')).toBeInTheDocument()
    expect(screen.getByText('法律依据明确')).toBeInTheDocument()
  })

  it('displays weakness items', () => {
    render(<SwotQuadrant {...defaultProps} />)
    expect(screen.getByText('时间紧迫')).toBeInTheDocument()
  })

  it('displays opponent weakness items', () => {
    render(<SwotQuadrant {...defaultProps} />)
    expect(screen.getByText('证据链不完整')).toBeInTheDocument()
  })

  it('displays opponent strength items', () => {
    render(<SwotQuadrant {...defaultProps} />)
    expect(screen.getByText('专业律师团队')).toBeInTheDocument()
  })

  it('renders empty quadrants when arrays are empty', () => {
    render(<SwotQuadrant strengths={[]} weaknesses={[]} opponentWeaknesses={[]} opponentStrengths={[]} />)
    expect(screen.getByText('我方优势')).toBeInTheDocument()
    expect(screen.queryByText('证据充分')).not.toBeInTheDocument()
  })
})
