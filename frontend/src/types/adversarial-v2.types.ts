// 增强的对抗性分析类型

export type AdversarialMode = 
  | 'question_preparation'   // 询问准备模式
  | 'cross_examination'       // 交叉询问模式  
  | 'strategy_planning';     // 策略规划模式

export type CourtRole = 
  | 'plaintiff'     // 原告
  | 'defendant'     // 被告
  | 'lawyer'        // 律师
  | 'judge';        // 法官

export interface Issue {
  id: string;
  caseId: string;
  title: string;
  description: string;
  ourPosition: string;
  opponentAttack?: string;
  keyEvidence?: string[];
  strategy?: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'prepared' | 'completed';
}

export interface SwotAnalysis {
  strengths: SwotItem[];
  weaknesses: SwotItem[];
  opponentWeaknesses: SwotItem[];
  opponentStrengths: SwotItem[];
}

export interface SwotItem {
  id: string;
  content: string;
  impact: 'high' | 'medium' | 'low';
  evidence?: string[];
}

export interface ScenarioPrediction {
  id: string;
  scenario: string;
  probability: number;  // 0-100
  description: string;
  counterMeasures?: string;
  evidence?: string[];
}

export interface CourtSession {
  id: string;
  caseId: string;
  date: string;
  court: string;
  judge: string;
  ourPosition: string;
  opponentPosition: string;
  keyIssues: string[];
  questions?: CourtQuestion[];
  notes?: string;
  recording?: string;
  status: 'upcoming' | 'in_progress' | 'completed';
}

export interface CourtQuestion {
  id: string;
  question: string;
  type: 'open' | 'closed' | 'leading' | 'hypothetical';
  purpose: string;
  expectedAnswer?: string;
  isPrepared: boolean;
  difficulty: 'easy' | 'medium' | 'hard';
  suggestedResponse?: string;
}

export interface CrossExaminationTarget {
  id: string;
  name: string;
  role: 'witness' | 'expert' | 'party';
  credibility?: number;
  statements: WitnessStatement[];
  vulnerabilities?: string[];
}

export interface WitnessStatement {
  id: string;
  statement: string;
  date: string;
  source: 'deposition' | 'hearing' | 'document';
  isFavorable: boolean;
  canImpeach: boolean;
  impeachmentEvidence?: string;
}

export interface TTSConfig {
  enabled: boolean;
  voice: 'female' | 'male';
  speed: number;  // 0.5 - 2.0
  pitch: number;  // 0.5 - 2.0
}

export interface VoicePrintConfig {
  enabled: boolean;
  speakerCount: number;
  identifySpeakers: boolean;
}

// 抗辩模式配置
export interface AdversarialModeConfig {
  mode: AdversarialMode;
  label: string;
  description: string;
  icon: string;
  steps: ModeStep[];
}

export interface ModeStep {
  id: string;
  title: string;
  description: string;
  isCompleted: boolean;
  isRequired: boolean;
}

export const ADVERSARIAL_MODES: AdversarialModeConfig[] = [
  {
    mode: 'question_preparation',
    label: '询问准备',
    description: '准备向对方提问的问题清单',
    icon: '❓',
    steps: [
      { id: 'q1', title: '确定询问目标', description: '明确每个问题的目的', isCompleted: false, isRequired: true },
      { id: 'q2', title: '编写问题清单', description: '按逻辑顺序排列问题', isCompleted: false, isRequired: true },
      { id: 'q3', title: '预判对方回答', description: '针对每个问题预设回答', isCompleted: false, isRequired: false },
      { id: 'q4', title: '准备追问要点', description: '设计可能的追问', isCompleted: false, isRequired: false },
    ],
  },
  {
    mode: 'cross_examination',
    label: '交叉询问',
    description: '针对证人/专家证人的询问策略',
    icon: '🎯',
    steps: [
      { id: 'c1', title: '分析证人陈述', description: '找出矛盾和漏洞', isCompleted: false, isRequired: true },
      { id: 'c2', title: '制定询问策略', description: '选择攻击角度', isCompleted: false, isRequired: true },
      { id: 'c3', title: '准备质证材料', description: '收集反驳证据', isCompleted: false, isRequired: true },
      { id: 'c4', title: '模拟询问演练', description: '预演询问过程', isCompleted: false, isRequired: false },
    ],
  },
  {
    mode: 'strategy_planning',
    label: '策略规划',
    description: '整体诉讼策略和应对方案',
    icon: '🎯',
    steps: [
      { id: 's1', title: 'SWOT分析', description: '分析双方优劣势', isCompleted: false, isRequired: true },
      { id: 's2', title: '场景预测', description: '预测可能的诉讼走向', isCompleted: false, isRequired: true },
      { id: 's3', title: '制定应对方案', description: '为每种情况准备方案', isCompleted: false, isRequired: true },
      { id: 's4', title: '模拟演练', description: '整体诉讼流程演练', isCompleted: false, isRequired: false },
    ],
  },
];

// 紧急接管配置
export interface EmergencyOverrideConfig {
  enabled: boolean;
  triggerConditions: {
    speakerDetected: boolean;
    keyEvidenceMentioned: boolean;
    hostileQuestion: boolean;
    emotionalEscalation: boolean;
  };
  autoActions: {
    alertLawyer: boolean;
    showReminder: boolean;
    voiceReminder: boolean;
  };
}
