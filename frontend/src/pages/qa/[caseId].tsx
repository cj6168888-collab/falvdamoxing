import { ChatContainer } from '@/components/chat/chat-container';
import { useParams } from 'react-router-dom';
export default function QAPage() {
  const { caseId } = useParams<{ caseId: string }>();
  return <ChatContainer caseId={caseId || ''} />;
}
