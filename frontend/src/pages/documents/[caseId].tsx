import { DocumentGenerator } from '@/components/document/document-generator';
import { useParams } from 'react-router-dom';
export default function DocumentsPage() {
  const { caseId } = useParams<{ caseId: string }>();
  return <DocumentGenerator caseId={caseId || ''} />;
}
