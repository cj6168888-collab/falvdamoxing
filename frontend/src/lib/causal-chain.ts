export interface CausalNode {
  id: string;
  label: string;
  type: 'evidence' | 'fact' | 'conclusion';
  source?: 'own' | 'opponent' | 'third_party';
  credibility?: number;
}

export interface CausalEdge {
  id: string;
  source: string;
  target: string;
  type: 'supports' | 'contradicts' | 'derives' | 'corroborates';
  label?: string;
}

export function buildCausalChain(nodes: CausalNode[], edges: CausalEdge[]): { nodes: CausalNode[]; edges: CausalEdge[] } {
  return { nodes, edges };
}

export function findPath(_nodes: CausalNode[], edges: CausalEdge[], fromId: string, toId: string): CausalEdge[] {
  const visited = new Set<string>();
  const path: CausalEdge[] = [];

  function dfs(currentId: string): boolean {
    if (currentId === toId) return true;
    visited.add(currentId);

    for (const edge of edges) {
      if (edge.source === currentId && !visited.has(edge.target)) {
        path.push(edge);
        if (dfs(edge.target)) return true;
        path.pop();
      }
    }
    return false;
  }

  dfs(fromId);
  return path;
}
