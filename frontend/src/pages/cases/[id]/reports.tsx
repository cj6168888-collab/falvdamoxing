import { ReportList } from '@/components/report/report-list';
import { useParams } from 'react-router-dom';
export default function CaseReportsPage() {
  const { id } = useParams<{ id: string }>();
  return <ReportList caseId={id || ''} />;
}
