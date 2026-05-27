import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@/test/test-utils'
import { CrossExaminationPanel } from './cross-examination-panel'

describe('CrossExaminationPanel', () => {
  it('renders evidence name', () => {
    render(<CrossExaminationPanel evidenceName="合同原件" onSubmit={vi.fn()} />)
    expect(screen.getByText('合同原件')).toBeInTheDocument()
  })

  it('renders three nature opinion selectors', () => {
    render(<CrossExaminationPanel evidenceName="合同原件" onSubmit={vi.fn()} />)
    expect(screen.getByText('真实性')).toBeInTheDocument()
    expect(screen.getByText('合法性')).toBeInTheDocument()
    expect(screen.getByText('关联性')).toBeInTheDocument()
  })

  it('renders opinion textarea', () => {
    render(<CrossExaminationPanel evidenceName="合同原件" onSubmit={vi.fn()} />)
    expect(screen.getByPlaceholderText('质证意见...')).toBeInTheDocument()
  })

  it('calls onSubmit with opinion data when save is clicked', () => {
    const onSubmit = vi.fn()
    render(<CrossExaminationPanel evidenceName="合同原件" onSubmit={onSubmit} />)
    fireEvent.click(screen.getByText('保存'))
    expect(onSubmit).toHaveBeenCalledWith({
      authenticity: '认可',
      legality: '认可',
      relevance: '认可',
      opinion: '',
    })
  })

  it('calls onSubmit with custom opinion when textarea filled', () => {
    const onSubmit = vi.fn()
    render(<CrossExaminationPanel evidenceName="合同原件" onSubmit={onSubmit} />)
    const textarea = screen.getByPlaceholderText('质证意见...')
    fireEvent.change(textarea, { target: { value: '该证据真实性存疑' } })
    fireEvent.click(screen.getByText('保存'))
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ opinion: '该证据真实性存疑' })
    )
  })
})
