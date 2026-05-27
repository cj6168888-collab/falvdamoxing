import { EvidenceGraph } from '@/components/evidence/evidence-graph';
import { useParams } from 'react-router-dom';
export default function EvidenceGraphPage() {
  const { caseId } = useParams<{ caseId: string }>();
  return <EvidenceGraph caseId={caseId || ''} />;
}
