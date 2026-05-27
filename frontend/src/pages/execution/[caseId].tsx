import { ExecutionDashboard } from '@/components/execution/execution-dashboard';
import { useParams } from 'react-router-dom';
export default function ExecutionPage() {
  const { caseId } = useParams<{ caseId: string }>();
  return <ExecutionDashboard caseId={caseId || ''} />;
}
