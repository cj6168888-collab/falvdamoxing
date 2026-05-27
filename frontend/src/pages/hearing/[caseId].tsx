import { HearingRecord } from '@/components/hearing/hearing-record';
import { useParams } from 'react-router-dom';
export default function HearingPage() {
  const { caseId } = useParams<{ caseId: string }>();
  return <HearingRecord caseId={caseId || ''} />;
}
