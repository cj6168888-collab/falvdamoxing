import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@/test/test-utils'
import { ActionPlan } from './action-plan'

describe('ActionPlan', () => {
  const mockActions = ['补充证据材料', '申请证人出庭', '提交代理词']

  it('renders all action items', () => {
    render(<ActionPlan actions={mockActions} onAction={vi.fn()} />)
    expect(screen.getByText('补充证据材料')).toBeInTheDocument()
    expect(screen.getByText('申请证人出庭')).toBeInTheDocument()
    expect(screen.getByText('提交代理词')).toBeInTheDocument()
  })

  it('displays execute button for each action', () => {
    render(<ActionPlan actions={mockActions} onAction={vi.fn()} />)
    const buttons = screen.getAllByText('执行')
    expect(buttons).toHaveLength(3)
  })

  it('calls onAction handler when execute button is clicked', () => {
    const onAction = vi.fn()
    render(<ActionPlan actions={mockActions} onAction={onAction} />)
    const buttons = screen.getAllByText('执行')
    fireEvent.click(buttons[0])
    expect(onAction).toHaveBeenCalledWith('补充证据材料')
    expect(onAction).toHaveBeenCalledTimes(1)
  })

  it('calls onAction with correct action for second item', () => {
    const onAction = vi.fn()
    render(<ActionPlan actions={mockActions} onAction={onAction} />)
    const buttons = screen.getAllByText('执行')
    fireEvent.click(buttons[1])
    expect(onAction).toHaveBeenCalledWith('申请证人出庭')
  })

  it('renders empty state when no actions', () => {
    render(<ActionPlan actions={[]} onAction={vi.fn()} />)
    expect(screen.queryByText('执行')).not.toBeInTheDocument()
  })
})
