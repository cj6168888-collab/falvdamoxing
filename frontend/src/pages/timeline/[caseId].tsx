import { DeadlineManager } from '@/components/timeline/deadline-manager';
import { useParams } from 'react-router-dom';
export default function TimelinePage() {
  const { caseId } = useParams<{ caseId: string }>();
  return <DeadlineManager caseId={caseId || ''} />;
}
