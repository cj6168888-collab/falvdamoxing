import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageSquare } from 'lucide-react';
import type { ProfileSummary } from '@/types/profile.types';

interface Props {
  conversations: ProfileSummary['recent_conversations'];
}

const inputTypeLabels: Record<string, string> = {
  question: '提问',
  answer: '回答',
  evidence: '证据',
  upload: '上传',
  chat: '对话',
};

export function ConversationTimeline({ conversations }: Props) {
  if (!conversations || conversations.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>交互历史</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="py-8 text-center">
            <MessageSquare className="mx-auto mb-2 h-8 w-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">暂无交互记录</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>交互历史</span>
          <Badge variant="secondary">最近 {conversations.length} 条</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[280px] pr-4">
          <div className="space-y-4">
            {conversations.map((conv) => (
              <div key={conv.turn_id} className="relative border-l-2 border-muted pl-4 pb-4 last:pb-0">
                <div className="absolute -left-[5px] top-0 h-2.5 w-2.5 rounded-full bg-primary" />
                <div className="flex items-center justify-between">
                  <Badge variant="outline">{inputTypeLabels[conv.input_type] || conv.input_type}</Badge>
                  <span className="text-xs text-muted-foreground">
                    {new Date(conv.created_at).toLocaleString('zh-CN')}
                  </span>
                </div>
                <p className="mt-2 text-sm">{conv.user_input}</p>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
