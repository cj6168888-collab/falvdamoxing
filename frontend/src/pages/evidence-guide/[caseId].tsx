import { EvidenceGuide } from '@/components/evidence/evidence-guide';
import { useParams } from 'react-router-dom';
export default function EvidenceGuidePage() {
  const { caseId } = useParams<{ caseId: string }>();
  return <EvidenceGuide caseId={caseId || ''} />;
}
