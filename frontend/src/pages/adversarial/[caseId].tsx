import { AdversarialPanel } from '@/components/adversarial/adversarial-panel';
import { useParams } from 'react-router-dom';
export default function AdversarialPage() {
  const { caseId } = useParams<{ caseId: string }>();
  return <AdversarialPanel caseId={caseId || ''} />;
}
