import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Props {
  conversations: { id: string; title: string; updatedAt: string }[];
  onSelect: (id: string) => void;
}

export function ChatSidebar({ conversations, onSelect }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>对话历史</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {conversations.map((c) => (
          <button key={c.id} onClick={() => onSelect(c.id)} className="w-full text-left p-2 rounded hover:bg-muted">
            <p className="text-sm font-medium truncate">{c.title}</p>
            <p className="text-xs text-muted-foreground">{c.updatedAt}</p>
          </button>
        ))}
      </CardContent>
    </Card>
  );
}
