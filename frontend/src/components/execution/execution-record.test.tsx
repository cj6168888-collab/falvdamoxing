import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { ExecutionRecordList } from './execution-record'

vi.mock('@/lib/date', () => ({
  formatChineseDate: (date: string) => date,
}))

describe('ExecutionRecordList', () => {
  const mockRecords = [
    { date: '2024-01-15', type: '冻结账户', amount: 50000, description: '冻结被告银行账户' },
    { date: '2024-02-20', type: '划扣款项', amount: 30000, description: '', operator: '张法官' },
  ]

  it('renders record list title', () => {
    render(<ExecutionRecordList records={mockRecords} />)
    expect(screen.getByText('执行记录')).toBeInTheDocument()
  })

  it('displays record types', () => {
    render(<ExecutionRecordList records={mockRecords} />)
    expect(screen.getByText('冻结账户')).toBeInTheDocument()
    expect(screen.getByText('划扣款项')).toBeInTheDocument()
  })

  it('displays record amounts', () => {
    render(<ExecutionRecordList records={mockRecords} />)
    expect(screen.getByText(/¥50,000/)).toBeInTheDocument()
    expect(screen.getByText(/¥30,000/)).toBeInTheDocument()
  })

  it('displays record descriptions', () => {
    render(<ExecutionRecordList records={mockRecords} />)
    expect(screen.getByText('冻结被告银行账户')).toBeInTheDocument()
  })

  it('shows empty state when no records', () => {
    render(<ExecutionRecordList records={[]} />)
    expect(screen.getByText('暂无记录')).toBeInTheDocument()
  })

  it('handles records without amount', () => {
    const recordsWithoutAmount = [{ date: '2024-03-01', type: '现场调查', description: '前往被告住所' }]
    render(<ExecutionRecordList records={recordsWithoutAmount} />)
    expect(screen.getByText('现场调查')).toBeInTheDocument()
    expect(screen.queryByText(/¥/)).not.toBeInTheDocument()
  })
})
