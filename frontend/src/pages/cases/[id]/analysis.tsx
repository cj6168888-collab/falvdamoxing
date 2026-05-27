import { AdversarialPanel } from '@/components/adversarial/adversarial-panel';
import { useParams } from 'react-router-dom';
export default function CaseAnalysisPage() {
  const { id } = useParams<{ id: string }>();
  return <AdversarialPanel caseId={id || ''} />;
}
