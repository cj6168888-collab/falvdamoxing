import { MeetingRecorder } from '@/components/meeting/meeting-recorder';
import { useParams } from 'react-router-dom';
export default function MeetingPage() {
  const { caseId } = useParams<{ caseId: string }>();
  return <MeetingRecorder caseId={caseId || ''} />;
}
