import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { ScenarioPrediction } from './scenario-prediction'

describe('ScenarioPrediction', () => {
  const mockScenarios = [
    { scenario: '胜诉', probability: 60, description: '法院支持我方全部诉求' },
    { scenario: '部分胜诉', probability: 30, description: '法院支持部分诉求' },
    { scenario: '败诉', probability: 10, description: '法院驳回全部诉求' },
  ]

  it('renders reviewable support-reference labels instead of outcome promises', () => {
    render(<ScenarioPrediction scenarios={mockScenarios} />)
    expect(screen.getByText('裁判支持度参考')).toBeInTheDocument()
    expect(screen.getByText('我方主张获较高支持')).toBeInTheDocument()
    expect(screen.getByText('我方主张获部分支持')).toBeInTheDocument()
    expect(screen.getByText('我方主张未获支持')).toBeInTheDocument()
    expect(screen.queryByText('胜诉')).not.toBeInTheDocument()
    expect(screen.queryByText('部分胜诉')).not.toBeInTheDocument()
    expect(screen.queryByText('败诉')).not.toBeInTheDocument()
  })

  it('displays support-reference percentages', () => {
    render(<ScenarioPrediction scenarios={mockScenarios} />)
    expect(screen.getByText('支持度参考 60%')).toBeInTheDocument()
    expect(screen.getByText('支持度参考 30%')).toBeInTheDocument()
    expect(screen.getByText('支持度参考 10%')).toBeInTheDocument()
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
    expect(screen.getByText('暂无情景参考数据')).toBeInTheDocument()
  })

  it('shows empty state when scenarios is null', () => {
    render(<ScenarioPrediction scenarios={null as unknown as []} />)
    expect(screen.getByText('暂无情景参考数据')).toBeInTheDocument()
  })
})
