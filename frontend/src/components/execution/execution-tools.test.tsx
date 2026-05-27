import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@/test/test-utils'
import { ExecutionTools } from './execution-tools'

describe('ExecutionTools', () => {
  it('renders tools title', () => {
    render(<ExecutionTools onAction={vi.fn()} />)
    expect(screen.getByText('执行辅助工具')).toBeInTheDocument()
  })

  it('renders all five tool buttons', () => {
    render(<ExecutionTools onAction={vi.fn()} />)
    expect(screen.getByText('申请执行')).toBeInTheDocument()
    expect(screen.getByText('财产保全')).toBeInTheDocument()
    expect(screen.getByText('限制高消费')).toBeInTheDocument()
    expect(screen.getByText('纳入失信')).toBeInTheDocument()
    expect(screen.getByText('执行和解')).toBeInTheDocument()
  })

  it('calls onAction with apply when 申请执行 clicked', () => {
    const onAction = vi.fn()
    render(<ExecutionTools onAction={onAction} />)
    fireEvent.click(screen.getByText('申请执行'))
    expect(onAction).toHaveBeenCalledWith('apply')
  })

  it('calls onAction with preserve when 财产保全 clicked', () => {
    const onAction = vi.fn()
    render(<ExecutionTools onAction={onAction} />)
    fireEvent.click(screen.getByText('财产保全'))
    expect(onAction).toHaveBeenCalledWith('preserve')
  })

  it('calls onAction with settle when 执行和解 clicked', () => {
    const onAction = vi.fn()
    render(<ExecutionTools onAction={onAction} />)
    fireEvent.click(screen.getByText('执行和解'))
    expect(onAction).toHaveBeenCalledWith('settle')
  })

  it('renders icons for each tool', () => {
    render(<ExecutionTools onAction={vi.fn()} />)
    const buttons = screen.getAllByRole('button')
    expect(buttons).toHaveLength(5)
  })
})
