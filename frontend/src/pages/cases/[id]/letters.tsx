import { LetterManager } from '@/components/timeline/letter-manager';
import { useParams } from 'react-router-dom';
export default function CaseLettersPage() {
  const { id } = useParams<{ id: string }>();
  return <LetterManager caseId={id || ''} />;
}
