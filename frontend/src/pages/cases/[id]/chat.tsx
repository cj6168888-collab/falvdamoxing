import { ChatContainer } from '@/components/chat/chat-container';
import { useParams } from 'react-router-dom';
export default function CaseChatPage() {
  const { id } = useParams<{ id: string }>();
  return <ChatContainer caseId={id || ''} />;
}
