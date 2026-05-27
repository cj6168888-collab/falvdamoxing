import { StageFlow } from '@/components/progress/stage-flow';
import { useParams } from 'react-router-dom';
export default function ProgressPage() {
  const { caseId } = useParams<{ caseId: string }>();
  return <StageFlow caseId={caseId || ''} />;
}
