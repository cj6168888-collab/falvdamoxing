import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@/test/test-utils'
import { TrapDetector } from './trap-detector'

describe('TrapDetector', () => {
  it('renders trap detector title', () => {
    render(<TrapDetector onDetect={vi.fn()} />)
    expect(screen.getByText('法庭陷阱识别')).toBeInTheDocument()
  })

  it('renders textarea for input', () => {
    render(<TrapDetector onDetect={vi.fn()} />)
    const textarea = screen.getByPlaceholderText('输入对方发言...')
    expect(textarea).toBeInTheDocument()
  })

  it('renders detect button', () => {
    render(<TrapDetector onDetect={vi.fn()} />)
    expect(screen.getByText('检测')).toBeInTheDocument()
  })

  it('calls onDetect with textarea content when button clicked', () => {
    const onDetect = vi.fn()
    render(<TrapDetector onDetect={onDetect} />)
    const textarea = screen.getByPlaceholderText('输入对方发言...')
    fireEvent.change(textarea, { target: { value: '对方发言内容' } })
    fireEvent.click(screen.getByText('检测'))
    expect(onDetect).toHaveBeenCalledWith('对方发言内容')
  })

  it('displays detection result when provided', () => {
    const result = { type: '诱导性提问', suggestion: '请保持冷静，不要直接回答' }
    render(<TrapDetector onDetect={vi.fn()} result={result} />)
    expect(screen.getByText('诱导性提问')).toBeInTheDocument()
    expect(screen.getByText('请保持冷静，不要直接回答')).toBeInTheDocument()
  })

  it('does not show result when not provided', () => {
    render(<TrapDetector onDetect={vi.fn()} />)
    expect(screen.queryByText('诱导性提问')).not.toBeInTheDocument()
  })
})
