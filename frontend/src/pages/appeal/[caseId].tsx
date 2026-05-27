import { AppealOverview } from '@/components/appeal/appeal-overview';
import { useParams } from 'react-router-dom';
export default function AppealPage() {
  const { caseId } = useParams<{ caseId: string }>();
  return <AppealOverview caseId={caseId || ''} />;
}
