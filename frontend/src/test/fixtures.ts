import type { Case } from '@/types/case.types';
import type { Evidence } from '@/types/evidence.types';
import type { Document } from '@/types/document.types';
import type { Deadline } from '@/types/deadline.types';
import type { Party } from '@/types/party.types';
import type { CaseThread } from '@/types/thread.types';
import type { Letter } from '@/types/letter.types';
import type { TimelineEvent } from '@/types/timeline.types';
import type { Hearing } from '@/types/hearing.types';
import type { ProfileSummary } from '@/types/profile.types';
import type { Issue, SwotAnalysis } from '@/types/adversarial.types';
import type { Appeal } from '@/types/appeal.types';
import type { Execution } from '@/types/execution.types';

export function createMockCase(overrides: Partial<Case> = {}): Case {
  return {
    id: 'case-1',
    title: 'Loan Dispute Case',
    type: 'civil',
    status: 'litigating',
    description: 'Loan dispute case',
    amount: 500000,
    plaintiff: { name: 'Zhang San', phone: '13800138000' },
    defendant: { name: 'Li Si', phone: '13900139000' },
    evidenceCount: 5,
    documentCount: 3,
    deadlineCount: 3,
    createdAt: '2024-01-10T10:00:00Z',
    updatedAt: '2024-03-15T14:30:00Z',
    ...overrides,
  };
}

export function createMockEvidence(overrides: Partial<Evidence> = {}): Evidence {
  return {
    id: 'ev-1',
    caseId: 'case-1',
    name: 'Loan Contract',
    type: 'document',
    source: 'own',
    description: 'Loan contract original',
    credibilityScore: 85,
    fileSize: 2048000,
    fileType: 'application/pdf',
    createdAt: '2024-01-20T10:00:00Z',
    updatedAt: '2024-01-20T10:00:00Z',
    ...overrides,
  };
}

export function createMockDocument(overrides: Partial<Document> = {}): Document {
  return {
    id: 'doc-1',
    caseId: 'case-1',
    title: 'Complaint',
    type: 'complaint',
    status: 'draft',
    version: 3,
    content: 'Complaint content...',
    createdAt: '2024-01-12T10:00:00Z',
    updatedAt: '2024-01-18T16:00:00Z',
    ...overrides,
  };
}

export function createMockDeadline(overrides: Partial<Deadline> = {}): Deadline {
  return {
    id: 'dl-1',
    caseId: 'case-1',
    title: 'Evidence Deadline',
    type: 'evidence',
    dueDate: '2024-04-15',
    status: 'pending',
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z',
    ...overrides,
  };
}

export function createMockParty(overrides: Partial<Party> = {}): Party {
  return {
    id: 'party-1',
    caseId: 'case-1',
    name: 'Zhang San',
    role: 'plaintiff',
    phone: '13800138000',
    email: 'zhangsan@example.com',
    address: 'Beijing Chaoyang District',
    createdAt: '2024-01-10T10:00:00Z',
    updatedAt: '2024-01-10T10:00:00Z',
    ...overrides,
  };
}

export function createMockThread(overrides: Partial<CaseThread> = {}): CaseThread {
  return {
    id: 'thread-1',
    caseId: 'case-1',
    title: 'Loan Fact Dispute',
    description: 'Dispute over whether loan was actually made',
    status: 'active',
    priority: 'high',
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-02-01T14:00:00Z',
    ...overrides,
  };
}

export function createMockLetter(overrides: Partial<Letter> = {}): Letter {
  return {
    id: 1,
    case_id: 1,
    direction: 'outgoing',
    letter_type: 'lawyer_letter',
    title: 'Lawyer Letter',
    content_summary: 'Regarding...',
    recipient: 'Li Si',
    reply_required: 'optional',
    urgent_level: 'medium',
    is_overdue: false,
    is_replied: false,
    mail_status: 'sent',
    has_reply: false,
    created_at: '2024-01-25T10:00:00Z',
    updated_at: '2024-01-25T10:00:00Z',
    ...overrides,
  };
}

export function createMockTimelineEvent(overrides: Partial<TimelineEvent> = {}): TimelineEvent {
  return {
    id: 'tl-1',
    title: 'Case Filed',
    description: 'Court officially filed the case',
    date: '2024-01-15',
    type: 'filing',
    ...overrides,
  };
}

export function createMockHearing(overrides: Partial<Hearing> = {}): Hearing {
  return {
    id: 'hearing-1',
    caseId: 'case-1',
    courtName: 'Beijing Chaoyang Court Room 3',
    date: '2024-06-20',
    type: 'first',
    status: 'scheduled',
    judge: 'Judge Zhang',
    createdAt: '2024-03-01T10:00:00Z',
    updatedAt: '2024-03-01T10:00:00Z',
    ...overrides,
  };
}

export function createMockCaseProfile(overrides: Partial<ProfileSummary> = {}): ProfileSummary {
  return {
    case_id: 1,
    summary: {
      case_id: 1,
      completeness: { score: 75, level: '详细' },
      knowledge_stats: { total: 5, by_type: { fact: 3, evidence: 2 } },
      conversation_count: 3,
      evidence_count: 2,
      unresolved_gaps: [],
      last_updated: '2024-03-15T14:30:00Z',
    },
    recent_conversations: [],
    recent_knowledge: [],
    profile_tips: ['案件信息较完整，可以生成详细分析报告'],
    persisted: true,
    ...overrides,
  };
}

export function createMockIssue(overrides: Partial<Issue> = {}): Issue {
  return {
    id: 'issue-1',
    caseId: 'case-1',
    title: 'Loan delivery dispute',
    ourPosition: 'Loan was delivered via bank transfer',
    opponentAttack: 'May claim transfer was for different purpose',
    keyEvidence: ['ev-1', 'ev-2'],
    strategy: 'Provide bank certificate',
    priority: 'high',
    ...overrides,
  };
}

export function createMockSwotAnalysis(overrides: Partial<SwotAnalysis> = {}): SwotAnalysis {
  return {
    strengths: ['Bank transfer record', 'Loan contract'],
    weaknesses: ['Transfer note unclear'],
    opponentWeaknesses: ['No counter-evidence'],
    opponentStrengths: ['Experienced lawyer'],
    ...overrides,
  };
}

export function createMockAppeal(overrides: Partial<Appeal> = {}): Appeal {
  return {
    id: 1,
    case_id: 1,
    appeal_type: 'first_to_second',
    appeal_reason: 'factual_error',
    original_court: 'Beijing Chaoyang Court',
    original_judgment_date: '2024-06-01',
    appeal_deadline: '2024-08-15',
    status: 'preparing',
    is_overdue: false,
    created_at: '2024-07-01T10:00:00Z',
    updated_at: '2024-07-01T10:00:00Z',
    ...overrides,
  };
}

export function createMockExecution(overrides: Partial<Execution> = {}): Execution {
  return {
    case_id: 1,
    case_title: 'Loan Dispute',
    execution_amount: '500000',
    executed_amount: '0',
    remaining_amount: '500000',
    status: 'pending',
    progress: 0,
    total_records: 0,
    total_tasks: 0,
    todo_tasks: 0,
    in_progress_tasks: 0,
    completed_tasks: 0,
    total_assets: 0,
    controlled_assets: 0,
    disposed_assets: 0,
    stages: [],
    ...overrides,
  };
}

export const mockCases = {
  preparing: createMockCase({ id: 'case-1', status: 'preparing' }),
  closed: createMockCase({ id: 'case-2', status: 'closed', title: 'Closed Case' }),
  negotiating: createMockCase({ id: 'case-3', status: 'negotiating', title: 'Negotiating Case' }),
  litigating: createMockCase({ id: 'case-4', status: 'litigating', title: 'Litigating Case' }),
  appealing: createMockCase({ id: 'case-5', status: 'appealing', title: 'Appealing Case' }),
  executing: createMockCase({ id: 'case-6', status: 'executing', title: 'Executing Case' }),
};

export const mockEvidenceList: Evidence[] = [
  createMockEvidence({ id: 'ev-1', name: 'Loan Contract', credibilityScore: 85 }),
  createMockEvidence({ id: 'ev-2', name: 'Bank Transfer Record', credibilityScore: 90 }),
  createMockEvidence({ id: 'ev-3', name: 'WeChat Chat Record', credibilityScore: 60 }),
  createMockEvidence({ id: 'ev-4', name: 'Witness Testimony', credibilityScore: 70 }),
  createMockEvidence({ id: 'ev-5', name: 'Audio Evidence', credibilityScore: 30 }),
];

export const mockDeadlines: Deadline[] = [
  createMockDeadline({ id: 'dl-1', title: 'Evidence Deadline', dueDate: '2024-04-15', status: 'pending' }),
  createMockDeadline({ id: 'dl-2', title: 'Hearing Date', dueDate: '2024-06-20', status: 'pending' }),
  createMockDeadline({ id: 'dl-3', title: 'Defense Deadline', dueDate: '2024-02-15', status: 'completed' }),
  createMockDeadline({ id: 'dl-4', title: 'Appeal Deadline', dueDate: '2024-08-15', status: 'pending' }),
];

export const mockParties: Party[] = [
  createMockParty({ id: 'party-1', name: 'Zhang San', role: 'plaintiff' }),
  createMockParty({ id: 'party-2', name: 'Li Si', role: 'defendant' }),
  createMockParty({ id: 'party-3', name: 'Wang Wu', role: 'third_party' }),
  createMockParty({ id: 'party-4', name: 'Zhao Liu', role: 'counter_claimant' }),
];
