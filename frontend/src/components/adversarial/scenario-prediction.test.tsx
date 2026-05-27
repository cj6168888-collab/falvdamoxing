import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { ScenarioPrediction } from './scenario-prediction'

describe('ScenarioPrediction', () => {
  const mockScenarios = [
    { scenario: '胜诉', probability: 60, description: '法院支持我方全部诉求' },
    { scenario: '部分胜诉', probability: 30, description: '法院支持部分诉求' },
    { scenario: '败诉', probability: 10, description: '法院驳回全部诉求' },
  ]

  it('renders scenario names', () => {
    render(<ScenarioPrediction scenarios={mockScenarios} />)
    expect(screen.getByText('胜诉')).toBeInTheDocument()
    expect(screen.getByText('部分胜诉')).toBeInTheDocument()
    expect(screen.getByText('败诉')).toBeInTheDocument()
  })

  it('displays probability percentages', () => {
    render(<ScenarioPrediction scenarios={mockScenarios} />)
    expect(screen.getByText('60%')).toBeInTheDocument()
    expect(screen.getByText('30%')).toBeInTheDocument()
    expect(screen.getByText('10%')).toBeInTheDocument()
  })

  it('shows scenario descriptions', () => {
    render(<ScenarioPrediction scenarios={mockScenarios} />)
    expect(screen.getByText('法院支持我方全部诉求')).toBeInTheDocument()
    expect(screen.getByText('法院支持部分诉求')).toBeInTheDocument()
    expect(screen.getByText('法院驳回全部诉求')).toBeInTheDocument()
  })

  it('renders progress bars for each scenario', () => {
    render(<ScenarioPrediction scenarios={mockScenarios} />)
    const progressBars = document.querySelectorAll('[role="progressbar"]')
    expect(progressBars).toHaveLength(3)
  })

  it('shows empty state when no scenarios', () => {
    render(<ScenarioPrediction scenarios={[]} />)
    expect(screen.getByText('暂无预测数据')).toBeInTheDocument()
  })

  it('shows empty state when scenarios is null', () => {
    render(<ScenarioPrediction scenarios={null as unknown as []} />)
    expect(screen.getByText('暂无预测数据')).toBeInTheDocument()
  })
})
