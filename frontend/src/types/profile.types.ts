export interface ProfileSummary {
  case_id: number;
  summary: {
    case_id: number;
    completeness: {
      score: number;
      level: string;
    };
    knowledge_stats: {
      total: number;
      by_type: Record<string, number>;
    };
    conversation_count: number;
    evidence_count: number;
    unresolved_gaps: Array<{
      id: string;
      type: string;
      status: string;
      severity: string;
    }>;
    last_updated: string;
  };
  recent_conversations: Array<{
    turn_id: string;
    turn_number: number;
    user_input: string;
    input_type: string;
    created_at: string;
  }>;
  recent_knowledge: Array<{
    atom_id: string;
    content: string;
    type: string;
    source: string;
    confidence: number;
    verified: boolean;
    keywords: string[];
    entity_tags: string[];
    extracted_at: string;
  }>;
  profile_tips: string[];
  persisted: boolean;
}

export interface KnowledgeGraphNode {
  id: string;
  label: string;
  type: string;
  color: string;
  verified: boolean;
  confidence: number;
}

export interface KnowledgeGraphEdge {
  source: string;
  target: string;
  type: string;
}

export interface KnowledgeGraphData {
  case_id: number;
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  stats: {
    total_nodes: number;
    total_edges: number;
    by_type: Record<string, number>;
  };
}

export interface EvidenceGap {
  case_id: number;
  unresolved_gaps: Array<{
    id: string;
    type: string;
    status: string;
    severity: string;
  }>;
  count: number;
}

export const completenessLevelMap: Record<string, { label: string; color: string; minScore: number }> = {
  '稀疏': { label: '稀疏', color: 'text-red-500', minScore: 0 },
  '基本': { label: '基本', color: 'text-yellow-500', minScore: 30 },
  '详细': { label: '详细', color: 'text-blue-500', minScore: 60 },
  '完整': { label: '完整', color: 'text-green-500', minScore: 80 },
};

export const knowledgeTypeLabels: Record<string, string> = {
  fact: '事实',
  evidence: '证据',
  claim: '主张',
  legal: '法律',
  relation: '关系',
};

export const knowledgeTypeColors: Record<string, string> = {
  fact: '#3b82f6',
  evidence: '#22c55e',
  claim: '#f59e0b',
  legal: '#8b5cf6',
  relation: '#ec4899',
};
